import customtkinter as ctk

FONT_HEADER = "Georgia"
FONT_UI = "Segoe UI"
DEFAULT_MAX_HP = 40


class PlayerBoardWidget(ctk.CTkFrame):
    def __init__(self, parent, player_id: str, player_name: str = "Player", engine=None, **kwargs):
        self.border_inactive = "#2a2a2a"
        self.border_active = "#00FF66"

        super().__init__(
            parent,
            fg_color="#121212",
            border_width=1,
            border_color=self.border_inactive,
            corner_radius=12,
            **kwargs,
        )

        self.player_id = player_id
        self.player_name = player_name
        self.engine = engine

        self.is_stats_visible = False
        self.is_cmdr_visible = False

        self.cmdr_dmg_labels = {}

        # --- MAIN BOARD ---
        self.main_board = ctk.CTkFrame(self, fg_color="transparent")
        self.main_board.pack(fill="both", expand=True, padx=6, pady=6)

        # --- TOP BAR ---
        self.top_bar = ctk.CTkFrame(self.main_board, fg_color="#1a1a1a", corner_radius=8)
        self.top_bar.pack(fill="x", side="top", pady=(0, 5), ipady=4)

        # Nick
        self.lbl_name = ctk.CTkLabel(
            self.top_bar,
            text=self.player_name,
            font=(FONT_UI, 15, "bold"),
            text_color="#FFFFFF",
            anchor="w",
        )
        self.lbl_name.pack(side="left", padx=(10, 5))

        # Status (ACTIVE / WAITING / DEAD)
        self.lbl_status = ctk.CTkLabel(
            self.top_bar,
            text="WAITING",
            font=(FONT_UI, 11, "bold"),
            text_color="#666666",
        )
        self.lbl_status.pack(side="right", padx=(0, 10))

        # --- ŚRODEK NAGŁÓWKA: TAX | -5 | -1 | HP | +1 | +5 | ⚔ | PSN ---
        self.center_stats_container = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.center_stats_container.place(relx=0.5, rely=0.5, anchor="center")

        # Tax
        self.btn_tax = ctk.CTkButton(
            self.center_stats_container,
            text="TAX: 0",
            font=(FONT_UI, 11, "bold"),
            width=52,
            height=26,
            fg_color="#252525",
            hover_color="#333333",
        )
        self.btn_tax.pack(side="left", padx=(0, 6))
        self.btn_tax.bind("<Button-1>", lambda e: self.change_tax(2))
        self.btn_tax.bind("<Button-3>", lambda e: self.change_tax(-2))

        # HP Minus 5
        self.btn_minus_5_hp = ctk.CTkButton(
            self.center_stats_container,
            text="-5",
            font=(FONT_UI, 11, "bold"),
            width=28,
            height=28,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            command=lambda: self.change_hp(-5),
        )
        self.btn_minus_5_hp.pack(side="left", padx=1)

        # HP Minus 1
        self.btn_minus_hp = ctk.CTkButton(
            self.center_stats_container,
            text="−",
            font=(FONT_UI, 16, "bold"),
            width=28,
            height=28,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            command=lambda: self.change_hp(-1),
        )
        self.btn_minus_hp.pack(side="left", padx=1)

        # HP Label
        self.lbl_hp = ctk.CTkLabel(
            self.center_stats_container,
            text=str(DEFAULT_MAX_HP),
            font=(FONT_HEADER, 22, "bold"),
            text_color="#00FF66",
            width=46,
        )
        self.lbl_hp.pack(side="left", padx=2)

        # HP Plus 1
        self.btn_plus_hp = ctk.CTkButton(
            self.center_stats_container,
            text="+",
            font=(FONT_UI, 16, "bold"),
            width=28,
            height=28,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            command=lambda: self.change_hp(1),
        )
        self.btn_plus_hp.pack(side="left", padx=1)

        # HP Plus 5
        self.btn_plus_5_hp = ctk.CTkButton(
            self.center_stats_container,
            text="+5",
            font=(FONT_UI, 11, "bold"),
            width=28,
            height=28,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            command=lambda: self.change_hp(5),
        )
        self.btn_plus_5_hp.pack(side="left", padx=1)

        # Przycisk Mieczyka (Commander Damage Panel)
        self.btn_cmdr_damage = ctk.CTkButton(
            self.center_stats_container,
            text="⚔",
            font=(FONT_UI, 12, "bold"),
            width=30,
            height=26,
            fg_color="#252525",
            hover_color="#333333",
            command=self.toggle_cmdr_panel,
        )
        self.btn_cmdr_damage.pack(side="left", padx=(6, 6))

        # Poison (PPM: -1, LPM: +1)
        self.btn_poison = ctk.CTkButton(
            self.center_stats_container,
            text="PSN: 0",
            font=(FONT_UI, 11, "bold"),
            width=52,
            height=26,
            fg_color="#252525",
            hover_color="#333333",
        )
        self.btn_poison.pack(side="left", padx=(0, 0))
        self.btn_poison.bind("<Button-1>", lambda e: self.change_poison(1))
        self.btn_poison.bind("<Button-3>", lambda e: self.change_poison(-1))

        # --- PLAYMAT / CENTER AREA ---
        self.center_area = ctk.CTkFrame(self.main_board, fg_color="transparent")
        self.center_area.pack(fill="both", expand=True)

        self.btn_stats = ctk.CTkButton(
            self.center_area,
            text="STATS",
            font=(FONT_UI, 10, "bold"),
            width=48,
            height=22,
            fg_color="#252525",
            hover_color="#333333",
            command=self.toggle_stats_panel,
        )
        self.btn_stats.place(x=4, y=4)

        # --- FLYOUT PANELS ---
        self.cmdr_dropdown_frame = ctk.CTkFrame(
            self.center_area,
            fg_color="#1a1a1a",
            border_width=1,
            border_color="#333333",
            corner_radius=8,
            width=200,
        )

        self.stats_panel = ctk.CTkFrame(
            self.center_area,
            fg_color="#1a1a1a",
            border_width=1,
            border_color="#333333",
            corner_radius=8,
            width=230,
        )

        lbl_stats_title = ctk.CTkLabel(
            self.stats_panel,
            text="Deck Stats & %",
            font=(FONT_HEADER, 11, "bold"),
            text_color="#FFFFFF",
        )
        lbl_stats_title.pack(pady=(6, 2))

        self.card_scroll_frame = ctk.CTkScrollableFrame(
            self.stats_panel,
            fg_color="transparent",
            width=210,
            height=160
        )
        self.card_scroll_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.populate_dummy_stats()

    def populate_dummy_stats(self):
        sample_cards = [
            ("Sol Ring", "38%"),
            ("Cyclonic Rift", "24%"),
            ("Rhystic Study", "18%"),
            ("Arcane Signet", "12%"),
            ("Counterspell", "8%"),
        ]
        for card_name, prob in sample_cards:
            row = ctk.CTkFrame(self.card_scroll_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            chk = ctk.CTkCheckBox(
                row, text="", width=20, height=20, checkbox_width=18, checkbox_height=18, border_width=1, corner_radius=4
            )
            chk.pack(side="left", padx=(2, 4))

            lbl = ctk.CTkLabel(row, text=f"{card_name}", font=(FONT_UI, 10), text_color="#DDDDDD", anchor="w")
            lbl.pack(side="left", expand=True, fill="x")

            lbl_pct = ctk.CTkLabel(row, text=prob, font=(FONT_UI, 10, "bold"), text_color="#00FF66", width=35, anchor="e")
            lbl_pct.pack(side="right", padx=(2, 2))

    def init_cmdr_damage_ui(self):
        for child in self.cmdr_dropdown_frame.winfo_children():
            child.destroy()
        self.cmdr_dmg_labels.clear()

        if not self.engine or not hasattr(self.engine, "state"):
            return

        lbl_title = ctk.CTkLabel(
            self.cmdr_dropdown_frame, text="Commander Damage", font=(FONT_UI, 10, "bold"), text_color="#888888"
        )
        lbl_title.pack(pady=(4, 2))

        for p_id, opponent in self.engine.state.players.items():
            if p_id == self.player_id:
                continue

            row_frame = ctk.CTkFrame(self.cmdr_dropdown_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=8, pady=3)

            lbl_opp = ctk.CTkLabel(
                row_frame, text=f"⚔ {opponent.name}", font=(FONT_UI, 11, "bold"), text_color="#FFFFFF", anchor="w"
            )
            lbl_opp.pack(side="left", expand=True, fill="x")

            btn_minus = ctk.CTkButton(
                row_frame,
                text="-",
                font=(FONT_UI, 11, "bold"),
                width=22,
                height=22,
                fg_color="#2d2d2d",
                hover_color="#3d3d3d",
                command=lambda opp_id=p_id: self.change_cmdr_damage(opp_id, -1),
            )
            btn_minus.pack(side="left", padx=2)

            lbl_dmg = ctk.CTkLabel(row_frame, text="0", font=(FONT_UI, 12, "bold"), text_color="#FFFFFF", width=24)
            lbl_dmg.pack(side="left", padx=2)

            btn_plus = ctk.CTkButton(
                row_frame,
                text="+",
                font=(FONT_UI, 11, "bold"),
                width=22,
                height=22,
                fg_color="#2d2d2d",
                hover_color="#3d3d3d",
                command=lambda opp_id=p_id: self.change_cmdr_damage(opp_id, 1),
            )
            btn_plus.pack(side="left", padx=2)

            self.cmdr_dmg_labels[p_id] = lbl_dmg

    def update_from_state(self, state):
        p_state = state.players.get(self.player_id)
        if not p_state:
            return

        # --- AUTOMATYCZNE SPRAWDZANIE WARUNKÓW ŚMIERCI (REGUŁY EDH) ---
        has_zero_hp = p_state.hp <= 0
        has_10_poison = getattr(p_state, "poison", 0) >= 10
        has_21_cmdr_dmg = any(dmg >= 21 for dmg in getattr(p_state, "cmdr_damage_received", {}).values())

        if has_zero_hp or has_10_poison or has_21_cmdr_dmg:
            p_state.is_alive = False
        else:
            p_state.is_alive = True

        # Odświeżenie nazwy gracza
        if hasattr(p_state, "name") and p_state.name:
            self.lbl_name.configure(text=p_state.name)

        max_hp = getattr(p_state, "max_hp", DEFAULT_MAX_HP)

        # Życie & Kolorystyka HP
        ratio = p_state.hp / max_hp if max_hp > 0 else 1.0
        hp_color = "#00FF66" if ratio > 0.75 else ("#B4FF00" if ratio > 0.5 else ("#FFB300" if ratio > 0.25 else "#FF3333"))
        self.lbl_hp.configure(text=str(p_state.hp), text_color=hp_color)

        # Poison & Commander Tax
        self.btn_poison.configure(text=f"PSN: {p_state.poison}")
        self.btn_tax.configure(text=f"TAX: {p_state.cmdr_tax}")

        # Obrażenia od Commanderów
        if not self.cmdr_dmg_labels:
            self.init_cmdr_damage_ui()

        for opp_id, lbl_dmg in self.cmdr_dmg_labels.items():
            damage_val = p_state.cmdr_damage_received.get(opp_id, 0)
            lbl_dmg.configure(
                text=str(damage_val),
                text_color="#FF4444" if damage_val >= 21 else "#FFFFFF",
            )

        # Status Śmierci / Aktywnej Tury
        current_player = state.get_current_player() if hasattr(state, "get_current_player") else None

        if not p_state.is_alive:
            self.lbl_status.configure(text="DEAD", text_color="#FF3333")
            self.configure(border_color="#FF3333")
        elif current_player and current_player.player_id == self.player_id:
            self.lbl_status.configure(text="● ACTIVE", text_color="#00FF66")
            self.configure(border_color=self.border_active)
        else:
            self.lbl_status.configure(text="WAITING", text_color="#666666")
            self.configure(border_color=self.border_inactive)

    def _refresh_and_notify(self):
        if self.engine:
            self.engine.notify_subscribers()

    def change_hp(self, delta: int):
        p_state = self.engine.state.players.get(self.player_id) if self.engine else None
        if p_state:
            p_state.update_hp(delta)
            self._refresh_and_notify()

    def change_poison(self, delta: int):
        p_state = self.engine.state.players.get(self.player_id) if self.engine else None
        if p_state:
            p_state.update_poison(delta)
            self._refresh_and_notify()

    def change_tax(self, delta: int):
        p_state = self.engine.state.players.get(self.player_id) if self.engine else None
        if p_state:
            p_state.update_tax(delta)
            self._refresh_and_notify()

    def change_cmdr_damage(self, opponent_id: str, delta: int):
        p_state = self.engine.state.players.get(self.player_id) if self.engine else None
        if p_state:
            p_state.receive_cmdr_damage(opponent_id, delta)
            self._refresh_and_notify()

    def toggle_stats_panel(self):
        if self.is_stats_visible:
            self.stats_panel.place_forget()
            self.is_stats_visible = False
        else:
            if self.is_cmdr_visible:
                self.toggle_cmdr_panel()
            self.stats_panel.place(x=4, y=30)
            self.stats_panel.lift()
            self.btn_stats.lift()
            self.is_stats_visible = True

    def toggle_cmdr_panel(self):
        if self.is_cmdr_visible:
            self.cmdr_dropdown_frame.place_forget()
            self.is_cmdr_visible = False
        else:
            if self.is_stats_visible:
                self.toggle_stats_panel()
            self.cmdr_dropdown_frame.place(relx=0.5, y=0, anchor="n")
            self.cmdr_dropdown_frame.lift()
            self.is_cmdr_visible = True