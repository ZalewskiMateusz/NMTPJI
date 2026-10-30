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

        # 1. Tabela talii (Decks)
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

        # 2. Tabela meczów (Matches)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                turns_count INTEGER NOT NULL,
                winner_name TEXT NOT NULL,
                winner_commander TEXT DEFAULT ''
            )
        """)

        # 3. Tabela graczy w meczu (Match Players)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                commander_name TEXT NOT NULL,
                partner_commander TEXT DEFAULT '',
                is_winner INTEGER DEFAULT 0,
                final_life INTEGER DEFAULT 0,
                FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

    # ==========================================
    # LOGIKA TALII (DECKS)
    # ==========================================

    @staticmethod
    def save_deck(deck_name: str, cards: dict, game_format: str = "Commander / EDH", commander: str = "") -> None:
        """Saves a new deck or updates an existing one."""
        DBManager.init_db()

        cards_json = json.dumps(cards)
        conn = sqlite3.connect(DBManager.DB_PATH)
        cursor = conn.cursor()

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

        cursor.execute("SELECT deck_name, cards_json, game_format, commander FROM decks WHERE deck_name = ?",
                       (deck_name,))
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

    # ==========================================
    # LOGIKA MECZÓW I STATYSTYK (MATCHES & STATS)
    # ==========================================

    @staticmethod
    def save_match_result(engine_state, winner_name: str) -> int:
        """Saves a finished match and its participants to the database."""
        DBManager.init_db()

        turns_cnt = getattr(engine_state, "turn_number", 1)

        # Znajdź dowódcę zwycięzcy
        winner_commander = ""
        if hasattr(engine_state, "players"):
            for p in engine_state.players.values():
                if p.name == winner_name:
                    winner_commander = getattr(p, "commander", "") or ""
                    break

        conn = sqlite3.connect(DBManager.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO matches (turns_count, winner_name, winner_commander)
            VALUES (?, ?, ?)
        """, (turns_cnt, winner_name, winner_commander))

        match_id = cursor.lastrowid

        # Zapisz uczestników
        if hasattr(engine_state, "players"):
            for p in engine_state.players.values():
                is_win = 1 if p.name == winner_name else 0
                cmd_name = getattr(p, "commander", "") or "Unknown Commander"
                partner_cmd = getattr(p, "partner_commander", "") or ""
                final_hp = getattr(p, "life", 0)

                cursor.execute("""
                    INSERT INTO match_players (match_id, player_name, commander_name, partner_commander, is_winner, final_life)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (match_id, p.name, cmd_name, partner_cmd, is_win, final_hp))

        conn.commit()
        conn.close()
        return match_id

    @staticmethod
    def get_commander_stats() -> list[dict]:
        """Returns overall Win Rate aggregated by Commander."""
        if not os.path.exists(DBManager.DB_PATH):
            return []

        conn = sqlite3.connect(DBManager.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT 
                commander_name,
                COUNT(*) as total_games,
                SUM(is_winner) as wins,
                COUNT(*) - SUM(is_winner) as losses,
                ROUND(CAST(SUM(is_winner) AS FLOAT) / COUNT(*) * 100, 1) as winrate
            FROM match_players
            WHERE commander_name != '' AND commander_name != 'Unknown Commander'
            GROUP BY commander_name
            ORDER BY total_games DESC, winrate DESC
        """
        rows = cursor.execute(query).fetchall()
        conn.close()

        return [dict(row) for row in rows]

    @staticmethod
    def get_matchup_stats(selected_commander: str) -> list[dict]:
        """Returns Win Rate vs opposing Commanders for a selected Commander."""
        if not os.path.exists(DBManager.DB_PATH):
            return []

        conn = sqlite3.connect(DBManager.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT 
                mp2.commander_name AS opponent_commander,
                COUNT(DISTINCT mp1.match_id) AS total_matches,
                SUM(mp1.is_winner) AS wins,
                COUNT(DISTINCT mp1.match_id) - SUM(mp1.is_winner) AS losses,
                ROUND(CAST(SUM(mp1.is_winner) AS FLOAT) / COUNT(DISTINCT mp1.match_id) * 100, 1) AS winrate
            FROM match_players mp1
            JOIN match_players mp2 ON mp1.match_id = mp2.match_id AND mp1.commander_name != mp2.commander_name
            WHERE mp1.commander_name = ? AND mp2.commander_name != ''
            GROUP BY mp2.commander_name
            ORDER BY total_matches DESC, winrate DESC
        """
        rows = cursor.execute(query, (selected_commander,)).fetchall()
        conn.close()

        return [dict(row) for row in rows]

    @staticmethod
    def delete_deck(deck_name: str) -> None:
        """Deletes a deck from the database by its name."""
        if not os.path.exists(DBManager.DB_PATH):
            return

        conn = sqlite3.connect(DBManager.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM decks WHERE deck_name = ?", (deck_name,))

        conn.commit()
        conn.close()


if __name__ == "__main__":
    DBManager.init_db()
    print("Baza danych zainicjalizowana pomyślnie ze wszystkimi tabelami!")