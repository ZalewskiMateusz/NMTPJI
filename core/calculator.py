from scipy.stats import hypergeom


class OddsCalculator:
    @staticmethod
    def calculate_chance(deck_size: int, copies_in_deck: int, hand_size: int) -> float:
        """
        deck_size: liczba pozostałych kart w talii (np. 99 - dociągnięte)
        copies_in_deck: ile sztuk szukanej karty zostało w talii (np. 1 lub 0)
        hand_size: ile kart dociągamy (Draw X)

        Returns: float (procent od 0.0 do 100.0)
        """
        if deck_size <= 0 or hand_size <= 0 or copies_in_deck <= 0:
            return 0.0

        # Zabezpieczenia matematyczne dla rozkładu hipergeometrycznego
        copies = min(copies_in_deck, deck_size)
        draw_amount = min(hand_size, deck_size)

        # Prawdopodobieństwo nie-trafienia ani jednej kopii (0 sukcesów)
        p_zero = hypergeom.pmf(0, deck_size, copies, draw_amount)

        # Szansa na dociągnięcie przynajmniej 1 kopii
        return round((1 - p_zero) * 100, 1)

    @staticmethod
    def calculate_group_chance(deck_size: int, selected_cards_copies: list[int], hand_size: int) -> float:
        """
        Prawdopodobieństwo dociągnięcia PRZYNAJMNIEJ JEDNEJ ze wskazanej grupy kart (outs).
        """
        total_copies = sum(selected_cards_copies)
        return OddsCalculator.calculate_chance(deck_size, total_copies, hand_size)

    @staticmethod
    def calculate_draw_chance(deck_size: int, outs_left: int, cards_to_draw: int) -> float:
        """
        Prawdopodobieństwo dociągnięcia szukanej karty przy dociągnięciu X kart.
        """
        return OddsCalculator.calculate_chance(deck_size, outs_left, cards_to_draw)