import socket
import threading
import json
from backend.room_engine import RoomEngine


class RoomServer:
    def __init__(self, host="0.0.0.0", port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.clients = []  # Lista powiązanych gniazd klientów (socket -> player_id)
        self.client_map = {}  # socket -> player_id
        self.players_data = []  # Dane graczy w lobby

        # Silnik gry uruchamiany po starcie meczu
        self.engine = None

    def start(self, host_player_info):
        """Uruchamia serwer i dodaje Hosta jako pierwszego gracza."""
        self.players_data = [host_player_info]
        self.is_running = True

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(4)

        threading.Thread(target=self._accept_clients, daemon=True).start()
        print(f"[SERVER] Uruchomiony na {self.host}:{self.port}")

    def _accept_clients(self):
        while self.is_running:
            try:
                client_sock, addr = self.server_socket.accept()
                if len(self.players_data) >= 4:
                    error_msg = json.dumps({"type": "ERROR", "msg": "Room is full"}) + "\n"
                    client_sock.sendall(error_msg.encode('utf-8'))
                    client_sock.close()
                    continue

                self.clients.append(client_sock)
                threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True).start()
            except Exception:
                break

    def _handle_client(self, client_sock):
        current_player_id = None
        buffer = ""

        while self.is_running:
            try:
                data = client_sock.recv(4096)
                if not data:
                    break

                buffer += data.decode('utf-8')
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        message = json.loads(line)
                        p_id = self._process_message(client_sock, message)
                        if p_id:
                            current_player_id = p_id
                            self.client_map[client_sock] = p_id
            except Exception as e:
                print(f"[SERVER ERROR] Handle client error: {e}")
                break

        # Czyszczenie po rozłączeniu gracza
        if client_sock in self.clients:
            self.clients.remove(client_sock)
        if client_sock in self.client_map:
            del self.client_map[client_sock]

        if current_player_id:
            self.players_data = [p for p in self.players_data if p.get("id") != current_player_id]
            if self.engine:
                self.engine.remove_player(current_player_id)
                self.broadcast({"type": "GAME_STATE_UPDATE", "state": self.engine.state.to_dict()})
            else:
                self.broadcast({"type": "LOBBY_UPDATE", "players": self.players_data})

        try:
            client_sock.close()
        except Exception:
            pass

    def _process_message(self, client_sock, message):
        msg_type = message.get("type")
        action_type = message.get("action", msg_type)

        # 1. Obsługa dołączania do lobby (JOIN / JOIN_LOBBY)
        if msg_type in ("JOIN", "JOIN_LOBBY") or action_type in ("JOIN", "JOIN_LOBBY"):
            player_info = message.get("player") or message.get("payload") or message
            if not isinstance(player_info, dict) or "id" not in player_info:
                player_info = message.get("payload", {}).get("player", {}) or message

            p_id = player_info.get("id")
            if p_id:
                existing_idx = next((i for i, p in enumerate(self.players_data) if p.get("id") == p_id), -1)
                if existing_idx >= 0:
                    self.players_data[existing_idx] = player_info
                else:
                    self.players_data.append(player_info)

                self.broadcast({"type": "LOBBY_UPDATE", "players": self.players_data})
                return p_id

        # 2. Obsługa akcji w grze (GAME_ACTION) z autorytatywnym przeliczaniem w RoomEngine
        elif msg_type == "GAME_ACTION":
            action = message.get("action")
            payload = message.get("payload", {})

            if self.engine:
                p_id = payload.get("player_id")
                player_state = self.engine.state.players.get(p_id) if p_id else None

                if action == "NEXT_TURN":
                    self.engine.next_turn()
                elif action == "UPDATE_HP" and player_state:
                    delta = payload.get("delta", 0)
                    abs_hp = payload.get("hp")
                    if abs_hp is not None:
                        player_state.hp = max(0, abs_hp)
                    else:
                        player_state.update_hp(delta)
                elif action == "UPDATE_POISON" and player_state:
                    delta = payload.get("delta", 0)
                    abs_poison = payload.get("poison")
                    if abs_poison is not None:
                        player_state.poison = max(0, abs_poison)
                    else:
                        player_state.update_poison(delta)
                elif action == "UPDATE_TAX" and player_state:
                    delta = payload.get("delta", 0)
                    abs_tax = payload.get("tax")
                    if abs_tax is not None:
                        player_state.cmdr_tax = max(0, abs_tax)
                    else:
                        player_state.update_tax(delta)
                elif action == "UPDATE_CMDR_DMG" and player_state:
                    cmdr_dmg = payload.get("cmdr_damage", {})
                    player_state.cmdr_damage_received = cmdr_dmg
                elif action == "START_GAME":
                    if not self.engine.state.game_started:
                        self.engine.start_game()

                # Po przetworzeniu akcji wysyłamy zaktualizowany stan do wszystkich
                self.broadcast({
                    "type": "GAME_STATE_UPDATE",
                    "action": action,
                    "payload": payload,
                    "state": self.engine.state.to_dict()
                })
            else:
                # Jeśli silnik jeszcze nie ruszył, rozsyłamy akcję bezpośrednio
                self.broadcast(message)

        elif msg_type == "START_GAME":
            # Inicjalizacja RoomEngine na podstawie graczy z lobby
            host_id = self.players_data[0].get("id") if self.players_data else "p1"
            self.engine = RoomEngine(room_id="room_1", host_id=host_id)

            for p_info in self.players_data:
                self.engine.add_player(p_info.get("id"), p_info.get("name", "Player"))

            first_player_id = message.get("first_player_id")
            if first_player_id and first_player_id in self.engine.state.turn_order:
                self.engine.state.current_turn_index = self.engine.state.turn_order.index(first_player_id)

            self.engine.start_game()

            game_data = message.get("room_config", {})
            game_data["state"] = self.engine.state.to_dict()
            game_data["players"] = self.players_data

            self.broadcast({"type": "START_GAME", "room_config": game_data})

        return None

    def broadcast(self, message):
        """Wysyła wiadomość do wszystkich podłączonych klientów z separatorem \n."""
        payload = (json.dumps(message) + "\n").encode('utf-8')
        for client in list(self.clients):
            try:
                client.sendall(payload)
            except Exception:
                pass

    def stop(self):
        self.broadcast({"type": "ROOM_CLOSED"})
        self.is_running = False

        for client in list(self.clients):
            try:
                client.close()
            except Exception:
                pass
        self.clients.clear()
        self.client_map.clear()

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass