import math
import os
import random
import threading
import time
import cv2
import requests
import customtkinter as ctk
from PIL import Image, ImageSequence

from core.calculator import OddsCalculator
from core.scryfall import ScryfallAPI
from database.db_manager import DBManager
from gui.components.stream_dialog import StreamSourceDialog
from utils.profile_manager import ProfileManager, AVATARS_DIR

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EMOTES_DIR = os.path.join(BASE_DIR, "assets", "emotes")

FONT_HEADER = "Georgia"
FONT_UI = "Segoe UI"
DEFAULT_MAX_HP = 40


class CardHoverTooltip(ctk.CTkToplevel):
    """Floating tooltip displaying a full-size preview of the MTG card with no clipping."""

    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#1E1E1E")
        self.withdraw()

        # Sztywny rozmiar etykiety dopasowany w 100% do karty MTG, zapobiegający ucinaniu
        self.lbl_image = ctk.CTkLabel(self, text="Loading...", fg_color="transparent", width=240, height=336)
        self.lbl_image.pack(padx=2, pady=2)
        self.active_card_name = None
        self._current_img = None

    def show_image(self, img_path, x, y, card_name):
        """Renders the card preview safely ensuring it stays fully visible on screen without clipping."""
        self.active_card_name = card_name
        if img_path and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path)
                # Pełny, prostokątny format karty MTG (proporcje 5:7)
                self._current_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(240, 336))
                self.lbl_image.configure(image=self._current_img, text="")
            except Exception:
                self._current_img = None
                self.lbl_image.configure(image="", text="Image Error")
        else:
            self._current_img = None
            self.lbl_image.configure(image="", text="No Image Available")

        # Bezpieczne pozycjonowanie na ekranie, żeby dymek nie wychodził poza krawędzie
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        pos_x = x + 20
        pos_y = y - 50

        if pos_x + 260 > screen_width:
            pos_x = x - 260

        if pos_y + 360 > screen_height:
            pos_y = screen_height - 360

        self.geometry(f"+{pos_x}+{pos_y}")
        self.deiconify()
        self.lift()

    def hide(self):
        """Hides the tooltip window."""
        self.active_card_name = None
        self._current_img = None
        self.withdraw()


class PlayerBoardWidget(ctk.CTkFrame):
    """
    Player overlay board widget displaying player stats, video feeds, deck statistics,
    life counters, and interactive card controls.
    """
    def __init__(self, parent, player_id: str, player_name: str = "Player", engine=None, deck_cards=None, client=None,
                 is_local=False, total_players=4, all_players=None,
                 on_fullscreen_callback=None, on_duel_callback=None, on_emote_callback=None, **kwargs):
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
        self.client = client
        self.is_local = is_local

        self.total_players = total_players
        self.all_players = all_players or {}
        self.on_fullscreen_callback = on_fullscreen_callback
        self.on_duel_callback = on_duel_callback
        self.on_emote_callback = on_emote_callback
        self._active_views_menu = None

        initial_avatar = "jace.png"
        if self.engine and hasattr(self.engine, "state") and self.engine.state and hasattr(self.engine.state, "players"):
            p_state = self.engine.state.players.get(self.player_id)
            if p_state:
                initial_avatar = getattr(p_state, "avatar", None) or getattr(p_state, "avatar_filename", "jace.png")

        if self.is_local:
            profile = ProfileManager.load_profile()
            self.player_name = profile.get("nickname", player_name)
            if not initial_avatar or initial_avatar == "jace.png":
                self.avatar_filename = profile.get("avatar_filename", "jace.png")
            else:
                self.avatar_filename = initial_avatar
        else:
            self.avatar_filename = initial_avatar or "jace.png"

        self.is_stats_visible = False
        self.is_cmdr_visible = False

        self.cmdr_dmg_labels = {}
        self.card_states = {}
        self.card_row_widgets = {}

        self.hide_drawn_var = ctk.BooleanVar(value=False)
        self.draw_x_var = ctk.StringVar(value="1")
        self.tooltip = CardHoverTooltip(self)
        self._hover_timer = None  # Timer for delayed hover preview

        # --- MAIN BOARD ---
        self.main_board = ctk.CTkFrame(self, fg_color="transparent")
        self.main_board.pack(fill="both", expand=True, padx=6, pady=6)

        # --- TOP BAR ---
        self.top_bar = ctk.CTkFrame(self.main_board, fg_color="#1a1a1a", corner_radius=8, height=44)
        self.top_bar.pack(fill="x", side="top", pady=(0, 5))
        self.top_bar.pack_propagate(False)

        self.right_group = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.right_group.pack(side="right", padx=10)

        self.lbl_status = ctk.CTkLabel(
            self.right_group, text="WAITING", font=(FONT_UI, 11, "bold"), text_color="#666666"
        )
        self.lbl_status.pack(side="right", padx=(5, 0))

        self.avatar_img_ref = None
        self.lbl_avatar = ctk.CTkLabel(self.right_group, text="", width=32, height=32, cursor="hand2")
        self.lbl_avatar.pack(side="right", padx=5)
        self.lbl_avatar.bind("<Button-1>", lambda e: self.open_emote_menu())

        self.lbl_name = ctk.CTkLabel(
            self.right_group, text=self.player_name, font=(FONT_UI, 14, "bold"), text_color="#FFFFFF", cursor="hand2"
        )
        self.lbl_name.pack(side="right", padx=5)
        self.lbl_name.bind("<Button-1>", lambda e: self.open_emote_menu())

        self.center_stats_container = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.center_stats_container.place(relx=0.42, rely=0.5, anchor="center")

        self.btn_tax = ctk.CTkButton(self.center_stats_container, text="TAX: 0", font=(FONT_UI, 11, "bold"), width=52,
                                     height=26, fg_color="#252525", hover_color="#333333")
        self.btn_tax.pack(side="left", padx=(0, 6))
        self.btn_tax.bind("<Button-1>", lambda e: self.change_tax(2))
        self.btn_tax.bind("<Button-3>", lambda e: self.change_tax(-2))

        self.btn_minus_5_hp = ctk.CTkButton(self.center_stats_container, text="-5", font=(FONT_UI, 11, "bold"),
                                            width=28, height=28, fg_color="#2a2a2a", hover_color="#3a3a3a",
                                            command=lambda: self.change_hp(-5))
        self.btn_minus_5_hp.pack(side="left", padx=1)

        self.btn_minus_hp = ctk.CTkButton(self.center_stats_container, text="−", font=(FONT_UI, 16, "bold"), width=28,
                                          height=28, fg_color="#2a2a2a", hover_color="#3a3a3a",
                                          command=lambda: self.change_hp(-1))
        self.btn_minus_hp.pack(side="left", padx=1)

        self.lbl_hp = ctk.CTkLabel(self.center_stats_container, text=str(DEFAULT_MAX_HP),
                                   font=(FONT_HEADER, 22, "bold"), text_color="#00FF66", width=46)
        self.lbl_hp.pack(side="left", padx=2)

        self.btn_plus_hp = ctk.CTkButton(self.center_stats_container, text="+", font=(FONT_UI, 16, "bold"), width=28,
                                         height=28, fg_color="#2a2a2a", hover_color="#3a3a3a",
                                         command=lambda: self.change_hp(1))
        self.btn_plus_hp.pack(side="left", padx=1)

        self.btn_plus_5_hp = ctk.CTkButton(self.center_stats_container, text="+5", font=(FONT_UI, 11, "bold"), width=28,
                                           height=28, fg_color="#2a2a2a", hover_color="#3a3a3a",
                                           command=lambda: self.change_hp(5))
        self.btn_plus_5_hp.pack(side="left", padx=1)

        self.btn_cmdr_damage = ctk.CTkButton(self.center_stats_container, text="⚔", font=(FONT_UI, 12, "bold"),
                                             width=30, height=26, fg_color="#252525", hover_color="#333333",
                                             command=self.toggle_cmdr_panel)
        self.btn_cmdr_damage.pack(side="left", padx=(6, 6))

        self.btn_poison = ctk.CTkButton(self.center_stats_container, text="PSN: 0", font=(FONT_UI, 11, "bold"),
                                        width=52, height=26, fg_color="#252525", hover_color="#333333")
        self.btn_poison.pack(side="left", padx=(0, 0))
        self.btn_poison.bind("<Button-1>", lambda e: self.change_poison(1))
        self.btn_poison.bind("<Button-3>", lambda e: self.change_poison(-1))

        # --- MAIN VIDEO AREA ---
        self.center_area = ctk.CTkFrame(self.main_board, fg_color="#0A0A0A", corner_radius=8)
        self.center_area.pack(fill="both", expand=True)

        self.lbl_video_frame = ctk.CTkLabel(self.center_area, text="", fg_color="transparent")
        self.lbl_video_frame.pack(fill="both", expand=True)

        self.center_area.bind("<Button-3>", lambda e: self._select_stream_source())
        self.lbl_video_frame.bind("<Button-3>", lambda e: self._select_stream_source())

        self.btn_connect_stream = ctk.CTkButton(
            self.center_area,
            text="🎥 SHARE / CONNECT TABLE",
            font=(FONT_UI, 11, "bold"),
            fg_color="#1E1E1E",
            border_color="#00FF66",
            border_width=1,
            hover_color="#2A2A2A",
            text_color="#00FF66",
            command=self._select_stream_source
        )
        self.btn_connect_stream.place(relx=0.5, rely=0.5, anchor="center")

        self.btn_stats = ctk.CTkButton(self.center_area, text="STATS", font=(FONT_UI, 10, "bold"), width=48, height=22,
                                       fg_color="#252525", hover_color="#333333", command=self.toggle_stats_panel)
        self.btn_stats.place(x=6, y=6)

        # --- VIEW OPTIONS MENU BUTTON ---
        view_img = None
        view_icon_path = os.path.join(BASE_DIR, "assets", "iconsNbuttons", "viewMenu.png")
        if os.path.exists(view_icon_path):
            try:
                pil_img = Image.open(view_icon_path)
                view_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(22, 22))
            except Exception:
                pass

        self.btn_view_options = ctk.CTkButton(
            self.center_area,
            text="" if view_img else "⛶",
            image=view_img,
            width=28,
            height=28,
            font=(FONT_UI, 13, "bold"),
            fg_color="#252525",
            hover_color="#3A3A3A",
            text_color="#00FF66",
            corner_radius=6,
            command=self.open_views_options_menu
        )
        self.btn_view_options.place(relx=0.98, rely=0.95, anchor="se")

        self.cmdr_dropdown_frame = ctk.CTkFrame(self.center_area, fg_color="#1a1a1a", border_width=1,
                                                border_color="#333333", corner_radius=8, width=200)

        self._setup_stats_panel_ui()
        self.load_deck(deck_cards or {})
        self.set_player_avatar(self.avatar_filename)

    def open_views_options_menu(self):
        """Opens view options menu (Full Screen and Duel Mode)."""
        if self._active_views_menu and self._active_views_menu.winfo_exists():
            self._active_views_menu.destroy()
            self._active_views_menu = None
            return

        menu = ctk.CTkFrame(self.center_area, fg_color="#1E1E1E", border_width=1, border_color="#333333",
                            corner_radius=8)
        self._active_views_menu = menu
        menu.place(relx=0.98, x=-5, rely=0.90, anchor="se")
        menu.lift()

        # 1. Full Screen option
        btn_fs = ctk.CTkButton(
            menu,
            text="⛶ Full Screen",
            font=(FONT_UI, 11, "bold"),
            fg_color="#2B2B2B",
            hover_color="#3A3A3A",
            text_color="#00FF66",
            anchor="w",
            height=32,
            command=lambda: (menu.destroy(), setattr(self, "_active_views_menu", None),
                             self.on_fullscreen_callback(self.player_id) if self.on_fullscreen_callback else None)
        )
        btn_fs.pack(fill="x", padx=6, pady=(6, 3))

        # 2. Duel Mode option
        duel_img = None
        duel_icon_path = os.path.join(BASE_DIR, "assets", "iconsNbuttons", "duelMode.png")
        if os.path.exists(duel_icon_path):
            try:
                pil_img = Image.open(duel_icon_path)
                duel_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(24, 24))
            except Exception:
                pass

        btn_duel = ctk.CTkButton(
            menu,
            text="  1v1 Duel Mode",
            image=duel_img,
            compound="left",
            font=(FONT_UI, 11, "bold"),
            fg_color="#2B2B2B",
            hover_color="#3A3A3A",
            text_color="#FFD700",
            anchor="w",
            height=32,
            command=self.open_duel_opponent_subselector
        )
        btn_duel.pack(fill="x", padx=6, pady=(3, 6))

    def open_duel_opponent_subselector(self):
        """Submenu for choosing an opponent in Duel Mode."""
        if self._active_views_menu and self._active_views_menu.winfo_exists():
            self._active_views_menu.destroy()

        menu = ctk.CTkFrame(self.center_area, fg_color="#1E1E1E", border_width=1, border_color="#333333",
                            corner_radius=8)
        self._active_views_menu = menu
        menu.place(relx=0.98, x=-5, rely=0.90, anchor="se")
        menu.lift()

        lbl_title = ctk.CTkLabel(menu, text="Select Opponent", font=(FONT_UI, 11, "bold"), text_color="#FFD700")
        lbl_title.pack(padx=10, pady=(8, 4))

        players_source = self.all_players if isinstance(self.all_players, dict) else {}
        for p_id, p_state in players_source.items():
            if p_id == self.player_id:
                continue

            p_name = getattr(p_state, "name", str(p_id))

            btn_opp = ctk.CTkButton(
                menu,
                text=f"⚔ {p_name}",
                font=(FONT_UI, 11, "bold"),
                fg_color="#2B2B2B",
                hover_color="#3A3A3A",
                text_color="#FFFFFF",
                anchor="w",
                height=28,
                command=lambda target_id=p_id: (menu.destroy(), setattr(self, "_active_views_menu", None),
                                                self.on_duel_callback(target_id) if self.on_duel_callback else None)
            )
            btn_opp.pack(fill="x", padx=6, pady=2)

    def _select_stream_source(self):
        StreamSourceDialog(self, on_select_callback=self.start_capturing_camera)

    def start_capturing_camera(self, camera_index):
        print(f"[STREAM] Starting video device index: {camera_index}")
        self.is_capturing = False
        self.after(200, lambda: self._init_capture_thread(camera_index))

    def _init_capture_thread(self, camera_index):
        self.is_capturing = True
        threading.Thread(target=self._capture_loop, args=(camera_index,), daemon=True).start()

    def _capture_loop(self, camera_index):
        cap = cv2.VideoCapture(camera_index, cv2.CAP_MSMF)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        while getattr(self, "is_capturing", True):
            try:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(cv_img)

                w = max(150, self.center_area.winfo_width())
                h = max(100, self.center_area.winfo_height())
                pil_img = pil_img.resize((w, h), Image.Resampling.LANCZOS)

                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
                self.after(0, lambda img=ctk_img: self.update_video_frame(img))

            except Exception as e:
                print(f"[STREAM ERROR] {e}")
                break

            time.sleep(0.033)

        cap.release()

    def update_video_frame(self, ctk_image):
        if self.btn_connect_stream.winfo_ismapped():
            self.btn_connect_stream.place_forget()
        self.lbl_video_frame.configure(image=ctk_image)
        self.lbl_video_frame.image = ctk_image

    def _setup_stats_panel_ui(self):
        """Constructs the slide-out deck statistics and card probability panel."""
        self.stats_panel = ctk.CTkFrame(self.center_area, fg_color="#1a1a1a", border_width=1, border_color="#333333",
                                        corner_radius=8, width=280)

        lbl_stats_title = ctk.CTkLabel(self.stats_panel, text="Deck Stats & Probability",
                                       font=(FONT_HEADER, 11, "bold"), text_color="#FFFFFF")
        lbl_stats_title.pack(pady=(6, 2))

        filter_bar = ctk.CTkFrame(self.stats_panel, fg_color="transparent")
        filter_bar.pack(fill="x", padx=6, pady=2)

        lbl_draw = ctk.CTkLabel(filter_bar, text="Draw X:", font=(FONT_UI, 9), text_color="#AAAAAA")
        lbl_draw.pack(side="left", padx=(2, 2))

        entry_draw = ctk.CTkEntry(filter_bar, textvariable=self.draw_x_var, width=32, height=20, font=(FONT_UI, 9),
                                  justify="center")
        entry_draw.pack(side="left", padx=(0, 2))
        entry_draw.bind("<KeyRelease>", lambda e: self.recalculate_probabilities())

        self.lbl_gen_prob = ctk.CTkLabel(filter_bar, text="(0.0%)", font=(FONT_UI, 9, "bold"), text_color="#00FF66")
        self.lbl_gen_prob.pack(side="left", padx=(2, 6))

        chk_hide = ctk.CTkCheckBox(
            filter_bar,
            text="Hide drawn",
            font=(FONT_UI, 9),
            variable=self.hide_drawn_var,
            checkbox_width=14,
            checkbox_height=14,
            border_width=1,
            command=self.apply_visibility_filter
        )
        chk_hide.pack(side="right", padx=(0, 2))

        self.card_scroll_frame = ctk.CTkScrollableFrame(self.stats_panel, fg_color="transparent", width=260, height=180)
        self.card_scroll_frame.pack(fill="both", expand=True, padx=4, pady=4)

    def load_deck(self, raw_deck):
        """Loads and parses raw deck dictionary/list data into internal state."""
        self.card_states.clear()
        cards_dict = {}

        if isinstance(raw_deck, str) and raw_deck.strip():
            if hasattr(DBManager, "get_deck_by_name"):
                deck_info = DBManager.get_deck_by_name(raw_deck) or {}
                cards_dict = deck_info.get("cards", {})
            elif hasattr(DBManager, "get_deck_cards"):
                cards_dict = DBManager.get_deck_cards(raw_deck) or {}
        elif isinstance(raw_deck, (dict, list)):
            cards_dict = raw_deck

        if isinstance(cards_dict, dict):
            for c_name, qty in cards_dict.items():
                try:
                    q = int(qty)
                except (ValueError, TypeError):
                    q = 1
                self.card_states[str(c_name)] = {"max_qty": q, "drawn_qty": 0}
        elif isinstance(cards_dict, list):
            for item in cards_dict:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("card_name") or "Unknown"
                    qty = item.get("count") or item.get("qty") or 1
                    self.card_states[str(name)] = {"max_qty": int(qty), "drawn_qty": 0}
                elif isinstance(item, str):
                    current = self.card_states.get(item, {}).get("max_qty", 0)
                    self.card_states[item] = {"max_qty": current + 1, "drawn_qty": 0}

        self.build_deck_stats_ui()

    @property
    def current_deck_size(self) -> int:
        total_remaining = 0
        for info in self.card_states.values():
            left = info["max_qty"] - info["drawn_qty"]
            total_remaining += max(0, left)
        return total_remaining

    def build_deck_stats_ui(self):
        """Builds scrollable deck list with card thumbnails and delayed hover preview bindings."""
        if not hasattr(self, "card_scroll_frame"):
            return

        for child in self.card_scroll_frame.winfo_children():
            child.destroy()
        self.card_row_widgets.clear()

        if not self.card_states:
            lbl_empty = ctk.CTkLabel(self.card_scroll_frame, text="No cards in deck", font=(FONT_UI, 11, "italic"),
                                     text_color="#666666")
            lbl_empty.pack(pady=20)
            return

        for card_name, info in sorted(self.card_states.items()):
            max_qty = info["max_qty"]
            drawn_qty = info["drawn_qty"]

            row = ctk.CTkFrame(self.card_scroll_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            self.card_row_widgets[card_name] = row

            if max_qty == 1:
                chk_var = ctk.BooleanVar(value=(drawn_qty > 0))
                chk = ctk.CTkCheckBox(
                    row, text="", width=18, height=18, checkbox_width=15, checkbox_height=15, border_width=1,
                    corner_radius=3, variable=chk_var,
                    command=lambda name=card_name, var=chk_var: self._on_single_card_toggle(name, var)
                )
                chk.pack(side="left", padx=(2, 4))
            else:
                cnt_var = ctk.StringVar(value=f"{drawn_qty}/{max_qty}")
                btn_m = ctk.CTkButton(row, text="-", width=16, height=16, font=(FONT_UI, 8),
                                      command=lambda n=card_name: self._change_card_qty(n, -1))
                btn_m.pack(side="left", padx=1)

                lbl_c = ctk.CTkLabel(row, textvariable=cnt_var, font=(FONT_UI, 9), width=22)
                lbl_c.pack(side="left")

                btn_p = ctk.CTkButton(row, text="+", width=16, height=16, font=(FONT_UI, 8),
                                      command=lambda n=card_name: self._change_card_qty(n, 1))
                btn_p.pack(side="left", padx=1)
                info["cnt_var"] = cnt_var

            # Thumbnail in stats list
            thumb_lbl = ctk.CTkLabel(
                row,
                text="Card",
                fg_color="#1E1E1E",
                text_color="#888888",
                corner_radius=4,
                width=36,
                height=50,
                font=(FONT_UI, 8)
            )
            thumb_lbl.pack(side="left", padx=(2, 6))

            self._load_stat_card_thumbnail(card_name, thumb_lbl)

            # Delayed hover implementation (800ms timer allows smooth scrolling without accidental popups)
            def on_enter(e, name=card_name):
                if self._hover_timer:
                    self.after_cancel(self._hover_timer)
                self._hover_timer = self.after(800, lambda: self._show_card_preview_on_hover(name, e.x_root, e.y_root))

            def on_leave(e):
                if self._hover_timer:
                    self.after_cancel(self._hover_timer)
                    self._hover_timer = None
                self.tooltip.hide()

            thumb_lbl.bind("<Enter>", on_enter)
            thumb_lbl.bind("<Leave>", on_leave)

            lbl_name = ctk.CTkLabel(row, text=card_name, font=(FONT_UI, 10, "bold"), text_color="#DDDDDD", anchor="w")
            lbl_name.pack(side="left", expand=True, fill="x")
            lbl_name.bind("<Enter>", on_enter)
            lbl_name.bind("<Leave>", on_leave)

            lbl_pct = ctk.CTkLabel(row, text="0.0%", font=(FONT_UI, 10, "bold"), text_color="#00FF66", width=42,
                                   anchor="e")
            lbl_pct.pack(side="right", padx=(2, 2))
            info["lbl_pct"] = lbl_pct

        self.apply_visibility_filter()
        self.recalculate_probabilities()

    def _load_stat_card_thumbnail(self, card_name, target_label):
        """Asynchronously loads card thumbnail for the stats row."""
        def _fetch():
            cache_dir = os.path.join(BASE_DIR, "cache", "card_images")
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            safe_name = "".join(c for c in card_name if c.isalnum() or c in (' ', '_')).rstrip()
            file_path = os.path.join(cache_dir, f"{safe_name}.jpg")

            if not os.path.exists(file_path):
                img_url = ScryfallAPI.get_card_image_path(card_name)
                if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                    try:
                        res = requests.get(img_url, timeout=4)
                        if res.status_code == 200:
                            with open(file_path, "wb") as f:
                                f.write(res.content)
                    except Exception:
                        file_path = None
                else:
                    file_path = img_url if (img_url and os.path.exists(img_url)) else None

            if file_path and os.path.exists(file_path):
                try:
                    pil_img = Image.open(file_path)
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(36, 50))
                    self.after(0, lambda: target_label.configure(image=ctk_img, text=""))
                    target_label.image = ctk_img
                except Exception:
                    pass

        threading.Thread(target=_fetch, daemon=True).start()

    def _show_card_preview_on_hover(self, card_name, x, y):
        """Displays full-resolution card tooltip preview on hover after delay."""
        self.tooltip.show_image(None, x, y, card_name)

        def _fetch():
            file_path = ScryfallAPI.get_card_image_path(card_name)
            self.after(0, lambda: self.tooltip.show_image(file_path, x, y, card_name))

        threading.Thread(target=_fetch, daemon=True).start()

    def apply_visibility_filter(self):
        hide_drawn = self.hide_drawn_var.get()
        for card_name, row_frame in self.card_row_widgets.items():
            info = self.card_states[card_name]
            is_fully_drawn = info["drawn_qty"] >= info["max_qty"]

            if hide_drawn and is_fully_drawn:
                row_frame.pack_forget()
            else:
                row_frame.pack_forget()
                row_frame.pack(fill="x", pady=2, side="top")

    def recalculate_probabilities(self):
        deck_left = self.current_deck_size
        for card_name, info in self.card_states.items():
            copies_left = info["max_qty"] - info["drawn_qty"]
            chance = 0.0 if copies_left <= 0 or deck_left <= 0 else OddsCalculator.calculate_chance(deck_size=deck_left,
                                                                                                    copies_in_deck=copies_left,
                                                                                                    hand_size=1)
            if "lbl_pct" in info:
                info["lbl_pct"].configure(text=f"{chance:.1f}%", text_color="#00FF66" if chance > 0 else "#666666")

        try:
            draw_x = max(1, int(self.draw_x_var.get()))
        except ValueError:
            draw_x = 1

        if deck_left > 0:
            draw_x_chance = OddsCalculator.calculate_draw_chance(deck_size=deck_left, outs_left=1, cards_to_draw=draw_x)
            self.lbl_gen_prob.configure(text=f"({draw_x_chance:.1f}%)")
        else:
            self.lbl_gen_prob.configure(text="(0.0%)")

    def _on_single_card_toggle(self, card_name, var):
        val = 1 if var.get() else 0
        self.card_states[card_name]["drawn_qty"] = val
        self.apply_visibility_filter()
        self.recalculate_probabilities()

        if self.client and self.is_local:
            self.client.send_action("TOGGLE_CARD",
                                    {"player_id": self.player_id, "card_name": card_name, "drawn_qty": val})

    def _change_card_qty(self, card_name, delta):
        info = self.card_states[card_name]
        new_val = max(0, min(info["max_qty"], info["drawn_qty"] + delta))
        info["drawn_qty"] = new_val
        if "cnt_var" in info:
            info["cnt_var"].set(f"{new_val}/{info['max_qty']}")

        self.apply_visibility_filter()
        self.recalculate_probabilities()

        if self.client and self.is_local:
            self.client.send_action("TOGGLE_CARD",
                                    {"player_id": self.player_id, "card_name": card_name, "drawn_qty": new_val})

    def sync_card_state_from_network(self, card_name, drawn_qty):
        if card_name in self.card_states:
            self.card_states[card_name]["drawn_qty"] = drawn_qty
            if "cnt_var" in self.card_states[card_name]:
                self.card_states[card_name]["cnt_var"].set(f"{drawn_qty}/{self.card_states[card_name]['max_qty']}")
            self.apply_visibility_filter()
            self.recalculate_probabilities()

    def init_cmdr_damage_ui(self):
        for child in self.cmdr_dropdown_frame.winfo_children():
            child.destroy()
        self.cmdr_dmg_labels.clear()

        if not self.engine or not hasattr(self.engine, "state"):
            return

        lbl_title = ctk.CTkLabel(self.cmdr_dropdown_frame, text="Commander Damage", font=(FONT_UI, 10, "bold"),
                                 text_color="#888888")
        lbl_title.pack(pady=(4, 2))

        for p_id, opponent in self.engine.state.players.items():
            if p_id == self.player_id:
                continue

            row_frame = ctk.CTkFrame(self.cmdr_dropdown_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=8, pady=3)

            lbl_opp = ctk.CTkLabel(row_frame, text=f"⚔ {opponent.name}", font=(FONT_UI, 11, "bold"),
                                   text_color="#FFFFFF", anchor="w")
            lbl_opp.pack(side="left", expand=True, fill="x")

            btn_minus = ctk.CTkButton(row_frame, text="-", font=(FONT_UI, 11, "bold"), width=22, height=22,
                                      fg_color="#2d2d2d", hover_color="#3d3d3d",
                                      command=lambda opp_id=p_id: self.change_cmdr_damage(opp_id, -1))
            btn_minus.pack(side="left", padx=2)

            lbl_dmg = ctk.CTkLabel(row_frame, text="0", font=(FONT_UI, 12, "bold"), text_color="#FFFFFF", width=24)
            lbl_dmg.pack(side="left", padx=2)

            btn_plus = ctk.CTkButton(row_frame, text="+", font=(FONT_UI, 11, "bold"), width=22, height=22,
                                     fg_color="#2d2d2d", hover_color="#3d3d3d",
                                     command=lambda opp_id=p_id: self.change_cmdr_damage(opp_id, 1))
            btn_plus.pack(side="left", padx=2)

            self.cmdr_dmg_labels[p_id] = lbl_dmg

    def update_from_state(self, state):
        p_state = state.players.get(self.player_id)
        if not p_state:
            return

        if not self.card_states and hasattr(p_state, "deck") and p_state.deck:
            self.load_deck(p_state.deck)

        avatar_to_set = getattr(p_state, "avatar", None) or getattr(p_state, "avatar_filename", None)
        if avatar_to_set:
            self.set_player_avatar(avatar_to_set)

        if hasattr(p_state, "name") and p_state.name:
            self.lbl_name.configure(text=p_state.name)

        max_hp = getattr(p_state, "max_hp", DEFAULT_MAX_HP)
        ratio = p_state.hp / max_hp if max_hp > 0 else 1.0
        hp_color = "#00FF66" if ratio > 0.75 else (
            "#B4FF00" if ratio > 0.5 else ("#FFB300" if ratio > 0.25 else "#FF3333"))
        self.lbl_hp.configure(text=str(p_state.hp), text_color=hp_color)

        self.btn_poison.configure(text=f"PSN: {p_state.poison}")
        self.btn_tax.configure(text=f"TAX: {p_state.cmdr_tax}")

        if not self.cmdr_dmg_labels:
            self.init_cmdr_damage_ui()

        for opp_id, lbl_dmg in self.cmdr_dmg_labels.items():
            damage_val = p_state.cmdr_damage_received.get(opp_id, 0)
            lbl_dmg.configure(text=str(damage_val), text_color="#FF4444" if damage_val >= 21 else "#FFFFFF")

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

    def _send_action(self, action_name, payload):
        if self.client and self.client.is_connected:
            self.client.send_action(action_name, payload)

    def change_hp(self, delta: int):
        p_state = self.engine.state.players.get(self.player_id) if self.engine else None
        if p_state:
            new_hp = max(0, p_state.hp + delta)
            self._send_action("UPDATE_HP", {"player_id": self.player_id, "hp": new_hp, "delta": delta})

    def change_poison(self, delta: int):
        p_state = self.engine.state.players.get(self.player_id) if self.engine else None
        if p_state:
            new_poison = max(0, p_state.poison + delta)
            self._send_action("UPDATE_POISON", {"player_id": self.player_id, "poison": new_poison, "delta": delta})

    def change_tax(self, delta: int):
        p_state = self.engine.state.players.get(self.player_id) if self.engine else None
        if p_state:
            new_tax = max(0, p_state.cmdr_tax + delta)
            self._send_action("UPDATE_TAX", {"player_id": self.player_id, "tax": new_tax, "delta": delta})

    def change_cmdr_damage(self, opponent_id: str, delta: int):
        p_state = self.engine.state.players.get(self.player_id) if self.engine else None
        if p_state:
            curr = p_state.cmdr_damage_received.get(opponent_id, 0)
            new_dmg = max(0, curr + delta)
            updated_dmg = dict(p_state.cmdr_damage_received)
            updated_dmg[opponent_id] = new_dmg
            self._send_action("UPDATE_CMDR_DMG", {
                "player_id": self.player_id,
                "cmdr_damage": updated_dmg
            })

    def toggle_stats_panel(self):
        if self.is_stats_visible:
            self.stats_panel.place_forget()
            self.is_stats_visible = False
        else:
            if self.is_cmdr_visible:
                self.toggle_cmdr_panel()
            self.stats_panel.place(x=6, y=32)
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

    def set_player_avatar(self, avatar_filename: str):
        avatar_path = os.path.join(AVATARS_DIR, avatar_filename)
        if not os.path.exists(avatar_path):
            avatar_path = os.path.join(AVATARS_DIR, "jace.png")

        try:
            pil_img = Image.open(avatar_path)
            self.avatar_img_ref = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(32, 32))
            self.lbl_avatar.configure(image=self.avatar_img_ref)
        except Exception as e:
            print(f"[AVATAR ERROR] Failed to load avatar image: {e}")

    def open_emote_menu(self):
        if not self.is_local:
            return

        if hasattr(self, "_active_emote_menu") and self._active_emote_menu:
            try:
                self._active_emote_menu.destroy()
            except Exception:
                pass
            self._active_emote_menu = None
            return

        profile = ProfileManager.load_profile() if self.is_local else {}
        emotes = profile.get("selected_emotes", [])

        if not emotes:
            try:
                emotes = [f for f in os.listdir(EMOTES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))][:6]
            except Exception:
                emotes = []

        if not emotes:
            return

        menu = ctk.CTkFrame(self.main_board, fg_color="#1E1E1E", corner_radius=8, border_width=1, border_color="#333333")
        self._active_emote_menu = menu
        menu.place(relx=1.0, x=-10, y=45, anchor="ne")
        menu.lift()

        def close_menu():
            try:
                menu.destroy()
            except Exception:
                pass
            if hasattr(self, "_active_emote_menu"):
                self._active_emote_menu = None

        for emote_filename in emotes:
            img_path = os.path.join(EMOTES_DIR, emote_filename)
            try:
                pil_img = Image.open(img_path)
                pil_img.seek(0)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(36, 36))
            except Exception:
                ctk_img = None

            btn = ctk.CTkButton(
                menu,
                text="",
                image=ctk_img,
                width=42,
                height=42,
                fg_color="#2B2B2B",
                hover_color="#3A3A3A",
                command=lambda fn=emote_filename: (close_menu(), self.send_and_show_emote(fn))
            )
            btn.pack(pady=4, padx=4)

    def send_and_show_emote(self, emote_filename):
        if self.is_local and self.on_emote_callback:
            self.on_emote_callback(self.player_id, emote_filename)

    def _animate_flying_emote(self, filename):
        img_path = os.path.join(EMOTES_DIR, filename)
        if not os.path.exists(img_path):
            return

        try:
            pil_img = Image.open(img_path)
        except Exception:
            return

        frames = []
        try:
            for frame in ImageSequence.Iterator(pil_img):
                frame_copy = frame.copy().convert("RGBA")
                ctk_img = ctk.CTkImage(light_image=frame_copy, dark_image=frame_copy, size=(64, 64))
                frames.append(ctk_img)
        except Exception:
            pass

        if not frames:
            return

        fly_win = ctk.CTkToplevel(self)
        fly_win.overrideredirect(True)
        fly_win.attributes("-topmost", True)
        fly_win.configure(fg_color="#121212")

        lbl = ctk.CTkLabel(fly_win, text="", image=frames[0], fg_color="transparent")
        lbl.pack(fill="both", expand=True)

        start_x = self.lbl_avatar.winfo_rootx()
        start_y = self.lbl_avatar.winfo_rooty()

        fly_win.geometry(f"64x64+{start_x}+{start_y}")
        fly_win.deiconify()
        fly_win.lift()

        arc_offset = random.randint(-80, 80)
        steps = 35
        duration_ms = 1100
        delay = duration_ms // steps

        def step_animation(current_step):
            if current_step > steps or not fly_win.winfo_exists():
                if fly_win.winfo_exists():
                    fly_win.destroy()
                return

            progress = current_step / steps
            curr_x = start_x + (arc_offset * progress)
            curr_y = start_y + (180 * progress) + (40 * math_parabola_curve(progress))

            frame_idx = current_step % len(frames)
            lbl.configure(image=frames[frame_idx])

            try:
                fly_win.geometry(f"64x64+{int(curr_x)}+{int(curr_y)}")
            except Exception:
                pass
            self.after(delay, lambda: step_animation(current_step + 1))

        step_animation(0)


def math_parabola_curve(p):
    return -4 * (p - 0.5) ** 2 + 1