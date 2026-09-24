import customtkinter as ctk
from backend.room_engine import RoomEngine
from gui.components.player_board_widget import PlayerBoardWidget

app = ctk.CTk()
app.geometry("900x600")
app.title("MTG Commander Room Test")

# 1. Tworzymy silnik pokoju
engine = RoomEngine(room_id="ROOM_001", host_id="p1")

# 2. Dodajemy 4 graczy
engine.add_player("p1", "Mateusz")
engine.add_player("p2", "Natala")
engine.add_player("p3", "Gracz 3")
engine.add_player("p4", "Gracz 4")
engine.start_game()

# --- TOP CONTROL BAR (Przycisk Tury) ---
top_bar = ctk.CTkFrame(app, height=40)
top_bar.pack(fill="x", side="top", padx=10, pady=(10, 0))

lbl_turn = ctk.CTkLabel(top_bar, text="TURA 1", font=("Segoe UI", 16, "bold"))
lbl_turn.pack(side="left", padx=15)

def next_turn_click():
    engine.next_turn()

btn_next_turn = ctk.CTkButton(
    top_bar,
    text="END TURN",
    font=("Segoe UI", 12, "bold"),
    fg_color="#00AA44",
    hover_color="#008833",
    command=next_turn_click,
)
btn_next_turn.pack(side="right", padx=15, pady=5)

# 3. Tworzymy grid dla widgetów
grid_frame = ctk.CTkFrame(app, fg_color="transparent")
grid_frame.pack(fill="both", expand=True, padx=10, pady=10)

widgets = []

# Rozmieszczamy 4 graczy w siatce 2x2
players_keys = list(engine.state.players.keys())
for idx, p_id in enumerate(players_keys):
    row = idx // 2
    col = idx % 2

    board = PlayerBoardWidget(grid_frame, player_id=p_id, engine=engine)
    board.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
    grid_frame.grid_rowconfigure(row, weight=1)
    grid_frame.grid_columnconfigure(col, weight=1)

    widgets.append(board)

# 4. SUBSKRYPCJA ZMIAN W SILNIKU
def refresh_ui(state):
    lbl_turn.configure(text=f"TURA {state.turn_number}")
    for widget in widgets:
        widget.update_from_state(state)

engine.subscribe(refresh_ui)
# Inicjalne odświeżenie UI
refresh_ui(engine.state)

app.mainloop()