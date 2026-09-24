import customtkinter as ctk


class RoomView(ctk.CTkFrame):
    def __init__(self, master, room_config):
        super().__init__(master, fg_color="#121212")
        self.room_config = room_config

        # --- HEADER ---
        self.header_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", height=50)
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))

        room_name = self.room_config.get("name", "Game Room")
        deck_name = self.room_config.get("selected_deck", "No Deck")

        self.info_label = ctk.CTkLabel(
            self.header_frame,
            text=f"ROOM: {room_name}  |  MY DECK: {deck_name}",
            font=("Segoe UI", 13, "bold"),
            text_color="#00FF66"
        )
        self.info_label.pack(side="left", padx=15, pady=10)

        self.leave_btn = ctk.CTkButton(
            self.header_frame,
            text="LEAVE ROOM",
            font=("Segoe UI", 12, "bold"),
            fg_color="#2B2B2B",
            hover_color="#5A1E1E",
            height=32,
            command=self.leave_room_action
        )
        self.leave_btn.pack(side="right", padx=15, pady=10)

        # --- GRID KONTENER NA GRACZY ---
        self.boards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.boards_container.pack(expand=True, fill="both", padx=10, pady=10)

        # Generujemy odpowiednią siatkę
        self._build_player_grid()

    def _build_player_grid(self):
        max_players = self.room_config.get("max_players", 4)

        # Słownik z pozycjami (row, col, columnspan) w zależności od liczby graczy
        layout_map = {
            2: [
                {"row": 0, "col": 0, "span": 1},
                {"row": 0, "col": 1, "span": 1}
            ],
            3: [
                {"row": 0, "col": 0, "span": 1},
                {"row": 0, "col": 1, "span": 1},
                {"row": 1, "col": 0, "span": 2}  # Trzeci gracz na dole na całą szerokość
            ],
            4: [
                {"row": 0, "col": 0, "span": 1},
                {"row": 0, "col": 1, "span": 1},
                {"row": 1, "col": 0, "span": 1},
                {"row": 1, "col": 1, "span": 1}
            ]
        }

        positions = layout_map.get(max_players, layout_map[4])

        # Configure Grid Weights (żeby kafelki proporcjonalnie się rozciągały)
        self.boards_container.grid_columnconfigure(0, weight=1)
        self.boards_container.grid_columnconfigure(1, weight=1)
        self.boards_container.grid_rowconfigure(0, weight=1)

        if max_players > 2:
            self.boards_container.grid_rowconfigure(1, weight=1)

        # Tworzenie kafelków graczy (na razie jako podglądowe punkty/frame'y)
        for i, pos in enumerate(positions):
            is_host = (i == 0)
            player_title = f"Player {i + 1} (YOU)" if is_host else f"Player {i + 1} (Waiting...)"

            # W tym miejscu w przyszłości wstawimy Twój gotowy PlayerBoardWidget!
            board_slot = ctk.CTkFrame(
                self.boards_container,
                fg_color="#1E1E1E",
                border_color="#00FF66" if is_host else "#333333",
                border_width=2 if is_host else 1,
                corner_radius=12
            )
            board_slot.grid(
                row=pos["row"],
                column=pos["col"],
                columnspan=pos["span"],
                sticky="nsew",
                padx=6,
                pady=6
            )

            # Tymczasowa etykieta wewnątrz slotu
            lbl = ctk.CTkLabel(
                board_slot,
                text=player_title,
                font=("Segoe UI", 16, "bold"),
                text_color="#FFFFFF" if is_host else "#666666"
            )
            lbl.place(relx=0.5, rely=0.5, anchor="center")

    def leave_room_action(self):
        if hasattr(self.master, "show_menu"):
            self.master.show_menu()