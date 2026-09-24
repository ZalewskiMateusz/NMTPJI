import customtkinter as ctk
from database.db_manager import DBManager
from gui.create_room_view import CreateRoomView  # 1. Import nowego widoku
from gui.deck_selection_view import DeckSelectionView
from gui.menu_view import MenuView
from gui.room_view import RoomView


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Tworzy folder i bazę na start aplikacji
        DBManager.init_db()

        self.title("NMTPJI - MTG Overlay")
        self.geometry("600x500")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Przypisanie referencji na widoki
        self.deck_view = None
        self.create_room_view = None

        self.menu_view = MenuView(self)
        self.menu_view.pack(fill="both", expand=True, padx=20, pady=20)

    def _hide_all_views(self):
        """Pomocnicza funkcja do ukrywania wszystkich aktywnych widoków."""
        if self.menu_view is not None:
            self.menu_view.pack_forget()

        if self.deck_view is not None:
            self.deck_view.pack_forget()

        if self.create_room_view is not None:
            self.create_room_view.pack_forget()

    def show_create_room(self):
        """Metoda wywoływana z MenuView do przejścia do formularza tworzenia pokoju."""
        print("[APP] Wyświetlam CreateRoomView")
        self._hide_all_views()

        # Tworzymy widok na nowo za każdym razem, aby zresetować formularz
        self.create_room_view = CreateRoomView(self)
        self.create_room_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_deck_selection(self, mode="editor"):
        self._hide_all_views()

        self.deck_view = DeckSelectionView(self, mode=mode)
        self.deck_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_menu(self):
        self._hide_all_views()
        self.menu_view.pack(fill="both", expand=True, padx=20, pady=20)

    def start_game_room(self, room_config):
        """Odbiera konfigurację formularza i odpala widok gry."""
        print(f"[APP] Uruchamianie pokoju z konfiguracją: {room_config}")
        self._hide_all_views()

        # Inicjalizujemy widok samej planszy/pokoju z przekazanymi danymi
        self.room_view = RoomView(self, room_config=room_config)
        self.room_view.pack(fill="both", expand=True, padx=10, pady=10)