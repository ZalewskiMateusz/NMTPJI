import os
import requests

CACHE_DIR = "cache/card_images"

class ScryfallAPI:
    BASE_URL = "https://api.scryfall.com/cards/named"

    @staticmethod
    def get_card_image_path(card_name: str) -> str | None:
        """
        Pobiera obrazek karty ze Scryfall i zapisuje go w cache.
        Zwraca lokalną ścieżkę do pliku JPG lub None w przypadku błędu.
        """
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR, exist_ok=True)

        safe_name = "".join(c for c in card_name if c.isalnum() or c in (' ', '_')).rstrip()
        file_path = os.path.join(CACHE_DIR, f"{safe_name}.jpg")

        # Jeśli plik już jest w cache, zwracamy go od razu
        if os.path.exists(file_path):
            return file_path

        headers = {
            "User-Agent": "MTGTrackerApp/1.0",
            "Accept": "application/json"
        }
        # Używamy fuzzy dla lepszego dopasowywania nazw
        params = {"fuzzy": card_name}

        try:
            response = requests.get(ScryfallAPI.BASE_URL, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                img_url = None

                if "image_uris" in data:
                    img_url = data["image_uris"].get("normal")
                elif "card_faces" in data and "image_uris" in data["card_faces"][0]:
                    img_url = data["card_faces"][0]["image_uris"].get("normal")

                if img_url:
                    img_resp = requests.get(img_url, headers=headers, timeout=10)
                    if img_resp.status_code == 200:
                        with open(file_path, "wb") as f:
                            f.write(img_resp.content)
                        return file_path
            return None
        except Exception as e:
            print(f"Error fetching card '{card_name}' from Scryfall: {e}")
            return None