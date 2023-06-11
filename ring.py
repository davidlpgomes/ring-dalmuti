import logging
import socket
import pickle

from enum import Enum


START_MARKER = 0b01110101
END_MARKER = 0b0111010101

BUFFER_SIZE = 1024
SOCKET_TIMEOUT = 1.0


class MessageType(Enum):
    PLAY_CARDS = 1
    PASS = 2
    TOKEN = 3
    SETUP = 4
    DEAL = 5
    REVOLUTION = 6
    GREAT_REVOLUTION = 7
    ROUND_READY = 8
    GIVE_CARDS = 9
    TOKEN_SETTLED = 10
    ROUND_FINISHED = 11
    HAND_EMPTY = 12


class Message():
    def __init__(self, origin: int, type: MessageType, move: str):
        self.start_marker = START_MARKER
        self.origin = origin

        self.type = type

        if isinstance(type, MessageType):
            self.type = type.value

        self.move = move

        self.recv_confirm = 0

        self.end_marker = END_MARKER
        pass

    def __repr__(self):
        return (f'--- Message: \n'
            f'\tstart_marker: {self.start_marker}\n'
            f'\torigin: {self.origin}\n'
            f'\ttype: {MessageType(self.type)}\n'
            f'\tmove: {self.move}\n'
            f'\treceipt_confirmation: {format(self.recv_confirm, "b")}\n'
            f'\tend_marker: {self.end_marker}\n'
        )
    
    def send_repr(self):
        return (f'\t--- Message: \n'
            f'\t\tstart_marker: {self.start_marker}\n'
            f'\t\torigin: {self.origin}\n'
            f'\t\ttype: {MessageType(self.type)}\n'
            f'\t\tmove: {self.move}\n'
            f'\t\treceipt_confirmation: {format(self.recv_confirm, "b")}\n'
            f'\t\tend_marker: {self.end_marker}\n'
        )

    def get_buffer(self):
        buffer = []

        buffer.append(self.start_marker)
        buffer.append(self.origin)
        buffer.append(self.type)
        buffer.append(self.move)
        buffer.append(self.recv_confirm)
        buffer.append(self.end_marker)

        return buffer

    @staticmethod
    def buffer_to_message(buffer):
        message = Message(buffer[1], buffer[2], buffer[3])

        message.start_marker = buffer[0]
        message.recv_confirm = buffer[4]
        message.end_marker = buffer[5]

        return message

    pass


class Ring():
    def __init__(
        self,
        num_machines: int,
        machine_id: int,
        send_port: int,
        recv_port: int,
        send_address
    ):
        self.num_machines = num_machines
        self.machine_id = machine_id

        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.send_port = send_port
        self.recv_port = recv_port

        self.send_address = send_address
        self.recv_address = socket.gethostbyname(socket.gethostname())

        self.has_token = False

        if machine_id == 1:
            self.has_token = True

        pass

    def setup(self):
        self.recv_socket.bind((self.recv_address, self.recv_port))
        logging.debug(f'Binded to {self.recv_address} on {self.recv_port}')

        self.recv_socket.settimeout(SOCKET_TIMEOUT)
        logging.debug(f'Set recv socket timeout to {SOCKET_TIMEOUT}')

        return

    def cleanup(self):
        self.send_socket.close()
        self.recv_socket.close()

        return

    def send(self, data):
        self.send_socket.sendto(data, (self.send_address, self.send_port))
        return

    def send_message(self, message: Message):
        logging.debug(f'[SEND] Sending {message}')

        data = pickle.dumps(message.get_buffer())
        recv_message = None

        while True:
            self.send(data)

            logging.debug('[SEND] Waiting message')
            recv_message = self.recv_message()
            logging.debug(f'[SEND] Received message {recv_message}')

            if recv_message.origin == self.machine_id:
                logging.debug(f'[SEND] Message went through the entire ring')
                recv_message = self.set_received(recv_message)
                break

            logging.warning(f'[SEND] Did not received the sent message')

        return

    def send_message_to_next(self, message: Message):
        logging.debug(f'[SEND-N] Sending to next machine {message}')

        data = pickle.dumps(message.get_buffer())
        self.send(data)

        return

    def recv_message(self) -> Message:
        start_marker = None

        addr = None
        data = None
        
        while (start_marker != START_MARKER):
            try:
                data, addr = self.recv_socket.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue

            buffer = pickle.loads(data)
            start_marker = buffer[0]

        message = Message.buffer_to_message(buffer)
        logging.debug(f'[RECV] Received message: {message}')

        if message.type == MessageType.TOKEN.value:
            id = int(message.move)

            logging.debug(f'[RECV] Message is TOKEN for machine {id}')

            if id == self.machine_id:
                logging.debug('[RECV] Received TOKEN')
                self.has_token = True
            else:
                logging.debug('[RECV] Giving TOKEN')
                self.give_token(int(message.move))

        return message
    
    def wait_token_settle(self):
        logging.debug('[WTS] Waiting token settle')

        while True:
            message = self.recv_and_send_message()

            if self.has_token:
                logging.debug('[WTS] Received token, senting TOKEN_SETTLED')
                self.send_message(Message(self.machine_id, MessageType.TOKEN_SETTLED, ''))
                break
            elif message.type == MessageType.TOKEN_SETTLED.value:
                logging.debug('[WTS] Received TOKEN_SETTLED')
                break

        return


    def recv_and_send_message(self) -> Message:
        logging.debug('[RECV&SEND] Receiving and sending message')

        message = self.recv_message()
        message = self.set_received(message)

        if message.type == MessageType.TOKEN.value:
            logging.debug('[RECV&SEND] Message is TOKEN, returning')
            return message

        if not self.has_token:
            logging.debug('[RECV&SEND] Sending message to next')
            self.send_message_to_next(message)

        return message

    def give_token(self, machine_id = -1):
        if machine_id == -1:
            machine_id = self.machine_id % self.num_machines + 1

        logging.debug(f'[GT] Giving TOKEN to {machine_id}')

        if machine_id == self.machine_id:
            message = Message(self.machine_id, MessageType.TOKEN_SETTLED, '')
            data = pickle.dumps(message.get_buffer())
            self.send(data)

            logging.debug(f'[GT] Giving TOKEN to yourself, TOKEN_SETTLED sent')
            return

        message = Message(self.machine_id, MessageType.TOKEN, str(machine_id))
        data = pickle.dumps(message.get_buffer())

        self.send(data)
        self.has_token = False

        logging.debug(f'[GT] TOKEN sent')

        return

    def set_received(self, message: Message):
        message.recv_confirm |= 2 ** (self.num_machines - self.machine_id)
        logging.debug('[SET-R] Set message received bit')

        return message

    pass

