import customtkinter as ctk

FONT_HEADER = "Georgia"
FONT_UI = "Segoe UI"


class StatisticsView(ctk.CTkFrame):
    def __init__(self, parent, db_manager, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_manager
        self.configure(fg_color="#121212")

        self._build_ui()

    def _build_ui(self):
        # Nagłówek
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 10))

        lbl_title = ctk.CTkLabel(
            header_frame,
            text="Match Statistics & Commander Analytics",
            font=(FONT_HEADER, 22, "bold"),
            text_color="#FFFFFF"
        )
        lbl_title.pack(side="left")

        # Kontener na statystyki
        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="#1a1a1a", corner_radius=12)
        self.content_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self.refresh_stats()

    def refresh_stats(self):
        # Czyszczenie widoku przed odświeżeniem
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        commander_stats = self.db.get_commander_stats()

        if not commander_stats:
            lbl_empty = ctk.CTkLabel(
                self.content_frame,
                text="No match history found. Finish some games to view your stats!",
                font=(FONT_UI, 14),
                text_color="#777777"
            )
            lbl_empty.pack(pady=40)
            return

        # 1. SEKJA: Podsumowanie Commanderów
        lbl_sec1 = ctk.CTkLabel(
            self.content_frame,
            text="YOUR COMMANDERS OVERVIEW",
            font=(FONT_UI, 12, "bold"),
            text_color="#00FF66"
        )
        lbl_sec1.pack(anchor="w", padx=16, pady=(16, 8))

        # Tabela Commanderów
        for stat in commander_stats:
            card = ctk.CTkFrame(self.content_frame, fg_color="#222222", corner_radius=8)
            card.pack(fill="x", padx=16, pady=4, ipady=4)

            lbl_name = ctk.CTkLabel(
                card,
                text=stat["commander_name"],
                font=(FONT_UI, 13, "bold"),
                text_color="#FFFFFF"
            )
            lbl_name.pack(side="left", padx=16)

            wr_color = "#00FF66" if stat["winrate"] >= 50 else "#FF4444"
            lbl_wr = ctk.CTkLabel(
                card,
                text=f"{stat['winrate']}% WR ({stat['wins']}W / {stat['losses']}L)",
                font=(FONT_UI, 12, "bold"),
                text_color=wr_color
            )
            lbl_wr.pack(side="right", padx=16)

        # 2. SEKCJA: Matchup Breakdown (Wybór Commandera)
        lbl_sec2 = ctk.CTkLabel(
            self.content_frame,
            text="MATCHUP BREAKDOWN VS OPPONENT COMMANDERS",
            font=(FONT_UI, 12, "bold"),
            text_color="#00FF66"
        )
        lbl_sec2.pack(anchor="w", padx=16, pady=(24, 8))

        commanders_list = [s["commander_name"] for s in commander_stats]

        self.combo_filter = ctk.CTkOptionMenu(
            self.content_frame,
            values=commanders_list,
            command=self._on_commander_selected,
            font=(FONT_UI, 12),
            fg_color="#252525",
            button_color="#333333",
            button_hover_color="#444444",
            text_color="#00FF66"
        )
        self.combo_filter.pack(anchor="w", padx=16, pady=(0, 12))

        self.matchups_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.matchups_container.pack(fill="x", padx=16, pady=0)

        if commanders_list:
            self._render_matchups(commanders_list[0])

    def _on_commander_selected(self, selected_commander: str):
        self._render_matchups(selected_commander)

    def _render_matchups(self, commander_name: str):
        for widget in self.matchups_container.winfo_children():
            widget.destroy()

        matchup_data = self.db.get_matchup_stats(commander_name)

        if not matchup_data:
            lbl_no_data = ctk.CTkLabel(
                self.matchups_container,
                text="No recorded matchups against other commanders yet.",
                font=(FONT_UI, 12),
                text_color="#666666"
            )
            lbl_no_data.pack(anchor="w", pady=8)
            return

        for m in matchup_data:
            row = ctk.CTkFrame(self.matchups_container, fg_color="#181818", corner_radius=6)
            row.pack(fill="x", pady=3)

            lbl_opp = ctk.CTkLabel(
                row,
                text=f"vs {m['opponent_commander']}",
                font=(FONT_UI, 12),
                text_color="#DDDDDD"
            )
            lbl_opp.pack(side="left", padx=12, pady=6)

            wr_color = "#00FF66" if m["winrate"] >= 50 else "#FF5555"
            lbl_stats = ctk.CTkLabel(
                row,
                text=f"{m['winrate']}% WR  [{m['wins']}W - {m['losses']}L] ({m['total_matches']} games)",
                font=(FONT_UI, 11, "bold"),
                text_color=wr_color
            )
            lbl_stats.pack(side="right", padx=12)