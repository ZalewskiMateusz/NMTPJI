import os
import threading
import requests
import customtkinter as ctk
from PIL import Image

# Import z Twojego istniejącego folderu core
from core.calculator import OddsCalculator
from core.scryfall import ScryfallAPI

CACHE_DIR = "cache/card_images"


class CardHoverTooltip(ctk.CTkToplevel):
    """Pływające okienko z podglądem karty ze Scryfall."""

    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#1E1E1E")
        self.withdraw()

        self.lbl_image = ctk.CTkLabel(self, text="Pobieranie grafiki...")
        self.lbl_image.pack(padx=2, pady=2)

    def show_image(self, img_path, x, y):
        if img_path and os.path.exists(img_path):
            pil_img = Image.open(img_path)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 280))
            self.lbl_image.configure(image=ctk_img, text="")
        else:
            self.lbl_image.configure(image="", text="Brak obrazu")

        self.geometry(f"+{x + 20}+{y - 100}")
        self.deiconify()

    def hide(self):
        self.withdraw()


class DeckStatsWidget(ctk.CTkFrame):
    def __init__(self, master, raw_cards: dict, commander_name: str = "", **kwargs):
        super().__init__(master, fg_color="#1E1E1E", corner_radius=10, **kwargs)

        self.commander_name = commander_name
        self.tooltip = CardHoverTooltip(self)

        # 1. Przefiltrujemy bibliotekę - usuwamy Commandera z puli talii
        self.library = {}
        for c_name, qty in raw_cards.items():
            if c_name.lower() != commander_name.lower():
                self.library[c_name] = int(qty)

        # Słownik do śledzenia stanu na żywo w meczu
        self.card_states = {}
        for c_name, qty in self.library.items():
            self.card_states[c_name] = {
                "max_qty": qty,
                "drawn_qty": 0  # ile egzemplarzy zagrał/wyciągnął gracz
            }

        # UI Layout
        lbl_title = ctk.CTkLabel(self, text="Deck Stats & %", font=("Segoe UI", 12, "bold"), text_color="#FFFFFF")
        lbl_title.pack(pady=(8, 4))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=180)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=2)

        self._build_card_rows()
        self._build_x_draw_calculator()
        self.recalculate_all()

    @property
    def current_deck_size(self) -> int:
        """Zwraca aktualną liczbę kart pozostałych w bibliotece."""
        total = 0
        for info in self.card_states.values():
            left = info["max_qty"] - info["drawn_qty"]
            total += max(0, left)
        return total

    def _build_card_rows(self):
        for card_name, info in sorted(self.card_states.items()):
            max_qty = info["max_qty"]
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            # Obsługa: Checkbox (gdy 1 sztuka) vs Licznik -/+ (gdy wielokrotność np. 7x Forest)
            if max_qty == 1:
                chk_var = ctk.BooleanVar(value=False)
                control = ctk.CTkCheckBox(
                    row_frame, text=card_name, font=("Segoe UI", 11),
                    checkbox_width=16, checkbox_height=16,
                    onvalue=True, offvalue=False, variable=chk_var,
                    command=lambda name=card_name, var=chk_var: self._on_single_toggle(name, var)
                )
                control.pack(side="left", anchor="w")
                lbl_target = control
            else:
                lbl_name = ctk.CTkLabel(row_frame, text=card_name, font=("Segoe UI", 11), anchor="w")
                lbl_name.pack(side="left", padx=(0, 5))

                cnt_var = ctk.StringVar(value=f"0/{max_qty}")
                btn_minus = ctk.CTkButton(row_frame, text="-", width=18, height=18,
                                          command=lambda n=card_name: self._change_qty(n, -1))
                btn_minus.pack(side="left", padx=1)

                lbl_cnt = ctk.CTkLabel(row_frame, textvariable=cnt_var, font=("Segoe UI", 10))
                lbl_cnt.pack(side="left", padx=2)

                btn_plus = ctk.CTkButton(row_frame, text="+", width=18, height=18,
                                         command=lambda n=card_name: self._change_qty(n, 1))
                btn_plus.pack(side="left", padx=1)

                lbl_target = lbl_name
                info["cnt_var"] = cnt_var

            # Etykieta procentowa
            lbl_chance = ctk.CTkLabel(row_frame, text="0.0%", font=("Segoe UI", 11, "bold"), text_color="#00FF66")
            lbl_chance.pack(side="right", padx=5)

            info["lbl_chance"] = lbl_chance

            # Podpięcie zdarzenia Hover ze Scryfall
            lbl_target.bind("<Enter>", lambda e, name=card_name: self._on_hover_enter(e, name))
            lbl_target.bind("<Leave>", lambda e: self.tooltip.hide())

    def _on_single_toggle(self, card_name, var):
        self.card_states[card_name]["drawn_qty"] = 1 if var.get() else 0
        self.recalculate_all()

    def _change_qty(self, card_name, delta):
        info = self.card_states[card_name]
        new_val = max(0, min(info["max_qty"], info["drawn_qty"] + delta))
        info["drawn_qty"] = new_val
        info["cnt_var"].set(f"{new_val}/{info['max_qty']}")
        self.recalculate_all()

    def recalculate_all(self):
        """Używa Twojej klasy OddsCalculator z core/calculator.py do wyliczenia %."""
        deck_left = self.current_deck_size

        for card_name, info in self.card_states.items():
            copies_left = info["max_qty"] - info["drawn_qty"]

            if copies_left <= 0 or deck_left <= 0:
                chance = 0.0
            else:
                # Dociąg 1 karty (Topdeck)
                chance = OddsCalculator.calculate_chance(
                    deck_size=deck_left,
                    copies_in_deck=copies_left,
                    hand_size=1
                )

            info["lbl_chance"].configure(text=f"{chance:.1f}%")

    def _on_hover_enter(self, event, card_name):
        x, y = event.x_root, event.y_root

        def _fetch_thread():
            if not os.path.exists(CACHE_DIR):
                os.makedirs(CACHE_DIR)

            safe_name = "".join(c for c in card_name if c.isalnum() or c in (' ', '_')).rstrip()
            file_path = os.path.join(CACHE_DIR, f"{safe_name}.jpg")

            if not os.path.exists(file_path):
                img_url = ScryfallAPI.get_card_image_url(card_name)
                if img_url:
                    try:
                        res = requests.get(img_url, timeout=5)
                        if res.status_code == 200:
                            with open(file_path, "wb") as f:
                                f.write(res.content)
                    except Exception:
                        file_path = None
                else:
                    file_path = None

            self.after(0, lambda: self.tooltip.show_image(file_path, x, y))

        threading.Thread(target=_fetch_thread, daemon=True).start()

    def _build_x_draw_calculator(self):
        """Kalkulator szans na wyciągnięcie karty w X dociągach."""
        calc_frame = ctk.CTkFrame(self, fg_color="#141414", corner_radius=6)
        calc_frame.pack(fill="x", padx=5, pady=(4, 6))

        lbl_calc = ctk.CTkLabel(calc_frame, text="X-Draw Probability", font=("Segoe UI", 10, "bold"),
                                text_color="#A0A0A0")
        lbl_calc.pack(anchor="w", padx=5, pady=(2, 0))

        inputs_frame = ctk.CTkFrame(calc_frame, fg_color="transparent")
        inputs_frame.pack(fill="x", padx=5, pady=2)

        self.ent_outs = ctk.CTkEntry(inputs_frame, placeholder_text="Outs (np. 3)", width=70, height=24,
                                     font=("Segoe UI", 10))
        self.ent_outs.pack(side="left", padx=(0, 2))

        self.ent_draws = ctk.CTkEntry(inputs_frame, placeholder_text="Draws (np. 2)", width=70, height=24,
                                      font=("Segoe UI", 10))
        self.ent_draws.pack(side="left", padx=2)

        btn_calc = ctk.CTkButton(inputs_frame, text="%", width=30, height=24, command=self._calculate_x_draw)
        btn_calc.pack(side="left", padx=2)

        self.lbl_res = ctk.CTkLabel(calc_frame, text="Szansa: --%", font=("Segoe UI", 10, "bold"), text_color="#00FF66")
        self.lbl_res.pack(anchor="e", padx=5, pady=(0, 2))

    def _calculate_x_draw(self):
        try:
            outs = int(self.ent_outs.get())
            draws = int(self.ent_draws.get())
            deck_left = self.current_deck_size

            res = OddsCalculator.calculate_draw_chance(
                deck_size=deck_left,
                outs_left=outs,
                cards_to_draw=draws
            )
            self.lbl_res.configure(text=f"Szansa: {res:.1f}%")
        except ValueError:
            self.lbl_res.configure(text="Szansa: Błąd")