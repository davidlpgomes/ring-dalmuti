import logging

from bisect import insort
from enum import Enum
from random import shuffle
from typing import List

from interface import Interface
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
        return f'{self.value}'

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

        players= ''
        for player in self.players:
            players += f'{player.id}:{player.initial_card.value},'

        return players[:-1]

    def deal(self) -> str:
        self.deck.shuffle()
        cards = self.deck.get_cards()
        for (i, card) in enumerate(cards):
            self.players[i%self.num_players].add_card(card)

        data=''
        for player in self.players:
            data += f'{player.id}:{player.cards};'

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
    
    def get_cards_by_copy(self) -> List[Card]:
        return self.__cards.copy()

    def add_card(self, card: int):
        card = Card(card)
        insort(self.__cards, card)

        return

    def add_cards(self, cards: List[int]):
        for card in cards:
            self.add_card(card)

        return
    
    def get_num_cards(self) -> int:
        return len(self.__cards)
    
    def use_card_on_index(self, index: int) -> Card:
        return self.__cards.pop(index)

    def use_card(self, card: int):
        cards = [c.value for c in self.__cards]
        i = -1

        try:
            i = cards.index(card) 
        except ValueError:
            return

        self.use_card_on_index(i)

        return

    def use_cards(self, cards: List[Card]):
        for card in cards:
            self.use_card(card.value)

        return

    def has_two_jesters(self):
        return self.__cards.count(Card.JESTER) >= 2
    
    def parse_deal(self, card_string: str, machine_id: int):
        for item in card_string.split(';'):
            id, cards_str = item.split(':')
            if machine_id == int(id):
                self.__cards = [Card(int(value)) for value in cards_str.strip('[]').split(',')]
                self.__cards.sort()
                return
            
        return
    
    def is_empty(self):
        return len(self.__cards) == 0
    
    def parse_given_cards(self, card_str: str):
        id, cards = card_str.split(':')
        id = int(id)

        cards = [Card(int(c)) for c in cards.strip('[]').split(',')]
        return id, cards

    def get_n_best_cards(self, n = 1) -> Card:
        return self.__cards[:n]


class Game:
    def __init__(self, ring: Ring, num_players: int):
        self.__num_players = num_players
        self.__ring = ring
        self.__hand = Hand()
        self.__had_revolution = False
        self.__table_cards: List[Card] = []
        self.__table_owner: int = 0
        self.__finish_order: List[int] = [] 
        self.__interface = Interface(self.__ring.machine_id)
        self.__current_player_index: int = 0

    def get_player_rank(self):
        rank = self.__player_order.index(self.__ring.machine_id)

        if rank == 0:
            return 'Greater Dalmuti'
        elif rank == 1:
            return 'Lesser Dalmuti'
        elif rank == self.__num_players - 1:
            return 'Greater Peon'
        elif rank == self.__num_players - 2:
            return 'Lesser Peon'

        return f'Merchant {rank - 1}'

    def run(self):
        if self.__ring.machine_id == 1:
            self.run_as_dealer()
            return

        self.run_as_player()
        return

    def run_as_player(self):
        logging.debug('Receiving SETUP')
        setup_message = self.__ring.recv_and_send_message()
        self.__parse_order(setup_message.move)

        self.__interface.set_order(self.get_player_order())
        self.__interface.set_rank(self.get_player_rank())

        logging.debug('Receiving DEAL')
        deal_message = self.__ring.recv_and_send_message()
        self.__hand.parse_deal(deal_message.move, self.__ring.machine_id)

        self.__interface.set_hand(self.__hand.get_cards())

        self.__interface.print_game()

        logging.debug('REVOLUTION step')
        message = self.__ring.recv_and_send_message()

        while message.type != MessageType.ROUND_READY.value:
            if message.type != MessageType.TOKEN.value:
                logging.debug('Received REVOLUTION')

                if message.type == MessageType.GREAT_REVOLUTION.value:
                    self.__player_order.reverse()

                    self.__interface.set_order(self.get_player_order())
                    self.__interface.set_rank(self.get_player_rank())
                    self.__interface.print_game()
                    print("GRANDE REVOLUÇÃO. A ordem foi invertida")

                self.__had_revolution = True
            else:
                logging.debug('Received TOKEN')
                self.__check_revolution()

                self.__ring.give_token()
                logging.debug('Giving TOKEN')

            message = self.__ring.recv_and_send_message()

        logging.debug('Received ROUND_READY')
        self.__run_game()

        return

    def run_as_dealer(self):
        deal = Deal(self.__num_players)

        logging.debug('Setting SETUP')
        setup = deal.setup()

        self.__parse_order(setup)
        self.__interface.set_order(self.get_player_order())
        self.__interface.set_rank(self.get_player_rank())

        self.__ring.send_message(MessageType.SETUP, setup)

        logging.debug('Setting DEAL')
        dealed_cards = deal.deal()

        self.__hand.parse_deal(dealed_cards, self.__ring.machine_id)

        self.__interface.set_hand(self.__hand.get_cards())
        self.__interface.print_game()

        self.__ring.send_message(MessageType.DEAL, dealed_cards)


        self.__check_revolution()
        
        if not self.__had_revolution:
            self.__ring.give_token()
            message = self.__ring.recv_and_send_message()

            if message.type != MessageType.TOKEN.value:
                logging.debug('Received REVOLUTION')

                if message.type == MessageType.GREAT_REVOLUTION.value:
                    self.__player_order.reverse()
                    self.__interface.set_order(self.get_player_order())
                    self.__interface.print_game()

                self.__had_revolution = True
            else:
                logging.debug('Received TOKEN')

        logging.debug('Sending ROUND_READY')
        self.__ring.send_message(MessageType.ROUND_READY)

        self.__ring.give_token(self.__player_order[0])

        self.__run_game()

        return

    def __run_game(self):
        if not self.__ring.has_token:
            self.__ring.wait_token_settle()

        if not self.__had_revolution:
            self.__pay_taxes()
            self.__interface.set_hand(self.__hand.get_cards())
            self.__interface.print_game()

        self.__play_game()

        return
    
    def __play_game(self):
        while len(self.__finish_order) != self.__num_players:
            self.__interface.print_game()
            
            if not self.__ring.has_token:
                message = self.__ring.recv_and_send_message()
            else:
                message = Message(self.__ring.machine_id, MessageType.MOCK_MESSAGE, '')

            while message.type != MessageType.ROUND_FINISHED.value:
                if message.type == MessageType.PLAY_CARDS.value:
                    self.__current_player_index = (self.__current_player_index + 1) % self.__num_players
                    self.__interface.set_order(self.get_player_order())
                    self.__interface.print_game()
                    table_owner, cards = message.move.split(":")

                    self.__table_owner = int(table_owner)
                    self.__table_cards = [Card(int(c)) for c in cards.strip('[]').split(',')]

                    self.__interface.set_table(self.__table_cards)
                    self.__interface.print_game()

                if message.type == MessageType.PASS.value:
                    self.__current_player_index = (self.__current_player_index + 1) % self.__num_players
                    self.__interface.set_order(self.get_player_order())
                    self.__interface.print_game()

                if message.type == MessageType.HAND_EMPTY.value:
                    self.__finish_order.append(message.origin)

                    self.__interface.set_finish(self.__finish_order)
                    self.__interface.print_game()

                if self.__ring.has_token:
                    if self.__table_owner == self.__ring.machine_id:
                        self.__ring.send_message(MessageType.ROUND_FINISHED)
                        break
                    else:
                        if not self.__hand.is_empty():
                            if len(self.__table_cards) == 0:
                                played_cards = self.__get_valid_first_play()
                            else:
                                played_cards = self.__get_valid_other_play()

                            if len(played_cards) == 0:
                                
                                self.__ring.send_message(MessageType.PASS)
                            else:
                                self.__play_cards(played_cards)
                        else:
                            self.__ring.send_message(MessageType.PASS)

                        self.__current_player_index = (self.__current_player_index + 1) % self.__num_players
                        self.__interface.set_order(self.get_player_order())
                        self.__interface.print_game()
                        self.__pass_to_next_player()

                message = self.__ring.recv_and_send_message()

            self.__table_cards = []
            self.__interface.set_table(self.__table_cards)
            self.__interface.print_game()
            self.__table_owner = 0

    def __get_valid_first_play(self) -> List[Card]:
        valid = False

        while not valid:
            cur_cards = self.__hand.get_cards_by_copy()
            self.__interface.print_game()
            played_cards = input('Insira as cartas que quer jogar:\n')
            played_cards = played_cards.split(' ')
            played_cards = list(filter(lambda x: x.isdigit(), played_cards))
            played_cards = list(filter(lambda x: int(x) <= 13 and int(x) >= 1, played_cards))

            if len(played_cards) == 0:
                continue

            played_cards = [Card(int(c)) for c in played_cards]

            unique_p_cards = list(set(played_cards))

            try:
                unique_p_cards.remove(Card.JESTER)
            except ValueError:
                pass

            if len(unique_p_cards) > 1:
                print('Você deve jogar apenas cartas do mesmo tipo ou coringas...')
                continue
                

            for card in played_cards:
                try:
                    cur_cards.remove(card)
                    valid = True
                except ValueError:
                    print('Você não tem alguma das cartas que jogou...')
                    valid = False
                    break
           
            if not valid:
                continue

            break


        return played_cards
    
    def __get_valid_other_play(self) -> List[Card]:
        while True:
            cur_cards = self.__hand.get_cards_by_copy()
            self.__interface.print_game()
            played_cards = input('Insira as cartas que quer jogar (0 para passar a vez):\n')
            played_cards = played_cards.split(' ')
            if played_cards[0] == '0':
                return []
            
            played_cards = list(filter(lambda x: x.isdigit(), played_cards))
            played_cards = list(filter(lambda x: int(x) <= 13 and int(x) >= 1, played_cards))

            if len(played_cards) == 0:
                continue

            played_cards = [Card(int(c)) for c in played_cards]

            unique_p_cards = list(set(played_cards))

            try:
                unique_p_cards.remove(Card.JESTER)
            except ValueError:
                pass

            if len(unique_p_cards) > 1:
                print('Você deve jogar apenas cartas do mesmo tipo ou coringas...')
                continue

            try:
                unique_p_cards.remove(Card.JESTER)
            except ValueError:
                pass

            unique_t_cards = list(set(self.__table_cards))

            if unique_p_cards[0].value >= unique_t_cards[0].value:
                print("Você precisa jogar cartas de valor menor que as que estão na mesa (ou passar)")
                continue

            if len(self.__table_cards) != len(played_cards):
                print("Você precisa jogar a mesma quantidade de cartas que estão na mesa")
                continue

            
            for card in played_cards:
                try:
                    cur_cards.remove(card)
                except ValueError:
                    print('Você não tem alguma das cartas que quer jogar...')
                    continue

            return played_cards
        
    def __play_cards(self, cards: List[Card]):
        self.__hand.use_cards(cards)
        self.__interface.set_hand(self.__hand.get_cards())

        move = f'{self.__ring.machine_id}:{cards}'

        self.__table_owner = self.__ring.machine_id
        self.__table_cards = cards

        self.__interface.set_table(self.__table_cards)
        self.__interface.print_game()

        self.__ring.send_message(MessageType.PLAY_CARDS, move)

        if self.__hand.is_empty():
            self.__ring.send_message(MessageType.HAND_EMPTY)
            self.__finish_order.append(self.__ring.machine_id)

            self.__interface.set_finish(self.__finish_order)
            self.__interface.print_game()


        return

    def __pass_to_next_player(self):
        next_index = (self.__player_order.index(self.__ring.machine_id) + 1) % self.__num_players
        self.__ring.give_token(self.__player_order[next_index])

    def __pay_taxes(self):
        if self.__ring.machine_id == self.__player_order[0]:
            self.__gd_taxes()
        elif self.__ring.machine_id == self.__player_order[1]:
            self.__ld_taxes()
        elif self.__ring.machine_id == self.__player_order[-2]:
            self.__lp_taxes()
        elif self.__ring.machine_id == self.__player_order[-1]:
            self.__gp_taxes()
        else:
            message = self.__ring.recv_and_send_message()
            while message.type != MessageType.ROUND_READY.value:
                if self.__ring.has_token:
                    self.__ring.give_token()
                message = self.__ring.recv_and_send_message()
            
        return

    def __gd_taxes(self):
        cards: List[Card] = []

        while len(cards) != 2:
            self.__interface.print_game()
            i_cards = input('escolha duas cartas para trocar pelas duas melhores do Greater Peon:\n')
            i_cards = i_cards.split(' ')

            i_cards = list(filter(lambda x: x.isdigit(), i_cards))
            i_cards = list(filter(lambda x: int(x) <= 13 and int(x) >= 1, i_cards))

            cards = [Card(int(c)) for c in i_cards]

            if len(cards) != 2:
                continue

            h_cards = self.__hand.get_cards_by_copy()
            for card in cards:
                try:
                    h_cards.remove(card)
                except ValueError:
                    print('Você não tem alguma das cartas que jogou...')
                    cards.remove(card)
                    break

        self.__hand.use_cards(cards)

        
        gp_id = self.__player_order[-1]
        move = f'{gp_id}:{cards}'
        self.__ring.send_message(MessageType.GIVE_CARDS, move)

        self.__ring.give_token()

        message = self.__ring.recv_and_send_message()
        while 1:
            if message.type == MessageType.GIVE_CARDS.value:
                id, g_cards = self.__hand.parse_given_cards(message.move)
                if id == self.__ring.machine_id:
                    self.__hand.add_cards(g_cards)
            if self.__ring.has_token:
                break
            message = self.__ring.recv_and_send_message()

        self.__ring.send_message(MessageType.ROUND_READY)

        return

    def __ld_taxes(self):
        message = self.__ring.recv_and_send_message()
        while message.type != MessageType.ROUND_READY.value:
            if message.type == MessageType.GIVE_CARDS.value:
                id, g_cards = self.__hand.parse_given_cards(message.move)
                if id == self.__ring.machine_id:
                    self.__hand.add_cards(g_cards)

            if self.__ring.has_token:
                cards: List[Card] = []
                while len(cards) != 1:
                    self.__interface.print_game()
                    i_cards = input('escolha uma carta para trocar pela melhor do Lesser Peon:\n')
                    i_cards = i_cards.split(' ')

                    i_cards = list(filter(lambda x: x.isdigit(), i_cards))
                    i_cards = list(filter(lambda x: int(x) <= 13 and int(x) >= 1, i_cards))

                    cards = [Card(int(c)) for c in i_cards]

                    h_cards = self.__hand.get_cards_by_copy()
                    for card in cards:
                        try:
                            h_cards.remove(card)
                        except ValueError:
                            print('Você não tem alguma das cartas que jogou...')
                            cards.remove(card)
                            break


                card = cards[0].value

                self.__hand.use_card(card)

                lp_id = self.__player_order[-2]
                move = f'{lp_id}:{card}'
                self.__ring.send_message(MessageType.GIVE_CARDS, move)

                self.__ring.give_token()
            message = self.__ring.recv_and_send_message()

        return

    def __lp_taxes(self):
        message = self.__ring.recv_and_send_message()
        while message.type != MessageType.ROUND_READY.value:
            if message.type == MessageType.GIVE_CARDS.value:
                id, g_cards = self.__hand.parse_given_cards(message.move)
                if id == self.__ring.machine_id:
                    self.__hand.add_cards(g_cards)

            if self.__ring.has_token:
                card = self.__hand.get_n_best_cards(1)
                self.__hand.use_cards(card)
                ld_id = self.__player_order[1]
                move = f'{ld_id}:{card}'
                self.__ring.send_message(MessageType.GIVE_CARDS, move)

                self.__ring.give_token()
            message = self.__ring.recv_and_send_message()

        return

    def __gp_taxes(self):
        message = self.__ring.recv_and_send_message()
        while message.type != MessageType.ROUND_READY.value:
            if message.type == MessageType.GIVE_CARDS.value:
                id, g_cards = self.__hand.parse_given_cards(message.move)
                if id == self.__ring.machine_id:
                    self.__hand.add_cards(g_cards)
            
            if self.__ring.has_token:
                cards = self.__hand.get_n_best_cards(2)
                self.__hand.use_cards(cards)
                gd_id = self.__player_order[0]
                move = f'{gd_id}:{cards}'
                self.__ring.send_message(MessageType.GIVE_CARDS, move)

                self.__ring.give_token()
            message = self.__ring.recv_and_send_message()

        return

    def __parse_order(self, setup: str):
        self.__player_order: List[int] = []
        for player in setup.split(','):
            p, _ = player.split(':')
            self.__player_order.append(int(p))

        return
    
    def get_player_order(self) -> str:
        ret = '['

        for i, player in enumerate(self.__player_order):
            if player == self.__player_order[self.__current_player_index] or (self.__current_player_index == 0 and i == 0):
                ret += '\033[31m' + f'{player}' + '\033[0m, '
            else:
                ret += f'{player}, '

        ret = ret[:-2]
        ret += ']'

        return ret



    def __check_revolution(self):
        if self.__hand.has_two_jesters():
            res = ''
            while res != 's' and res != 'n':
                self.__interface.print_game()
                res = input('Você tem 2 Jesters! Portanto deseja fazer uma revolução?[s/n]')[0]

            if res == 's':
                if self.__ring.machine_id == self.__player_order[-1]:
                    self.__player_order.reverse()
                    self.__had_revolution = True

                    self.__interface.set_order(self.get_player_order())
                    self.__interface.set_rank(self.get_player_rank())
                    self.__interface.print_game()
                    print("GRANDE REVOLUÇÃO. A ordem foi invertida")

                    self.__ring.send_message(MessageType.GREAT_REVOLUTION)
                else:
                    self.__had_revolution = True
                    self.__ring.send_message(MessageType.REVOLUTION)

        return

        
        
