from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PlayerState:
    # 1. Identyfikatory i podstawowe informacje
    player_id: str                      # Unikalny identyfikator
    name: str                           # Wyświetlana nazwa
    is_host: bool = False               # Czy dany gracz jest hostem pokoju

    # 2. Główne liczniki MTG Commander
    hp: int = 40                        # Domyślny stan życia w Commanderze
    poison: int = 0                     # Licznik znaczników trucizny
    cmdr_tax: int = 0                   # Koszt nakładany na rzucenie dowódcy (+2 za każde rzucenie)

    # 3. Obrażenia od Dowódców (Commander Damage)
    # Słownik: [player_id_przeciwnika] -> ilość odebranych obrażeń
    cmdr_damage_received: Dict[str, int] = field(default_factory=dict)

    # 4. Dodatkowe statystyki talii / gry
    deck_cards_remaining: int = 99      # Liczba kart w bibliotece
    turn_order: int = 0                 # Kolejność w tury (0, 1, 2, 3)

    # ------------------------------------------------------------------ #
    #  DYNAMICZNY STAN ŻYCIA (MTG COMMANDER RULES)
    # ------------------------------------------------------------------ #
    @property
    def is_alive(self) -> bool:
        """
        Automatycznie wylicza, czy gracz żyje.
        Gracz PRZEGRYWA gdy:
        - HP <= 0
        - Poison >= 10
        - Otrzymał >= 21 Commander Damage od jakiegokolwiek pojedynczego przeciwnika
        """
        if self.hp <= 0:
            return False
        if self.poison >= 10:
            return False
        if any(dmg >= 21 for dmg in self.cmdr_damage_received.values()):
            return False
        return True

    # ------------------------------------------------------------------ #
    #  ALIAS - DLA BEZPIECZEŃSTWA KOMPATYBILNOŚCI Z UI
    # ------------------------------------------------------------------ #
    @property
    def commander_tax(self) -> int:
        return self.cmdr_tax

    @commander_tax.setter
    def commander_tax(self, value: int):
        self.cmdr_tax = max(0, value)

    @property
    def commander_damage(self) -> Dict[str, int]:
        return self.cmdr_damage_received

    @commander_damage.setter
    def commander_damage(self, value: Dict[str, int]):
        self.cmdr_damage_received = value

    # ------------------------------------------------------------------ #
    #  METODY POMOCNICZE
    # ------------------------------------------------------------------ #
    def receive_cmdr_damage(self, attacker_id: str, delta: int):
        """Zwiększa lub zmniejsza obrażenia od konkretnego dowódcy."""
        current = self.cmdr_damage_received.get(attacker_id, 0)
        self.cmdr_damage_received[attacker_id] = max(0, current + delta)

    def update_hp(self, delta: int):
        """Aktualizuje HP."""
        self.hp += delta

    def update_poison(self, delta: int):
        """Aktualizuje trutkę."""
        self.poison = max(0, self.poison + delta)

    def update_tax(self, delta: int):
        """Aktualizuje Commander Tax."""
        self.cmdr_tax = max(0, self.cmdr_tax + delta)

    def to_dict(self) -> dict:
        """Konwertuje obiekt do słownika w celu serializacji do JSON."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "is_host": self.is_host,
            "is_alive": self.is_alive,
            "hp": self.hp,
            "poison": self.poison,
            "cmdr_tax": self.cmdr_tax,
            "cmdr_damage_received": self.cmdr_damage_received,
            "deck_cards_remaining": self.deck_cards_remaining,
            "turn_order": self.turn_order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerState":
        """Tworzy obiekt PlayerState z słownika JSON."""
        return cls(
            player_id=data["player_id"],
            name=data["name"],
            is_host=data.get("is_host", False),
            hp=data.get("hp", 40),
            poison=data.get("poison", 0),
            cmdr_tax=data.get("cmdr_tax", 0),
            cmdr_damage_received=data.get("cmdr_damage_received", {}),
            deck_cards_remaining=data.get("deck_cards_remaining", 99),
            turn_order=data.get("turn_order", 0),
        )


@dataclass
class RoomState:
    room_id: str
    host_id: str
    players: Dict[str, PlayerState] = field(default_factory=dict)
    turn_order: List[str] = field(default_factory=list)
    current_turn_index: int = 0
    turn_number: int = 1
    game_started: bool = False

    def get_current_player(self) -> Optional[PlayerState]:
        if not self.turn_order:
            return None
        current_id = self.turn_order[self.current_turn_index]
        return self.players.get(current_id)

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "host_id": self.host_id,
            "players": {p_id: p.to_dict() for p_id, p in self.players.items()},
            "turn_order": self.turn_order,
            "current_turn_index": self.current_turn_index,
            "turn_number": self.turn_number,
            "game_started": self.game_started,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RoomState":
        players = {
            p_id: PlayerState.from_dict(p_data)
            for p_id, p_data in data.get("players", {}).items()
        }
        return cls(
            room_id=data["room_id"],
            host_id=data["host_id"],
            players=players,
            turn_order=data.get("turn_order", []),
            current_turn_index=data.get("current_turn_index", 0),
            turn_number=data.get("turn_number", 1),
            game_started=data.get("game_started", False),
        )