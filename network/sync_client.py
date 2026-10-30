import socket
import threading
import json


class SyncClient:
    def __init__(self, on_message_received=None):
        self.socket = None
        self.is_connected = False
        self.on_message_received = on_message_received
        self.buffer = ""

    def connect(self, host_ip, port=5555):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host_ip, port))
            self.is_connected = True

            threading.Thread(target=self._listen, daemon=True).start()
            return True
        except Exception as e:
            print(f"[CLIENT ERROR] Could not connect to {host_ip}:{port} -> {e}")
            return False

    def send_join(self, player_info):
        if self.is_connected:
            payload = {"type": "JOIN", "player": player_info}
            self.send(payload)

    def send(self, data_dict):
        """Wysyła słownik jako JSON zakończony znakiem nowej linii (\n)."""
        if self.is_connected and self.socket:
            try:
                message_str = json.dumps(data_dict) + "\n"
                self.socket.sendall(message_str.encode('utf-8'))
            except Exception as e:
                print(f"[CLIENT ERROR] Send failed: {e}")

    def _listen(self):
        """Nasłuchuje strumienia TCP z buforowaniem linii, co zapobiega sklejaniu JSON-ów."""
        while self.is_connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break

                self.buffer += data.decode('utf-8')
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        message = json.loads(line)
                        if self.on_message_received:
                            self.on_message_received(message)
            except Exception as e:
                print(f"[CLIENT ERROR] Listen stream error: {e}")
                break

        self.is_connected = False

    def disconnect(self):
        self.is_connected = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass

    def send_action(self, action_type, payload):
        """Wysyła akcję gracza do serwera gry."""
        if self.is_connected:
            payload_data = {
                "type": "GAME_ACTION",
                "action": action_type,
                "payload": payload
            }
            self.send(payload_data)