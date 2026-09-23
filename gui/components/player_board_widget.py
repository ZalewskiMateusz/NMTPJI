import os
import customtkinter as ctk

FONT_PATH = os.path.join("assets", "fonts", "Kanisah.ttf")
if os.path.exists(FONT_PATH):
    ctk.FontManager.load_font(FONT_PATH)


class PlayerBoardWidget(ctk.CTkFrame):
    def __init__(self, master, player_name: str = "Player", opponents: list = None):
        super().__init__(master)

        self.player_name = player_name
        self.opponents = opponents or ["Opponent 1", "Opponent 2", "Opponent 3"]

        self.is_stats_visible = False
        self.is_cmdr_visible = False

        self.state = {
            "hp": 40,
            "poison": 0,
            "cmdr_tax": 0,
            "cmdr_damage": {opp: 0 for opp in self.opponents}
        }

        self.configure(fg_color="#1a1a1a", corner_radius=10, border_width=1, border_color="#333333")

        # UKŁAD: Wiersz 0 (Górny pasek), Wiersz 1 (Stół / Widok gry)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # =====================================================================
        # 1. GÓRNA BELKA (Kompaktowa)
        # =====================================================================
        self.top_bar = ctk.CTkFrame(self, fg_color="#222222", corner_radius=6)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

        # Przyciski zbite z lewej strony
        self.toggle_stats_btn = ctk.CTkButton(
            self.top_bar, text="📊 Stats", width=60, height=24,
            font=("Kanisah", 10, "bold"), fg_color="#333333", hover_color="#444444",
            command=self.toggle_stats_panel
        )
        self.toggle_stats_btn.pack(side="left", padx=6, pady=5)

        self.name_lbl = ctk.CTkLabel(
            self.top_bar, text=self.player_name, font=("Kanisah", 14, "bold")
        )
        self.name_lbl.pack(side="left", padx=6)

        # --- SEKCJA HP & DROPDOWN CMDR DAMAGE ---
        self.hp_container = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.hp_container.pack(side="left", padx=10)

        self.hp_row = ctk.CTkFrame(self.hp_container, fg_color="transparent")
        self.hp_row.pack(side="top")

        self.sub_hp_btn = ctk.CTkButton(
            self.hp_row, text="-", width=22, height=22,
            font=("Kanisah", 12, "bold"), fg_color="#8b0000", hover_color="#a10000",
            command=lambda: self.adjust_hp(-1)
        )
        self.sub_hp_btn.pack(side="left", padx=1)

        self.hp_lbl = ctk.CTkLabel(
            self.hp_row, text="40", width=36, height=24,
            font=("Kanisah", 16, "bold"), fg_color="#2b2b2b", corner_radius=4
        )
        self.hp_lbl.pack(side="left", padx=2)

        self.add_hp_btn = ctk.CTkButton(
            self.hp_row, text="+", width=22, height=22,
            font=("Kanisah", 12, "bold"), fg_color="#1b5e20", hover_color="#2e7d32",
            command=lambda: self.adjust_hp(1)
        )
        self.add_hp_btn.pack(side="left", padx=1)

        self.toggle_cmdr_btn = ctk.CTkButton(
            self.hp_container, text="⚔️", width=36, height=16,
            font=("Kanisah", 10), fg_color="#3a2323", hover_color="#522b2b",
            command=self.toggle_cmdr_panel
        )
        self.toggle_cmdr_btn.pack(side="top", pady=(2, 0))

        # Prawostronne liczniki (Poison / Tax)
        self.tax_lbl = self._create_top_counter(self.top_bar, "Tax:", "cmdr_tax", "#d4af37", step=2)
        self.poison_lbl = self._create_top_counter(self.top_bar, "Poison:", "poison", "#2e7d32")

        # =====================================================================
        # 2. GŁÓWNY STÓŁ GRACZA (Main Board Area)
        # =====================================================================
        self.main_board = ctk.CTkFrame(self, fg_color="#141414", corner_radius=6)
        self.main_board.grid(row=1, column=0, sticky="nsew", padx=8, pady=(2, 8))

        # --- NAKŁADKA STATS (Półprzezroczysty Flyout Panel) ---
        self.stats_panel = ctk.CTkFrame(
            self.main_board, fg_color="#1e1e1e", border_width=1, border_color="#333333",
            corner_radius=6, width=150
        )

        ctk.CTkLabel(self.stats_panel, text="Deck Stats & %", font=("Kanisah", 11, "bold")).pack(pady=4)
        self.card_list = ctk.CTkScrollableFrame(self.stats_panel, fg_color="transparent")
        self.card_list.pack(fill="both", expand=True, padx=2, pady=2)

        for i in range(1, 8):
            ctk.CTkLabel(self.card_list, text=f"Card #{i}: {100 // i}%", font=("Kanisah", 9), anchor="w").pack(fill="x")

        # --- CMDR DAMAGE DROPDOWN FLYOUT ---
        self.cmdr_dropdown_frame = ctk.CTkFrame(
            self.main_board, fg_color="#1e1e1e", border_width=1, border_color="#333333",
            corner_radius=6, width=150
        )

        self.cmdr_labels = {}
        for opp in self.opponents:
            self._create_cmdr_damage_row(opp)

        self.refresh_ui()

    def _create_top_counter(self, parent, title: str, key: str, color: str, step: int = 1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="right", padx=4)

        ctk.CTkLabel(frame, text=title, font=("Kanisah", 10)).pack(side="left", padx=1)

        btn_sub = ctk.CTkButton(
            frame, text="-", width=16, height=16, font=("Kanisah", 8, "bold"),
            command=lambda: self.adjust_state(key, -step)
        )
        btn_sub.pack(side="left", padx=1)

        lbl_val = ctk.CTkLabel(frame, text="0", width=18, font=("Kanisah", 10, "bold"), text_color=color)
        lbl_val.pack(side="left", padx=1)

        btn_add = ctk.CTkButton(
            frame, text="+", width=16, height=16, font=("Kanisah", 8, "bold"),
            command=lambda: self.adjust_state(key, step)
        )
        btn_add.pack(side="left", padx=1)

        return lbl_val

    def _create_cmdr_damage_row(self, opp_name: str):
        row = ctk.CTkFrame(self.cmdr_dropdown_frame, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=2)

        ctk.CTkLabel(row, text=f"{opp_name}:", font=("Kanisah", 9), anchor="w").pack(side="left")

        btn_add = ctk.CTkButton(
            row, text="+", width=16, height=16, font=("Kanisah", 9, "bold"),
            command=lambda: self.adjust_cmdr_damage(opp_name, 1)
        )
        btn_add.pack(side="right", padx=1)

        val_lbl = ctk.CTkLabel(row, text="0", width=18, font=("Kanisah", 10, "bold"), text_color="#c62828")
        val_lbl.pack(side="right", padx=1)

        btn_sub = ctk.CTkButton(
            row, text="-", width=16, height=16, font=("Kanisah", 9, "bold"),
            command=lambda: self.adjust_cmdr_damage(opp_name, -1)
        )
        btn_sub.pack(side="right", padx=1)

        self.cmdr_labels[opp_name] = val_lbl

    def toggle_stats_panel(self):
        """Wysuwa/chowa statystyki talii jako nakładkę (overlay)."""
        if self.is_stats_visible:
            self.stats_panel.place_forget()
            self.is_stats_visible = False
        else:
            self.stats_panel.place(relx=0.0, rely=0.0, relheight=1.0)
            self.stats_panel.lift()
            self.is_stats_visible = True

    def toggle_cmdr_panel(self):
        """Wysuwa/chowa podgląd Commander Damage jako małe pływające okienko."""
        if self.is_cmdr_visible:
            self.cmdr_dropdown_frame.place_forget()
            self.is_cmdr_visible = False
        else:
            self.cmdr_dropdown_frame.place(x=85, y=5)
            self.cmdr_dropdown_frame.lift()
            self.is_cmdr_visible = True

    def adjust_hp(self, delta: int):
        self.state["hp"] += delta
        self.refresh_ui()

    def adjust_state(self, key: str, delta: int):
        self.state[key] = max(0, self.state[key] + delta)
        self.refresh_ui()

    def adjust_cmdr_damage(self, opp_name: str, delta: int):
        self.state["cmdr_damage"][opp_name] = max(0, self.state["cmdr_damage"][opp_name] + delta)
        self.refresh_ui()

    def refresh_ui(self):
        self.hp_lbl.configure(text=str(self.state["hp"]))
        self.poison_lbl.configure(text=str(self.state["poison"]))
        self.tax_lbl.configure(text=f"+{self.state['cmdr_tax']}")

        for opp, lbl in self.cmdr_labels.items():
            lbl.configure(text=str(self.state["cmdr_damage"][opp]))