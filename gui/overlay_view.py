import customtkinter as ctk
from gui.components.game_header_widget import GameHeaderWidget
from gui.components.player_board_widget import PlayerBoardWidget


class DummyPlayerState:
    def __init__(self, player_id, name, max_hp=40):
        self.player_id = player_id
        self.name = name
        self.hp = max_hp
        self.max_hp = max_hp
        self.poison = 0
        self.cmdr_tax = 0
        self.is_alive = True
        self.cmdr_damage_received = {}

    def update_hp(self, delta):
        self.hp += delta

    def update_poison(self, delta):
        self.poison = max(0, self.poison + delta)

    def update_tax(self, delta):
        self.cmdr_tax = max(0, self.cmdr_tax + delta)

    def receive_cmdr_damage(self, opp_id, delta):
        curr = self.cmdr_damage_received.get(opp_id, 0)
        self.cmdr_damage_received[opp_id] = max(0, curr + delta)


class DummyGameState:
    def __init__(self, players):
        self.players = players
        self.turn_number = 1
        self.active_player_index = 0

    def get_current_player(self):
        player_ids = list(self.players.keys())
        if player_ids:
            return self.players[player_ids[self.active_player_index]]
        return None


class DummyEngine:
    def __init__(self, players_dict):
        self.state = DummyGameState(players_dict)
        self.subscribers = []

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def notify_subscribers(self):
        for callback in self.subscribers:
            callback(self.state)

    def next_turn(self):
        # 1. Filtrujemy tylko żywych graczy
        alive_players = [p for p in self.state.players.values() if getattr(p, "is_alive", True)]

        # Jeśli nikt lub tylko 1 osoba żyje, nie przełączamy tury
        if len(alive_players) <= 1:
            self.notify_subscribers()
            return

        player_ids = list(self.state.players.keys())
        num_players = len(player_ids)

        # 2. Szukamy następnego ŻYWEGO gracza
        for _ in range(num_players):
            self.state.active_player_index = (self.state.active_player_index + 1) % num_players
            current_id = player_ids[self.state.active_player_index]
            current_player = self.state.players[current_id]

            if getattr(current_player, "is_alive", True):
                break

        # 3. Zwiększamy numer tury i odświeżamy UI
        self.state.turn_number += 1
        self.notify_subscribers()


class OverlayView(ctk.CTkFrame):
    def __init__(self, master, room_config=None):
        super().__init__(master, fg_color="#121212")
        self.room_config = room_config or {}

        # 1. Górny pasek z akcjami
        self.top_bar = ctk.CTkFrame(self, fg_color="#1E1E1E", height=45)
        self.top_bar.pack(fill="x", padx=10, pady=(10, 5))

        # Przycisk NEXT TURN obok EXIT MATCH
        self.btn_next_turn = ctk.CTkButton(
            self.top_bar,
            text="NEXT TURN ➔",
            font=("Segoe UI", 11, "bold"),
            fg_color="#1F6AA5",
            hover_color="#144870",
            height=30,
            command=self.next_turn_action,
        )
        self.btn_next_turn.pack(side="right", padx=(0, 10), pady=8)

        self.btn_exit = ctk.CTkButton(
            self.top_bar,
            text="EXIT MATCH",
            font=("Segoe UI", 11, "bold"),
            fg_color="#2B2B2B",
            hover_color="#5A1E1E",
            height=30,
            command=self.exit_match,
        )
        self.btn_exit.pack(side="right", padx=10, pady=8)

        self.header_widget = GameHeaderWidget(self.top_bar)
        self.header_widget.pack(side="left", fill="x", expand=True, padx=10)

        # 2. Inicjalizacja silnika
        self.engine = self._init_engine()

        # 3. Kontener na siatkę graczy 2x2
        self.boards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.boards_container.pack(expand=True, fill="both", padx=10, pady=5)

        self.player_widgets = {}
        self._build_player_grid()

        self.engine.subscribe(self.on_state_changed)
        self.on_state_changed(self.engine.state)

    def _init_engine(self):
        starting_hp = self.room_config.get("starting_hp", 40)
        host_name = self.room_config.get("host_name", "Mateusz")

        players = {
            "p1": DummyPlayerState("p1", f"{host_name} (YOU)", max_hp=starting_hp),
            "p2": DummyPlayerState("p2", "Player 2", max_hp=starting_hp),
            "p3": DummyPlayerState("p3", "Player 3", max_hp=starting_hp),
            "p4": DummyPlayerState("p4", "Player 4", max_hp=starting_hp),
        }
        return DummyEngine(players)

    def _build_player_grid(self):
        self.boards_container.grid_columnconfigure(0, weight=1)
        self.boards_container.grid_columnconfigure(1, weight=1)
        self.boards_container.grid_rowconfigure(0, weight=1)
        self.boards_container.grid_rowconfigure(1, weight=1)

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for i, (p_id, p_state) in enumerate(self.engine.state.players.items()):
            row, col = positions[i]
            board = PlayerBoardWidget(
                parent=self.boards_container,
                player_id=p_id,
                player_name=p_state.name,
                engine=self.engine,
            )
            board.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            self.player_widgets[p_id] = board

    def on_state_changed(self, state):
        self.header_widget.update_from_state(state)
        for p_id, board in self.player_widgets.items():
            board.update_from_state(state)

    def next_turn_action(self):
        if hasattr(self.engine, "next_turn"):
            self.engine.next_turn()

    def exit_match(self):
        if hasattr(self.master, "show_menu"):
            self.master.show_menu()