import logging

class Interface():
    def __init__(self, id: int):
        self.__id = id
        self.__rank = ''
        self.__order = ''
        self.__table = ''
        self.__finish_order = ''
        self.__hand = ''
        pass

    @staticmethod
    def clear():
        print('\033c', end='')
        return

    def print_game(self):
        Interface.clear()
        self.__print_id()
        self.__print_rank()
        self.__print_order()
        self.__print_finish()
        self.__print_table()
        self.__print_hand()
        return
    
    def set_rank(self, rank: str):
        self.__rank = rank

    def set_order(self, order: str):
        self.__order = order

    def set_table(self, table: str):
        self.__table = table

    def set_finish(self, finish: str):
        self.__finish_order = finish

    def set_hand(self, hand: str):
        self.__hand = hand
    
    def __print_id(self):
        print(f'ID: {self.__id}')

    def __print_rank(self):
        print(f'Rank: {self.__rank}')

    def __print_order(self):
        print(f'Ordem: {self.__order}')

    def __print_table(self):
        print(f'Mesa: {self.__table}')

    def __print_finish(self):
        print(f'Terminaram: {self.__finish_order}')

    def __print_hand(self):
        print(f'Mão: {self.__hand}')

    def ask_for_revolution(self) -> bool:
        return False

    pass

