import customtkinter as ctk
from gui.components.game_header_widget import GameHeaderWidget
from gui.components.player_board_widget import PlayerBoardWidget
from gui.end_match_window import EndMatchWindow
from utils.profile_manager import ProfileManager


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
        self.hp = max(0, self.hp + delta)

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
        if player_ids and self.active_player_index < len(player_ids):
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
        alive_players = [p for p in self.state.players.values() if getattr(p, "is_alive", True)]

        if len(alive_players) <= 1:
            self.notify_subscribers()
            return

        player_ids = list(self.state.players.keys())
        num_players = len(player_ids)

        for _ in range(num_players):
            self.state.active_player_index = (self.state.active_player_index + 1) % num_players
            current_id = player_ids[self.state.active_player_index]
            current_player = self.state.players[current_id]

            if getattr(current_player, "is_alive", True):
                break

        self.state.turn_number += 1
        self.notify_subscribers()


class OverlayView(ctk.CTkFrame):
    def __init__(self, master, room_config=None):
        super().__init__(master, fg_color="#121212")
        self.room_config = room_config or {}

        # Pobieramy klienta sieciowego z room_config i podpinamy nasłuch akcji gry
        self.client = self.room_config.get("client")
        if self.client:
            self.client.on_message_received = self._on_network_message

        # 1. Górny pasek z akcjami
        self.top_bar = ctk.CTkFrame(self, fg_color="#1E1E1E", height=45)
        self.top_bar.pack(fill="x", padx=10, pady=(10, 5))

        # --- PRZYCISKI PO PRAWEJ STRONIE ---
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

        self.btn_end_match = ctk.CTkButton(
            self.top_bar,
            text="END MATCH",
            font=("Segoe UI", 11, "bold"),
            fg_color="#A51F1F",
            hover_color="#701414",
            height=30,
            command=self.open_end_match_modal,
        )
        self.btn_end_match.pack(side="right", padx=10, pady=8)

        self.header_widget = GameHeaderWidget(self.top_bar)
        self.header_widget.pack(side="left", fill="x", expand=True, padx=10)

        # 2. Inicjalizacja silnika na podstawie listy graczy z lobby
        self.engine = self._init_engine()

        # 3. Kontener na siatkę graczy (grid 2x2)
        self.boards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.boards_container.pack(expand=True, fill="both", padx=10, pady=5)

        self.player_widgets = {}
        self._build_player_grid()

        self.engine.subscribe(self.on_state_changed)
        self.on_state_changed(self.engine.state)

    def _init_engine(self):
        starting_hp = self.room_config.get("starting_hp", 40)
        players_list = self.room_config.get("players", [])

        players_dict = {}

        if players_list:
            for idx, p_info in enumerate(players_list):
                p_id = p_info.get("id", f"p{idx + 1}")
                p_name = p_info.get("name", f"Player {idx + 1}")
                players_dict[p_id] = DummyPlayerState(p_id, p_name, max_hp=starting_hp)
        else:
            host_name = self.room_config.get("host_name", "Player")
            players_dict = {
                "p1": DummyPlayerState("p1", f"{host_name} (YOU)", max_hp=starting_hp),
                "p2": DummyPlayerState("p2", "Player 2", max_hp=starting_hp),
                "p3": DummyPlayerState("p3", "Player 3", max_hp=starting_hp),
                "p4": DummyPlayerState("p4", "Player 4", max_hp=starting_hp),
            }

        return DummyEngine(players_dict)

    def _build_player_grid(self):
        self.boards_container.grid_columnconfigure(0, weight=1, uniform="board_col")
        self.boards_container.grid_columnconfigure(1, weight=1, uniform="board_col")
        self.boards_container.grid_rowconfigure(0, weight=1, uniform="board_row")
        self.boards_container.grid_rowconfigure(1, weight=1, uniform="board_row")

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        players_list = self.room_config.get("players", [])

        player_decks = {p.get("id"): p.get("deck") for p in players_list if isinstance(p, dict)}
        fallback_deck = self.room_config.get("deck_cards") or self.room_config.get("selected_deck")

        # Określamy lokalnego gracza na podstawie profilu
        profile = ProfileManager.load_profile()
        my_nick = profile.get("nickname", "Player")

        for i, (p_id, p_state) in enumerate(self.engine.state.players.items()):
            if i >= len(positions):
                break

            row, col = positions[i]
            deck_to_pass = player_decks.get(p_id) or (fallback_deck if i == 0 else None)

            # Kafelek jest "nasz", jeśli nazwa gracza pasuje do naszego nicku lub to pierwszy gracz gdy brak sieci
            is_local_player = (p_state.name.startswith(my_nick) or (i == 0 and not self.client))

            board = PlayerBoardWidget(
                parent=self.boards_container,
                player_id=p_id,
                player_name=p_state.name,
                engine=self.engine,
                deck_cards=deck_to_pass,
                client=self.client,
                is_local=is_local_player
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
            if self.client:
                self.client.send_action("NEXT_TURN", {})

    # --- ODBIERANIE AKCJI Z SIECI ---
    def _on_network_message(self, message):
        if message.get("type") != "GAME_ACTION":
            return

        action = message.get("action")
        payload = message.get("payload", {})
        self.after(0, lambda: self._process_game_action(action, payload))

    def _process_game_action(self, action, payload):
        p_id = payload.get("player_id")
        p_state = self.engine.state.players.get(p_id) if p_id else None

        if action == "NEXT_TURN":
            self.engine.next_turn()

        elif action == "UPDATE_HP" and p_state:
            p_state.hp = payload.get("hp", p_state.hp)
            self.engine.notify_subscribers()

        elif action == "UPDATE_POISON" and p_state:
            p_state.poison = payload.get("poison", p_state.poison)
            self.engine.notify_subscribers()

        elif action == "UPDATE_TAX" and p_state:
            p_state.cmdr_tax = payload.get("tax", p_state.cmdr_tax)
            self.engine.notify_subscribers()

        elif action == "UPDATE_CMDR_DMG" and p_state:
            p_state.cmdr_damage_received = payload.get("cmdr_damage", {})
            self.engine.notify_subscribers()

        elif action == "TOGGLE_CARD" and p_id in self.player_widgets:
            card_name = payload.get("card_name")
            drawn_qty = payload.get("drawn_qty")
            self.player_widgets[p_id].sync_card_state_from_network(card_name, drawn_qty)

    # --- OBSŁUGA OKNA END MATCH ---
    def open_end_match_modal(self):
        EndMatchWindow(
            parent=self,
            engine=self.engine,
            on_confirm=self.handle_match_finished,
            on_rematch=self.handle_rematch,
            on_resume=self.handle_resume,
        )

    def handle_match_finished(self, winner_name: str):
        print(f"[MATCH FINISHED] Winner: {winner_name}")
        self.exit_match()

    def handle_rematch(self, winner_name: str):
        print(f"[REMATCH INITIATED] Previous Winner: {winner_name}")
        self.exit_match()

    def handle_resume(self):
        print("[MATCH RESUMED] Returning to active game.")

    def exit_match(self):
        if hasattr(self.master, "show_menu"):
            self.master.show_menu()