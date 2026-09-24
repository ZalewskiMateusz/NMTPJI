import os
import customtkinter as ctk

from database.db_manager import DBManager
from gui.new_deck_window import NewDeckWindow
from gui.styles import BTN_STYLE_NORMAL, BTN_STYLE_QUIT, LBL_STYLE_BIG

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
        super().__init__(master, fg_color="#121212")
        self.mode = mode

        self.selected_deck_name = None
        self.deck_buttons = []
        self.scroll_frame = None  # Dynamic list container for stored decks

        # Main Container
        self.main_container = ctk.CTkFrame(self, fg_color="#121212")
        self.main_container.pack(expand=True, fill="both")

        # Central Column Frame (centered on screen)
        self.central_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.central_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Dynamic label for the action trigger button
        second_btn_text = "Edit Deck" if self.mode == "editor" else "Load Deck"

        # 1. View Header
        self.title_label = ctk.CTkLabel(
            self.central_frame,
            text="DECK MANAGEMENT",
            **LBL_STYLE_BIG
        )
        self.title_label.pack(pady=(20, 30), padx=20)

        # 2. Button: Create new deck popup (Accent)
        self.new_deck_btn = ctk.CTkButton(
            self.central_frame,
            text="New Deck",
            **BTN_STYLE_NORMAL,
            command=self.new_deck_action
        )
        self.new_deck_btn.pack(pady=10, padx=20, fill="x")

        # 3. Button: Opens the deck selection list (Normal)
        self.second_action_btn = ctk.CTkButton(
            self.central_frame,
            text=second_btn_text,
            **BTN_STYLE_NORMAL,
            command=self.load_deck_list
        )
        self.second_action_btn.pack(pady=10, padx=20, fill="x")

        # 4. Button: Return to main menu (Quit/Back style)
        self.back_btn = ctk.CTkButton(
            self.central_frame,
            text="Back to Menu",
            **BTN_STYLE_QUIT,
            command=self.back_to_menu
        )
        self.back_btn.pack(pady=(30, 20), padx=20, fill="x")

    def new_deck_action(self):
        """Opens the modal to import/save a new deck."""
        NewDeckWindow(parent=self, on_save_callback=self.refresh_deck_list_if_visible)

    def load_deck_list(self):
        """
        Primary action handler: Lazily instantiates the scrollable list container
        if not present, then populates it with saved decks from SQLite.
        """
        if self.scroll_frame is None:
            # Temporarily hide trigger to make room for scroll frame
            self.second_action_btn.pack_forget()
            self.back_btn.pack_forget()

            self.scroll_frame = ctk.CTkScrollableFrame(
                self.central_frame,
                label_text="Select Deck from Database",
                label_text_color="#8A9BA8",
                fg_color="#1A1A1A",
                width=320,
                height=220,
                corner_radius=12
            )
            self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

            # Re-pack back button below the scroll frame
            self.back_btn.pack(pady=(15, 20), padx=20, fill="x")

        self.load_decks_from_db()

    def refresh_deck_list_if_visible(self):
        """Callback triggered after saving a deck if list frame is currently rendered."""
        if self.scroll_frame is not None:
            self.load_decks_from_db()

    def load_decks_from_db(self):
        """Fetches stored deck records and generates list item buttons."""
        for btn in self.deck_buttons:
            btn.destroy()
        self.deck_buttons.clear()
        self.selected_deck_name = None

        deck_names = DBManager.get_all_deck_names()

        if not deck_names:
            no_decks_label = ctk.CTkLabel(
                self.scroll_frame,
                text="No decks found in database.",
                text_color="#666666"
            )
            no_decks_label.pack(pady=20)
            self.deck_buttons.append(no_decks_label)
            return

        for name in deck_names:
            btn = ctk.CTkButton(
                self.scroll_frame,
                text=name,
                font=("Segoe UI", 14),
                fg_color="#252525",
                hover_color="#333333",
                border_color="#00FF66",
                border_width=0,
                anchor="w",
                height=34,
                corner_radius=8,
                command=lambda d=name: self.select_deck(d)
            )
            btn.pack(fill="x", pady=4, padx=5)
            self.deck_buttons.append(btn)

    def select_deck(self, deck_name):
        """
        Execution step triggered when a specific deck is chosen from the rendered list.
        """
        self.selected_deck_name = deck_name
        cards = DBManager.get_deck_cards(self.selected_deck_name)

        if self.mode == "editor":
            print(f"[EDITOR] Opening editor for '{self.selected_deck_name}'")
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
        if hasattr(self.master, "show_menu"):
            self.master.show_menu()
        else:
            print("Back to Menu Action")