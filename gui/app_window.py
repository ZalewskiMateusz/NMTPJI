import customtkinter as ctk
from gui.menu_view import MenuView

class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Konfiguracja głównego okna
        self.title("NMTPJI - MTG Overlay")
        self.geometry("600x500")

        # Ustawienie motywu (ciemny/jasny)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Osadzenie naszego widoku menu w oknie
        self.menu_view = MenuView(self)
        self.menu_view.pack(fill="both", expand=True, padx=20, pady=20)