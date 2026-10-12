import customtkinter as ctk
from database.db_manager import DBManager
from gui.create_room_view import CreateRoomView
from gui.deck_selection_view import DeckSelectionView
from gui.find_room_view import FindRoomView  # <--- IMPORT FIND ROOM
from gui.join_room_view import JoinRoomView  # <--- IMPORT JOIN ROOM
from gui.menu_view import MenuView
from gui.room_view import RoomView
from gui.overlay_view import OverlayView
from utils.profile_manager import ProfileManager


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        DBManager.init_db()

        self.title("NMTPJI - MTG Overlay")
        self.geometry("800x600")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.deck_view = None
        self.create_room_view = None
        self.find_room_view = None  # <--- ZMIENNA NA HOSTOWANIE
        self.join_room_view = None  # <--- ZMIENNA NA DOŁĄCZANIE
        self.room_view = None
        self.overlay_view = None

        self.menu_view = MenuView(self)
        self.menu_view.pack(fill="both", expand=True, padx=20, pady=20)

    def _hide_all_views(self):
        """Ukrywa wszystkie aktywne widoki."""
        if self.menu_view is not None:
            self.menu_view.pack_forget()

        if self.deck_view is not None:
            self.deck_view.pack_forget()

        if self.create_room_view is not None:
            self.create_room_view.pack_forget()

        if self.find_room_view is not None:
            self.find_room_view.pack_forget()

        if self.join_room_view is not None:
            self.join_room_view.pack_forget()

        if self.room_view is not None:
            self.room_view.pack_forget()

        if self.overlay_view is not None:
            self.overlay_view.pack_forget()

    def show_create_room(self):
        self._hide_all_views()
        self.create_room_view = CreateRoomView(self)
        self.create_room_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_find_room(self):
        """Otwiera widok hostowania / szukania pokoju."""
        self._hide_all_views()
        self.find_room_view = FindRoomView(
            self,
            on_start_game_callback=self.launch_game_overlay,
            on_back_callback=self.show_menu
        )
        self.find_room_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_join_room(self):
        """Otwiera widok dołączania do istniejącego pokoju."""
        self._hide_all_views()
        self.join_room_view = JoinRoomView(
            self,
            on_start_game_callback=self.launch_game_overlay,
            on_back_callback=self.show_menu
        )
        self.join_room_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_deck_selection(self, mode="editor"):
        self._hide_all_views()
        self.deck_view = DeckSelectionView(self, mode=mode)
        self.deck_view.pack(fill="both", expand=True, padx=20, pady=20)

    def show_menu(self):
        self._hide_all_views()
        if self.find_room_view is not None:
            self.find_room_view.destroy()
            self.find_room_view = None
        if self.join_room_view is not None:
            self.join_room_view.destroy()
            self.join_room_view = None
        if self.room_view is not None:
            self.room_view.destroy()
            self.room_view = None
        if self.overlay_view is not None:
            self.overlay_view.destroy()
            self.overlay_view = None
        self.menu_view.pack(fill="both", expand=True, padx=20, pady=20)

    def start_game_room(self, room_config):
        """Przechodzi z formularza tworzenia do lobby pokoju."""
        self._hide_all_views()
        self.room_view = RoomView(self, room_config=room_config)
        self.room_view.pack(fill="both", expand=True, padx=10, pady=10)

    def launch_game_overlay(self, room_config=None):
        """Startuje bezpośredni mecz / planszę nakładki."""
        self._hide_all_views()
        self.overlay_view = OverlayView(self, room_config=room_config)
        self.overlay_view.pack(fill="both", expand=True, padx=10, pady=10)

    def show_room_view(
            self,
            deck_data=None,
            is_host=True,
            client=None,
            player_nick=None,
            avatar_filename=None,
            deck_name=None,
            commander=None,
            room_config=None
    ):
        self._hide_all_views()

        # Jeśli przekazano słownik w pierwszym argumencie (np. z wyboru talii)
        if isinstance(deck_data, dict):
            deck_name = deck_data.get("deck_name", deck_name or "Unknown Deck")

        profile = ProfileManager.load_profile()
        nick = player_nick or profile.get("nickname", "Player")
        avatar = avatar_filename or profile.get("avatar_filename", "jace.png")

        self.room_view = RoomView(
            self,
            room_config=room_config,
            player_nick=nick,
            avatar_filename=avatar,
            deck_name=deck_name,
            commander=commander,
            is_host=is_host,
            client=client
        )
        self.room_view.pack(expand=True, fill="both", padx=10, pady=10)