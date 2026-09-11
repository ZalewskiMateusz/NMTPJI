from scipy.stats import hypergeom


class OddsCalculator:
    @staticmethod
    def calculate_chance(deck_size: int, copies_in_deck: int, hand_size: int) -> float:
        """
        deck_size: number of cards remaining in the deck + in hand
        copies_in_deck: how many copies of a given card remain in the deck/hand
        hand_size: how many cards the opponent currently has in hand

        Returns: float (percentage chance from 0.0 to 100.0)
        """
        if deck_size <= 0 or hand_size <= 0 or copies_in_deck <= 0:
            return 0.0

            # Safeguard: the number of available items cannot exceed the entire deck.
        copies = min(copies_in_deck, deck_size)

        # Probability of zero units on hand
        p_zero = hypergeom.pmf(0, deck_size, copies, hand_size)

        # Chance of at least 1 card
        return round((1 - p_zero) * 100, 2)

    @staticmethod
    def calculate_group_chance(deck_size: int, selected_cards_copies: list[int], hand_size: int) -> float:
        """
        Calculates the probability of holding AT LEAST ONE of the selected cards.

        selected_cards_copies: a list containing the number of remaining copies of each selected card,
                               e.g., [1, 1, 1] for three single cards in Commander.
        """
        total_copies = sum(selected_cards_copies)
        return OddsCalculator.calculate_chance(deck_size, total_copies, hand_size)

    @staticmethod
    def calculate_draw_chance(deck_size: int, outs_left: int, cards_to_draw: int) -> float:
        """
        Chance of drawing the needed card when drawing X cards
        """
        if deck_size <= 0 or cards_to_draw <= 0 or outs_left <= 0:
            return 0.0

        p_zero = hypergeom.pmf(0, deck_size, outs_left, cards_to_draw)
        return round((1 - p_zero) * 100, 2)