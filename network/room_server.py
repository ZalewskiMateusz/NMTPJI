import socket
import threading
import json


class RoomServer:
    def __init__(self, host="0.0.0.0", port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.clients = []  # Lista połączonych gniazd klientów
        self.players_data = []  # Dane graczy w pokoju (w tym Host)

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
                    client_sock.sendall(json.dumps({"type": "ERROR", "msg": "Room is full"}).encode('utf-8'))
                    client_sock.close()
                    continue

                self.clients.append(client_sock)
                threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True).start()
            except Exception:
                break

    def _handle_client(self, client_sock):
        current_player_id = None
        while self.is_running:
            try:
                data = client_sock.recv(4096)
                if not data:
                    break

                message = json.loads(data.decode('utf-8'))
                player_id = self._process_message(client_sock, message)
                if player_id:
                    current_player_id = player_id
            except Exception:
                break

        # Czyszczenie po rozłączeniu gracza
        if client_sock in self.clients:
            self.clients.remove(client_sock)

        if current_player_id:
            self.players_data = [p for p in self.players_data if p.get("id") != current_player_id]
            self.broadcast({"type": "LOBBY_UPDATE", "players": self.players_data})

        client_sock.close()

    def _process_message(self, client_sock, message):
        msg_type = message.get("type")
        action_type = message.get("action", msg_type)

        # Obsługujemy JOIN, JOIN_LOBBY oraz wiadomości zapakowane jako akcje
        if msg_type in ("JOIN", "JOIN_LOBBY") or action_type in ("JOIN", "JOIN_LOBBY"):
            player_info = message.get("player", {}) or message.get("payload", {})
            if not player_info and "id" in message:
                player_info = message

            p_id = player_info.get("id")
            if p_id:
                existing_idx = next((i for i, p in enumerate(self.players_data) if p.get("id") == p_id), -1)
                if existing_idx >= 0:
                    self.players_data[existing_idx] = player_info
                else:
                    self.players_data.append(player_info)

                self.broadcast({"type": "LOBBY_UPDATE", "players": self.players_data})
                return p_id

        elif msg_type == "GAME_ACTION":
            self.broadcast(message)

        return None

    def broadcast(self, message):
        """Wysyła wiadomość do wszystkich podłączonych klientów."""
        payload = json.dumps(message).encode('utf-8')
        for client in list(self.clients):
            try:
                client.sendall(payload)
            except Exception:
                pass

    def stop(self):
        # 1. Wysyłamy informację o zamknięciu pokoju do wszystkich graczy
        self.broadcast({"type": "ROOM_CLOSED"})
        self.is_running = False

        # 2. Zamykamy połączenia klientów
        for client in list(self.clients):
            try:
                client.close()
            except Exception:
                pass
        self.clients.clear()

        # 3. Zamykamy gniazdo serwera
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass