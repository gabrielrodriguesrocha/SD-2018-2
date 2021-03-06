# Autores:
# Breno Vinicius Viana de Oliveira - RA 726498
# Gabriel Rodrigues Rocha - RA 726518

import socket
import sys
import time
import random
import threading
import pickle
from queue import Queue

server_address = ('127.0.0.1', 10000+int(sys.argv[1]))

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Bind to the server address
sock.bind(server_address)

chosen_node = { 'PID': sys.argv[1], 'CAPACITY': sys.argv[3] }
num_acks = 0
turn = 1
elid = '-1'
parent = '-1'
is_sender = 0

# use the code below for testing purposes
#if (int(sys.argv[2]) == 1):
#    turn = 1
#else:
#    turn = 2

def sender(p, neighbours):
    global turn, chosen_node, num_acks, parent, elid, is_sender
    current_message_id = 0
    request_resource = 0
    while turn == 1:
        input()
        #if (int(elid) != -1):
        #    continue
        print ('\033[93m STARTING ELECTION WITH ID %d \033[0m' % p)
        is_sender = 1
        parent = '0'
        elid = p
        message = { 'TYPE': 'election', 'PID': p, 'ELID': p }
        for i in neighbours:
            time.sleep(3)
            sent = sock.sendto(pickle.dumps(message), ('127.0.0.1', 10000 + int(i)))
        
        while num_acks != len(neighbours):
            #print ('NODE: %s CAPACITY: %s' % (chosen_node['PID'], chosen_node['CAPACITY']))
            #print ('NUM OF ACKS: %d' % num_acks)
            time.sleep(random.random() * 5)
        print('CURRENT ELID: %s' % elid)
        if (int(elid) == int(p)):
            print ('\033[93m RECEIVED ALL ACKS \033[0m')
            print ('CHOSEN NODE: %s WITH CAPACITY %s' % (chosen_node['PID'], chosen_node['CAPACITY']))
            message = { 'TYPE': 'info', 'PID': p, 'ELID': elid, 'NODE': chosen_node['PID'], 'CAPACITY': chosen_node['CAPACITY']}
            for i in neighbours:
                sent = sock.sendto(pickle.dumps(message), ('127.0.0.1', 10000 + int(i)))
        else:
            print ('ELECTION OVERRULED')
        parent = '-1'
        elid = '-1'
        time.sleep(random.random())

def receiver(p, neighbours, capacity):
    election_ended = 0
    global turn, chosen_node, num_acks, parent, elid, is_sender
    while True:
        #print('MESSAGE QUEUE:')
        #print(rd.queue[0])

        print ('\nwaiting to receive message')
        data = sock.recv(1024)

        if turn != 1:
            turn = 1

        message = pickle.loads(data)

        message_type = message['TYPE']
        message_pid = message['PID']
        message_elid = message['ELID']
        message_sender = ('127.0.0.1', 10000 + int(message_pid))

        print('MESSAGE TYPE: %s' % message_type)

        if message_type == 'election':
            print ('RECEIVED ELECTION FROM %s' % message_pid)
            print ('CURRENT ELID: %s MESSAGE ELID: %s' % (elid, message_elid))
            if int(message_elid) > int(elid):
                print('ASSIGNING MY PARENT TO %s' % message_pid)
                message = { 'TYPE': 'election', 'PID': p, 'ELID': message_elid }
                parent = message_pid
                elid = message_elid
                for i in filter(lambda x: int(x) != parent, neighbours): # error
                    print ('SENDING TO %s, MY PARENT IS %s' % (i, parent))
                    sent = sock.sendto(pickle.dumps(message), ('127.0.0.1', 10000 + int(i)))
                    time.sleep(3)
                num_acks = 0
                is_sender = 0
            elif message_pid != parent and is_sender != 1:
                print('I HAVE A PARENT')
                message = { 'TYPE': 'ack', 'PID': p, 'ELID': elid, 'NODE': p, 'CAPACITY': capacity }
                sent = sock.sendto(pickle.dumps(message), message_sender)
        elif message_type == 'info' and election_ended != 1: # Election ended
            message_node = message['NODE']
            message_capacity = message['CAPACITY']
            message = { 'TYPE': 'info', 'PID': p, 'ELID': elid, 'NODE': message_node, 'CAPACITY': message_capacity}
            print ('THE NODE %s WITH CAPACITY %s HAS BEEN ELECTED' % (message_node, message_capacity))
            for i in filter(lambda x: int(x) != int(message_pid), neighbours):
                print ('SENDING TO %s, MY INFORMANT IS %s' % (i, message_pid))
                sent = sock.sendto(pickle.dumps(message), ('127.0.0.1', 10000 + int(i)))
            chosen_node['PID'] = message_node
            chosen_node['CAPACITY'] = message_capacity
            election_ended = 1
        elif message_type == 'ack' and int(message_elid) == int(elid):
            print ('RECEIVED ACK FROM %s' % message_pid)
            num_acks = num_acks + 1
            message_node = message['NODE']
            message_capacity = message['CAPACITY']
            if int(message_capacity) > int(chosen_node['CAPACITY']):
                chosen_node['PID'] = message_node
                chosen_node['CAPACITY'] = message_capacity

        if num_acks == len(neighbours) - 1 and election_ended != 1 and is_sender != 1:
            print ('RECEIVED ALL ACKS FROM NEIGHBOURS')
            print ('SENDING TO PARENT NODE %s' % parent)
            message = { 'TYPE': 'ack', 'PID': p, 'ELID': elid, 'NODE': chosen_node['PID'], 'CAPACITY': chosen_node['CAPACITY']}
            sent = sock.sendto(pickle.dumps(message), ('127.0.0.1', 10000 + int(parent)))


        time.sleep(random.random() * 5)


# Receive/respond loop
def rr_loop (p, n, capacity):
    neighbours = n.split(",")
    elid = -1
    parent = -1
    num_acks = Queue()
    num_acks.put(0)

    print('MY NEIGHBOURS ARE:')
    print(neighbours)

    t_sender = threading.Thread(target=sender, args=(p, neighbours))
    t_receiver = threading.Thread(target=receiver, args=(p, neighbours, capacity))

    t_sender.start()
    t_receiver.start()
    t_sender.join()
    t_receiver.join()

rr_loop(int(sys.argv[1]), sys.argv[2], sys.argv[3])
