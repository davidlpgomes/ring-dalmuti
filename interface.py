import logging

from game import Hand


class Interface():
    @staticmethod
    def clear():
        print('\033c', end='')
        return

    def print_order(setup: str, id: int):
        pass


    def print_hand(hand: Hand):
        pass


    def ask_for_revolution() -> bool:
        return False

    pass

