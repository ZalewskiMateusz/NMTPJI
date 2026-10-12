import customtkinter as ctk

FONT_HEADER = "Georgia"
FONT_UI = "Segoe UI"


class EndMatchWindow(ctk.CTkToplevel):
    def __init__(self, parent, engine=None, on_confirm=None, on_rematch=None, on_resume=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.engine = engine
        self.on_confirm_callback = on_confirm
        self.on_rematch_callback = on_rematch
        self.on_resume_callback = on_resume

        # --- MODAL WINDOW SETTINGS ---
        self.title("End Match - Summary")
        self.geometry("420x460")  # Zwiększona wysokość pod pełny zestaw przycisków
        self.resizable(False, False)
        self.configure(fg_color="#121212")

        # Keep window on top and modal
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

        # Override default close button [X] to trigger Resume
        self.protocol("WM_DELETE_WINDOW", self._cmd_resume)

        self._build_ui()

    def _build_ui(self):
        # Main container frame
        main_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=12, border_width=1, border_color="#333333")
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)

        # HEADER
        lbl_title = ctk.CTkLabel(
            main_frame,
            text="Match Conclusion",
            font=(FONT_HEADER, 18, "bold"),
            text_color="#FFFFFF"
        )
        lbl_title.pack(pady=(16, 4))

        lbl_subtitle = ctk.CTkLabel(
            main_frame,
            text="Select the winner and confirm the match results.",
            font=(FONT_UI, 11),
            text_color="#888888"
        )
        lbl_subtitle.pack(pady=(0, 16))

        # WINNER SELECTION
        lbl_winner_tag = ctk.CTkLabel(
            main_frame,
            text="Winner:",
            font=(FONT_UI, 12, "bold"),
            text_color="#CCCCCC",
            anchor="w"
        )
        lbl_winner_tag.pack(fill="x", padx=24, pady=(0, 4))

        player_names = self._get_player_names()

        self.combo_winner = ctk.CTkOptionMenu(
            main_frame,
            values=player_names,
            font=(FONT_UI, 12),
            dropdown_font=(FONT_UI, 11),
            fg_color="#252525",
            button_color="#333333",
            button_hover_color="#444444",
            text_color="#00FF66",
            height=32
        )
        self.combo_winner.pack(fill="x", padx=24, pady=(0, 16))

        default_winner = self._get_default_winner()
        if default_winner:
            self.combo_winner.set(default_winner)

        # STATS PREVIEW
        stats_frame = ctk.CTkFrame(main_frame, fg_color="#121212", corner_radius=8)
        stats_frame.pack(fill="x", padx=24, pady=(0, 16), ipady=6)

        turns_cnt = getattr(self.engine.state, "turn_number", 1) if (
                    self.engine and hasattr(self.engine, "state")) else 1

        lbl_turns = ctk.CTkLabel(
            stats_frame,
            text=f"Total Turns Played: {turns_cnt}",
            font=(FONT_UI, 11),
            text_color="#AAAAAA"
        )
        lbl_turns.pack(pady=2)

        # ACTION BUTTONS CONTAINER (spakowany kolejno)
        btn_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_container.pack(fill="x", padx=24, pady=(0, 16))

        btn_confirm = ctk.CTkButton(
            btn_container,
            text="Save & Finish Match",
            font=(FONT_UI, 11, "bold"),
            fg_color="#00FF66",
            hover_color="#00CC52",
            text_color="#000000",
            height=34,
            command=self._cmd_confirm
        )
        btn_confirm.pack(fill="x", pady=(0, 6))

        btn_rematch = ctk.CTkButton(
            btn_container,
            text="Rematch (Next Game)",
            font=(FONT_UI, 11, "bold"),
            fg_color="#252525",
            hover_color="#333333",
            border_width=1,
            border_color="#00FF66",
            text_color="#00FF66",
            height=32,
            command=self._cmd_rematch
        )
        btn_rematch.pack(fill="x", pady=(0, 6))

        btn_resume = ctk.CTkButton(
            btn_container,
            text="Resume Match",
            font=(FONT_UI, 11),
            fg_color="transparent",
            hover_color="#222222",
            text_color="#888888",
            height=28,
            command=self._cmd_resume
        )
        btn_resume.pack(fill="x")

    def _get_player_names(self) -> list[str]:
        """Returns list of all player names for dropdown."""
        if not self.engine or not hasattr(self.engine, "state") or not self.engine.state.players:
            return ["Player 1", "No Winner / Draw"]

        names = [p.name for p in self.engine.state.players.values()]
        names.append("No Winner / Draw")
        return names

    def _get_default_winner(self) -> str:
        """Returns first alive player name or fallback."""
        if not self.engine or not hasattr(self.engine, "state") or not self.engine.state.players:
            return "Player 1"

        alive_players = [p.name for p in self.engine.state.players.values() if getattr(p, "is_alive", True)]
        if alive_players:
            return alive_players[0]
        return "No Winner / Draw"

    def _cmd_confirm(self):
        winner_name = self.combo_winner.get()
        self.grab_release()
        self.destroy()
        if self.on_confirm_callback:
            self.on_confirm_callback(winner_name)

    def _cmd_rematch(self):
        winner_name = self.combo_winner.get()
        self.grab_release()
        self.destroy()
        if self.on_rematch_callback:
            self.on_rematch_callback(winner_name)

    def _cmd_resume(self):
        self.grab_release()
        self.destroy()
        if self.on_resume_callback:
            self.on_resume_callback()