import os
import random
import customtkinter as ctk
from PIL import Image

FONT_PATH = os.path.join("assets", "fonts", "Kanisah.ttf")
if os.path.exists(FONT_PATH):
    ctk.FontManager.load_font(FONT_PATH)


class GameHeaderWidget(ctk.CTkFrame):
    def __init__(self, master, current_player_name: str = "Mateusz"):
        super().__init__(master, fg_color="transparent")

        self.current_player_name = current_player_name
        self.turn_number = 1

        # 1. Ładowanie obrazu tła
        img_path = os.path.join("assets", "images", "header_bg.jpeg")

        if os.path.exists(img_path):
            self.bg_pil = Image.open(img_path)
            # Skalujemy grafikę do wysokości paska (np. 100px)
            self.bg_image = ctk.CTkImage(
                light_image=self.bg_pil,
                dark_image=self.bg_pil,
                size=(1000, 65)
            )
            self.bg_container = ctk.CTkLabel(self, image=self.bg_image, text="")
            self.bg_container.pack(fill="x", expand=True)
        else:
            # Fallback w razie braku pliku
            self.bg_container = ctk.CTkFrame(self, fg_color="#121212", height=65)
            self.bg_container.pack(fill="x", expand=True)

        # 2. Kontener osadzony DOKŁADNIE wewnątrz drewnianej ramki ze zdjęcia
        # Dzięki relwidth i relheight trafiamy idealnie w środek szyldu!
        self.content_frame = ctk.CTkFrame(self.bg_container, fg_color="transparent")
        self.content_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.48, relheight=0.45)

        # ---------------------------------------------------------------------
        # SEKCJA LEWA: Kostka i Moneta
        # ---------------------------------------------------------------------
        self.left_box = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.left_box.pack(side="left", padx=5)

        self.coin_btn = ctk.CTkButton(
            self.left_box, text="🪙", width=32, height=32,
            font=("Kanisah", 14), fg_color="#2b231b", hover_color="#423629",
            text_color="#d4af37", border_width=1, border_color="#57451c",
            command=self.flip_coin
        )
        self.coin_btn.pack(side="left", padx=2)

        self.dice_btn = ctk.CTkButton(
            self.left_box, text="🎲", width=32, height=32,
            font=("Kanisah", 14), fg_color="#2b231b", hover_color="#423629",
            text_color="#d4af37", border_width=1, border_color="#57451c",
            command=self.roll_d20
        )
        self.dice_btn.pack(side="left", padx=2)

        self.result_lbl = ctk.CTkLabel(
            self.left_box, text="", font=("Kanisah", 14, "bold"), text_color="#d4af37"
        )
        self.result_lbl.pack(side="left", padx=5)

        # ---------------------------------------------------------------------
        # SEKCJA ŚRODKOWA: Wskaźnik Tury
        # ---------------------------------------------------------------------
        self.center_box = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.center_box.pack(side="left", expand=True)

        self.turn_lbl = ctk.CTkLabel(
            self.center_box,
            text=f"TUR {self.turn_number}: {self.current_player_name.upper()}",
            font=("Kanisah", 18, "bold"),
            text_color="#c8a870"  # Ciepłe, starodawne złoto/drewno
        )
        self.turn_lbl.pack()

        # ---------------------------------------------------------------------
        # SEKCJA PRAWA: Przycisk Zmiany Tury
        # ---------------------------------------------------------------------
        self.right_box = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_box.pack(side="right", padx=5)

        self.next_turn_btn = ctk.CTkButton(
            self.right_box, text="End Turn ➔", width=95, height=32,
            font=("Kanisah", 12, "bold"), fg_color="#4a1515", hover_color="#6e2020",
            text_color="#e0e0e0", border_width=1, border_color="#7d2222",
            command=self.pass_turn
        )
        self.next_turn_btn.pack(side="right")

    def flip_coin(self):
        result = random.choice(["HEADS", "TAILS"])
        self.result_lbl.configure(text=f"{result}")

    def roll_d20(self):
        result = random.randint(1, 20)
        self.result_lbl.configure(text=f"D20: {result}")

    def pass_turn(self):
        self.turn_number += 1
        self.turn_lbl.configure(
            text=f"TUR {self.turn_number}: {self.current_player_name.upper()}"
        )