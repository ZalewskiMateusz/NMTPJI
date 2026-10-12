import customtkinter as ctk
from database.db_manager import DBManager
from network.room_server import RoomServer


class FindRoomView(ctk.CTkFrame):
    def __init__(self, master, on_start_game_callback=None, on_back_callback=None):
        super().__init__(master, fg_color="#121212")
        self.on_start_game_callback = on_start_game_callback
        self.on_back_callback = on_back_callback

        self.server = None
        self.players = []

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="HOST LOBBY ROOM", font=("Segoe UI", 20, "bold")).pack(pady=(20, 10))

        # Nick + Deck
        form_frame = ctk.CTkFrame(self, fg_color="#1E1E1E")
        form_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(form_frame, text="Your Nickname:").pack(anchor="w", padx=15, pady=(10, 0))
        self.entry_nick = ctk.CTkEntry(form_frame)
        self.entry_nick.insert(0, "Mateusz")
        self.entry_nick.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(form_frame, text="Select Deck:").pack(anchor="w", padx=15)
        decks = DBManager.get_all_deck_names() or ["Default Deck"]
        self.combo_decks = ctk.CTkOptionMenu(form_frame, values=decks)
        self.combo_decks.pack(fill="x", padx=15, pady=(0, 15))

        self.btn_host = ctk.CTkButton(form_frame, text="START HOSTING", fg_color="#1F6AA5", command=self._start_hosting)
        self.btn_host.pack(fill="x", padx=15, pady=(0, 15))

        # Lista graczy
        ctk.CTkLabel(self, text="Connected Players (Max 4):", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.players_box = ctk.CTkTextbox(self, height=120)
        self.players_box.pack(fill="x", padx=20, pady=5)

        # Dolne przyciski
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(bar, text="← BACK", fg_color="#333333", command=self._go_back).pack(side="left")
        self.btn_start = ctk.CTkButton(bar, text="LAUNCH MATCH ➔", fg_color="#2E7D32", state="disabled", command=self._launch_match)
        self.btn_start.pack(side="right")

    def _start_hosting(self):
        nick = self.entry_nick.get().strip() or "Host"
        deck_name = self.combo_decks.get()
        deck_data = DBManager.get_deck_by_name(deck_name)
        cmdr = deck_data.get("commander", "Unknown Commander")

        host_player = {"id": "p1", "name": f"{nick} (HOST)", "commander": cmdr}
        self.players = [host_player]

        self.server = RoomServer()
        self.server.start(host_player)

        self.btn_host.configure(state="disabled", text="ROOM ACTIVE (Listening...)")
        self.btn_start.configure(state="normal")
        self._update_players_ui()

    def _update_players_ui(self):
        self.players_box.configure(state="normal")
        self.players_box.delete("1.0", "end")
        for p in self.players:
            self.players_box.insert("end", f"• {p['name']} | Commander: {p['commander']}\n")
        self.players_box.configure(state="disabled")

    def _launch_match(self):
        if self.server:
            self.server.broadcast({"type": "START_GAME"})
        if self.on_start_game_callback:
            self.on_start_game_callback({"players": self.players, "host_name": self.entry_nick.get()})

    def _go_back(self):
        if self.server:
            self.server.stop()
        if self.on_back_callback:
            self.on_back_callback()