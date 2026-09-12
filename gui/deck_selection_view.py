import os
import customtkinter as ctk
from database.db_manager import DBManager
from gui.new_deck_window import NewDeckWindow

FONT_PATH = os.path.join("assets", "fonts", "Kanisah.ttf")
if os.path.exists(FONT_PATH):
    ctk.FontManager.load_font(FONT_PATH)


class DeckSelectionView(ctk.CTkFrame):
    def __init__(self, master, mode="editor"):
        """
        Context-aware view for deck management:
        - "editor" -> triggers deck editing flow
        - "room"   -> triggers room loading flow
        """
        super().__init__(master)
        self.mode = mode

        self.selected_deck_name = None
        self.deck_buttons = []
        self.scroll_frame = None  # Dynamic list container for stored decks

        # Dynamic label for the action trigger button
        second_btn_text = "Edit Deck" if self.mode == "editor" else "Load Deck"

        # 1. View Header
        self.title_label = ctk.CTkLabel(
            self,
            text="Deck Management",
            font=("Kanisah", 24, "bold")
        )
        self.title_label.pack(pady=15)

        # 2. Button: Create new deck popup
        self.new_deck_btn = ctk.CTkButton(
            self,
            text="New Deck",
            font=("Kanisah", 18, "bold"),
            command=self.new_deck_action
        )
        self.new_deck_btn.pack(pady=10, padx=20)

        # 3. Button: Opens the deck selection list (shared trigger for Load & Edit)
        self.second_action_btn = ctk.CTkButton(
            self,
            text=second_btn_text,
            font=("Kanisah", 18, "bold"),
            command=self.load_deck_list
        )
        self.second_action_btn.pack(pady=10, padx=20)

        # 4. Button: Return to main menu
        self.back_btn = ctk.CTkButton(
            self,
            text="Back",
            font=("Kanisah", 14),
            command=self.back_to_menu
        )
        self.back_btn.pack(pady=20, padx=20)

    def new_deck_action(self):
        """Opens the modal to import/save a new deck."""
        NewDeckWindow(parent=self, on_save_callback=self.refresh_deck_list_if_visible)

    def load_deck_list(self):
        """
        Primary action handler: Lazily instantiates the scrollable list container
        if not present, then populates it with saved decks from SQLite.
        """
        if self.scroll_frame is None:
            # Temporarily hide trigger and back buttons to adjust layout spacing
            self.second_action_btn.pack_forget()
            self.back_btn.pack_forget()

            self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Select Deck from Database")
            self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

            # Re-pack back button below the newly injected frame
            self.back_btn.pack(pady=10, padx=20)

        self.load_decks_from_db()

    def refresh_deck_list_if_visible(self):
        """Callback triggered after saving a deck if list frame is currently rendered."""
        if self.scroll_frame is not None:
            self.load_decks_from_db()

    def load_decks_from_db(self):
        """Fetches stored deck records and generates list item buttons."""
        # Clean up existing buttons
        for btn in self.deck_buttons:
            btn.destroy()
        self.deck_buttons.clear()
        self.selected_deck_name = None

        deck_names = DBManager.get_all_deck_names()

        if not deck_names:
            no_decks_label = ctk.CTkLabel(self.scroll_frame, text="No decks found in database.")
            no_decks_label.pack(pady=10)
            self.deck_buttons.append(no_decks_label)
            return

        # Render clickable buttons for each deck entry
        for name in deck_names:
            btn = ctk.CTkButton(
                self.scroll_frame,
                text=name,
                fg_color="transparent",
                border_width=1,
                anchor="w",
                command=lambda d=name: self.select_deck(d)
            )
            btn.pack(fill="x", pady=2, padx=5)
            self.deck_buttons.append(btn)

    def select_deck(self, deck_name):
        """
        Execution step triggered when a specific deck is chosen from the rendered list.
        """
        self.selected_deck_name = deck_name
        cards = DBManager.get_deck_cards(self.selected_deck_name)

        if self.mode == "editor":
            print(f"[EDITOR] Opening editor for '{self.selected_deck_name}'")
            # Open existing modal pre-filled with selected deck data
            NewDeckWindow(
                parent=self,
                on_save_callback=self.refresh_deck_list_if_visible,
                deck_name=self.selected_deck_name,
                cards_dict=cards
            )
        else:
            print(f"[ROOM] Loading '{self.selected_deck_name}' into Game Room ({len(cards)} unique cards)")
            # TODO: Transition to Game Room View

    def back_to_menu(self):
        """Navigates back to the main menu view."""
        self.master.show_menu()