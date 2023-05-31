import socket
import pickle

from enum import Enum


START_MARKER = 0b01110101
END_MARKER = 0b0111010101


class MessageType(Enum):
    PLAY_CARDS = 1
    PASS = 2
    TOKEN = 3
    # etc. 


class Message():
    def __init__(self, origin: bool, type, move: str):
        self.start_marker = START_MARKER
        self.origin = 1 if bool else 0

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
            f'\ttype: {self.type}\n'
            f'\tmove: {self.move}\n'
            f'\treceipt_confirmation: {self.recv_confirm}\n'
            f'\tend_marker: {self.end_marker}\n'
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
        machine_id: int,
        send_port: int,
        recv_port: int,
        send_address,
        recv_address
    ):
        self.machine_id = machine_id

        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.send_port = send_port
        self.recv_port = recv_port

        self.send_address = send_address
        self.recv_address = recv_address

        self.has_token = False

        if machine_id == 1:
            self.has_token = True

        pass

    def setup(self):
        print(f'[S-SEND] Connecting to {self.send_address} on {self.send_port}')
        self.send_socket.connect((self.send_address, self.send_port))
        print('[S-SEND] Connected')

        print(f'[S-RECV] Binding to {self.recv_address} on {self.recv_port}')
        self.recv_socket.bind((self.recv_address, self.recv_port))
        print('[S-RECV] Connected')

        return

    def cleanup(self):
        self.send_socket.close()
        self.recv_socket.close()

        return

    def send_message(self, message: Message):
        print(f'Sending message: {message}')
    
        data = pickle.dumps(message.get_buffer())
        self.send_socket.send(data)

        return

    def recv_message(self) -> Message:
        print(f'Receiving...')

        start_marker = None
        
        while (start_marker != START_MARKER):
            data = self.recv_socket.recv(self.recv_port)
            buffer = pickle.loads(data)
            start_marker = buffer[0]

        print(f'Data: {buffer}')
        
        message = Message.buffer_to_message(buffer)
        print(f'Message: {message}')

        return message

    pass

