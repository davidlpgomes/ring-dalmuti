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

    def __lt__(self, other) -> bool:
        return self.value < other.value


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


class Deal():
    def __init__(self, num_players: int):
        self.num_players = num_players

        self.players: List[Player] = []
        for p in range(num_players):
            self.players.append(Player(p+1))

        self.deck = Deck()
        return

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

    def add_card(self, card: Card):
        self.cards.append(card)
        return
    
    def set_initial_card(self, card: Card):
        self.initial_card = card
        return


class Hand():
    def __init__(self):
        self.__cards = []

    def get_cards(self) -> str:
        return self.__cards
    
    def use_cards(self, start: int, end: int):
        self.__cards = self.__cards[:start] + self.__cards[end+1:]
        return

    def has_two_jesters(self):
        return self.__cards.count(Card.JESTER) == 2
    
    def parse_deal(self, card_string: str, machine_id: int):
        for item in card_string.split(";"):
            id, cards_str = item.split(":")
            if machine_id == int(id):
                self.__cards = [Card(int(value)) for value in cards_str.strip("[]").split(",")]
                self.__cards.sort()
                return
            
        return


class Game:
    def __init__(self, ring: Ring, num_players: int, id: int):
        self.__num_players = num_players
        self.__id = id
        self.__ring = ring
        self.__hand = Hand()
        self.__had_revolution = False

    def run(self):
        if self.__id == 1:
            self.run_as_dealer()
            return

        self.run_as_player()
        return

    def run_as_player(self):
        print('Recebendo SETUP')
        setup_message = self.__ring.recv_and_send_message()
        self.__set_order(setup_message.move)

        print('Recebendo DEAL')
        deal_message = self.__ring.recv_and_send_message()
        self.__hand.parse_deal(deal_message.move, self.__id)

        print('Etapa REVOLUCAO')
        message = self.__ring.recv_and_send_message()
        while message.type != MessageType.ROUND_READY.value:
            if message.type != MessageType.TOKEN.value:
                print('Received REVOLUTION')
                if message.type == MessageType.GREAT_REVOLUTION.value:
                    self.__player_order.reverse()
                self.__had_revolution = True
            else:
                print('Received TOKEN')
                self.__check_revolution()
                self.__ring.give_token()
                print('Giving TOKEN')

            message = self.__ring.recv_and_send_message()

        print('Received ROUND_READY')

        return

    def run_as_dealer(self):
        deal = Deal(self.__num_players)

        print('Setting SETUP')
        setup = deal.setup()
        self.__set_order(setup)
        self.__ring.send_message(Message(self.__id, MessageType.SETUP, setup))

        print('Setting DEAL')
        dealed_cards = deal.deal()
        self.__hand.parse_deal(dealed_cards, self.__id)
        self.__ring.send_message(Message(self.__id, MessageType.DEAL, dealed_cards))

        self.__check_revolution()
        
        if not self.__had_revolution:
            print('Giving token')
            self.__ring.give_token()
            message = self.__ring.recv_and_send_message()
            if message.type != MessageType.TOKEN.value:
                print('Received REVOLUTION')
                if message.type == MessageType.GREAT_REVOLUTION.value:
                    self.__player_order.reverse()
                self.__had_revolution = True
            else:
                print('Received TOKEN')

        print('Sending ROUND_READY')
        self.__ring.send_message(Message(self.__id, MessageType.ROUND_READY, ''))
        print('Round ready!') 

        return

    def __set_order(self, setup: str):
        self.__player_order: List[int] = []
        for player in setup.split(","):
            (p,_) = player.split(":")
            self.__player_order.append(p)

        return

    def __check_revolution(self):
        if self.__hand.has_two_jesters():
            res = ""
            while res != "s" and res != "n":
                res = input("Você tem 2 Jesters! Portanto deseja fazer uma revolução?[s/n]")[0]

            if res == "s":
                if self.__id == self.__player_order[-1]:
                    self.__player_order.reverse()
                    self.__ring.send_message(Message(self.__id, MessageType.GREAT_REVOLUTION, ""))
                else:
                    self.__ring.send_message(Message(self.__id, MessageType.REVOLUTION, ""))

        return

        
        
