import sys

from ring import Ring, Message, MessageType


def main():
    print('Hello world!')

    send_port = 6000
    recv_port = 6001
    machine_id = 2

    if sys.argv[1] == 's':
        machine_id = 1
        send_port = 6001
        recv_port = 6000

    ring = None

    ring = Ring(machine_id, send_port, recv_port, '127.0.0.1', '127.0.0.1')
    ring.setup()

    if sys.argv[1] == 's':
        ring.send_message(Message(True, MessageType.PLAY_CARDS, 'this is a move'))
    else:
        ring.recv_message()

    ring.cleanup()

    return

if __name__ == '__main__':
    main()

