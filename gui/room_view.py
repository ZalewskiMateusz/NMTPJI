# gui/room_view.py
import os
import customtkinter as ctk
from PIL import Image
from utils.profile_manager import ProfileManager, AVATARS_DIR


class RoomView(ctk.CTkFrame):
    def __init__(self, master, room_config=None, player_nick=None, avatar_filename=None, deck_name=None):
        super().__init__(master, fg_color="#121212")
        self.room_config = room_config or {}

        # Odczyt danych z profilu / konfiguracji pokoju
        profile = ProfileManager.load_profile()
        self.host_nick = player_nick or profile.get("nickname", "HOST")
        self.host_avatar = avatar_filename or profile.get("avatar_filename", "jace.png")

        self.host_deck = (
                deck_name
                or self.room_config.get("selected_deck")
                or self.room_config.get("deck_name")
                or "Selected Deck"
        )
        self.host_commander = self.room_config.get("commander", "")
        self.game_format = self.room_config.get("format", "Commander / EDH")
        self.room_name = self.room_config.get("name") or self.room_config.get("room_name", "Test Room")

        # --- 1. GÓRNY PASEK ---
        self.top_bar = ctk.CTkFrame(self, fg_color="#1E1E1E", height=50, corner_radius=8)
        self.top_bar.pack(fill="x", padx=15, pady=(15, 10))

        self.room_title = ctk.CTkLabel(
            self.top_bar,
            text=f"ROOM: {self.room_name}  [{self.game_format}]",
            font=("Segoe UI", 15, "bold"),
            text_color="#00FF66"
        )
        self.room_title.pack(side="left", padx=20, pady=10)

        # Kontener na przyciski po prawej stronie górnego paska
        self.top_buttons_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.top_buttons_frame.pack(side="right", padx=15, pady=9)

        # Przycisk START GAME / READY na górnym pasku
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

        # Przycisk LEAVE ROOM
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

        # --- 2. KONTENER NA SLOTY 2x2 ---
        self.slots_container = ctk.CTkFrame(self, fg_color="transparent")
        self.slots_container.pack(expand=True, fill="both", padx=15, pady=(0, 15))

        self.slots_container.grid_columnconfigure(0, weight=1)
        self.slots_container.grid_columnconfigure(1, weight=1)
        self.slots_container.grid_rowconfigure(0, weight=1)
        self.slots_container.grid_rowconfigure(1, weight=1)

        self._build_slots()

    def _build_slots(self):
        # Slot 1: HOST (Ty)
        self.slot1 = ctk.CTkFrame(
            self.slots_container,
            fg_color="#1A1A1A",
            border_color="#00FF66",
            border_width=2,
            corner_radius=12
        )
        self.slot1.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        lbl_badge = ctk.CTkLabel(
            self.slot1,
            text="👑 HOST (YOU)",
            font=("Segoe UI", 11, "bold"),
            text_color="#A0A0A0"
        )
        lbl_badge.pack(pady=(12, 2))

        # Karta wnętrza dla hosta
        card_inner = ctk.CTkFrame(self.slot1, fg_color="#141414", corner_radius=10)
        card_inner.pack(expand=True, fill="both", padx=15, pady=(0, 12))

        # Avatar Hosta
        avatar_path = os.path.join(AVATARS_DIR, self.host_avatar)
        if os.path.exists(avatar_path):
            img = Image.open(avatar_path)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(90, 90))
            lbl_avatar = ctk.CTkLabel(card_inner, image=ctk_img, text="")
            lbl_avatar.pack(expand=True, pady=(10, 2))

        # Nick
        lbl_nick = ctk.CTkLabel(
            card_inner,
            text=self.host_nick,
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        )
        lbl_nick.pack(pady=(0, 2))

        # Deck
        lbl_deck = ctk.CTkLabel(
            card_inner,
            text=f"Deck: {self.host_deck}",
            font=("Segoe UI", 13, "bold"),
            text_color="#00FF66"
        )
        lbl_deck.pack(pady=(0, 2))

        # Commander (jeśli podany)
        if self.host_commander:
            lbl_cmd = ctk.CTkLabel(
                card_inner,
                text=f"CMD: {self.host_commander}",
                font=("Segoe UI", 11, "italic"),
                text_color="#8A9BA8"
            )
            lbl_cmd.pack(pady=(0, 10))

        # Sloty 2, 3, 4 (Waiting for player)
        max_players = self.room_config.get("max_players", 4)
        positions = [(0, 1), (1, 0), (1, 1)]

        for idx, (r, c) in enumerate(positions, start=2):
            slot = ctk.CTkFrame(
                self.slots_container,
                fg_color="#141414",
                border_color="#222222",
                border_width=1,
                corner_radius=12
            )
            slot.grid(row=r, column=c, sticky="nsew", padx=8, pady=8)

            if idx <= max_players:
                lbl_slot_num = ctk.CTkLabel(
                    slot,
                    text=f"Slot {idx}",
                    font=("Segoe UI", 13, "bold"),
                    text_color="#555555"
                )
                lbl_slot_num.pack(expand=True, pady=(20, 0))

                lbl_wait = ctk.CTkLabel(
                    slot,
                    text="Waiting for player...",
                    font=("Segoe UI", 12),
                    text_color="#444444"
                )
                lbl_wait.pack(expand=True, pady=(0, 20))
            else:
                lbl_closed = ctk.CTkLabel(
                    slot,
                    text="LOCKED",
                    font=("Segoe UI", 12, "bold"),
                    text_color="#333333"
                )
                lbl_closed.pack(expand=True)

    def start_match(self):
        if hasattr(self.master, "launch_game_overlay"):
            self.master.launch_game_overlay(self.room_config)

    def leave_room(self):
        if hasattr(self.master, "show_menu"):
            self.master.show_menu()