import requests

class ScryfallAPI:
    BASE_URL = "https://api.scryfall.com/cards/named"

    @staticmethod
    def get_card_image_url(card_name: str) -> str | None:
        """
        Sends a GET request to Scryfall API and returns the image URL for the card.
        """
        # 1. Przygotuj parametry zapytania (słownik z kluczem 'exact')
        params = {"exact": card_name}

        headers = {
            "User-Agent": "NMTPJI/1.0",
            "Accept": "application/json"
        }

        try:
            response = requests.get(ScryfallAPI.BASE_URL, params=params, headers=headers)


            if response.status_code == 200:
                data = response.json()

                # Get Image
                if "image_uris" in data:
                    return data["image_uris"]["normal"]
                elif "card_faces" in data:
                    return data["card_faces"][0]["image_uris"]["normal"]

            return None

        except Exception as e:
            print(f"Error fetching card from Scryfall: {e}")
            return None


# --- TEST W KONSOLI ---
if __name__ == "__main__":
    url = ScryfallAPI.get_card_image_url("Sol Ring")
    print("Link do Sol Ring:", url)
    url2 = ScryfallAPI.get_card_image_url("Counterspell")
    print("Link do Counterspell:", url2)