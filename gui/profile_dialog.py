import os
import customtkinter as ctk
from PIL import Image
from utils.profile_manager import ProfileManager, AVATARS_DIR

# Determine the project root directory relative to AVATARS_DIR
PROJECT_ROOT = os.path.abspath(os.path.join(AVATARS_DIR, "..", ".."))
EMOTES_DIR = os.path.join(PROJECT_ROOT, "assets", "emotes")

FONT_UI = "Segoe UI"


class ProfileDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_profile=None, on_save_callback=None, warning_msg=None):
        super().__init__(parent)
        self.title("Player Profile")
        self.geometry("520x720")
        self.resizable(False, False)

        self.on_save_callback = on_save_callback
        self.current_profile = current_profile or ProfileManager.load_profile()
        self.selected_avatar = self.current_profile.get("avatar_filename", "jace.png")

        # Load up to 6 equipped emotes (pad with None if less than 6)
        saved_emotes = self.current_profile.get("selected_emotes", [])
        self.equipped_emotes = (saved_emotes + [None] * 6)[:6]

        # Modal window configuration (always on top)
        self.transient(parent)
        self.grab_set()

        # --- HEADER ---
        ctk.CTkLabel(
            self,
            text="PLAYER PROFILE",
            font=(FONT_UI, 16, "bold"),
            text_color="#00FF66"
        ).pack(pady=(15, 5))

        # Warning message (if passed)
        if warning_msg:
            ctk.CTkLabel(
                self,
                text=warning_msg,
                font=(FONT_UI, 12, "bold"),
                text_color="#FF4444"
            ).pack(pady=(0, 5))

        # --- NICKNAME INPUT ---
        ctk.CTkLabel(self, text="Enter Nickname:", font=(FONT_UI, 12)).pack(pady=(5, 2))
        self.nick_entry = ctk.CTkEntry(self, width=260, placeholder_text="Your Nickname...")
        self.nick_entry.pack(pady=2)
        if "nickname" in self.current_profile:
            self.nick_entry.insert(0, self.current_profile["nickname"])

        # --- AVATAR SELECTION ---
        ctk.CTkLabel(self, text="Select Avatar:", font=(FONT_UI, 12)).pack(pady=(10, 2))

        self.avatars_frame = ctk.CTkScrollableFrame(self, width=440, height=110, fg_color="#1E1E1E",
                                                    orientation="horizontal")
        self.avatars_frame.pack(pady=2, padx=20)

        self.avatar_buttons = []
        self._load_avatar_list()

        # --- EMOTE LOADOUT SELECTION (6 SLOTS) ---
        ctk.CTkLabel(self, text="Equipped Emotes (Max 6):", font=(FONT_UI, 12)).pack(pady=(10, 2))

        self.slots_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=8)
        self.slots_frame.pack(pady=2, padx=20, fill="x")

        self.slot_buttons = []
        self._build_emote_slots()

        # --- AVAILABLE EMOTES GALLERY ---
        ctk.CTkLabel(self, text="Available Emotes (Click to equip):", font=(FONT_UI, 11, "italic"),
                     text_color="#AAAAAA").pack(pady=(8, 2))

        self.emotes_gallery_frame = ctk.CTkScrollableFrame(self, width=440, height=110, fg_color="#1E1E1E",
                                                           orientation="horizontal")
        self.emotes_gallery_frame.pack(pady=2, padx=20)
        self._load_available_emotes()

        # --- SAVE BUTTON ---
        self.save_btn = ctk.CTkButton(
            self,
            text="SAVE PROFILE",
            font=(FONT_UI, 12, "bold"),
            fg_color="#00FF66",
            text_color="#000000",
            hover_color="#00CC52",
            height=38,
            width=200,
            command=self.save_and_close
        )
        self.save_btn.pack(pady=(15, 15))

    def _load_avatar_list(self):
        avatars = ProfileManager.get_available_avatars()

        for filename in avatars:
            img_path = os.path.join(AVATARS_DIR, filename)
            try:
                pil_img = Image.open(img_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(50, 50))
            except Exception:
                ctk_img = None

            is_selected = (filename == self.selected_avatar)

            btn = ctk.CTkButton(
                self.avatars_frame,
                text="",
                image=ctk_img,
                width=60,
                height=60,
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

    def _build_emote_slots(self):
        for widget in self.slots_frame.winfo_children():
            widget.destroy()
        self.slot_buttons.clear()

        container = ctk.CTkFrame(self.slots_frame, fg_color="transparent")
        container.pack(anchor="center", pady=6)

        for idx in range(6):
            slot_frame = ctk.CTkFrame(container, fg_color="#141414", border_width=1, border_color="#333333",
                                      width=55, height=55, corner_radius=6)
            slot_frame.pack(side="left", padx=4)
            slot_frame.pack_propagate(False)

            emote_filename = self.equipped_emotes[idx]
            btn = ctk.CTkButton(
                slot_frame,
                text=str(idx + 1),
                font=(FONT_UI, 12, "bold"),
                text_color="#666666",
                fg_color="transparent",
                hover_color="#2A2A2A",
                anchor="center",
                command=lambda i=idx: self.unequip_emote(i)
            )
            btn.pack(fill="both", expand=True)

            if emote_filename:
                self._update_slot_button_image(btn, emote_filename)

            self.slot_buttons.append((btn, slot_frame))

    def _update_slot_button_image(self, btn, filename):
        img_path = os.path.join(EMOTES_DIR, filename)
        if os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(40, 40))
                btn.configure(image=ctk_img, text="")
                btn.image = ctk_img
            except Exception:
                pass

    def _load_available_emotes(self):
        for widget in self.emotes_gallery_frame.winfo_children():
            widget.destroy()

        if not os.path.exists(EMOTES_DIR):
            os.makedirs(EMOTES_DIR, exist_ok=True)

        try:
            emotes = [f for f in os.listdir(EMOTES_DIR) if f.lower().endswith(('.png', '.jpg', '.gif', '.jpeg'))]
        except Exception:
            emotes = []

        if not emotes:
            lbl = ctk.CTkLabel(self.emotes_gallery_frame, text="No emotes found in assets/emotes",
                               font=(FONT_UI, 10, "italic"), text_color="#666666")
            lbl.pack(padx=10, pady=10)
            return

        for filename in emotes:
            img_path = os.path.join(EMOTES_DIR, filename)
            is_equipped = filename in self.equipped_emotes

            try:
                pil_img = Image.open(img_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(45, 45))
            except Exception:
                ctk_img = None

            btn = ctk.CTkButton(
                self.emotes_gallery_frame,
                text="",
                image=ctk_img,
                width=55,
                height=55,
                fg_color="#141414" if is_equipped else "#2B2B2B",
                hover_color="#141414" if is_equipped else "#3A3A3A",
                state="disabled" if is_equipped else "normal",
                command=lambda fn=filename: self.equip_emote(fn)
            )
            btn.pack(side="left", padx=5, pady=5)

    def equip_emote(self, filename):
        for idx in range(6):
            if self.equipped_emotes[idx] is None:
                self.equipped_emotes[idx] = filename
                self._build_emote_slots()
                self._load_available_emotes()  # Refresh gallery to disable equipped emote
                break

    def unequip_emote(self, index):
        self.equipped_emotes[index] = None
        self._build_emote_slots()
        self._load_available_emotes()  # Refresh gallery to enable unequipped emote

    def save_and_close(self):
        nick = self.nick_entry.get().strip()
        if not nick:
            nick = "Player"

        active_emotes = [e for e in self.equipped_emotes if e is not None]

        # Ensure profile dictionary is updated correctly
        try:
            ProfileManager.save_profile(
                nickname=nick,
                avatar_filename=self.selected_avatar,
                selected_emotes=active_emotes
            )
        except TypeError:
            # Fallback if save_profile in ProfileManager doesn't accept kwargs directly
            profile_data = ProfileManager.load_profile()
            profile_data["nickname"] = nick
            profile_data["avatar_filename"] = self.selected_avatar
            profile_data["selected_emotes"] = active_emotes
            ProfileManager.save_profile(profile_data)

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()