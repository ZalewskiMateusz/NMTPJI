import os
import random
import customtkinter as ctk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT_KANISAH_PATH = os.path.join(BASE_DIR, "assets", "fonts", "Kanisah.ttf")

FONT_FAMILY_TITLE = "Georgia"
if os.path.exists(FONT_KANISAH_PATH):
    try:
        ctk.FontManager.load_font(FONT_KANISAH_PATH)
        FONT_FAMILY_TITLE = "Kanisah"
    except Exception:
        pass


class GameHeaderWidget(ctk.CTkFrame):
    def __init__(
        self,
        master,
        room_config=None,
        is_host: bool = True,
        on_action_callback=None,
        **kwargs,
    ):
        super().__init__(master, fg_color="#181818", corner_radius=0, **kwargs)

        self.room_config = room_config or {}

        config_dict = self.room_config.get("config", {})
        self.room_name = (
            config_dict.get("name")
            or self.room_config.get("name")
            or self.room_config.get("room_name")
            or "Commander Room"
        )
        self.is_host = is_host
        self.on_action_callback = on_action_callback

        # =========================================================
        # 1. LEWA STRONA: Nazwa Pokoju & Narzędzia Gry (Losowania)
        # =========================================================
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.pack(side="left", padx=15, pady=8)

        self.lbl_room = ctk.CTkLabel(
            self.left_frame,
            text=f"Room: {self.room_name}",
            font=("Segoe UI", 13, "bold"),
            text_color="#00FF66",
        )
        self.lbl_room.pack(side="left", padx=(0, 15))

        self.random_options = [
            "🎲 Pick Starting Player",
            "🪙 Flip Coin",
            "🎲 Roll D6",
            "🎲 Roll D20",
            "🎲 Roll D100",
        ]
        self.random_dropdown = ctk.CTkOptionMenu(
            self.left_frame,
            values=self.random_options,
            command=self.handle_random_selection,
            font=("Segoe UI", 11, "bold"),
            fg_color="#2B2B2B",
            button_color="#3A3A3A",
            button_hover_color="#4A4A4A",
            dropdown_fg_color="#1E1E1E",
            width=140,
            height=32,
        )
        self.random_dropdown.set("🎲 Roll / Tools")
        self.random_dropdown.pack(side="left", padx=(0, 0))

        # =========================================================
        # 2. ŚRODEK: Tytuł / Nazwa aplikacji
        # =========================================================
        self.lbl_title = ctk.CTkLabel(
            self,
            text="NMTPJI",
            font=(FONT_FAMILY_TITLE, 26, "bold"),
            text_color="#FFFFFF",
        )
        self.lbl_title.place(relx=0.5, rely=0.5, anchor="center")

        # =========================================================
        # 3. PRAWA STRONA: Follow, Tura, End Match & Next Turn
        # =========================================================
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.pack(side="right", padx=15, pady=8)

        self.follow_var = ctk.BooleanVar(value=False)
        self.chk_follow = ctk.CTkCheckBox(
            self.right_frame,
            text="Follow Active",
            font=("Segoe UI", 10),
            variable=self.follow_var,
            checkbox_width=16,
            checkbox_height=16,
            command=self.toggle_follow_action
        )
        self.chk_follow.pack(side="left", padx=(0, 10))

        self.lbl_info = ctk.CTkLabel(
            self.right_frame,
            text="Turn: 1 | Active: -",
            font=("Segoe UI", 12, "bold"),
            text_color="#CCCCCC",
        )
        self.lbl_info.pack(side="left", padx=(0, 15))

        self.btn_end_match = ctk.CTkButton(
            self.right_frame,
            text="END MATCH",
            font=("Segoe UI", 11, "bold"),
            fg_color="#2B2B2B",
            hover_color="#5A1E1E",
            border_color="#7A2222",
            border_width=1,
            corner_radius=8,
            height=32,
            width=90,
            command=self.end_match_action,
        )
        self.btn_end_match.pack(side="left", padx=(0, 8))

        self.btn_next_turn = ctk.CTkButton(
            self.right_frame,
            text="NEXT TURN ➔",
            font=("Segoe UI", 11, "bold"),
            fg_color="#1F6AA5",
            hover_color="#144870",
            corner_radius=8,
            height=32,
            width=110,
            command=self.next_turn_action,
        )
        self.btn_next_turn.pack(side="left", padx=0)

    def update_from_state(self, state):
        """Aktualizuje informacje o turze na podstawie globalnego RoomState."""
        active_player = (
            state.get_current_player()
            if hasattr(state, "get_current_player")
            else None
        )
        active_name = active_player.name if active_player else "Unknown"
        turn_num = getattr(state, "turn_number", 1)
        self.lbl_info.configure(
            text=f"Turn: {turn_num} | Active: {active_name}"
        )

    def handle_random_selection(self, choice):
        self.random_dropdown.set("🎲 Roll / Tools")
        if "Starting Player" in choice and self.on_action_callback:
            self.on_action_callback("ROLL_FIRST_PLAYER", {})
        elif "Coin" in choice and self.on_action_callback:
            result = random.choice(["Heads", "Tails"])
            self.on_action_callback("COIN_FLIP", {"result": result})
        elif "D6" in choice and self.on_action_callback:
            self.on_action_callback("ROLL_DICE", {"sides": 6, "result": random.randint(1, 6)})
        elif "D20" in choice and self.on_action_callback:
            self.on_action_callback("ROLL_DICE", {"sides": 20, "result": random.randint(1, 20)})
        elif "D100" in choice and self.on_action_callback:
            self.on_action_callback("ROLL_DICE", {"sides": 100, "result": random.randint(1, 100)})

    def next_turn_action(self):
        if self.on_action_callback:
            self.on_action_callback("NEXT_TURN", {})

    def end_match_action(self):
        if self.on_action_callback:
            self.on_action_callback("END_MATCH", {})

    def toggle_follow_action(self):
        if self.on_action_callback:
            self.on_action_callback("TOGGLE_FOLLOW_PLAYER", {"active": self.follow_var.get()})