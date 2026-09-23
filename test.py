import customtkinter as ctk

# Importujemy cały RoomView, który spina w sobie GameHeaderWidget oraz PlayerBoardWidget
from gui.room_view import RoomView


def run_preview():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("MTG Commander Room - Full Preview")
    root.geometry("1100x850")

    # Osadzamy cały gotowy widok gry
    room = RoomView(root)
    room.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    run_preview()