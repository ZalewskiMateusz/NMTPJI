import re


class DeckParser:
    @staticmethod
    def parse_decklist(raw_text: str) -> dict[str, int]:
        """
        Parses raw text decklists from Archidekt, Moxfield, or standard .txt files
        and returns a dictionary: {card_name: quantity}.
        Ignores Sideboard, Maybeboard, and text inside brackets/parentheses.
        """
        deck = {}

        for line in raw_text.splitlines():
            line = line.strip()

            # Skip empty lines or comment lines
            if not line or line.startswith("//") or line.startswith("#"):
                continue

            # Skip cards tagged as Sideboard or Maybeboard
            if "Sideboard" in line or "Maybeboard" in line:
                continue

            # 1. Clean up brackets () and []
            # Removes everything inside square brackets [tags] and parentheses (set codes)
            clean_line = re.sub(r'\[.*?\]', '', line)
            clean_line = re.sub(r'\(.*?\)', '', clean_line)

            # Strip remaining whitespace or trailing foil markers like "*F*"
            clean_line = clean_line.strip()

            # 2. Extract quantity and card name
            # Matches leading digits (e.g., "1", "1x", "24") and the rest as card name
            match = re.match(r'^(\d+)[xX]?\s+(.+)$', clean_line)

            if match:
                quantity = int(match.group(1))
                # Remove trailing collector numbers if present (e.g., "Forest 198" -> "Forest")
                card_name = match.group(2).strip()
                card_name = re.sub(r'\s+\d+$', '', card_name)

                # Add quantity to dictionary, handling duplicates safely
                deck[card_name] = deck.get(card_name, 0) + quantity

        return deck


# --- QUICK LOCAL TEST ---
if __name__ == "__main__":
    test_data = """
    1x Aftermath Analyst (eoc)
    1x Ancient Greenwarden (j25) [Land from Graveyard]
    1x Bane of Progress (ecc) [Maybeboard{noDeck}{noPrice}]
    8x Forest (spm) 198
    1x Lord Windgrace (c18) *F* [Land from Graveyard]
    """

    parsed = DeckParser.parse_decklist(test_data)
    print("Parsed Result:")
    for card, qty in parsed.items():
        print(f"  {qty}x {card}")