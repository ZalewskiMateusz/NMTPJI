from typing import Callable, List, Optional
from backend.models import PlayerState, RoomState


class RoomEngine:
    def __init__(self, room_id: str, host_id: str):
        # Inicjalizujemy stan pokoju
        self.state = RoomState(room_id=room_id, host_id=host_id)
        # Lista funkcji (callbacków), które słuchają zmian stanu (np. UI)
        self._subscribers: List[Callable[[RoomState], None]] = []

    def subscribe(self, callback: Callable[[RoomState], None]):
        """Rejestruje funkcję z UI, która ma być wywołana po każdej zmianie stanu."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    subscribe_state_change = subscribe

    def notify_subscribers(self):
        """Powiadamia wszystkie zapisane komponenty (UI) o zmianie stanu."""
        for callback in self._subscribers:
            callback(self.state)

    def add_player(self, player_id: str, name: str) -> PlayerState:
        """Dodaje nowego gracza do pokoju."""
        is_host = player_id == self.state.host_id
        player = PlayerState(player_id=player_id, name=name, is_host=is_host)

        self.state.players[player_id] = player
        if player_id not in self.state.turn_order:
            self.state.turn_order.append(player_id)

        self.notify_subscribers()
        return player

    def remove_player(self, player_id: str):
        """Usuwa gracza z pokoju."""
        if player_id in self.state.players:
            del self.state.players[player_id]
        if player_id in self.state.turn_order:
            self.state.turn_order.remove(player_id)
        self.notify_subscribers()

    def start_game(self):
        """Rozpoczyna grę."""
        if self.state.players:
            self.state.game_started = True
            self.state.current_turn_index = 0
            self.state.turn_number = 1
            self.notify_subscribers()

    def pass_turn(self):
        """Przechodzi do tury następnego ŻYWEGO gracza."""
        if not self.state.turn_order or not self.state.game_started:
            return

        total_players = len(self.state.turn_order)
        attempts = 0

        while attempts < total_players:
            self.state.current_turn_index = (self.state.current_turn_index + 1) % total_players

            if self.state.current_turn_index == 0:
                self.state.turn_number += 1

            current_player = self.state.get_current_player()
            if current_player and current_player.is_alive:
                break

            attempts += 1

        self.notify_subscribers()

    # Alias dla wstecznej kompatybilności z test.py:
    next_turn = pass_turn