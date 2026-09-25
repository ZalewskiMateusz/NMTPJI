import os
import customtkinter as ctk
from PIL import Image
from utils.profile_manager import ProfileManager, AVATARS_DIR


class ProfileDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_profile=None, on_save_callback=None, warning_msg=None):
        super().__init__(parent)
        self.title("Player Profile")
        self.geometry("480x450")
        self.resizable(False, False)

        self.on_save_callback = on_save_callback
        self.current_profile = current_profile or ProfileManager.load_profile()
        self.selected_avatar = self.current_profile.get("avatar_filename", "jace.png")

        # Okno modalne (zawsze na wierzchu)
        self.transient(parent)
        self.grab_set()

        # Nagłówek
        ctk.CTkLabel(
            self,
            text="PLAYER PROFILE",
            font=("Segoe UI", 16, "bold"),
            text_color="#00FF66"
        ).pack(pady=(20, 5))

        # --- TUTAJ: Komunikat ostrzegawczy (jeśli przekazany) ---
        if warning_msg:
            ctk.CTkLabel(
                self,
                text=warning_msg,
                font=("Segoe UI", 12, "bold"),
                text_color="#FF4444"
            ).pack(pady=(0, 10))

        # Pole na Nick
        ctk.CTkLabel(self, text="Enter Nickname:", font=("Segoe UI", 12)).pack(pady=(5, 2))
        self.nick_entry = ctk.CTkEntry(self, width=260, placeholder_text="Your Nickname...")
        self.nick_entry.pack(pady=5)
        if "nickname" in self.current_profile:
            self.nick_entry.insert(0, self.current_profile["nickname"])

        # Sekcja wyboru Avatara
        ctk.CTkLabel(self, text="Select Avatar:", font=("Segoe UI", 12)).pack(pady=(15, 5))

        self.avatars_frame = ctk.CTkScrollableFrame(self, width=420, height=140, fg_color="#1E1E1E",
                                                    orientation="horizontal")
        self.avatars_frame.pack(pady=5, padx=20)

        self.avatar_buttons = []
        self._load_avatar_list()

        # Przycisk Zapisz
        self.save_btn = ctk.CTkButton(
            self,
            text="SAVE PROFILE",
            font=("Segoe UI", 12, "bold"),
            fg_color="#00FF66",
            text_color="#000000",
            hover_color="#00CC52",
            height=35,
            command=self.save_and_close
        )
        self.save_btn.pack(pady=(20, 10))

    def _load_avatar_list(self):
        avatars = ProfileManager.get_available_avatars()

        for filename in avatars:
            img_path = os.path.join(AVATARS_DIR, filename)

            # Wczytujemy obrazek przez PIL i konwertujemy do CTkImage
            pil_img = Image.open(img_path)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60, 60))

            is_selected = (filename == self.selected_avatar)

            btn = ctk.CTkButton(
                self.avatars_frame,
                text="",
                image=ctk_img,
                width=70,
                height=70,
                fg_color="#00FF66" if is_selected else "#2B2B2B",
                hover_color="#00CC52",
                command=lambda fn=filename: self.select_avatar(fn)
            )
            btn.pack(side="left", padx=5, pady=5)
            self.avatar_buttons.append((filename, btn))

    def select_avatar(self, filename):
        self.selected_avatar = filename
        for fn, btn in self.avatar_buttons:
            if fn == filename:
                btn.configure(fg_color="#00FF66")
            else:
                btn.configure(fg_color="#2B2B2B")

    def save_and_close(self):
        nick = self.nick_entry.get().strip()
        if not nick:
            nick = "Player"

        ProfileManager.save_profile(nickname=nick, avatar_filename=self.selected_avatar)

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()