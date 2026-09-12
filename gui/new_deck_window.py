import customtkinter as ctk
from core.deck_parser import DeckParser
from database.db_manager import DBManager


class NewDeckWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback=None, deck_name=None, cards_dict=None):
        super().__init__(parent)

        self.on_save_callback = on_save_callback
        self.original_deck_name = deck_name

        # Set title based on edit/create mode
        window_title = f"Edit Deck: {deck_name}" if deck_name else "Add New Deck"
        self.title(window_title)
        self.geometry("400x500")

        # Keep modal window on top
        self.attributes("-topmost", True)
        self.focus_force()

        # 1. Deck Name Label & Entry
        self.name_label = ctk.CTkLabel(self, text="Deck Name:")
        self.name_label.pack(pady=(10, 0), padx=20, anchor="w")

        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Krenko Goblins")
        self.name_entry.pack(fill="x", padx=20, pady=5)

        if deck_name:
            self.name_entry.insert(0, deck_name)

        # 2. Decklist Label & Textbox
        self.list_label = ctk.CTkLabel(self, text="Paste Archidekt / Decklist:")
        self.list_label.pack(pady=(10, 0), padx=20, anchor="w")

        self.decklist_textbox = ctk.CTkTextbox(self, height=250)
        self.decklist_textbox.pack(fill="both", expand=True, padx=20, pady=5)

        # Pre-fill cards if editing an existing deck
        if cards_dict:
            formatted_text = "\n".join([f"{qty}x {card}" for card, qty in cards_dict.items()])
            self.decklist_textbox.insert("1.0", formatted_text)

        # 3. Save Button
        self.save_button = ctk.CTkButton(self, text="Save Deck", command=self.save_deck)
        self.save_button.pack(pady=15, padx=20)

    def save_deck(self):
        deck_name = self.name_entry.get().strip()
        raw_text = self.decklist_textbox.get("1.0", "end-1c").strip()

        if not deck_name or not raw_text:
            print("Warning: Fill in both Name and Decklist!")
            return

        try:
            # Parse text and persist to SQLite
            parsed_cards = DeckParser.parse_decklist(raw_text)
            DBManager.save_deck(deck_name=deck_name, cards=parsed_cards)

            print(f"Deck '{deck_name}' successfully saved to database!")

            # Refresh parent UI list if callback is assigned
            if self.on_save_callback:
                self.on_save_callback()

            self.destroy()

        except Exception as e:
            print(f"Error saving deck: {e}")