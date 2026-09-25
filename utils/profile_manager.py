import json
import os

PROFILE_FILE = os.path.join("saved_decks", "user_profile.json")
AVATARS_DIR = os.path.join("assets", "avatars")

DEFAULT_PROFILE = {
    "nickname": "Player",
    "avatar_filename": "jace.png"
}

class ProfileManager:
    @staticmethod
    def has_profile():
        """Zwraca True, jeśli plik profilu istnieje i zawiera niepusty nickname."""
        if not os.path.exists(PROFILE_FILE):
            return False
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("nickname") and data.get("nickname").strip())
        except Exception:
            return False

    @staticmethod
    def load_profile():
        if not os.path.exists(PROFILE_FILE):
            return DEFAULT_PROFILE.copy()
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Błąd odczytu profilu: {e}")
            return DEFAULT_PROFILE.copy()

    @staticmethod
    def save_profile(nickname, avatar_filename):
        os.makedirs("saved_decks", exist_ok=True)
        profile_data = {
            "nickname": nickname.strip() if nickname.strip() else "Player",
            "avatar_filename": avatar_filename
        }
        try:
            with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] Błąd zapisu profilu: {e}")
            return False

    @staticmethod
    def get_available_avatars():
        if not os.path.exists(AVATARS_DIR):
            return []
        return [f for f in os.listdir(AVATARS_DIR) if f.lower().endswith(".png")]