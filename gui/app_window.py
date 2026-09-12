import customtkinter as ctk
from database.db_manager import DBManager
from gui.deck_selection_view import DeckSelectionView
from gui.menu_view import MenuView


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Tworzy folder i bazę na start aplikacji
        DBManager.init_db()

        self.title("NMTPJI - MTG Overlay")
        self.geometry("600x500")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.deck_view = None

        self.menu_view = MenuView(self)
        self.menu_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_deck_selection(self, mode="editor"):
        self.menu_view.pack_forget()

        if self.deck_view is not None:
            self.deck_view.pack_forget()

        self.deck_view = DeckSelectionView(self, mode=mode)
        self.deck_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_menu(self):
        if self.deck_view is not None:
            self.deck_view.pack_forget()
        self.menu_view.pack(fill="both", expand=True, padx=20, pady=20)