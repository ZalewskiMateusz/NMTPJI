import customtkinter as ctk

# Importujemy osobne komponenty z folderu components
from gui.components.game_header_widget import GameHeaderWidget
from gui.components.player_board_widget import PlayerBoardWidget


class RoomView(ctk.CTkFrame):
    def __init__(self, master, deck_name: str = "", cards: dict = None):
        super().__init__(master)

        self.deck_name = deck_name
        self.cards = cards or {}

        # Siatka główna: Wiersz 0 (Header), Wiersz 1 (4 x Player Board)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Nagłówek (Góra)
        self.header = GameHeaderWidget(self, current_player_name="Mateusz")
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # 2. Kontener na graczy (Dół 2x2)
        self.players_container = ctk.CTkFrame(self, fg_color="transparent")
        self.players_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self.players_container.grid_columnconfigure((0, 1), weight=1)
        self.players_container.grid_rowconfigure((0, 1), weight=1)

        players_data = [
            {"name": "Mateusz (You)", "row": 0, "col": 0},
            {"name": "Opponent 1", "row": 0, "col": 1},
            {"name": "Opponent 2", "row": 1, "col": 0},
            {"name": "Opponent 3", "row": 1, "col": 1},
        ]

        self.player_boards = []
        for p in players_data:
            board = PlayerBoardWidget(self.players_container, player_name=p["name"])
            board.grid(row=p["row"], column=p["col"], padx=5, pady=5, sticky="nsew")
            self.player_boards.append(board)