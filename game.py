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
        return f"{self.value}"


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

        for (i, card) in enumerate(cards):
            self.players[i].set_initial_card(card)

        self.players.sort(key=lambda p: p.initial_card.value)

        players= ""
        for player in self.players:
            players += f"{player.id}:{player.initial_card.value},"
        players[:-1]

        self.ring.send_message(Message(True, MessageType.SETUP, players))

    def deal(self):
        self.deck.shuffle()
        cards = self.deck.get_cards()
        for (i, card) in enumerate(cards):
            self.players[i%self.num_of_players].recv_card(card)

        data=""
        for player in self.players:
            data += f"{player.id}:{player.cards};"
        data[:-1]

        self.ring.send_message(Message(True, MessageType.DEAL, data))



        
class Player():
    def __init__(self, id: int):
        self.id = id
        self.cards: List[Card] = []
        self.is_dalmuti = False

    def recv_card(self, card: Card):
        self.cards.append(card)
    
    def set_initial_card(self, card: Card):
        self.initial_card = card

    def has_two_jesters(self):
        return self.cards.count(Card.JESTER)
    
    

        