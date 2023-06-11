import logging


class Interface():
    def __init__(self, game):
        self.__game = game
        pass

    @staticmethod
    def clear():
        print('\033c', end='')
        return

    def print_game(self):
        Interface.clear()
        print(self.__game.get_player_rank())

        return

    def print_order(self, setup: str, id: int):
        return


    def print_hand(self, hand):
        print('Mão: ', end='')

        cards = [c.value for c in hand.get_cards()]

        if not cards:
            print('vazia')
            return

        card_present = sorted(set(cards))

        for c in card_present[:len(card_present) - 1]:
            print(f'{cards.count(c)}x {c}, ', end='')

        last_c = card_present[len(card_present) - 1]
        print(f'{cards.count(last_c)}x {last_c}')

        return

    def ask_for_revolution(self) -> bool:
        return False

    pass

