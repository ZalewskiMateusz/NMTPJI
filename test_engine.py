from backend.room_engine import RoomEngine

def on_state_changed(state):
    print("\n--- [NOTIF] ZMIANA STANU POKOJU ---")
    print(f"Tura {state.turn_number} | Aktywny gracz: {state.get_current_player().name if state.get_current_player() else 'Brak'}")
    for p_id, p in state.players.items():
        print(f"  • {p.name}: HP={p.hp}, Poison={p.poison}, Żywy={p.is_alive}, CmdrDmg={p.cmdr_damage_received}")

# 1. Inicjalizacja pokoju
engine = RoomEngine(room_id="ROOM_123", host_id="player_1")
engine.subscribe_state_change(on_state_changed)

# 2. Dodanie graczy
p1 = engine.add_player("player_1", "Mateusz")
p2 = engine.add_player("player_2", "Natala")
p3 = engine.add_player("player_3", "Opponent 3")

# 3. Start gry i testowanie akcji
engine.start_game()

# Zmiana HP
engine.update_player_hp("player_1", -5)

# Obrażenia dowódcy: Natala zadaje Mateuszowi 15 obrażeń dowódcy
engine.apply_cmdr_damage(target_player_id="player_1", attacker_id="player_2", damage=15)

# Przejście do następnej tury
engine.next_turn()
engine.next_turn()