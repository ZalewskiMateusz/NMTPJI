import customtkinter as ctk


class GameHeaderWidget(ctk.CTkFrame):
    def __init__(self, master, current_player_name: str = "Mateusz", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.lbl_title = ctk.CTkLabel(
            self,
            text="COMMANDER MATCH",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_title.pack(side="left", padx=10)

        self.lbl_info = ctk.CTkLabel(
            self,
            text="Turn: 1 | Active: -",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_info.pack(side="right", padx=10)

    def update_from_state(self, state):
        """Odświeża numer tury oraz nazwę gracza, którego jest ruch."""
        active_player = state.get_current_player()
        active_name = active_player.name if active_player else "Unknown"
        self.lbl_info.configure(text=f"Turn: {state.turn_number} | Active: {active_name}")