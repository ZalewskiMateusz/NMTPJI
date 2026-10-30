# gui/new_deck_window.py
import os
import threading
import requests
import customtkinter as ctk
from PIL import Image

from core.deck_parser import DeckParser
from database.db_manager import DBManager
from core.scryfall import ScryfallAPI

CACHE_DIR = "cache/card_images"


class NewDeckWindow(ctk.CTkToplevel):
    """
    Modal window for creating a new deck or editing an existing one,
    featuring dynamic card list parsing, commander selection, and API image preview.
    """

    def __init__(self, parent, on_save_callback=None, deck_name=None, cards_dict=None):
        super().__init__(parent)

        self.on_save_callback = on_save_callback
        self.original_deck_name = deck_name

        window_title = f"Edit Deck: {deck_name}" if deck_name else "Add New Deck"
        self.title(window_title)
        self.geometry("450x720")

        self.attributes("-topmost", True)
        self.focus_force()

        # 1. Deck Name Input Field
        self.name_label = ctk.CTkLabel(self, text="Deck Name:", font=("Segoe UI", 12, "bold"))
        self.name_label.pack(pady=(10, 0), padx=20, anchor="w")

        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Krenko Goblins")
        self.name_entry.pack(fill="x", padx=20, pady=(2, 5))

        if deck_name:
            self.name_entry.insert(0, deck_name)

        # 2. Game Format Selection
        self.format_label = ctk.CTkLabel(self, text="Deck Format:", font=("Segoe UI", 12, "bold"))
        self.format_label.pack(pady=(5, 0), padx=20, anchor="w")

        self.format_option_menu = ctk.CTkOptionMenu(
            self,
            values=["Commander / EDH"],
            command=self.on_format_change
        )
        self.format_option_menu.set("Commander / EDH")
        self.format_option_menu.pack(fill="x", padx=20, pady=(2, 5))

        # 3. Commander Selection + Thumbnail Container Frame
        self.commander_label = ctk.CTkLabel(self, text="Select Commander:", font=("Segoe UI", 12, "bold"))
        self.commander_label.pack(pady=(5, 0), padx=20, anchor="w")

        cmd_frame = ctk.CTkFrame(self, fg_color="transparent")
        cmd_frame.pack(fill="x", padx=20, pady=(2, 5))

        # Dropdown menu on the left side of cmd_frame
        self.commander_option_menu = ctk.CTkOptionMenu(
            cmd_frame,
            values=["Paste decklist first"],
            command=self.on_commander_selected
        )
        self.commander_option_menu.set("Paste decklist first")
        self.commander_option_menu.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Commander card thumbnail preview on the right side of cmd_frame
        self.commander_img_label = ctk.CTkLabel(
            cmd_frame,
            text="No Image",
            fg_color="#1E1E1E",
            text_color="#666666",
            corner_radius=6,
            width=70,
            height=98,
            font=("Segoe UI", 9)
        )
        self.commander_img_label.pack(side="right")

        # 4. Decklist Textbox Input
        self.list_label = ctk.CTkLabel(self, text="Paste Archidekt / Decklist:", font=("Segoe UI", 12, "bold"))
        self.list_label.pack(pady=(5, 0), padx=20, anchor="w")

        self.decklist_textbox = ctk.CTkTextbox(self, height=180)
        self.decklist_textbox.pack(fill="both", expand=True, padx=20, pady=(2, 5))

        # Bind key release to dynamically update the commander dropdown list in real-time
        self.decklist_textbox.bind("<KeyRelease>", self.update_commander_list)

        # Pre-fill data if editing an existing deck
        if cards_dict:
            formatted_text = "\n".join([f"{qty}x {card}" for card, qty in cards_dict.items()])
            self.decklist_textbox.insert("1.0", formatted_text)
            self.update_commander_list()

            # Retrieve saved commander data from database if available
            if hasattr(DBManager, "get_deck_by_name"):
                deck_info = DBManager.get_deck_by_name(deck_name)
                if isinstance(deck_info, dict) and deck_info.get("commander"):
                    saved_cmd = deck_info.get("commander")
                    if saved_cmd in self.commander_option_menu.cget("values"):
                        self.commander_option_menu.set(saved_cmd)
                        self.load_commander_image(saved_cmd)

        # 5. Save Deck Button
        self.save_button = ctk.CTkButton(self, text="Save Deck", command=self.save_deck, fg_color="#1F6AA5")
        self.save_button.pack(pady=15, padx=20)

    def on_format_change(self, selected_format):
        """Placeholder for future format switching logic."""
        pass

    def update_commander_list(self, event=None):
        """Parses the textbox content on the fly and updates available commanders in the option menu."""
        raw_text = self.decklist_textbox.get("1.0", "end-1c").strip()
        if not raw_text:
            self.commander_option_menu.configure(values=["Paste decklist first"])
            self.commander_option_menu.set("Paste decklist first")
            self.commander_img_label.configure(image="", text="No Image")
            return

        try:
            parsed_cards = DeckParser.parse_decklist(raw_text)
            card_names = sorted(list(parsed_cards.keys()))

            if card_names:
                current_selection = self.commander_option_menu.get()
                self.commander_option_menu.configure(values=card_names)

                if current_selection in card_names:
                    self.commander_option_menu.set(current_selection)
                else:
                    self.commander_option_menu.set(card_names[0])

                # Load image for the currently active selection
                self.load_commander_image(self.commander_option_menu.get())
            else:
                self.commander_option_menu.configure(values=["No valid cards found"])
                self.commander_option_menu.set("No valid cards found")
                self.commander_img_label.configure(image="", text="No Image")
        except Exception:
            pass

    def on_commander_selected(self, selected_commander):
        """Triggered when a new commander is selected from the dropdown menu."""
        if selected_commander not in ["Paste decklist first", "No valid cards found", ""]:
            self.load_commander_image(selected_commander)

    def load_commander_image(self, commander_name):
        """Fetches the commander image asynchronously in a background thread via Scryfall API."""
        self.commander_img_label.configure(text="Loading...", image="")

        def _fetch_thread():
            if not os.path.exists(CACHE_DIR):
                os.makedirs(CACHE_DIR)

            safe_name = "".join(c for c in commander_name if c.isalnum() or c in (' ', '_')).rstrip()
            file_path = os.path.join(CACHE_DIR, f"{safe_name}.jpg")

            if not os.path.exists(file_path):
                img_url = None
                try:
                    if hasattr(ScryfallAPI, "get_card_image_url"):
                        img_url = ScryfallAPI.get_card_image_url(commander_name)
                    elif hasattr(ScryfallAPI, "get_card_image_path"):
                        img_url = ScryfallAPI.get_card_image_path(commander_name)
                except Exception:
                    img_url = None

                if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                    try:
                        res = requests.get(img_url, timeout=5)
                        if res.status_code == 200:
                            with open(file_path, "wb") as f:
                                f.write(res.content)
                    except Exception:
                        file_path = None
                else:
                    file_path = img_url if (img_url and os.path.exists(img_url)) else None

            self.after(0, lambda: self._update_commander_image_widget(file_path))

        threading.Thread(target=_fetch_thread, daemon=True).start()

    def _update_commander_image_widget(self, file_path):
        """Safely renders the downloaded image file inside the GUI label widget."""
        try:
            if not self.commander_img_label.winfo_exists():
                return
        except Exception:
            return

        if file_path and os.path.exists(file_path):
            try:
                pil_img = Image.open(file_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(70, 98))
                self.commander_img_label.configure(image=ctk_img, text="")
                self.commander_img_label.image = ctk_img
            except Exception:
                self.commander_img_label.configure(image="", text="Error")
        else:
            self.commander_img_label.configure(image="", text="No Image")

    def save_deck(self):
        """Validates inputs, parses the decklist, and persists data into the SQLite database."""
        deck_name = self.name_entry.get().strip()
        raw_text = self.decklist_textbox.get("1.0", "end-1c").strip()
        game_format = self.format_option_menu.get()
        commander = self.commander_option_menu.get()

        if commander in ["Paste decklist first", "No valid cards found"]:
            commander = ""

        if not deck_name or not raw_text:
            print("Warning: Fill in both Name and Decklist!")
            return

        try:
            parsed_cards = DeckParser.parse_decklist(raw_text)

            if hasattr(DBManager, "save_deck"):
                try:
                    DBManager.save_deck(
                        deck_name=deck_name,
                        cards=parsed_cards,
                        game_format=game_format,
                        commander=commander
                    )
                except TypeError:
                    DBManager.save_deck(deck_name=deck_name, cards=parsed_cards)

            print(f"Deck '{deck_name}' [{game_format}] with Commander '{commander}' saved successfully!")

            if self.on_save_callback:
                self.on_save_callback()

            self.destroy()

        except Exception as e:
            print(f"Error saving deck: {e}")