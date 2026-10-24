import os
import random
import customtkinter as ctk
from PIL import Image
from utils.profile_manager import ProfileManager, AVATARS_DIR
from utils.room_code import encode_ip_to_code, get_local_ip
from network.room_server import RoomServer


class RoomView(ctk.CTkFrame):
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

        self.slot_frames = {}
        self.selected_first_player_id = None

        # --- GÓRNY PASEK ---
        self._build_top_bar()

        # --- KONTENER SLOTÓW ---
        self.slots_container = ctk.CTkFrame(self, fg_color="transparent")
        self.slots_container.pack(expand=True, fill="both", padx=15, pady=(0, 15))

        self._configure_grid_layout()
        self._build_slots()

        # --- OBSŁUGA SIECI ---
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
                    # Zawsze dołączamy aktualny config pokoju, aby klient znał max_players i nazwę pokoju
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
            except Exception as e:
                print(f"[ROOM VIEW] Błąd startu serwera: {e}")
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
                    self.client.send_action("JOIN_LOBBY", client_player_info)
                except Exception as e:
                    print(f"[ROOM VIEW] Błąd wysyłania JOIN_LOBBY: {e}")

    def _configure_grid_layout(self):
        """Konfiguruje wagi i kolumny siatki pod 2 (góra/dół), 3 (Piramida) lub 4 graczy."""
        self.slots_container.grid_columnconfigure(0, weight=1, uniform="slot_col")
        self.slots_container.grid_columnconfigure(1, weight=1, uniform="slot_col")
        self.slots_container.grid_rowconfigure(0, weight=1, uniform="slot_row")
        self.slots_container.grid_rowconfigure(1, weight=1, uniform="slot_row")

    def _get_slot_config(self, slot_idx):
        """Zwraca parametry układu (row, col, columnspan) dla wybranego slotu."""
        max_players = int(self.room_config.get("max_players", 4))

        if max_players == 2:
            pos = [(0, 0, 2), (1, 0, 2)]
        elif max_players == 3:
            pos = [(0, 0, 1), (0, 1, 1), (1, 0, 2)]
        else:
            pos = [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]

        return pos[slot_idx - 1] if slot_idx <= len(pos) else (0, 0, 1)

    def _build_top_bar(self):
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
        for widget in self.slots_container.winfo_children():
            widget.destroy()

        max_players = int(self.room_config.get("max_players", 4))

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
            self.slot_frames[idx] = slot

            slot_center = ctk.CTkFrame(slot, fg_color="transparent")
            slot_center.pack(expand=True)

            # Rysujemy Hosta w pierwszym slocie od razu przy starcie
            if idx == 1 and self.is_host:
                slot.configure(border_color="#00FF66", border_width=2, fg_color="#1A1A1A")
                lbl_badge = ctk.CTkLabel(slot, text="👑 HOST", font=("Segoe UI", 10, "bold"), text_color="#A0A0A0")
                lbl_badge.pack(pady=(8, 0))

                avatar_path = os.path.join(AVATARS_DIR, self.player_avatar)
                if os.path.exists(avatar_path):
                    try:
                        img = Image.open(avatar_path)
                        avatar_img = ctk.CTkImage(light_image=img, dark_image=img, size=(70, 70))
                        lbl_av = ctk.CTkLabel(slot_center, image=avatar_img, text="")
                        lbl_av.image = avatar_img
                        lbl_av.pack(pady=(0, 6))
                    except Exception:
                        pass

                lbl_nick = ctk.CTkLabel(slot_center, text=self.player_nick, font=("Segoe UI", 16, "bold"), text_color="#FFFFFF")
                lbl_nick.pack(pady=(0, 2))

                lbl_deck = ctk.CTkLabel(slot_center, text=f"Deck: {self.player_deck}", font=("Segoe UI", 12, "bold"),
                                        text_color="#00FF66")
                lbl_deck.pack(pady=(0, 2))

                if self.player_commander:
                    lbl_cmd = ctk.CTkLabel(slot_center, text=f"CMD: {self.player_commander}", font=("Segoe UI", 10, "italic"),
                                           text_color="#8A9BA8")
                    lbl_cmd.pack()
            else:
                lbl_slot_num = ctk.CTkLabel(slot_center, text=f"Slot {idx}", font=("Segoe UI", 14, "bold"),
                                            text_color="#555555")
                lbl_slot_num.pack(pady=(0, 4))

                lbl_wait = ctk.CTkLabel(slot_center, text="Waiting for player...", font=("Segoe UI", 12),
                                        text_color="#444444")
                lbl_wait.pack()

    def _update_lobby_ui(self, players):
        max_players = int(self.room_config.get("max_players", 4))

        for slot_idx in range(1, max_players + 1):
            if slot_idx not in self.slot_frames:
                continue

            slot = self.slot_frames[slot_idx]
            for child in slot.winfo_children():
                child.destroy()

            slot_center = ctk.CTkFrame(slot, fg_color="transparent")
            slot_center.pack(expand=True)

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

                border_col = "#FFD700" if is_first_player else ("#00FF66" if is_host_player else "#444444")
                slot.configure(
                    border_color=border_col,
                    border_width=2 if (is_host_player or is_first_player) else 1,
                    fg_color="#1A1A1A" if is_host_player else "#141414"
                )

                badge_text = "👑 FIRST PLAYER" if is_first_player else ("👑 HOST" if is_host_player else "")
                if badge_text:
                    badge_col = "#FFD700" if is_first_player else "#A0A0A0"
                    lbl_badge = ctk.CTkLabel(slot, text=badge_text, font=("Segoe UI", 10, "bold"), text_color=badge_col)
                    lbl_badge.pack(pady=(8, 0))

                avatar_path = os.path.join(AVATARS_DIR, p_avatar)
                if os.path.exists(avatar_path):
                    try:
                        img = Image.open(avatar_path)
                        avatar_img = ctk.CTkImage(light_image=img, dark_image=img, size=(70, 70))
                        lbl_av = ctk.CTkLabel(slot_center, image=avatar_img, text="")
                        lbl_av.image = avatar_img
                        lbl_av.pack(pady=(0, 6))
                    except Exception:
                        pass

                lbl_nick = ctk.CTkLabel(slot_center, text=p_nick, font=("Segoe UI", 16, "bold"), text_color="#FFFFFF")
                lbl_nick.pack(pady=(0, 2))

                lbl_deck = ctk.CTkLabel(slot_center, text=f"Deck: {p_deck}", font=("Segoe UI", 12, "bold"),
                                        text_color="#00FF66")
                lbl_deck.pack(pady=(0, 2))

                if p_cmd:
                    lbl_cmd = ctk.CTkLabel(slot_center, text=f"CMD: {p_cmd}", font=("Segoe UI", 10, "italic"),
                                           text_color="#8A9BA8")
                    lbl_cmd.pack()
            else:
                slot.configure(border_color="#222222", border_width=1, fg_color="#141414")
                lbl_slot_num = ctk.CTkLabel(slot_center, text=f"Slot {slot_idx}", font=("Segoe UI", 14, "bold"),
                                            text_color="#555555")
                lbl_slot_num.pack(pady=(0, 4))

                lbl_wait = ctk.CTkLabel(slot_center, text="Waiting for player...", font=("Segoe UI", 12),
                                        text_color="#444444")
                lbl_wait.pack()

    def roll_first_player_action(self):
        if not self.is_host or not hasattr(self, "server") or not self.server:
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

        self._show_first_player_announcement(chosen_player.get("name"))
        self._update_lobby_ui(players)

    def _show_first_player_announcement(self, player_name):
        if hasattr(self, "btn_roll_first"):
            original_text = "🎲 ROLL FIRST PLAYER"
            self.btn_roll_first.configure(text=f"FIRST: {player_name} 👑", text_color="#FFD700")
            self.after(3000, lambda: self.btn_roll_first.configure(text=original_text, text_color="#FFFFFF"))

    def _on_client_message(self, message):
        msg_type = message.get("type")

        if msg_type == "LOBBY_UPDATE":
            players = message.get("players", [])
            if "config" in message:
                self.room_config.update(message.get("config", {}))
                self.room_name = self.room_config.get("name", self.room_name)
                self.room_title.configure(text=f"ROOM: {self.room_name}  [{self.game_format}]")
                self._configure_grid_layout()
                self._build_slots()
            self.after(0, lambda: self._update_lobby_ui(players))

        elif msg_type == "FIRST_PLAYER_ROLLED":
            self.selected_first_player_id = message.get("player_id")
            p_name = message.get("player_name")
            self.after(0, lambda: self._show_first_player_announcement(p_name))

        elif msg_type == "START_GAME":
            room_data = message.get("room_config", self.room_config)
            if hasattr(self.master, "launch_game_overlay"):
                self.after(0, lambda: self.master.launch_game_overlay(room_data))

        elif msg_type == "ROOM_CLOSED":
            if self.client:
                self.client.disconnect()
            if hasattr(self.master, "show_menu"):
                self.after(0, self.master.show_menu)

    def copy_room_code(self):
        self.clipboard_clear()
        self.clipboard_append(self.room_code)

        default_text = f"CODE: {self.room_code}  📋"
        self.btn_copy_code.configure(text="COPIED TO CLIPBOARD! ✓", text_color="#FFFFFF")
        self.after(2000, lambda: self.btn_copy_code.configure(text=default_text, text_color="#00FF66"))

    def start_match(self):
        if self.is_host and hasattr(self, "server") and self.server:
            game_data = {
                "config": self.room_config,
                "players": self.server.players_data,
                "first_player_id": self.selected_first_player_id
            }
            self.server.broadcast({"type": "START_GAME", "room_config": game_data})

            if hasattr(self.master, "launch_game_overlay"):
                self.master.launch_game_overlay(game_data)

    def leave_room(self):
        if self.is_host and hasattr(self, "server") and self.server:
            self.server.stop()
        elif self.client:
            self.client.disconnect()

        if hasattr(self.master, "show_menu"):
            self.master.show_menu()