from bisect import insort
from enum import Enum
from random import shuffle
from typing import List

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
        shuffle(self.__cards)
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
        self.__cards: List[Card] = []

    def get_cards(self) -> List[Card]:
        return self.__cards

    def add_card(self, card: int):
        card = Card(card)
        insort(self.__cards, card)

        return

    def add_cards(self, cards: List[int]):
        for card in cards:
            self.add_card(card)

        return
    
    def use_card_on_index(self, index: int):
        self.__cards.pop(index)
        return

    def use_card(self, card: int):
        cards = [c.value for c in self.__cards]
        i = -1

        try:
            i = cards.index(card) 
        except ValueError:
            # Card is not in hand
            return

        self.use_card_on_index(i)

        return

    def use_cards(self, cards: List[int]):
        for card in cards:
            self.use_card(card)

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

    def get_n_best_cards(self, n = 1) -> str:
        cards = [str(c.value) for c in self.__cards[:n]]
        return ','.join(cards) 


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
        self.__run_game()

        return

    def run_as_dealer(self):
        deal = Deal(self.__num_players)

        print('Setting SETUP')
        setup = deal.setup()
        self.__set_order(setup)
        self.__ring.send_message(Message(self.__id, MessageType.SETUP, setup))
        print(setup)

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

        if self.__had_revolution:
            self.__ring.give_token(self.__player_order[0])
        else:
            self.__ring.give_token(self.__player_order[-2])

        self.__run_game()

        return

    def __run_game(self):
        self.__ring.wait_token_settle()
        
        if not self.__had_revolution:
            self.__pay_taxes()

        print(f"{self.__player_order}")

        if self.__ring.has_token:
            print("I AM THE GREAT DALMUTI")

        return

    def __pay_taxes(self):
        """
            - Lesser Peon has the token (!!!) ✅
            - Lesser Peon sends their best one card
            - Lesser Peon gives the token to the Lesser Dalmuti
            - Lesser Dalmuti sends one card to the Lesser Peon
            - Lesser Dalmuti gives the token to the Greater Peon
            - Greater Peon sends their best two cards to the Greater Dalmuti
            - Greater Peon gives the token to the Greater Dalmuti
            - Greater Dalmuti sends two cards to the Greater Peon
            - Greater Dalmuti sends ROUND_READY
        """

        # Lesser Peon stuff
        if self.__ring.has_token:
            ld_id = self.__player_order[1]

            card = self.__hand.get_n_best_cards(1)
            self.__hand.use_card(card)
            print(f"giving {card}")
            card = f'{ld_id}:{card}'

            self.__ring.send_message(
                Message(self.__id, MessageType.GIVE_CARDS, card)
            )
            self.__ring.give_token(ld_id)

        message = self.__ring.recv_and_send_message()
        while message.type != MessageType.ROUND_READY.value:
            if message.type == MessageType.TOKEN.value:
                if int(message.move) != self.__id:
                    self.__ring.give_token()
                else:
                    if self.__player_order[0] == self.__id:
                        # GREATER DALMUTI STUFF
                        cards = '11,12' # TODO: Escolhe duas cartas

                        u_cards = [int(c) for c in cards.split(',')]
                        self.__hand.use_cards(u_cards)

                        print(f"giving {u_cards}")
                        
                        cards = f'{self.__player_order[-1]}:{cards}'
                        self.__ring.send_message(
                            Message(self.__id, MessageType.GIVE_CARDS, cards)
                        )

                        self.__ring.send_message(
                            Message(self.__id, MessageType.ROUND_READY, '')
                        )

                        break
                    elif self.__player_order[1] == self.__id:
                        # LESSER DALMUTI STUFF
                        card = '12' # TODO: Escolhe carta
                        self.__hand.use_card(int(card))

                        card = f'{self.__player_order[-2]}:{card}'
                        print(f"giving {card}")
                        self.__ring.send_message(
                            Message(self.__id, MessageType.GIVE_CARDS, card)
                        )

                        self.__ring.give_token(self.__player_order[-1])
                    elif self.__player_order[-1] == self.__id:
                        # GREATER PEON STUFF
                        cards = self.__hand.get_n_best_cards(2)
                        
                        u_cards = [int(c) for c in cards.split(',')]
                        self.__hand.use_cards(u_cards)

                        print(f"giving {u_cards}")
                        cards = f'{self.__player_order[0]}:{cards}'
                        self.__ring.send_message(
                            Message(self.__id, MessageType.GIVE_CARDS, cards)
                        )

                        self.__ring.give_token(self.__player_order[0])
            elif message.type == MessageType.GIVE_CARDS.value:
                id, cards = message.move.split(':')
                id = int(id)
                cards = [Card(int(c)) for c in cards.split(',')]

                if id == self.__id:
                    self.__hand.add_cards(cards)

            message = self.__ring.recv_and_send_message()

        return

    def __set_order(self, setup: str):
        self.__player_order: List[int] = []
        for player in setup.split(","):
            p, _ = player.split(":")
            self.__player_order.append(int(p))

        return

    def __check_revolution(self):
        if self.__hand.has_two_jesters():
            res = ""
            while res != "s" and res != "n":
                res = input("Você tem 2 Jesters! Portanto deseja fazer uma revolução?[s/n]")[0]

            if res == "s":
                if self.__id == self.__player_order[-1]:
                    self.__player_order.reverse()
                    self.__had_revolution = True
                    self.__ring.send_message(Message(self.__id, MessageType.GREAT_REVOLUTION, ""))
                else:
                    self.__had_revolution = True
                    self.__ring.send_message(Message(self.__id, MessageType.REVOLUTION, ""))

        return

        
        
