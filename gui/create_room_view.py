# gui/create_room_view.py
import uuid
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
            width=420
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
        self.subtitle_label.pack(pady=(0, 15))

        # 1. Room Name
        self.name_label = ctk.CTkLabel(self.card_frame, text="Room Name", font=("Segoe UI", 12), anchor="w")
        self.name_label.pack(fill="x", padx=30, pady=(2, 0))

        self.room_name_entry = ctk.CTkEntry(
            self.card_frame,
            placeholder_text="e.g. Commander Night",
            fg_color="#2B2B2B",
            border_width=0,
            corner_radius=8,
            height=34
        )
        self.room_name_entry.pack(fill="x", padx=30, pady=(0, 8))

        # 2. Game Format
        self.format_label = ctk.CTkLabel(self.card_frame, text="Game Format", font=("Segoe UI", 12), anchor="w")
        self.format_label.pack(fill="x", padx=30, pady=(2, 0))

        self.format_option_menu = ctk.CTkOptionMenu(
            self.card_frame,
            values=["Commander / EDH", "Standard", "Casual 60-Card", "1v1 Duel Commander"],
            fg_color="#2B2B2B",
            button_color="#3A3A3A",
            button_hover_color="#00FF66",
            dropdown_fg_color="#1E1E1E",
            corner_radius=8,
            height=34
        )
        self.format_option_menu.pack(fill="x", padx=30, pady=(0, 8))

        # 3. Max Players
        self.players_label = ctk.CTkLabel(self.card_frame, text="Max Players", font=("Segoe UI", 12), anchor="w")
        self.players_label.pack(fill="x", padx=30, pady=(2, 0))

        self.players_segmented = ctk.CTkSegmentedButton(
            self.card_frame,
            values=["2", "3", "4"],
            selected_color="#00FF66",
            selected_hover_color="#00CC52",
            unselected_color="#2B2B2B",
            unselected_hover_color="#3A3A3A",
            text_color="#FFFFFF",
            corner_radius=8,
            height=34
        )
        self.players_segmented.set("4")
        self.players_segmented.pack(fill="x", padx=30, pady=(0, 8))

        # 4. Password
        self.pass_label = ctk.CTkLabel(self.card_frame, text="Password (Optional)", font=("Segoe UI", 12), anchor="w")
        self.pass_label.pack(fill="x", padx=30, pady=(2, 0))

        self.password_entry = ctk.CTkEntry(
            self.card_frame,
            placeholder_text="Leave empty for public",
            show="*",
            fg_color="#2B2B2B",
            border_width=0,
            corner_radius=8,
            height=34
        )
        self.password_entry.pack(fill="x", padx=30, pady=(0, 8))

        # 5. Select Deck
        self.deck_label = ctk.CTkLabel(self.card_frame, text="Select Deck", font=("Segoe UI", 12), anchor="w")
        self.deck_label.pack(fill="x", padx=30, pady=(2, 0))

        deck_names = DBManager.get_all_deck_names() or ["No decks available"]

        self.deck_option_menu = ctk.CTkOptionMenu(
            self.card_frame,
            values=deck_names,
            command=self.on_deck_change,
            fg_color="#2B2B2B",
            button_color="#3A3A3A",
            button_hover_color="#00FF66",
            dropdown_fg_color="#1E1E1E",
            corner_radius=8,
            height=34
        )
        self.deck_option_menu.pack(fill="x", padx=30, pady=(0, 8))

        # 6. Commander (dla EDH)
        self.commander_label = ctk.CTkLabel(self.card_frame, text="Commander Name", font=("Segoe UI", 12), anchor="w")
        self.commander_label.pack(fill="x", padx=30, pady=(2, 0))

        self.commander_entry = ctk.CTkEntry(
            self.card_frame,
            placeholder_text="e.g. Nekusar, the Mindrazer",
            fg_color="#2B2B2B",
            border_width=0,
            corner_radius=8,
            height=34
        )
        self.commander_entry.pack(fill="x", padx=30, pady=(0, 20))

        # Automatyczne odczytanie dowódcy dla pierwszej talii na liście
        if deck_names and deck_names[0] != "No decks available":
            self.on_deck_change(deck_names[0])

        # 7. Action Buttons
        self.btn_frame = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=30, pady=(0, 20))

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

    def on_deck_change(self, selected_deck_name):
        """Pobiera dane talii z bazy i automatycznie wpisuje przypisanego Commandera."""
        deck = DBManager.get_deck_by_name(selected_deck_name) if hasattr(DBManager, "get_deck_by_name") else None
        if deck and isinstance(deck, dict):
            commander_name = deck.get("commander", "")
            self.commander_entry.delete(0, "end")
            self.commander_entry.insert(0, commander_name)

    def create_room_action(self):
        room_config = {
            "game_id": str(uuid.uuid4()),
            "name": self.room_name_entry.get() or "Commander Match",
            "format": self.format_option_menu.get(),
            "max_players": int(self.players_segmented.get()),
            "password": self.password_entry.get(),
            "selected_deck": self.deck_option_menu.get(),
            "commander": self.commander_entry.get()
        }

        if hasattr(self.master, "start_game_room"):
            self.master.start_game_room(room_config)
        else:
            print(f"[CREATE ROOM] Configured: {room_config}")

    def cancel_action(self):
        if hasattr(self.master, "show_menu"):
            self.master.show_menu()