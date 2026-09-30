# gui/new_deck_window.py
import customtkinter as ctk
from core.deck_parser import DeckParser
from database.db_manager import DBManager


class NewDeckWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback=None, deck_name=None, cards_dict=None):
        super().__init__(parent)

        self.on_save_callback = on_save_callback
        self.original_deck_name = deck_name

        window_title = f"Edit Deck: {deck_name}" if deck_name else "Add New Deck"
        self.title(window_title)
        self.geometry("450x620")

        self.attributes("-topmost", True)
        self.focus_force()

        # 1. Nazwa Talii
        self.name_label = ctk.CTkLabel(self, text="Deck Name:", font=("Segoe UI", 12, "bold"))
        self.name_label.pack(pady=(10, 0), padx=20, anchor="w")

        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Krenko Goblins")
        self.name_entry.pack(fill="x", padx=20, pady=(2, 5))

        if deck_name:
            self.name_entry.insert(0, deck_name)

        # 2. Format Gry (SZTYWNO: Commander / EDH z możliwością rozbudowy)
        self.format_label = ctk.CTkLabel(self, text="Deck Format:", font=("Segoe UI", 12, "bold"))
        self.format_label.pack(pady=(5, 0), padx=20, anchor="w")

        self.format_option_menu = ctk.CTkOptionMenu(
            self,
            values=["Commander / EDH"],
            command=self.on_format_change
        )
        self.format_option_menu.set("Commander / EDH")
        self.format_option_menu.pack(fill="x", padx=20, pady=(2, 5))

        # 3. Wybór Commandera
        self.commander_label = ctk.CTkLabel(self, text="Select Commander:", font=("Segoe UI", 12, "bold"))
        self.commander_label.pack(pady=(5, 0), padx=20, anchor="w")

        self.commander_option_menu = ctk.CTkOptionMenu(
            self.card_frame if hasattr(self, "card_frame") else self,
            values=["Paste decklist first"]
        )
        self.commander_option_menu.set("Paste decklist first")
        self.commander_option_menu.pack(fill="x", padx=20, pady=(2, 5))

        # 4. Lista kart (Textbox)
        self.list_label = ctk.CTkLabel(self, text="Paste Archidekt / Decklist:", font=("Segoe UI", 12, "bold"))
        self.list_label.pack(pady=(5, 0), padx=20, anchor="w")

        self.decklist_textbox = ctk.CTkTextbox(self, height=200)
        self.decklist_textbox.pack(fill="both", expand=True, padx=20, pady=(2, 5))

        # Reagowanie na wklejanie / wpisywanie kart, by odświeżać menu Commandera
        self.decklist_textbox.bind("<KeyRelease>", self.update_commander_list)

        # Wypełnienie w przypadku edycji istniejącej talii
        if cards_dict:
            formatted_text = "\n".join([f"{qty}x {card}" for card, qty in cards_dict.items()])
            self.decklist_textbox.insert("1.0", formatted_text)
            self.update_commander_list()

            # Pobranie zapisanego dowódcy z bazy dla edytowanej talii (jeśli istnieje)
            if hasattr(DBManager, "get_deck_by_name"):
                deck_info = DBManager.get_deck_by_name(deck_name)
                if isinstance(deck_info, dict) and deck_info.get("commander"):
                    saved_cmd = deck_info.get("commander")
                    if saved_cmd in self.commander_option_menu.cget("values"):
                        self.commander_option_menu.set(saved_cmd)

        # 5. Przycisk zapisu
        self.save_button = ctk.CTkButton(self, text="Save Deck", command=self.save_deck, fg_color="#1F6AA5")
        self.save_button.pack(pady=15, padx=20)

    def on_format_change(self, selected_format):
        """Obsługa przełączania formatu na przyszłość."""
        if selected_format == "Commander / EDH":
            self.commander_label.pack(pady=(5, 0), padx=20, anchor="w")
            self.commander_option_menu.pack(fill="x", padx=20, pady=(2, 5))
        else:
            self.commander_label.pack_forget()
            self.commander_option_menu.pack_forget()

    def update_commander_list(self, event=None):
        """Parsuje tekst w locie i aktualizuje listę rozwijaną Commandera."""
        raw_text = self.decklist_textbox.get("1.0", "end-1c").strip()
        if not raw_text:
            self.commander_option_menu.configure(values=["Paste decklist first"])
            self.commander_option_menu.set("Paste decklist first")
            return

        try:
            parsed_cards = DeckParser.parse_decklist(raw_text)
            # Wyciągnięcie samych nazw kart
            card_names = sorted(list(parsed_cards.keys()))

            if card_names:
                current_selection = self.commander_option_menu.get()
                self.commander_option_menu.configure(values=card_names)

                # Zostawiamy poprzednio wybranego commandera, jeśli wciąż jest na liście
                if current_selection in card_names:
                    self.commander_option_menu.set(current_selection)
                else:
                    self.commander_option_menu.set(card_names[0])
            else:
                self.commander_option_menu.configure(values=["No valid cards found"])
                self.commander_option_menu.set("No valid cards found")
        except Exception:
            pass

    def save_deck(self):
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

            # Zapis do bazy danych wraz z formatem i commanderem
            if hasattr(DBManager, "save_deck"):
                # Próbujemy przekazać rozszerzone parametry
                try:
                    DBManager.save_deck(
                        deck_name=deck_name,
                        cards=parsed_cards,
                        game_format=game_format,
                        commander=commander
                    )
                except TypeError:
                    # Fallback gdyby metoda save_deck w DBManagerze nie przyjmowała jeszcze nowych parametrów
                    DBManager.save_deck(deck_name=deck_name, cards=parsed_cards)

            print(f"Deck '{deck_name}' [{game_format}] with Commander '{commander}' saved successfully!")

            if self.on_save_callback:
                self.on_save_callback()

            self.destroy()

        except Exception as e:
            print(f"Error saving deck: {e}")