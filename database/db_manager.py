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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_name TEXT UNIQUE NOT NULL,
                cards_json TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def save_deck(deck_name: str, cards: dict) -> None:
        """Saves a new deck or updates an existing one."""
        DBManager._ensure_data_dir_exists()

        cards_json = json.dumps(cards)
        conn = sqlite3.connect(DBManager.DB_PATH)
        cursor = conn.cursor()

        # If name already exists -> replace
        cursor.execute("""
            INSERT OR REPLACE INTO decks (deck_name, cards_json)
            VALUES (?, ?)
        """, (deck_name, cards_json))

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

        # fetchall() zwraca krotki [('Gimli Deck',), ('Krenko Deck',)] -> zamieniamy na prostą listę
        return [row[0] for row in rows]

    @staticmethod
    def get_deck_cards(deck_name: str) -> dict:
        """Retrieves the card dictionary for a specific deck name."""
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

if __name__ == "__main__":
    # 1. Inicjalizacja bazy i folderu
    DBManager.init_db()

    # 2. Testowy słownik talii z Archidekta
    sample_cards = {
        "Sol Ring": 1,
        "Command Tower": 1,
        "Forest": 30
    }

    # 3. Zapis talii
    DBManager.save_deck("Krenko Test Deck", sample_cards)
    print("Zapisano talię!")

    # 4. Pobranie listy zapisanych talii
    saved_decks = DBManager.get_all_deck_names()
    print("Zapisane talie w bazie:", saved_decks)

    # 5. Odczyt konkretnej talii
    loaded_cards = DBManager.get_deck_cards("Krenko Test Deck")
    print("Zawartość wczytanej talii:", loaded_cards)