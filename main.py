import sys
import socket

from ring import Ring, Message, MessageType
from game import Deal


def get_local_address():
    return socket.gethostbyname(socket.gethostname())


def get_config_data():
    num_players = 1
    machine_id = -1
    send_address = -1
    send_port = -1
    recv_port = -1

    local_address = get_local_address()

    with open('config.txt') as f:
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

    return num_players, machine_id, send_port, recv_port, send_address


def main():
    num_players, id, send_port, recv_port, send_address = get_config_data()

    if id == -1:
        print('Machine configuration not found, exiting')
        exit(-1)

    print('Machine configuration:\n'
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

    if id == 1:
        deal = Deal(num_players)
        game_setup = deal.setup()
        ring.send_message(Message(id, MessageType.SETUP, game_setup))
    else:
        msg = ring.recv_and_send_message()

    ring.cleanup()

    return


if __name__ == '__main__':
    main()

