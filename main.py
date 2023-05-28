import sys

from ring import Ring, Message


def main():
    print('Hello world!')

    send_port = 6000
    recv_port = 6001

    if sys.argv[1] == 's':
        send_port = 6001
        recv_port = 6000

    ring = Ring(send_port, recv_port, '127.0.0.1', '127.0.0.1')
    ring.setup()

    if sys.argv[1] == 's':
        ring.send_message(Message('this is a move'))
    else:
        ring.recv_message()

    ring.cleanup()

    return

if __name__ == '__main__':
    main()

