import argparse
import logging
import socket

from ring import Ring, Message, MessageType
from game import Game


def get_args():
    parser = argparse.ArgumentParser(
        description='The Great Dalmuti on a ring network.'
    )

    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help='run logging in debug mode'
    )
    
    return parser.parse_args()


def get_local_address():
    return socket.gethostbyname(socket.gethostname())


def get_config_data():
    num_players = 1
    machine_id = -1
    send_address = -1
    send_port = -1
    recv_port = -1

    local_address = get_local_address()

    f = None
    try:
        f = open('config.txt')
    except:
        logging.error('File config.txt does not exist, exiting...')
        exit(-1)

    num_players = int(f.readline().split()[1])

    line = f.readline()
    while line != '':
        line = f.readline()

        if 'MACHINE' not in line:
            continue
            
        id = int(line.split()[1])
        address = f.readline().split()[1].strip()

        if address == local_address:
            machine_id = id 
            send_address = f.readline().split()[1].strip()
            send_port = int(f.readline().split()[1])
            recv_port = int(f.readline().split()[1])
            break

    if machine_id == -1:
        print('Error: machine address is not in config.txt')
        exit(1)

    return num_players, machine_id, send_port, recv_port, send_address


def main():
    args = get_args()

    logging.basicConfig(
        format='[%(levelname)s] %(message)s',
        level=logging.DEBUG if args.debug else logging.WARNING
    )

    num_players, id, send_port, recv_port, send_address = get_config_data()

    logging.info('Machine configuration:\n'
          f'\tID: {id}\n'
          f'\tAddress: {get_local_address()}\n'
          f'\tSend address: {send_address}\n'
          f'\tSend port: {send_port}\n'
          f'\tRecv port: {recv_port}\n'
    )

    ring = Ring(
        num_players,
        id,
        send_port,
        recv_port,
        send_address
    )
    ring.setup()
    game = Game(ring, num_players)

    game.run()

    ring.cleanup()

    return


if __name__ == '__main__':
    main()

