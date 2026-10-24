import customtkinter as ctk
from gui.components.game_header_widget import GameHeaderWidget
from gui.components.player_board_widget import PlayerBoardWidget
from gui.end_match_window import EndMatchWindow
from utils.profile_manager import ProfileManager


class DummyPlayerState:

    def __init__(self, player_id, name, max_hp=40, avatar="jace.png"):
        self.player_id = player_id
        self.name = name
        self.hp = max_hp
        self.max_hp = max_hp
        self.avatar = avatar
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
        alive_players = [
            p for p in self.state.players.values() if getattr(p, "is_alive", True)
        ]

        if len(alive_players) <= 1:
            self.notify_subscribers()
            return

        player_ids = list(self.state.players.keys())
        num_players = len(player_ids)

        for _ in range(num_players):
            self.state.active_player_index = (
                                                     self.state.active_player_index + 1
                                             ) % num_players
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

        # Zmienne śledzenia widoku (lokalne preferencje użytkownika)
        self.focused_player_id = None  # None = widok siatki, p_id = full screen
        self.follow_active_player = False  # Czy automatycznie powiększać aktywnego gracza

        # Pobieramy klienta sieciowego z room_config i podpinamy nasłuch akcji gry
        self.client = self.room_config.get("client")
        if self.client:
            self.client.on_message_received = self._on_network_message

        # Identyfikator lokalnego gracza
        profile = ProfileManager.load_profile()
        self.my_nickname = profile.get("nickname", "Player")
        self.my_player_id = self._resolve_my_player_id()

        # 1. Inicjalizacja silnika na podstawie listy graczy z lobby i wylosowanego pierwszego gracza
        self.engine = self._init_engine()

        # 2. Górny pasek z GameHeaderWidget (zawsze widoczny na górze)
        self.top_bar = ctk.CTkFrame(
            self, fg_color="#1E1E1E", height=50, corner_radius=0
        )
        self.top_bar.pack(fill="x", padx=0, pady=0)
        self.top_bar.pack_propagate(False)

        self.header_widget = GameHeaderWidget(
            master=self.top_bar,
            room_config=self.room_config,
            is_host=self.room_config.get("is_host", True),
            on_action_callback=self.handle_header_action,
        )
        self.header_widget.pack(fill="both", expand=True)

        # 3. Kontener na siatkę graczy
        self.boards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.boards_container.pack(expand=True, fill="both", padx=10, pady=5)

        self.player_widgets = {}
        self.player_positions = {}  # Zapamiętujemy oryginalne pozycje (row, col, columnspan)

        self._configure_grid_layout()
        self._build_player_grid()

        self.engine.subscribe(self.on_state_changed)
        self.on_state_changed(self.engine.state)

    def _resolve_my_player_id(self):
        players_list = self.room_config.get("players", [])
        for p in players_list:
            if isinstance(p, dict) and p.get("name") == self.my_nickname:
                return p.get("id")
        return "p1"

    def _init_engine(self):
        starting_hp = self.room_config.get("starting_hp", 40)
        players_list = self.room_config.get("players", [])
        first_player_id = self.room_config.get("first_player_id")

        players_dict = {}
        active_index = 0

        if players_list:
            for idx, p_info in enumerate(players_list):
                p_id = p_info.get("id", f"p{idx + 1}")
                p_name = p_info.get("name", f"Player {idx + 1}")
                p_avatar = p_info.get("avatar", "jace.png")  # Pobieramy awatar z danych gracza

                players_dict[p_id] = DummyPlayerState(p_id, p_name, max_hp=starting_hp, avatar=p_avatar)

                if first_player_id and p_id == first_player_id:
                    active_index = idx
        else:
            host_name = self.room_config.get("host_name", "Player")
            players_dict = {
                "p1": DummyPlayerState("p1", f"{host_name} (YOU)", max_hp=starting_hp),
                "p2": DummyPlayerState("p2", "Player 2", max_hp=starting_hp),
                "p3": DummyPlayerState("p3", "Player 3", max_hp=starting_hp),
                "p4": DummyPlayerState("p4", "Player 4", max_hp=starting_hp),
            }

        engine = DummyEngine(players_dict)
        engine.state.active_player_index = active_index
        return engine

    def _configure_grid_layout(self):
        """Konfiguruje wagi kolumn i wierszy siatki zależnie od liczby graczy."""
        self.boards_container.grid_columnconfigure(0, weight=1, uniform="board_col")
        self.boards_container.grid_columnconfigure(1, weight=1, uniform="board_col")
        self.boards_container.grid_rowconfigure(0, weight=1, uniform="board_row")
        self.boards_container.grid_rowconfigure(1, weight=1, uniform="board_row")

    def _get_slot_config(self, idx, num_players):
        """Zwraca parametry układu (row, col, columnspan) dla graczy w overlayu."""
        if num_players == 2:
            pos = [(0, 0, 2), (1, 0, 2)]
        elif num_players == 3:
            pos = [(0, 0, 1), (0, 1, 1), (1, 0, 2)]
        else:
            pos = [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]

        return pos[idx] if idx < len(pos) else (0, 0, 1)

    def _build_player_grid(self):
        num_players = len(self.engine.state.players)
        players_list = self.room_config.get("players", [])

        player_decks = {
            p.get("id"): p.get("deck")
            for p in players_list
            if isinstance(p, dict)
        }
        fallback_deck = self.room_config.get("deck_cards") or self.room_config.get(
            "selected_deck"
        )

        for i, (p_id, p_state) in enumerate(self.engine.state.players.items()):
            row, col, c_span = self._get_slot_config(i, num_players)
            self.player_positions[p_id] = (row, col, c_span)

            deck_to_pass = player_decks.get(p_id) or (
                fallback_deck if i == 0 else None
            )
            is_local_player = (p_id == self.my_player_id or p_state.name.startswith(self.my_nickname))

            padx_val = (120, 120) if (num_players == 3 and i == 2) else 5

            board = PlayerBoardWidget(
                parent=self.boards_container,
                player_id=p_id,
                player_name=p_state.name,
                engine=self.engine,
                deck_cards=deck_to_pass,
                client=self.client,
                is_local=is_local_player,
            )
            board.grid(row=row, column=col, columnspan=c_span, sticky="nsew", padx=padx_val, pady=5)
            self.player_widgets[p_id] = board

            # Dodajemy uniwersalny, lokalny przycisk Full Screen w prawym dolnym rogu każdego kafelka
            self._add_fullscreen_button_to_board(board, p_id)

    def _add_fullscreen_button_to_board(self, board_widget, player_id):
        """Dodaje dyskretny przycisk Full Screen w prawym dolnym rogu planszy gracza."""
        btn_fs = ctk.CTkButton(
            board_widget,
            text="⛶",
            width=26,
            height=26,
            font=("Segoe UI", 12, "bold"),
            fg_color="#2B2B2B",
            hover_color="#3A3A3A",
            text_color="#00FF66",
            corner_radius=6,
            command=lambda: self.toggle_focus_player(player_id)
        )
        btn_fs.place(relx=0.98, rely=0.95, anchor="se")

    def toggle_focus_player(self, player_id):
        """Lokalne przełączenie Full Screen dla wybranego stołu (header pozostaje widoczny)."""
        if self.focused_player_id == player_id:
            self.reset_to_grid_view()
        else:
            self.focus_player(player_id)

    def focus_player(self, player_id):
        """Rozciąga kafel wskazanego gracza na cały kontener pod headerem i ukrywa pozostałe."""
        if player_id not in self.player_widgets:
            return

        self.focused_player_id = player_id

        for p_id, widget in self.player_widgets.items():
            if p_id == player_id:
                widget.grid(
                    row=0, column=0, rowspan=2, columnspan=2, sticky="nsew", padx=5, pady=5
                )
            else:
                widget.grid_remove()

    def reset_to_grid_view(self):
        """Przywraca standardowy widok siatki dla wszystkich graczy."""
        self.focused_player_id = None
        num_players = len(self.engine.state.players)

        for p_id, widget in self.player_widgets.items():
            if p_id in self.player_positions:
                row, col, c_span = self.player_positions[p_id]
                i = list(self.player_widgets.keys()).index(p_id)
                padx_val = (120, 120) if (num_players == 3 and i == 2) else 5

                widget.grid(
                    row=row,
                    column=col,
                    rowspan=1,
                    columnspan=c_span,
                    sticky="nsew",
                    padx=padx_val,
                    pady=5,
                )

    def send_global_action(self, action_type, payload):
        """Uniwersalna procedura wysyłająca akcję globalną do wszystkich graczy przez sieć."""
        data = {
            "type": "GAME_ACTION",
            "action": action_type,
            "player_id": self.my_player_id,
            "payload": payload
        }

        if self.client:
            self.client.send_raw(data)
        elif hasattr(self, "server") and self.server:
            self.server.broadcast(data)
            self._process_game_action(action_type, payload)

    def on_state_changed(self, state):
        self.header_widget.update_from_state(state)
        for p_id, board in self.player_widgets.items():
            board.update_from_state(state)

        if self.follow_active_player:
            active_player = state.get_current_player()
            if active_player:
                self.focus_player(active_player.player_id)

    def handle_header_action(self, action_type, payload):
        """Obsługuje akcje globalne z nagłówka (Next Turn, End Match, Rzuty itp.)."""
        if action_type == "NEXT_TURN":
            if hasattr(self.engine, "next_turn"):
                self.engine.next_turn()
                self.send_global_action("NEXT_TURN", {})

        elif action_type == "END_MATCH":
            self.open_end_match_modal()
            self.send_global_action("END_MATCH", {})

        elif action_type == "START_GAME":
            self.send_global_action("START_GAME", payload)

        elif action_type == "TOGGLE_FOLLOW_PLAYER":
            self.follow_active_player = not self.follow_active_player
            if self.follow_active_player:
                active_p = self.engine.state.get_current_player()
                if active_p:
                    self.focus_player(active_p.player_id)
            else:
                self.reset_to_grid_view()

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

        elif action == "END_MATCH":
            self.open_end_match_modal()

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
            self.player_widgets[p_id].sync_card_state_from_network(
                card_name, drawn_qty
            )

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
        self.exit_match()

    def handle_rematch(self, winner_name: str):
        self.exit_match()

    def handle_resume(self):
        pass

    def exit_match(self):
        if hasattr(self.master, "show_menu"):
            self.master.show_menu()