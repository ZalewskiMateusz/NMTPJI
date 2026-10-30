import os
import customtkinter as ctk
from gui.components.game_header_widget import GameHeaderWidget
from gui.components.player_board_widget import PlayerBoardWidget
from gui.end_match_window import EndMatchWindow
from utils.profile_manager import ProfileManager, AVATARS_DIR
from backend.models import RoomState, PlayerState

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ClientEngine:
    """Client engine maintaining current room state and notifying UI subscribers."""

    def __init__(self, room_state: RoomState):
        self.state = room_state
        self.subscribers = []

    def subscribe(self, callback):
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def notify_subscribers(self):
        for callback in self.subscribers:
            callback(self.state)

    def update_state(self, state_dict):
        self.state = RoomState.from_dict(state_dict)
        self.notify_subscribers()


class OverlayView(ctk.CTkFrame):
    def __init__(self, master, room_config=None):
        super().__init__(master, fg_color="#121212")
        self.room_config = room_config or {}

        # View tracking variables (local user preferences)
        self.focused_player_id = None
        self.current_duel_opponent = None
        self.follow_active_player = False

        # Retrieve network client from room_config and bind game action listener
        self.client = self.room_config.get("client")
        if self.client:
            self.client.on_message_received = self._on_network_message

        # Local player identifier
        profile = ProfileManager.load_profile()
        self.my_nickname = profile.get("nickname", "Player")

        # 1. Initialize client engine based on room_config state or lobby players
        self.engine = self._init_client_engine()
        self.my_player_id = self._resolve_my_player_id()

        # 2. Top bar with GameHeaderWidget
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

        # 3. Players grid container
        self.boards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.boards_container.pack(expand=True, fill="both", padx=10, pady=5)

        self.player_widgets = {}
        self.player_positions = {}

        self._configure_grid_layout()
        self._build_player_grid()

        self.engine.subscribe(self.on_state_changed)
        self.on_state_changed(self.engine.state)

    def _init_client_engine(self):
        state_data = self.room_config.get("state")
        if state_data:
            room_state = RoomState.from_dict(state_data)
        else:
            starting_hp = self.room_config.get("starting_hp", 40)
            players_list = self.room_config.get("players", [])
            first_player_id = self.room_config.get("first_player_id")

            host_id = players_list[0].get("id", "p1") if players_list else "p1"
            room_state = RoomState(room_id="room_1", host_id=host_id, game_started=True)

            if players_list:
                for idx, p_info in enumerate(players_list):
                    p_id = p_info.get("id", f"p{idx + 1}")
                    p_name = p_info.get("name", f"Player {idx + 1}")
                    p_avatar = p_info.get("avatar", "jace.png")

                    p_state = PlayerState(player_id=p_id, name=p_name, hp=starting_hp)
                    p_state.avatar = p_avatar
                    room_state.players[p_id] = p_state
                    if p_id not in room_state.turn_order:
                        room_state.turn_order.append(p_id)
            else:
                profile = ProfileManager.load_profile()
                host_name = profile.get("nickname", "Host")
                p_state = PlayerState(player_id="p1", name=host_name, hp=starting_hp, is_host=True)
                room_state.players["p1"] = p_state
                room_state.turn_order.append("p1")

            if first_player_id and first_player_id in room_state.turn_order:
                room_state.current_turn_index = room_state.turn_order.index(first_player_id)

        return ClientEngine(room_state)

    def _resolve_my_player_id(self):
        players_list = self.room_config.get("players", [])
        for p in players_list:
            if isinstance(p, dict) and p.get("name") == self.my_nickname:
                return p.get("id")

        for p_id, p_state in self.engine.state.players.items():
            if p_state.name.startswith(self.my_nickname):
                return p_id

        return list(self.engine.state.players.keys())[0] if self.engine.state.players else "p1"

    def _configure_grid_layout(self):
        self.boards_container.grid_columnconfigure(0, weight=1, uniform="board_col")
        self.boards_container.grid_columnconfigure(1, weight=1, uniform="board_col")
        self.boards_container.grid_rowconfigure(0, weight=1, uniform="board_row")
        self.boards_container.grid_rowconfigure(1, weight=1, uniform="board_row")

    def _get_slot_config(self, idx, num_players):
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
                total_players=num_players,
                all_players=self.engine.state.players,
                on_fullscreen_callback=self.toggle_focus_player,
                on_duel_callback=self.enable_duel_mode,
                on_emote_callback=lambda pid, emote: self.send_global_action("PLAY_EMOTE",
                                                                             {"player_id": pid, "emote": emote})
            )
            board.grid(row=row, column=col, columnspan=c_span, sticky="nsew", padx=padx_val, pady=5)
            self.player_widgets[p_id] = board

    def enable_duel_mode(self, opponent_id):
        self.current_duel_opponent = opponent_id
        self.focused_player_id = f"duel_{opponent_id}"

        for p_id, widget in self.player_widgets.items():
            if p_id == self.my_player_id:
                widget.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
            elif p_id == opponent_id:
                widget.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
            else:
                widget.grid_remove()

    def toggle_focus_player(self, player_id):
        if self.focused_player_id == player_id:
            self.reset_to_grid_view()
        else:
            self.focus_player(player_id)

    def focus_player(self, player_id):
        if player_id not in self.player_widgets:
            return

        self.focused_player_id = player_id
        self.current_duel_opponent = None

        for p_id, widget in self.player_widgets.items():
            if p_id == player_id:
                widget.grid(
                    row=0, column=0, rowspan=2, columnspan=2, sticky="nsew", padx=5, pady=5
                )
            else:
                widget.grid_remove()

    def reset_to_grid_view(self):
        self.focused_player_id = None
        self.current_duel_opponent = None
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
        """Sends an action through the network client to the server."""
        if self.client and self.client.is_connected:
            self.client.send_action(action_type, payload)

    def on_state_changed(self, state):
        self.header_widget.update_from_state(state)
        for p_id, board in self.player_widgets.items():
            board.update_from_state(state)

        if self.follow_active_player:
            active_player = state.get_current_player()
            if active_player:
                self.focus_player(active_player.player_id)

    def handle_header_action(self, action_type, payload):
        if action_type == "NEXT_TURN":
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

    # --- NETWORK MESSAGE HANDLING ---
    def _on_network_message(self, message):
        msg_type = message.get("type")

        if msg_type == "GAME_STATE_UPDATE":
            state_dict = message.get("state")
            if state_dict:
                self.after(0, lambda: self.engine.update_state(state_dict))

            action = message.get("action")
            payload = message.get("payload", {})
            if action == "PLAY_EMOTE":
                self.after(0, lambda: self._process_emote(payload))

        elif msg_type == "GAME_ACTION":
            action = message.get("action")
            payload = message.get("payload", {})
            if action == "PLAY_EMOTE":
                self.after(0, lambda: self._process_emote(payload))

    def _process_emote(self, payload):
        actual_payload = payload.get("payload") if isinstance(payload, dict) and "payload" in payload else payload
        if not isinstance(actual_payload, dict):
            actual_payload = payload

        sender_id = actual_payload.get("player_id")
        emote_filename = actual_payload.get("emote")

        if sender_id in self.player_widgets:
            self.player_widgets[sender_id]._animate_flying_emote(emote_filename)

    # --- END MATCH MODAL HANDLING ---
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