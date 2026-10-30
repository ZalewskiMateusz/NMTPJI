# gui/find_room_view.py (Zaktualizowana wersja integrująca RoomView i SyncClient)
import customtkinter as ctk
from database.db_manager import DBManager
from utils.profile_manager import ProfileManager


class FindRoomView(ctk.CTkFrame):
    def __init__(self, master, room_config=None, on_back_callback=None):
        super().__init__(master, fg_color="#121212")
        self.room_config = room_config or {}
        self.on_back_callback = on_back_callback

        profile = ProfileManager.load_profile()
        self.my_nick = profile.get("nickname", "Host")
        self.my_avatar = profile.get("avatar_filename", "jace.png")

        self._build_ui()

    def _build_ui(self):
        self.card = ctk.CTkFrame(
            self,
            fg_color="#1E1E1E",
            border_color="#00FF66",
            border_width=2,
            corner_radius=16,
            width=420
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self.card,
            text="HOST LOBBY ROOM",
            font=("Kanisah", 26, "bold"),
            text_color="#FFFFFF"
        ).pack(pady=(25, 2))

        ctk.CTkLabel(
            self.card,
            text="INITIALIZING ROOM SERVER...",
            font=("Segoe UI", 10, "bold"),
            text_color="#8A9BA8"
        ).pack(pady=(0, 20))

        # Automatyczne przejście do RoomView jako host
        self.after(500, self._launch_room_view)

    def _launch_room_view(self):
        if hasattr(self.master, "show_room_view"):
            self.master.show_room_view(
                is_host=True,
                room_config=self.room_config,
                player_nick=self.my_nick,
                avatar_filename=self.my_avatar
            )
        elif self.on_back_callback:
            self.on_back_callback()