import hashlib
from threading import Timer
from threading import Thread
from time import sleep
from copy import copy
from fastapi import FastAPI, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_utils.tasks import repeat_every
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import json



def sha256_hash(s):
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)

fastapi = FastAPI()
ip = ''
port = ''
node_id = ''
successor = '' # 'IP:PORT'
predecessor = '' # 'IP:PORT'

pred_predecessor = '' #IP:PORT

# keys are the concatenation of sha1 hash of the pieces of the files, pieces key in .torrent
# values ip and port of the peers that potentially have the piece  , list of tuples (ip,port)
database = {}

replication_database = {}

# To test locally host must be ip, to use it in docker host must be:'0.0.0.0'
def run():
    uvicorn.run(fastapi, host=ip, port=port)


def set_ip_port(incoming_ip, incoming_port):
    ip = incoming_ip
    port = incoming_port
    node_id = sha256_hash(self.ip + ':' + str(self.port))


def ping(ip, port):    
    try:
        requests.get(f'http://{ip}:{port}/active')
        return 200
    except:
        return 500
    
@fastapi.get("/active")
def active():
  return True


def fix_connection():
    global predecessor
    global pred_predecessor
    global successor

    print('INFO: Fixing Chord Connections')

    pred_pred_ip, pred_pred_port = pred_predecessor.split(':')

    pred_pred_id = requests.get(f'http://{pred_pred_ip}:{pred_pred_port}/get_node_id').json()

    if pred_pred_id == get_node_id:
        print('INFO: Im the predecessor of my predecessor')
        successor = ''
        predecessor = ''
        pred_predecessor = ''
        clean_replication_database()

    else:
        predecessor = pred_predecessor
        requests.put(f"http://{pred_pred_ip}:{pred_pred_port}/set_successor", params={'node': get_ip_port()})

        pred_predecessor = requests.get(f"http://{pred_pred_ip}:{pred_pred_port}/get_predecessor").json()

    stabilize_databases()




def stabilize_databases():
    print('INFO: running stabilize_databases')
    global predecessor
    predecessor_ip, predecessor_port = predecessor.split(':')
    predecessor_replication_database = requests.get(f"http://{predecessor_ip}:{predecessor_port}/get_replication_database").json()
    for pieces_sha256, peers in predecessor_replication_database.items():
        for ip, port in peers:
            add_to_database(int(pieces_sha256), ip, port)
    requests.delete(f"http://{predecessor_ip}:{predecessor_port}/clean_replication_database")
    for pieces_sha256, peers in database.items():
        for ip, port in peers:
            requests.put(f"http://{predecessor_ip}:{predecessor_port}/add_to_replication_database", params={'pieces_sha256':pieces_sha256, 'ip':ip, 'port':port})
    

@fastapi.on_event('startup')
@repeat_every(seconds=10)
def check_chord_connection():
    global predecessor
    global pred_predecessor

    print(f'Predecessor: {predecessor}')
    print(f'Predecessor predecessor: {pred_predecessor}')
    print(f'database: {database}')
    print(f'replication_database: {replication_database}')
    
    
    if predecessor != '':
        print('INFO: Predecessor exists')
        pred_ip, pred_port = predecessor.split(':')
        ping_response = ping(pred_ip, pred_port)
        print(f'Ping response: {ping_response}')

        if ping_response != 200:
            print('INFO: Ping with predecessor fail')
            pred_pred_ip, pred_pred_port = pred_predecessor.split(':')
            ping_response = ping(pred_pred_ip, pred_pred_port)

            if ping_response != 200:
                print('INFO: Predeccessor predeccessor ping failed. Chord Ring Incosisteng')
                predecessor = ''
                pred_predecessor = ''

            else:
                #TODO :Ver casos extremos de dos trackers
                print('INFO: Predeccessor predecessor ping succefully')
                
                fix_connection()

        else:
            print('INFO: Ping with predecessor succefully')



@fastapi.get("/get_peers")
def get_peers(pieces_sha1):
    pieces_sha256 = sha256_hash(pieces_sha1)

    if successor != '':
        owner_ip, owner_port = find_successor(pieces_sha256).split(':')
        print(f'Asking to: {owner_ip}:{owner_port} for the file')
        try:
            peers = requests.get(f"http://{owner_ip}:{owner_port}/get_database").json()[str(pieces_sha256)]
        except KeyError:
            print("INFO: Not exist the torrent file")
            peers = []
    else:
        try:
            peers = database[pieces_sha256]
        except KeyError:
            print("INFO: Not exist the torrent file")
            peers = []
    return peers


@fastapi.get("/get_node_id")
def get_node_id():
    return node_id


@fastapi.get("/get_database")
def get_database():
    return database

@fastapi.get("/get_replication_database")
def get_replication_database():
    return replication_database

@fastapi.get("/get_ip_port")
def get_ip_port():
    return f'{ip}:{str(port)}'  

    
@fastapi.get("/get_predecessor")
def get_predecessor():
    return predecessor


@fastapi.get("/get_successor")
def get_successor():
    return successor


@fastapi.put("/add_to_database")
def add_to_database(pieces_sha256:int, ip, port):
    global predecessor
    if predecessor != '':
    
        pred_ip, pred_port = predecessor.split(':')
        requests.put(f"http://{pred_ip}:{pred_port}/add_to_replication_database", params={'pieces_sha256':pieces_sha256, 'ip':ip, 'port':port})
    if pieces_sha256 in database.keys():
        if not (ip,port) in database[pieces_sha256]:
            database[pieces_sha256].append((ip, port))
            print(f'INFO: File updated in database: {pieces_sha256}')

    else:
        database[pieces_sha256] = [(ip, port)]
        print(f'INFO: File added to the database: {pieces_sha256}')

@fastapi.put("/add_to_replication_database")
def add_to_replication_database(pieces_sha256:int, ip, port):
    print(type(pieces_sha256))
    if pieces_sha256 in replication_database.keys():
        if not (ip,port) in replication_database[pieces_sha256]:
            replication_database[pieces_sha256].append((ip, port))
            print(f'INFO: File updated in replication_database: {pieces_sha256}')
    else:
        replication_database[pieces_sha256] = [(ip, port)]
        print(f'INFO: File added to the database: {pieces_sha256}')

@fastapi.delete("/clean_replication_database")
def clean_replication_database():
    global replication_database
    print('INFO: Cleaning database')
    replication_database.clear()

@fastapi.delete("/remove_from_database")
def remove_from_database(pieces_sha1, ip, port):
    pieces_sha256 = sha256_hash(pieces_sha1)
    if pieces_sha1 in database.keys():
        if (ip,port) in database[pieces_sha1]:
            database[pieces_sha1].remove((ip, port))
            print(f'INFO: Owner {ip}:{port} of {pieces_256} removed from database')

#TODO: When remove sometime from database, remove it from replication_database

@fastapi.delete("/remove_key_from_database")
def remove_key_from_database(key:int):
    if key in database.keys():
        database.pop(key)
        print(f'INFO: File {key} removed from database')


@fastapi.put("/add_to_trackers")
def add_to_trackers(pieces_sha1, ip, port):
    pieces_sha256 = sha256_hash(pieces_sha1)
    if successor == '':
        add_to_database(pieces_sha256, ip, port)
    else:
        tracker_ip, tracker_port = find_successor(pieces_sha256).split(':')
        requests.put(f"http://{tracker_ip}:{tracker_port}/add_to_database", params={'pieces_sha256':pieces_sha256, 'ip':ip, 'port':port})



@fastapi.get("/find_successor")
def find_successor(key:int):
    global node_id
    global predecessor
    global successor
    actual_node_id = node_id
    if (key < actual_node_id):
        ip_port_next = predecessor
        ip_next, port_next = ip_port_next.split(':')
        next_node_id = requests.get(f"http://{ip_next}:{port_next}/get_node_id").json()
        while(key < int(next_node_id)):
            actual_node_id = int(next_node_id)
            ip_port_next = requests.get(f"http://{ip_next}:{port_next}/get_predecessor").json()
            ip_next, port_next = ip_port_next.split(':')
            next_node_id = requests.get(f"http://{ip_next}:{port_next}/get_node_id").json()
            if int(next_node_id) > actual_node_id:
                ip_port_succ = requests.get(f"http://{ip_next}:{port_next}/get_successor").json()
                return ip_port_succ
        
        ip_next, port_next = ip_port_next.split(':')
        return requests.get(f"http://{ip_next}:{port_next}/get_successor").json()

    else:
        ip_port_next = successor
        ip_next, port_next = ip_port_next.split(':')
        next_node_id = requests.get(f"http://{ip_next}:{port_next}/get_node_id").json()
        while(key > int(next_node_id)):
            actual_node_id = int(next_node_id)
            ip_port_next = requests.get(f"http://{ip_next}:{port_next}/get_successor").json()
            ip_next, port_next = ip_port_next.split(':')
            next_node_id = requests.get(f"http://{ip_next}:{port_next}/get_node_id").json()
            if int(next_node_id) < actual_node_id:
                return requests.get(f"http://{ip_next}:{port_next}/get_ip_port").json()
        
        ip_next, port_next = ip_port_next.split(':')
        return requests.get(f"http://{ip_next}:{port_next}/get_ip_port").json()


def distribute_information():
    print('voy a distribuir la info')
    for pieces_sha256, peers in database.items():
        owner_ip, owner_port = find_successor(pieces_sha256).split(':')
        owner_id = requests.get(f"http://{owner_ip}:{owner_port}/get_node_id").json()

        if int(owner_id) == node_id:
            successor_ip, successor_port = successor.split(':')
            successor_database = requests.get(f"http://{successor_ip}:{successor_port}/get_database").json()
            if str(pieces_sha256) in successor_database.keys():
                for ip, port in successor_database[str(pieces_sha256)]:
                    add_to_database(pieces_sha256, ip, port)
                    requests.delete(f"http://{successor_ip}:{successor_port}/remove_key_from_database", params={'key':int(pieces_sha256)})
            continue

        for ip, port in peers:
            requests.put(f"http://{owner_ip}:{owner_port}/add_to_database", params={'pieces_sha256':pieces_sha256, 'ip':ip, 'port':port})

        database.pop(pieces_sha256)

    successor_ip, successor_port = successor.split(':')
    predecessor_ip, predecessor_port = predecessor.split(':')

    succ_id = requests.get(f"http://{successor_ip}:{successor_port}/get_node_id").json()
    pred_id = requests.get(f"http://{predecessor_ip}:{predecessor_port}/get_node_id").json()
    
    if int(succ_id) < node_id:
        succ_database = requests.get(f"http://{successor_ip}:{successor_port}/get_database").json()
        for pieces_sha256, peers in succ_database.items():
            if int(pieces_sha256) <= node_id and int(pieces_sha256) > int(succ_id):
                for ip, port in peers:
                    add_to_database(int(pieces_sha256), ip, port)
                requests.delete(f"http://{successor_ip}:{successor_port}/remove_key_from_database", params={'key':int(pieces_sha256)})

        print(node_id)
        print('mi database')
        print(database)
        print('la otra id')

        print(requests.get(f"http://{'127.0.0.1'}:{'6203'}/get_node_id").json())
        print("La otra database")
        print(requests.get(f"http://{'127.0.0.1'}:{'6203'}/get_database").json())
                    
    elif int(pred_id) > node_id:
        succ_database = requests.get(f"http://{successor_ip}:{successor_port}/get_database").json()
        for pieces_sha256, peers in succ_database.items():
            if int(pieces_sha256) <= node_id or int(pieces_sha256) > int(succ_id):
                for ip, port in peers:
                    add_to_database(int(pieces_sha256), ip, port)
                requests.delete(f"http://{successor_ip}:{successor_port}/remove_key_from_database", params={'key':int(pieces_sha256)})


        print(node_id)
        print('mi database')
        print(database)
        print('la otra id')

        print(requests.get(f"http://{'127.0.0.1'}:{'6203'}/get_node_id").json())
        print("La otra database")
        print(requests.get(f"http://{'127.0.0.1'}:{'6203'}/get_database").json())

    else:
        print('voy a entrar al for')
        succ_database = requests.get(f"http://{successor_ip}:{successor_port}/get_database").json()
        print(succ_database)
        succ_succesor = requests.get(f"http://{successor_ip}:{successor_port}/get_successor").json()

        for pieces_sha256, peers in succ_database.items():
            print(f'estoy revisando la pieza {pieces_sha256}')
            if int(pieces_sha256) <= node_id or (node_id<sha256_hash(successor) and int(pieces_sha256)>sha256_hash(successor) and succ_succesor==get_ip_port()):
                print(f'la tenia que copiar para mi')
                for ip, port in peers:
                    print('voy a annadirla')
                    add_to_database(int(pieces_sha256), ip, port)

                requests.delete(f"http://{successor_ip}:{successor_port}/remove_key_from_database", params={'key':int(pieces_sha256)})

    
    #updating replication_databases
    requests.delete(f"http://{predecessor_ip}:{predecessor_port}/clean_replication_database")
    for pieces_sha256, peers in database.items():
        for ip, port in peers:
            requests.put(f"http://{predecessor_ip}:{predecessor_port}/add_to_replication_database", params={'pieces_sha256':pieces_sha256, 'ip':ip, 'port':port})
    
    
    clean_replication_database()
    succ_database = requests.get(f"http://{successor_ip}:{successor_port}/get_database").json()
    for pieces_sha256, peers in succ_database.items():
        for ip, port in peers:
            add_to_replication_database(int(pieces_sha256), ip, port)

            
def join(ip, port):
    global successor
    global predecessor
    global pred_predecessor
    
    succ_of_entry = requests.get(f"http://{ip}:{port}/get_successor").json()
    if succ_of_entry == '':
        successor = requests.get(f"http://{ip}:{port}/get_ip_port").json()
        predecessor = requests.get(f"http://{ip}:{port}/get_ip_port").json()
        pred_predecessor = get_ip_port()
        requests.put(f"http://{ip}:{port}/set_successor", params={'node': get_ip_port()})
        requests.put(f"http://{ip}:{port}/set_predecessor", params={'node': get_ip_port()})
        requests.put(f"http://{ip}:{port}/set_pred_predecessor", params={'node': predecessor})

    else:
        successor = requests.get(f"http://{ip}:{port}/find_successor", params={'key': node_id}).json()
        suc_ip, suc_port = successor.split(':') 

        predecessor = requests.get(f"http://{suc_ip}:{suc_port}/get_predecessor").json()
        requests.put(f"http://{suc_ip}:{suc_port}/set_predecessor", params={'node': get_ip_port()})
        requests.put(f"http://{suc_ip}:{suc_port}/set_pred_predecessor", params={'node': predecessor})

        pre_ip, pre_port = predecessor.split(':')
        requests.put(f"http://{pre_ip}:{pre_port}/set_successor", params={'node': get_ip_port()})
        pred_predecessor = requests.get(f"http://{pre_ip}:{pre_port}/get_predecessor").json()
        succ_succesor = requests.get(f"http://{suc_ip}:{suc_port}/get_successor").json()
        succ_succesor_ip, succ_succesor_port = succ_succesor.split(':')
        requests.put(f"http://{succ_succesor_ip}:{succ_succesor_port}/set_pred_predecessor", params={'node': get_ip_port()})

    distribute_information()
        

@fastapi.put("/set_successor")
def set_successor(node:str):
    global successor
    successor = node


@fastapi.put("/set_predecessor")
def set_predecessor(node:str):
    global predecessor
    predecessor = node
            
@fastapi.put("/set_pred_predecessor")
def set_pred_predecessor(node:str):
    global pred_predecessor
    pred_predecessor = node  


if __name__ == '__main__':
    import argparse

    # Define los argumentos de línea de comandos
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, metavar='', help='Tu ip')
    parser.add_argument('--port', type=int, metavar='', help='Tu puerto')
    parser.add_argument('--join', type=str, metavar='', help='ip:port de la puerta de entrada al chord')

    def action_dispatcher(args):
        if args.join != None:
            node_ip, node_port = args.join.split(':')
            join(node_ip, node_port)
            print(f'predecesor: {predecessor}')
            print(f'successor: {successor}')
            print('Este es el predecesor del que me uni')
            print(requests.get(f"http://{node_ip}:{node_port}/get_predecessor").json())
            print('Este es el sucesor del que me uni')
            print(requests.get(f"http://{node_ip}:{node_port}/get_successor").json())

    # Procesa los argumentos de línea de comandos
    args = parser.parse_args()

    ip = args.ip
    port = args.port
    node_id = sha256_hash(ip + ':' + str(port))

    t1 = Thread(target=run)
    t1.start()
    sleep(1)

    t2 = Thread(target=action_dispatcher, args=[args])
    t2.start()
    
    t1.join()
    t2.join()
