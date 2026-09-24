# gui/create_room_view.py
import customtkinter as ctk
from database.db_manager import DBManager
from gui.styles import BTN_STYLE_ACCENT, BTN_STYLE_QUIT


class CreateRoomView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#121212")

        # Główny wyśrodkowany kontener (karta formularza)
        self.card_frame = ctk.CTkFrame(
            self,
            fg_color="#1E1E1E",
            border_color="#00FF66",
            border_width=2,
            corner_radius=16,
            width=400
        )
        self.card_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        self.title_label = ctk.CTkLabel(
            self.card_frame,
            text="CREATE GAME ROOM",
            font=("Kanisah", 24, "bold"),
            text_color="#FFFFFF"
        )
        self.title_label.pack(pady=(20, 2), padx=30)

        self.subtitle_label = ctk.CTkLabel(
            self.card_frame,
            text="CONFIGURE YOUR MATCH",
            font=("Segoe UI", 11, "bold"),
            text_color="#8A9BA8"
        )
        self.subtitle_label.pack(pady=(0, 20))

        # 1. Room Name
        self.name_label = ctk.CTkLabel(self.card_frame, text="Room Name", font=("Segoe UI", 12), anchor="w")
        self.name_label.pack(fill="x", padx=30, pady=(5, 0))

        self.room_name_entry = ctk.CTkEntry(
            self.card_frame,
            placeholder_text="e.g. Commander Night",
            fg_color="#2B2B2B",
            border_width=0,
            corner_radius=8,
            height=36
        )
        self.room_name_entry.pack(fill="x", padx=30, pady=(0, 10))

        # 2. Max Players
        self.players_label = ctk.CTkLabel(self.card_frame, text="Max Players", font=("Segoe UI", 12), anchor="w")
        self.players_label.pack(fill="x", padx=30, pady=(5, 0))

        self.players_segmented = ctk.CTkSegmentedButton(
            self.card_frame,
            values=["2", "3", "4"],
            selected_color="#00FF66",
            selected_hover_color="#00CC52",
            unselected_color="#2B2B2B",
            unselected_hover_color="#3A3A3A",
            text_color="#FFFFFF",
            corner_radius=8,
            height=36
        )
        self.players_segmented.set("4")
        self.players_segmented.pack(fill="x", padx=30, pady=(0, 10))

        # 3. Password
        self.pass_label = ctk.CTkLabel(self.card_frame, text="Password (Optional)", font=("Segoe UI", 12), anchor="w")
        self.pass_label.pack(fill="x", padx=30, pady=(5, 0))

        self.password_entry = ctk.CTkEntry(
            self.card_frame,
            placeholder_text="Leave empty for public",
            show="*",
            fg_color="#2B2B2B",
            border_width=0,
            corner_radius=8,
            height=36
        )
        self.password_entry.pack(fill="x", padx=30, pady=(0, 10))

        # 4. Select Deck
        self.deck_label = ctk.CTkLabel(self.card_frame, text="Select Deck", font=("Segoe UI", 12), anchor="w")
        self.deck_label.pack(fill="x", padx=30, pady=(5, 0))

        deck_names = DBManager.get_all_deck_names() or ["No decks available"]

        self.deck_option_menu = ctk.CTkOptionMenu(
            self.card_frame,
            values=deck_names,
            fg_color="#2B2B2B",
            button_color="#3A3A3A",
            button_hover_color="#00FF66",
            dropdown_fg_color="#1E1E1E",
            corner_radius=8,
            height=36
        )
        self.deck_option_menu.pack(fill="x", padx=30, pady=(0, 25))

        # 5. Action Buttons
        self.btn_frame = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=30, pady=(0, 25))

        self.create_btn = ctk.CTkButton(
            self.btn_frame,
            text="CREATE ROOM",
            **BTN_STYLE_ACCENT,
            command=self.create_room_action
        )
        self.create_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.cancel_btn = ctk.CTkButton(
            self.btn_frame,
            text="CANCEL",
            **BTN_STYLE_QUIT,
            command=self.cancel_action
        )
        self.cancel_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))

    def create_room_action(self):
        # Pobieramy wpisane dane
        room_config = {
            "name": self.room_name_entry.get() or "Commander Match",
            "max_players": int(self.players_segmented.get()),
            "password": self.password_entry.get(),
            "selected_deck": self.deck_option_menu.get()
        }

        # Wywołujemy metodę w głównym oknie aplikacji (app.py)
        if hasattr(self.master, "start_game_room"):
            self.master.start_game_room(room_config)
        else:
            print(f"[CREATE ROOM] Configured: {room_config}")

    def cancel_action(self):
        if hasattr(self.master, "show_menu"):
            self.master.show_menu()