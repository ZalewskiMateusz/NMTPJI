# gui/room_view.py
import os
import random
import threading
import requests
import customtkinter as ctk
from PIL import Image

from utils.profile_manager import ProfileManager, AVATARS_DIR
from utils.room_code import encode_ip_to_code, get_local_ip
from network.room_server import RoomServer
from network.sync_client import SyncClient
from database.db_manager import DBManager
from core.scryfall import ScryfallAPI

CACHE_DIR = "cache/card_images"


class CardPreviewTooltip(ctk.CTkToplevel):
    """Floating popup displaying a full-sized commander card preview on hover."""
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#1E1E1E")
        self.withdraw()

        self.lbl_image = ctk.CTkLabel(self, text="", fg_color="transparent")
        self.lbl_image.pack(padx=2, pady=2)

    def show_image(self, img_path, x, y):
        """Renders the preview image cleanly at specified screen coordinates without system frames."""
        if img_path and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path)
                # Full MTG card size preview
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(240, 336))
                self.lbl_image.configure(image=ctk_img, text="")
                self.lbl_image.image = ctk_img
            except Exception:
                self.lbl_image.configure(image="", text="Error loading image")
        else:
            self.lbl_image.configure(image="", text="No Image")

        # Offset down and right from cursor to avoid clipping
        self.geometry(f"+{x + 15}+{y + 15}")
        self.deiconify()

    def hide(self):
        """Hides the floating tooltip window."""
        self.withdraw()


class DeckSelectionModal(ctk.CTkToplevel):
    """Small popup modal allowing the player to switch their active deck in the lobby."""
    def __init__(self, parent, on_deck_selected_callback):
        super().__init__(parent)
        self.on_deck_selected_callback = on_deck_selected_callback

        self.title("Change Deck")
        self.geometry("320x380")
        self.attributes("-topmost", True)
        self.focus_force()

        lbl_title = ctk.CTkLabel(self, text="Select New Deck", font=("Segoe UI", 14, "bold"), text_color="#00FF66")
        lbl_title.pack(pady=(15, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1A1A1A", width=280, height=240, corner_radius=8)
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.load_decks()

    def load_decks(self):
        """Loads all available user decks from the database into the selection list."""
        deck_names = DBManager.get_all_deck_names()
        if not deck_names:
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text="No decks found in database.", text_color="#666666")
            lbl_empty.pack(pady=20)
            return

        for name in deck_names:
            btn = ctk.CTkButton(
                self.scroll_frame,
                text=name,
                font=("Segoe UI", 13),
                fg_color="#252525",
                hover_color="#333333",
                anchor="w",
                height=32,
                corner_radius=6,
                command=lambda d=name: self.select_deck(d)
            )
            btn.pack(fill="x", pady=3, padx=5)

    def select_deck(self, deck_name):
        """Handles selection of a deck and triggers the callback."""
        deck_info = DBManager.get_deck_by_name(deck_name)
        if deck_info:
            self.on_deck_selected_callback(
                deck_name=deck_info.get("name", deck_name),
                commander=deck_info.get("commander", "")
            )
        self.destroy()


class RoomView(ctk.CTkFrame):
    """
    Multiplayer game room lobby view managing player slots, network synchronization,
    room configuration, and real-time deck switching.
    """
    def __init__(
            self,
            master,
            room_config=None,
            player_nick=None,
            avatar_filename=None,
            deck_name=None,
            commander=None,
            is_host=True,
            client=None
    ):
        super().__init__(master, fg_color="#121212")
        self.room_config = room_config or {}
        self.is_host = is_host
        self.client = client
        self.server = None

        self.tooltip = CardPreviewTooltip(self)

        host_ip = get_local_ip()
        self.room_code = encode_ip_to_code(host_ip)

        profile = ProfileManager.load_profile()
        self.player_nick = player_nick or profile.get("nickname", "HOST")
        self.player_avatar = avatar_filename or profile.get("avatar_filename", "jace.png")
        self.player_deck = (
                deck_name
                or self.room_config.get("selected_deck")
                or "Selected Deck"
        )
        self.player_commander = commander or self.room_config.get("commander", "")
        self.game_format = self.room_config.get("format", "Commander / EDH")
        self.room_name = self.room_config.get("name", "Commander Room")

        self.slot_widgets = {}
        self.selected_first_player_id = None

        # --- TOP BAR ---
        self._build_top_bar()

        # --- SLOTS CONTAINER ---
        self.slots_container = ctk.CTkFrame(self, fg_color="transparent")
        self.slots_container.pack(expand=True, fill="both", padx=15, pady=(0, 15))

        self._configure_grid_layout()
        self._build_slots()

        # --- NETWORK SETUP ---
        if self.is_host:
            self.server = RoomServer()
            host_player_info = {
                "id": f"p_{self.player_nick}",
                "name": self.player_nick,
                "deck": self.player_deck,
                "commander": self.player_commander,
                "avatar": self.player_avatar,
                "is_host": True
            }
            try:
                self.server.start(host_player_info)

                original_broadcast = self.server.broadcast

                def broadcast_and_update_host(msg):
                    if isinstance(msg, dict):
                        msg["config"] = self.room_config
                    original_broadcast(msg)

                    if isinstance(msg, dict):
                        msg_type = msg.get("type")
                        if msg_type == "LOBBY_UPDATE":
                            players = msg.get("players", [])
                            self.after(0, lambda: self._update_lobby_ui(players))
                        elif msg_type == "FIRST_PLAYER_ROLLED":
                            p_name = msg.get("player_name")
                            self.selected_first_player_id = msg.get("player_id")
                            self.after(0, lambda: self._show_first_player_announcement(p_name))

                self.server.broadcast = broadcast_and_update_host

                self.client = SyncClient(on_message_received=self._on_client_message)
                if self.client.connect("127.0.0.1", port=5555):
                    self.client.send_join(host_player_info)

            except Exception as e:
                print(f"[ROOM VIEW] Host server/client start error: {e}")
        else:
            if self.client:
                self.client.on_message_received = self._on_client_message
                client_player_info = {
                    "id": f"p_{self.player_nick}",
                    "name": self.player_nick,
                    "deck": self.player_deck,
                    "commander": self.player_commander,
                    "avatar": self.player_avatar,
                    "is_host": False
                }
                try:
                    self.client.send_join(client_player_info)
                except Exception as e:
                    print(f"[ROOM VIEW] Error sending JOIN: {e}")

    def _configure_grid_layout(self):
        """Configures responsive grid layout for player slots."""
        self.slots_container.grid_columnconfigure(0, weight=1, uniform="slot_col")
        self.slots_container.grid_columnconfigure(1, weight=1, uniform="slot_col")
        self.slots_container.grid_rowconfigure(0, weight=1, uniform="slot_row")
        self.slots_container.grid_rowconfigure(1, weight=1, uniform="slot_row")

    def _get_slot_config(self, slot_idx):
        """Returns grid placement rules depending on max players configuration."""
        max_players = int(self.room_config.get("max_players", 4))

        if max_players == 2:
            pos = [(0, 0, 2), (1, 0, 2)]
        elif max_players == 3:
            pos = [(0, 0, 1), (0, 1, 1), (1, 0, 2)]
        else:
            pos = [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]

        return pos[slot_idx - 1] if slot_idx <= len(pos) else (0, 0, 1)

    def _build_top_bar(self):
        """Builds top control bar with room info, invite code, start and leave actions."""
        self.top_bar = ctk.CTkFrame(self, fg_color="#1E1E1E", height=50, corner_radius=8)
        self.top_bar.pack(fill="x", padx=15, pady=(15, 10))

        self.room_title = ctk.CTkLabel(
            self.top_bar,
            text=f"ROOM: {self.room_name}  [{self.game_format}]",
            font=("Segoe UI", 15, "bold"),
            text_color="#00FF66"
        )
        self.room_title.pack(side="left", padx=20, pady=10)

        if self.is_host:
            self.btn_copy_code = ctk.CTkButton(
                self.top_bar,
                text=f"CODE: {self.room_code}  📋",
                font=("Segoe UI", 12, "bold"),
                fg_color="#2B2B2B",
                hover_color="#3A3A3A",
                border_color="#00FF66",
                border_width=1,
                text_color="#00FF66",
                height=32,
                command=self.copy_room_code
            )
            self.btn_copy_code.pack(side="left", padx=10)

            self.btn_roll_first = ctk.CTkButton(
                self.top_bar,
                text="🎲 ROLL FIRST PLAYER",
                font=("Segoe UI", 11, "bold"),
                fg_color="#2B2B2B",
                hover_color="#3A3A3A",
                border_color="#1F6AA5",
                border_width=1,
                text_color="#FFFFFF",
                height=32,
                command=self.roll_first_player_action
            )
            self.btn_roll_first.pack(side="left", padx=10)

        self.top_buttons_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.top_buttons_frame.pack(side="right", padx=15, pady=9)

        if self.is_host:
            self.btn_start_top = ctk.CTkButton(
                self.top_buttons_frame,
                text="START GAME",
                font=("Segoe UI", 11, "bold"),
                fg_color="#1F6AA5",
                hover_color="#144870",
                height=32,
                command=self.start_match
            )
            self.btn_start_top.pack(side="left", padx=(0, 10))
        else:
            lbl_waiting = ctk.CTkLabel(
                self.top_buttons_frame,
                text="Waiting for host to start...",
                font=("Segoe UI", 11, "italic"),
                text_color="#8A9BA8"
            )
            lbl_waiting.pack(side="left", padx=(0, 15))

        self.btn_leave = ctk.CTkButton(
            self.top_buttons_frame,
            text="LEAVE ROOM",
            font=("Segoe UI", 11, "bold"),
            fg_color="#2B2B2B",
            hover_color="#5A1E1E",
            height=32,
            command=self.leave_room
        )
        self.btn_leave.pack(side="left")

    def _build_slots(self):
        """Initializes empty player slots in the grid container once to prevent layout destruction bugs."""
        for widget in self.slots_container.winfo_children():
            widget.destroy()

        max_players = int(self.room_config.get("max_players", 4))
        self.slot_widgets = {}

        for idx in range(1, max_players + 1):
            r, c, c_span = self._get_slot_config(idx)
            padx_val = (120, 120) if (max_players == 3 and idx == 3) else 8

            slot = ctk.CTkFrame(
                self.slots_container,
                fg_color="#141414",
                border_color="#222222",
                border_width=1,
                corner_radius=12
            )
            slot.grid(row=r, column=c, columnspan=c_span, sticky="nsew", padx=padx_val, pady=8)

            slot_center = ctk.CTkFrame(slot, fg_color="transparent")
            slot_center.pack(expand=True, padx=10, pady=5)

            # References to internal slot elements for safe in-place updating
            lbl_badge = ctk.CTkLabel(slot_center, text="", font=("Segoe UI", 10, "bold"))
            lbl_badge.pack(pady=(2, 0))

            lbl_avatar = ctk.CTkLabel(slot_center, text="", width=45, height=45)
            lbl_avatar.pack(pady=(0, 2))

            lbl_nick = ctk.CTkLabel(slot_center, text=f"Slot {idx}", font=("Segoe UI", 14, "bold"), text_color="#555555")
            lbl_nick.pack(pady=(0, 2))

            deck_row = ctk.CTkFrame(slot_center, fg_color="transparent")
            deck_row.pack(pady=(0, 2))

            lbl_deck = ctk.CTkLabel(deck_row, text="Waiting for player...", font=("Segoe UI", 11), text_color="#444444")
            lbl_deck.pack(side="left", padx=(0, 5))

            # Isolated container for the change button
            btn_wrapper = ctk.CTkFrame(deck_row, fg_color="transparent", width=55, height=22)
            btn_wrapper.pack(side="left", padx=2)
            btn_wrapper.pack_propagate(False)

            btn_change_deck = ctk.CTkButton(
                btn_wrapper,
                text="Change",
                width=50,
                height=20,
                font=("Segoe UI", 9, "bold"),
                fg_color="#1F6AA5",
                hover_color="#144870",
                command=self.open_deck_change_modal
            )
            btn_change_deck.place(relx=0.5, rely=0.5, anchor="center")
            btn_change_deck.pack_forget()

            lbl_cmd = ctk.CTkLabel(slot_center, text="", font=("Segoe UI", 10, "italic"), text_color="#8A9BA8")
            lbl_cmd.pack(pady=(0, 2))

            img_lbl = ctk.CTkLabel(
                slot_center,
                text="No Commander",
                fg_color="#1E1E1E",
                text_color="#666666",
                corner_radius=6,
                width=120,
                height=168,
                font=("Segoe UI", 9)
            )
            img_lbl.pack(pady=(2, 0))

            self.slot_widgets[idx] = {
                "frame": slot,
                "badge": lbl_badge,
                "avatar": lbl_avatar,
                "nick": lbl_nick,
                "deck": lbl_deck,
                "btn_change": btn_change_deck,
                "btn_wrapper": btn_wrapper,
                "cmd": lbl_cmd,
                "img_lbl": img_lbl
            }

    def _update_lobby_ui(self, players):
        """Safely updates existing player slots in-place with new data without destroying widgets."""
        max_players = int(self.room_config.get("max_players", 4))

        for slot_idx in range(1, max_players + 1):
            if slot_idx not in self.slot_widgets:
                continue

            widgets = self.slot_widgets[slot_idx]
            slot = widgets["frame"]
            lbl_badge = widgets["badge"]
            lbl_avatar = widgets["avatar"]
            lbl_nick = widgets["nick"]
            lbl_deck = widgets["deck"]
            btn_change = widgets["btn_change"]
            btn_wrapper = widgets["btn_wrapper"]
            lbl_cmd = widgets["cmd"]
            img_lbl = widgets["img_lbl"]

            player_data_idx = slot_idx - 1
            if player_data_idx < len(players):
                p_info = players[player_data_idx]
                p_id = p_info.get("id")
                p_nick = p_info.get("name", f"Player {slot_idx}")
                p_deck = p_info.get("deck", "Unknown Deck")
                p_cmd = p_info.get("commander", "")
                p_avatar = p_info.get("avatar", "jace.png")
                is_host_player = p_info.get("is_host", False) or player_data_idx == 0
                is_first_player = (p_id == self.selected_first_player_id)
                is_local_player = (p_nick == self.player_nick)

                # Frame styling
                border_col = "#FFD700" if is_first_player else ("#00FF66" if is_host_player else "#444444")
                slot.configure(
                    border_color=border_col,
                    border_width=2 if (is_host_player or is_first_player) else 1,
                    fg_color="#1A1A1A" if is_host_player else "#141414"
                )

                # Badge
                badge_text = "👑 FIRST PLAYER" if is_first_player else ("👑 HOST" if is_host_player else "")
                if badge_text:
                    badge_col = "#FFD700" if is_first_player else "#A0A0A0"
                    lbl_badge.configure(text=badge_text, text_color=badge_col)
                else:
                    lbl_badge.configure(text="")

                # Avatar
                avatar_path = os.path.join(AVATARS_DIR, p_avatar)
                if os.path.exists(avatar_path):
                    try:
                        img = Image.open(avatar_path)
                        avatar_img = ctk.CTkImage(light_image=img, dark_image=img, size=(45, 45))
                        lbl_avatar.configure(image=avatar_img, text="")
                        lbl_avatar.image = avatar_img
                    except Exception:
                        lbl_avatar.configure(image="", text="")

                # Nickname & Deck
                lbl_nick.configure(text=p_nick, text_color="#FFFFFF")
                lbl_deck.configure(text=f"Deck: {p_deck}", text_color="#00FF66")

                # Change deck button visibility for local player
                if is_local_player:
                    btn_wrapper.pack(side="left", padx=2)
                    btn_change.place(relx=0.5, rely=0.5, anchor="center")
                else:
                    btn_change.place_forget()
                    btn_wrapper.pack_forget()

                # Commander info
                if p_cmd:
                    lbl_cmd.configure(text=f"CMD: {p_cmd}")
                    img_lbl.configure(text="Loading Card...")
                    self._load_slot_commander_image(p_cmd, img_lbl)
                else:
                    lbl_cmd.configure(text="")
                    img_lbl.configure(text="No Commander", image="")

            else:
                # Empty slot fallback
                slot.configure(border_color="#222222", border_width=1, fg_color="#141414")
                lbl_badge.configure(text="")
                lbl_avatar.configure(image="", text="")
                lbl_nick.configure(text=f"Slot {slot_idx}", text_color="#555555")
                lbl_deck.configure(text="Waiting for player...", text_color="#444444")
                btn_change.place_forget()
                btn_wrapper.pack_forget()
                lbl_cmd.configure(text="")
                img_lbl.configure(text="No Commander", image="")

    def open_deck_change_modal(self):
        """Opens the modal to pick a new deck."""
        DeckSelectionModal(self, on_deck_selected_callback=self.on_new_deck_chosen)

    def on_new_deck_chosen(self, deck_name, commander):
        """Callback triggered upon selecting a new deck, synchronizing state over network."""
        self.player_deck = deck_name
        self.player_commander = commander

        if self.client:
            updated_info = {
                "id": f"p_{self.player_nick}",
                "name": self.player_nick,
                "deck": self.player_deck,
                "commander": self.player_commander,
                "avatar": self.player_avatar,
                "is_host": self.is_host
            }
            self.client.send_join(updated_info)

    def _load_slot_commander_image(self, commander_name, target_label):
        """Asynchronously or synchronously loads commander image with strict lifecycle checks."""
        if not commander_name:
            try:
                if target_label.winfo_exists():
                    target_label.configure(image="", text="No Commander")
            except Exception:
                pass
            return

        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        safe_name = "".join(c for c in commander_name if c.isalnum() or c in (' ', '_')).rstrip()
        file_path = os.path.join(CACHE_DIR, f"{safe_name}.jpg")

        # Synchronous load from cache if available
        if os.path.exists(file_path):
            try:
                pil_img = Image.open(file_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(120, 168))
                if target_label.winfo_exists():
                    target_label.configure(image=ctk_img, text="")
                    target_label.image = ctk_img
                    target_label.bind("<Enter>", lambda e: self.tooltip.show_image(file_path, e.x_root, e.y_root))
                    target_label.bind("<Leave>", lambda e: self.tooltip.hide())
                return
            except Exception:
                pass

        try:
            if target_label.winfo_exists():
                target_label.configure(text="Loading...", image="")
        except Exception:
            return

        def _fetch_thread():
            img_url = None
            try:
                if hasattr(ScryfallAPI, "get_card_image_url"):
                    img_url = ScryfallAPI.get_card_image_url(commander_name)
                elif hasattr(ScryfallAPI, "get_card_image_path"):
                    img_url = ScryfallAPI.get_card_image_path(commander_name)
            except Exception:
                img_url = None

            downloaded_path = None
            if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                try:
                    res = requests.get(img_url, timeout=5)
                    if res.status_code == 200:
                        with open(file_path, "wb") as f:
                            f.write(res.content)
                        downloaded_path = file_path
                except Exception:
                    downloaded_path = None
            else:
                downloaded_path = img_url if (img_url and os.path.exists(img_url)) else None

            try:
                if target_label.winfo_exists():
                    target_label.after(0, lambda: self._update_slot_image_widget(downloaded_path, target_label))
            except Exception:
                pass

        threading.Thread(target=_fetch_thread, daemon=True).start()

    def _update_slot_image_widget(self, file_path, target_label):
        """Safely updates target label with downloaded image and binds hover preview events."""
        try:
            if not target_label.winfo_exists():
                return
        except Exception:
            return

        if file_path and os.path.exists(file_path):
            try:
                pil_img = Image.open(file_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(120, 168))

                if target_label.winfo_exists():
                    target_label.configure(image=ctk_img, text="")
                    target_label.image = ctk_img

                    target_label.bind("<Enter>", lambda e: self.tooltip.show_image(file_path, e.x_root, e.y_root))
                    target_label.bind("<Leave>", lambda e: self.tooltip.hide())
            except Exception:
                pass
        else:
            try:
                if target_label.winfo_exists():
                    target_label.configure(image="", text="No Image")
            except Exception:
                pass

    def roll_first_player_action(self):
        """Rolls a random first player among connected participants (Host only)."""
        if not self.is_host or not self.server:
            return

        players = self.server.players_data
        if not players:
            return

        chosen_player = random.choice(players)
        self.selected_first_player_id = chosen_player.get("id")

        self.server.broadcast({
            "type": "FIRST_PLAYER_ROLLED",
            "player_id": chosen_player.get("id"),
            "player_name": chosen_player.get("name")
        })

    def _show_first_player_announcement(self, player_name):
        """Displays visual banner when first player is rolled."""
        if hasattr(self, "btn_roll_first"):
            original_text = "🎲 ROLL FIRST PLAYER"
            self.btn_roll_first.configure(text=f"FIRST: {player_name} 👑", text_color="#FFD700")
            self.after(3000, lambda: self.btn_roll_first.configure(text=original_text, text_color="#FFFFFF"))

    def _on_client_message(self, message):
        """Handles incoming messages from the synchronization server."""
        msg_type = message.get("type")

        if msg_type == "LOBBY_UPDATE":
            players = message.get("players", [])
            if "config" in message:
                self.room_config.update(message.get("config", {}))
                self.room_name = self.room_config.get("name", self.room_name)
                self.room_title.configure(text=f"ROOM: {self.room_name}  [{self.game_format}]")
            self.after(0, lambda: self._update_lobby_ui(players))

        elif msg_type == "FIRST_PLAYER_ROLLED":
            self.selected_first_player_id = message.get("player_id")
            p_name = message.get("player_name")
            self.after(0, lambda: self._show_first_player_announcement(p_name))

        elif msg_type == "START_GAME":
            room_data = message.get("room_config", self.room_config)
            room_data["client"] = self.client
            room_data["is_host"] = self.is_host
            if hasattr(self.master, "launch_game_overlay"):
                self.after(0, lambda: self.master.launch_game_overlay(room_data))

        elif msg_type == "ROOM_CLOSED":
            if self.client:
                self.client.disconnect()
            if hasattr(self.master, "show_menu"):
                self.after(0, self.master.show_menu)

    def copy_room_code(self):
        """Copies room code to system clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.room_code)

        default_text = f"CODE: {self.room_code}  📋"
        self.btn_copy_code.configure(text="COPIED TO CLIPBOARD! ✓", text_color="#FFFFFF")
        self.after(2000, lambda: self.btn_copy_code.configure(text=default_text, text_color="#00FF66"))

    def start_match(self):
        """Initiates game match start sequence (Host only)."""
        if self.is_host and self.client:
            if self.server and self.server.players_data:
                self.server.players_data[0]["avatar"] = self.player_avatar
                self.server.players_data[0]["name"] = self.player_nick
                self.server.players_data[0]["deck"] = self.player_deck
                self.server.players_data[0]["commander"] = self.player_commander

            game_data = {
                "config": self.room_config,
                "players": self.server.players_data if self.server else [],
                "first_player_id": self.selected_first_player_id,
                "is_host": True
            }
            self.client.send({
                "type": "START_GAME",
                "first_player_id": self.selected_first_player_id,
                "room_config": game_data
            })

    def leave_room(self):
        """Disconnects from room and returns to main menu."""
        if self.is_host and self.server:
            self.server.stop()
        elif self.client:
            self.client.disconnect()

        if hasattr(self.master, "show_menu"):
            self.master.show_menu()