from enum import Enum
from typing import List
import random


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

        self.shuffle()
        pass

    def shuffle(self):
        random.shuffle(self.__cards)
        return
    
    def get_n_cards(self, n: int) -> List[Card]:
        return self.__cards[0:n]
    
    def get_cards(self):
        return self.__cards

    pass


class Deal():
    def __init__(self, num_players: int):
        self.num_players = num_players

        self.players: List[Player] = []
        for p in range(num_players):
            self.players.append(Player(p+1))

        self.deck = Deck()

    def setup(self) -> str:
        cards = self.deck.get_n_cards(self.num_players)

        for (i, card) in enumerate(cards):
            self.players[i].set_initial_card(card)

        self.players.sort(key=lambda p: p.initial_card.value)

        players= ""
        for player in self.players:
            players += f"{player.id}:{player.initial_card.value},"

        return players[:-1]

    def deal(self) -> str:
        self.deck.shuffle()
        cards = self.deck.get_cards()
        for (i, card) in enumerate(cards):
            self.players[i%self.num_players].add_card(card)

        data=""
        for player in self.players:
            data += f"{player.id}:{player.cards};"

        return data[:-1]

        
class Player():
    def __init__(self, id: int):
        self.id = id
        self.cards: List[Card] = []
        self.is_dalmuti = False

    def add_card(self, card: Card):
        self.cards.append(card)
    
    def set_initial_card(self, card: Card):
        self.initial_card = card


class Hand():
    def __init__(self, cards: List[Card]):
        self.__cards = cards

    def get_cards(self) -> str:
        return self.__cards
    
    def use_cards(self, start: int, end: int):
        self.__cards = self.__cards[:start] + self.__cards[end+1:]

    def has_two_jesters(self):
        return self.__cards.count(Card.JESTER) == 2
    
    @staticmethod
    def parse_hand(card_string: str, machine_id: int) -> List[Card]:
        for item in card_string.split(";"):
            id, cards_str = item.split(":")
            if machine_id == int(id):
                return [Card(int(value)) for value in cards_str.strip("[]").split(",")]


    
class Game:
    pass