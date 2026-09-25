import os
import customtkinter as ctk
from gui.styles import BTN_STYLE_NORMAL, BTN_STYLE_QUIT
from utils.profile_manager import ProfileManager
from gui.profile_dialog import ProfileDialog

# 1. Path to font
FONT_PATH = os.path.join("assets", "fonts", "Kanisah.ttf")

# 2. Register font
if os.path.exists(FONT_PATH):
    ctk.FontManager.load_font(FONT_PATH)


class MenuView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        # Main Container - Ciemne Tło
        self.Main_Container = ctk.CTkFrame(self, fg_color="#121212")
        self.Main_Container.pack(expand=True, fill="both")

        # --- CENTRALNA KOLUMNA MENU ---
        self.menu_central_frame = ctk.CTkFrame(self.Main_Container, fg_color="transparent")
        self.menu_central_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Main Title
        self.Project_Title = ctk.CTkLabel(
            self.menu_central_frame,
            text="NMTPJI",
            font=("Kanisah", 36, "bold"),
            text_color="#FFFFFF"
        )
        self.Project_Title.pack(pady=(20, 0), padx=20)

        # Subtitle
        self.Project_Subtitle = ctk.CTkLabel(
            self.menu_central_frame,
            text="TCG MATCH MANAGER",
            font=("Segoe UI", 14, "bold"),
            text_color="#8A9BA8"
        )
        self.Project_Subtitle.pack(pady=(0, 40), padx=20)

        # 1. Create Room Button (Akcent)
        self.new_room_button = ctk.CTkButton(
            self.menu_central_frame,
            text="Create Room",
            **BTN_STYLE_NORMAL,
            command=self.create_new_room_action
        )
        self.new_room_button.pack(pady=10, padx=20, fill="x")

        # 2. Join Room Button (Normal)
        self.find_room_button = ctk.CTkButton(
            self.menu_central_frame,
            text="Join Room",
            **BTN_STYLE_NORMAL,
            command=self.join_room_action
        )
        self.find_room_button.pack(pady=10, padx=20, fill="x")

        # 3. DECKS Button (Normal)
        self.deck_editor_button = ctk.CTkButton(
            self.menu_central_frame,
            text="DECKS",
            **BTN_STYLE_NORMAL,
            command=self.deck_editor_action
        )
        self.deck_editor_button.pack(pady=10, padx=20, fill="x")

        # 4. Profile button (Normal)
        self.profile_button = ctk.CTkButton(
            self.menu_central_frame,
            text="PROFILE",
            **BTN_STYLE_NORMAL,
            command=self.profile_editor_action
        )
        self.profile_button.pack(pady=10, padx=20, fill="x")

        # 5. STATISTICS Button (Zablokowany Soon)
        self.stats_button = ctk.CTkButton(
            self.menu_central_frame,
            text="STATISTICS",
            font=("Segoe UI", 16, "bold"),
            fg_color="#1E1E1E",
            text_color="#555555",
            state="disabled",
            corner_radius=12,
            height=40
        )
        self.stats_button.pack(pady=10, padx=20, fill="x")

        # 6. Quit Button (Quit Style)
        self.quit_button = ctk.CTkButton(
            self.menu_central_frame,
            text="QUIT",
            **BTN_STYLE_QUIT,
            command=self.master.destroy
        )
        self.quit_button.pack(pady=(50, 20), padx=20, fill="x")

    def _ensure_profile_or_open_dialog(self, on_success_callback):
        """Sprawdza, czy gracz ma profil. Jeśli nie – otwiera pop-up tworzenia profilu z wymuszeniem."""
        if ProfileManager.has_profile():
            on_success_callback()
        else:
            ProfileDialog(
                self,
                current_profile=ProfileManager.load_profile(),
                on_save_callback=on_success_callback,
                warning_msg="You must create a profile first!"
            )

    def create_new_room_action(self):
        def proceed():
            if hasattr(self.master, "show_create_room"):
                self.master.show_create_room()

        self._ensure_profile_or_open_dialog(proceed)

    def join_room_action(self):
        def proceed():
            print("Click: Join Room")

        self._ensure_profile_or_open_dialog(proceed)

    def deck_editor_action(self):
        if hasattr(self.master, "show_deck_selection"):
            self.master.show_deck_selection(mode="editor")
        else:
            print("Deck Editor Action (no show_deck_selection in master)")

    def profile_editor_action(self):
        profile = ProfileManager.load_profile()
        ProfileDialog(self, current_profile=profile)