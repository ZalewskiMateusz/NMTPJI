# database/db_manager.py
import os
import sqlite3
import json


class DBManager:
    # Ścieżka do folderu z danymi i pliku bazy
    DATA_DIR = "saved_decks"
    DB_PATH = os.path.join(DATA_DIR, "nmtpji.db")

    @staticmethod
    def _ensure_data_dir_exists():
        """Creates the saved_decks directory if it doesn't exist."""
        if not os.path.exists(DBManager.DATA_DIR):
            os.makedirs(DBManager.DATA_DIR)

    @staticmethod
    def init_db():
        """Creates the database file inside saved_decks and sets up tables."""
        DBManager._ensure_data_dir_exists()

        conn = sqlite3.connect(DBManager.DB_PATH)
        cursor = conn.cursor()

        # Tworzenie bazowej tabeli jeśli nie istnieje
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_name TEXT UNIQUE NOT NULL,
                cards_json TEXT NOT NULL,
                game_format TEXT DEFAULT 'Commander / EDH',
                commander TEXT DEFAULT ''
            )
        """)

        # Migracja bazy – dodanie kolumn game_format i commander dla istniejącej bazy
        cursor.execute("PRAGMA table_info(decks)")
        columns = [row[1] for row in cursor.fetchall()]

        if "game_format" not in columns:
            cursor.execute("ALTER TABLE decks ADD COLUMN game_format TEXT DEFAULT 'Commander / EDH'")
        if "commander" not in columns:
            cursor.execute("ALTER TABLE decks ADD COLUMN commander TEXT DEFAULT ''")

        conn.commit()
        conn.close()

    @staticmethod
    def save_deck(deck_name: str, cards: dict, game_format: str = "Commander / EDH", commander: str = "") -> None:
        """Saves a new deck or updates an existing one."""
        DBManager.init_db()  # Upewnia się, że struktura jest aktualna

        cards_json = json.dumps(cards)
        conn = sqlite3.connect(DBManager.DB_PATH)
        cursor = conn.cursor()

        # Zapis lub nadpisanie (UPSERT)
        cursor.execute("""
            INSERT INTO decks (deck_name, cards_json, game_format, commander)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(deck_name) DO UPDATE SET
                cards_json = excluded.cards_json,
                game_format = excluded.game_format,
                commander = excluded.commander
        """, (deck_name, cards_json, game_format, commander))

        conn.commit()
        conn.close()

    @staticmethod
    def get_all_deck_names() -> list[str]:
        """Returns a list of all saved deck names for the GUI selection menu."""
        if not os.path.exists(DBManager.DB_PATH):
            return []

        conn = sqlite3.connect(DBManager.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT deck_name FROM decks")
        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]

    @staticmethod
    def get_deck_cards(deck_name: str) -> dict:
        """Retrieves the card dictionary {card_name: qty} for a specific deck name."""
        if not os.path.exists(DBManager.DB_PATH):
            return {}

        conn = sqlite3.connect(DBManager.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT cards_json FROM decks WHERE deck_name = ?", (deck_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return {}

    @staticmethod
    def get_cards_for_deck(deck_name: str) -> list[str]:
        """Returns a sorted list of card names for GUI drop-down menus."""
        cards_dict = DBManager.get_deck_cards(deck_name)
        return sorted(list(cards_dict.keys()))

    @staticmethod
    def get_deck_by_name(deck_name: str) -> dict:
        """Retrieves complete deck data including cards, format, and commander."""
        if not os.path.exists(DBManager.DB_PATH):
            return {}

        conn = sqlite3.connect(DBManager.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT deck_name, cards_json, game_format, commander FROM decks WHERE deck_name = ?", (deck_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "name": row[0],
                "cards": json.loads(row[1]),
                "format": row[2] or "Commander / EDH",
                "commander": row[3] or ""
            }
        return {}


if __name__ == "__main__":
    # 1. Inicjalizacja bazy
    DBManager.init_db()

    # 2. Testowy słownik talii
    sample_cards = {
        "Krenko, Mob Boss": 1,
        "Sol Ring": 1,
        "Mountain": 38
    }

    # 3. Zapis talii z formatem i dowódcą
    DBManager.save_deck("Krenko Test Deck", sample_cards, "Commander / EDH", "Krenko, Mob Boss")
    print("Zapisano talię!")

    # 4. Odczyt pełnych danych talii
    deck_info = DBManager.get_deck_by_name("Krenko Test Deck")
    print("Wczytana talia z bazy:", deck_info)