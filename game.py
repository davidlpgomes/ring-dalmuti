from enum import Enum
from typing import List
import random

from ring import Ring, Message, MessageType

class Card(Enum):
    DALMUTI = 1
    ARCHBISHOP = 2
    EARL_MARSHAL = 3
    BARONESS = 4
    ABBESS = 5
    KNIGHT = 6
    SEAMSTRESS = 7
    MASON = 8
    COOK = 9
    SHEPHERDESS = 10
    STONECUTTER = 11
    PEASANT = 12
    JESTER = 13

    def __repr__(self) -> str:
        return f"{self.name} {self.value}"

class Deck():
    def __init__(self):
        self.__cards = []
        for card_type in Card:
            if card_type != Card.JESTER:
                self.__cards += card_type.value * [card_type]
            else:
                self.__cards += 2 * [card_type]

        self.shuffle(self)
        pass

    def shuffle(self):
        random.shuffle(self.__cards)
        return
    
    def get_n_cards(self, n: int) -> List[Card]:
        return self.__cards[0:n]
    
    def get_cards(self):
        return self.__cards

    pass

class Game():
    def __init__(self, num_of_players: int, ring: Ring):
        self.num_of_players = num_of_players
        self.players: List[Player] = []

        for p in range(num_of_players):
            self.players.append(Player(p+1))

        self.ring = ring
        self.deck = Deck()

    
    def setup(self):
        cards = self.deck.get_n_cards(self.num_of_players)

        best_index = cards.index(max(cards, key=lambda c: c.value))

        move=""
        for (i, card) in enumerate(cards):
            move += f"player{i+1}: {card}"
            if i == best_index:
                move += " *Great Dalmuti*"
                self.players[i].is_dalmuti = True
            move += "\n"

        self.ring.send_message(Message(True, MessageType.SETUP, move))
        #PASSAR O BASTÃO PARA O DALMUTI

        self.deck.shuffle()

    def deal(self):
        cards = self.deck.get_cards()
        for (i, card) in enumerate(cards):
            self.players[i%self.num_of_players].recv_card(card)

        #PASSAR AS CARTAS PROS JOGADORES

        



class Player():
    def __init__(self, id: int):
        self.id = id
        self.cards: List[Card] = []
        self.is_dalmuti = False

    def recv_card(self, card: Card):
        self.cards.append(card)

        