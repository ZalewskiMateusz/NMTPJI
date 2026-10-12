import os
import customtkinter as ctk
from database.db_manager import DBManager
from network.sync_client import SyncClient
from utils.profile_manager import ProfileManager
from utils.room_code import decode_code_to_ip

FONT_PATH = os.path.join("assets", "fonts", "Kanisah.ttf")
if os.path.exists(FONT_PATH):
    ctk.FontManager.load_font(FONT_PATH)


class JoinRoomView(ctk.CTkFrame):
    def __init__(self, master, on_start_game_callback=None, on_back_callback=None):
        super().__init__(master, fg_color="#121212")
        self.on_start_game_callback = on_start_game_callback
        self.on_back_callback = on_back_callback

        self.client = SyncClient(on_message_received=self._on_server_message)
        self.players = []

        self._build_ui()

    def _build_ui(self):
        self.card = ctk.CTkFrame(
            self,
            fg_color="#1E1E1E",
            border_color="#00E676",
            border_width=2,
            corner_radius=16,
            width=420
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        lbl_title = ctk.CTkLabel(
            self.card,
            text="JOIN GAME ROOM",
            font=("Kanisah", 28, "bold"),
            text_color="#FFFFFF"
        )
        lbl_title.pack(pady=(25, 2))

        lbl_subtitle = ctk.CTkLabel(
            self.card,
            text="ENTER LOBBY DETAILS",
            font=("Segoe UI", 10, "bold"),
            text_color="#8A9BA8"
        )
        lbl_subtitle.pack(pady=(0, 20))

        # 1. Host IP / Room Code
        ctk.CTkLabel(self.card, text="Host IP Address / Room Code", font=("Segoe UI", 11), text_color="#CCCCCC").pack(
            anchor="w", padx=30)
        self.entry_ip = ctk.CTkEntry(
            self.card,
            placeholder_text="e.g. RAVNICA-SOLRING-ATRAXA-SCRY",
            fg_color="#2B2B2B",
            border_color="#333333",
            height=38
        )
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.pack(fill="x", padx=30, pady=(4, 12))

        # 2. Password
        ctk.CTkLabel(self.card, text="Password (Optional)", font=("Segoe UI", 11), text_color="#CCCCCC").pack(
            anchor="w", padx=30)
        self.entry_password = ctk.CTkEntry(
            self.card,
            placeholder_text="Enter password if required",
            show="*",
            fg_color="#2B2B2B",
            border_color="#333333",
            height=38
        )
        self.entry_password.pack(fill="x", padx=30, pady=(4, 12))

        # 3. Select Deck
        saved_decks = DBManager.get_all_deck_names() or ["Mój Deck"]
        ctk.CTkLabel(self.card, text="Select Deck", font=("Segoe UI", 11), text_color="#CCCCCC").pack(anchor="w",
                                                                                                      padx=30)
        self.combo_decks = ctk.CTkOptionMenu(
            self.card,
            values=saved_decks,
            fg_color="#2B2B2B",
            button_color="#333333",
            button_hover_color="#444444",
            height=38,
            command=self._on_deck_selected
        )
        self.combo_decks.pack(fill="x", padx=30, pady=(4, 12))

        # 4. Select Commander
        ctk.CTkLabel(self.card, text="Select Commander", font=("Segoe UI", 11), text_color="#CCCCCC").pack(anchor="w",
                                                                                                           padx=30)
        self.combo_commander = ctk.CTkOptionMenu(
            self.card,
            values=["Aftermath Analyst"],
            fg_color="#2B2B2B",
            button_color="#333333",
            button_hover_color="#444444",
            height=38
        )
        self.combo_commander.pack(fill="x", padx=30, pady=(4, 20))

        self._on_deck_selected(self.combo_decks.get())

        self.lbl_status = ctk.CTkLabel(self.card, text="", font=("Segoe UI", 11), text_color="#FF5252")
        self.lbl_status.pack(pady=(0, 5))

        btn_container = ctk.CTkFrame(self.card, fg_color="transparent")
        btn_container.pack(fill="x", padx=30, pady=(0, 25))

        self.btn_join = ctk.CTkButton(
            btn_container,
            text="JOIN ROOM",
            font=("Segoe UI", 13, "bold"),
            fg_color="transparent",
            border_color="#00E676",
            border_width=2,
            hover_color="#00C853",
            text_color="#FFFFFF",
            height=42,
            command=self._join_room_action
        )
        self.btn_join.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self.btn_cancel = ctk.CTkButton(
            btn_container,
            text="CANCEL",
            font=("Segoe UI", 13, "bold"),
            fg_color="#2B2B2B",
            border_color="#D32F2F",
            border_width=1,
            hover_color="#B71C1C",
            text_color="#FFFFFF",
            height=42,
            command=self._go_back
        )
        self.btn_cancel.pack(side="right", expand=True, fill="x", padx=(8, 0))

    def _on_deck_selected(self, selected_deck_name):
        deck_data = DBManager.get_deck_by_name(selected_deck_name)
        if deck_data and "commander" in deck_data:
            cmdr = deck_data["commander"]
            self.combo_commander.configure(values=[cmdr])
            self.combo_commander.set(cmdr)
        else:
            self.combo_commander.configure(values=["Aftermath Analyst"])
            self.combo_commander.set("Aftermath Analyst")

    def _join_room_action(self):
        raw_code = self.entry_ip.get().strip()
        password = self.entry_password.get().strip()

        profile = ProfileManager.load_profile()
        nick = profile.get("nickname", "Player")
        avatar = profile.get("avatar_filename", "jace.png")

        selected_deck = self.combo_decks.get()
        selected_cmdr = self.combo_commander.get()

        if not raw_code:
            self.lbl_status.configure(text="Please enter IP address or Room Code!")
            return

        target_ip = decode_code_to_ip(raw_code)
        self.lbl_status.configure(text=f"Connecting to {target_ip}...", text_color="#00E676")

        # 1. Łączymy gniazdo TCP
        if self.client.connect(target_ip):
            player_info = {
                "id": f"p_{nick}",
                "name": nick,
                "deck": selected_deck,
                "commander": selected_cmdr,
                "avatar": avatar,
                "password": password,
                "is_host": False
            }

            # 2. PRZEŁĄCZAMY EKRAN U KLIENTA NA ROOMVIEW (LOBBY)
            # Sprawdź w main.py / app.py jak dokładnie nazywa się ta metoda u Ciebie na masterze!
            if hasattr(self.master, "show_room_view"):
                self.master.show_room_view(
                    is_host=False,
                    client=self.client,
                    player_nick=nick,
                    avatar_filename=avatar,
                    deck_name=selected_deck,
                    commander=selected_cmdr
                )
            elif hasattr(self.master, "show_frame"):
                # Jeśli używasz uniwersalnego menedżera ramek:
                self.master.show_frame("RoomView", is_host=False, client=self.client)

            # 3. Wysyłamy pakiet JOIN dopiero po przełączeniu widoku
            if hasattr(self.client, "send_join"):
                self.client.send_join(player_info)
            else:
                self.client.send({"type": "JOIN", "player": player_info})
        else:
            self.lbl_status.configure(text="Failed to connect to host!", text_color="#FF5252")

    def _on_server_message(self, message):
        msg_type = message.get("type")

        if msg_type == "LOBBY_UPDATE":
            self.players = message.get("players", [])

        elif msg_type == "START_GAME":
            if self.on_start_game_callback:
                self.after(0, lambda: self.on_start_game_callback({"players": self.players}))

    def _go_back(self):
        self.client.disconnect()
        if self.on_back_callback:
            self.on_back_callback()