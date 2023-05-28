import socket
import pickle


START_MARKER = 0b01110101
END_MARKER = 0b0111010101


class Message():
    def __init__(self, move: str):
        self.start_marker = START_MARKER
        self.origin = 1
        self.move = move
        self.recv_confirm = 0
        self.end_marker = END_MARKER
        pass

    def __repr__(self):
        return (f'--- Message: \n'
            f'\tstart_marker: {self.start_marker}\n'
            f'\torigin: {self.origin}\n'
            f'\tmove: {self.move}\n'
            f'\treceipt_confirmation: {self.recv_confirm}\n'
            f'\tend_marker: {self.end_marker}\n'
        )

    pass


class Ring():
    def __init__(
        self,
        send_port: int,
        recv_port: int,
        send_address,
        recv_address
    ):
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.send_port = send_port
        self.recv_port = recv_port

        self.send_address = send_address
        self.recv_address = recv_address

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

        data = pickle.dumps(message)
        self.send_socket.send(data)

        return

    def recv_message(self) -> Message:
        print(f'Receiving...')

        data = self.recv_socket.recv(self.recv_port)

        message: Message = pickle.loads(data)
        print(message)

        return message

    pass

