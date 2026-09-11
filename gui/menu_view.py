import os
import customtkinter as ctk

# 1. Path to font
FONT_PATH = os.path.join("assets", "fonts", "Kanisah.ttf")

# 2. Register font
if os.path.exists(FONT_PATH):
    ctk.FontManager.load_font(FONT_PATH)


class MenuView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        # New Room Button
        self.new_room_button = ctk.CTkButton(
            self,
            text="New Room",
            font=("Kanisah", 20, "bold"),
            command=self.create_new_room_action
        )
        self.new_room_button.pack(pady=10, padx=20)

        # Join Room Button
        self.find_room_button = ctk.CTkButton(
            self,
            text="Join Room",
            font=("Kanisah", 20, "bold"),
            command=self.join_room_action
        )
        self.find_room_button.pack(pady=10, padx=20)

        # Decks Editor Button
        self.deck_editor_button = ctk.CTkButton(
            self,
            text="DECKS",
            font=("Kanisah", 20, "bold"),
            command=self.deck_editor_action
        )
        self.deck_editor_button.pack(pady=10, padx=20)

    # Reakcje na nawigację w GUI (zarządza nimi widok/okno)
    def create_new_room_action(self):
        print("Click: New Room")

    def join_room_action(self):
        print("Click: Join Room")

    def deck_editor_action(self):
        print("Click: DECKS")