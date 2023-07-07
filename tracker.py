import Pyro4
import hashlib
from threading import Timer
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


def set_ip_port(incoming_ip, incoming_port):
    ip = incoming_ip
    port = incoming_port
    node_id = sha256_hash(self.ip + ':' + str(self.port))


@server_routes.get("/ping")
def ping(ip, port):    
    try:
        requests.get(f'http://{ip}:{port}/active', timeout=1.5)
        return 200
    except:
        return 500
    
@server_routes.get("/active")
def active():
  return True


def fix_connection():
    global predecessor
    global pred_predecessor

    print('INFO: Fixing Chord Connections')

    #TODO: Metodo del Kuko para volver a distribuir la informacion
    pred_pred_ip, pred_pred_port = pred_predecessor.split(':')

    predecessor = pred_predecessor
    requests.put(f"http://{pred_pred_ip}:{pred_pred_port}/set_successor", params={'node': get_ip_port()})

    pred_predecessor = requests.get(f"http://{pred_pred_ip}:{pred_pred_port}/get_predecessor").json()




@fastapi.on_event('startup')
@repeat_every(seconds=10)
def check_chord_connection():
    global predecessor
    global pred_predecessor

    if predecessor != '':
        pred_ip, pred_port = predecessor.split(':')
        ping = requests.get(f'http://{pred_ip}:{pred_port}/ping').json()

        if ping != '200':
            print('INFO: Ping with predecessor fail')
            pred_pred_ip, pred_pred_port = pred_predecessor.split(':')
            ping = requests.get(f'http://{pred_pred_ip}:{pred_pred_port}/ping').json()

            if ping != '200':
                print('INFO: Predeccessor predeccessor ping failed. Chord Ring Incosisteng')
                predecessor = ''
                pred_predecessor = ''

            else:
                print('INFO: Predeccessor predecessor ping succefully')
                fix_connection()

        else:
            print('INFO: Ping with predecessor succefully')



@fastapi.get("/get_peers")
def get_peers(pieces_sha1):
    pieces_sha256 = sha256_hash(pieces_sha1)

    if successor != '':
        owner_ip, owner_port = find_successor(pieces_sha256).split(':')
        print(f'Ese archivo lo debe tener segun find_succesor: {owner_ip}:{owner_port}')
        try:
            #TODO: Ver si se pregunta a si mismo
            peers = requests.get(f"http://{owner_ip}:{owner_port}/get_database").json()[str(pieces_sha256)]
        except KeyError:
            print("Not exist the torrent file")
            peers = []
    else:
        try:
            peers = database[pieces_sha256]
        except KeyError:
            print("Not exist the torrent file")
            peers = []
    return peers


@fastapi.get("/get_node_id")
def get_node_id():
    return node_id


@fastapi.get("/get_database")
def get_database():
    return database


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
    print(type(pieces_sha256))
    if predecessor != '':
        pred_ip, pred_port = predecessor.split(':')
        requests.put(f"http://{pred_ip}:{pred_port}/add_to_replication_database", params={'pieces_sha256':pieces_sha256, 'ip':ip, 'port':port})
    if pieces_sha256 in database.keys():
        print("llegue aqui")
        if not (ip,port) in database[pieces_sha256]:
            database[pieces_sha256].append((ip, port))

    else:
        print(f'annadi la pieza a la database de {port}')
        database[pieces_sha256] = [(ip, port)]

@fastapi.put("/add_to_replication_database")
def add_to_replication_database(pieces_sha256:int, ip, port):
    print(type(pieces_sha256))
    if pieces_sha256 in replication_database.keys():
        print("llegue aqui")
        if not (ip,port) in replication_database[pieces_sha256]:
            replication_database[pieces_sha256].append((ip, port))

    else:
        print(f'annadi la pieza a la database de {port}')
        replication_database[pieces_sha256] = [(ip, port)]

@fastapi.delete("/clean_replication_database")
def clean_replication_database():
    global replication_database
    replication_database.clear()

@fastapi.delete("/remove_from_database")
def remove_from_database(pieces_sha1, ip, port):
    pieces_sha256 = sha256_hash(pieces_sha1)
    if pieces_sha1 in database.keys():
        if not (ip,port) in database[pieces_sha1]:
            database[pieces_sha1].remove((ip, port))


@fastapi.delete("/remove_key_from_database")
def remove_key_from_database(key:int): #TODO: Revisar el tipo que tengo que ponerle en la anotacion
    if key in database.keys():
        database.pop(key)
    else:
        print(f"No puedo remover la llave {key}")
        print(f'Esta es mi database: {database}')


@fastapi.put("/add_to_trackers") #Check this, use of post, put or get
def add_to_trackers(pieces_sha1, ip, port):
    pieces_sha256 = sha256_hash(pieces_sha1)
    if successor == '':
        add_to_database(pieces_sha256, ip, port)
    else:
        tracker_ip, tracker_port = find_successor(pieces_sha256).split(':')
        requests.put(f"http://{tracker_ip}:{tracker_port}/add_to_database", params={'pieces_sha256':pieces_sha256, 'ip':ip, 'port':port})
        # proxy_tracker = self.connect_to(tracker_ip, int(tracker_port), 'tracker')
        # proxy_tracker.add_to_database(pieces_sha256, ip, port)


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
        #proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
        while(key < int(next_node_id)):
            actual_node_id = int(next_node_id)
            ip_port_next = requests.get(f"http://{ip_next}:{port_next}/get_predecessor").json()
            ip_next, port_next = ip_port_next.split(':')
            #proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
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
        #proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
        while(key > int(next_node_id)):
            actual_node_id = int(next_node_id)
            ip_port_next = requests.get(f"http://{ip_next}:{port_next}/get_successor").json()
            print(f'este fue el ip_port_next que me llego: {ip_port_next}')
            ip_next, port_next = ip_port_next.split(':')
            #proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
            next_node_id = requests.get(f"http://{ip_next}:{port_next}/get_node_id").json()
            if int(next_node_id) < actual_node_id:
                return requests.get(f"http://{ip_next}:{port_next}/get_ip_port").json()
        
        ip_next, port_next = ip_port_next.split(':')
        return requests.get(f"http://{ip_next}:{port_next}/get_ip_port").json()


def distribute_information():
    print('voy a distribuir la info')
    for pieces_sha256, peers in database.items():
        owner_ip, owner_port = find_successor(pieces_sha256).split(':')
        #owner_proxy = self.connect_to(owner_ip, int(owner_port), 'tracker')
        owner_id = requests.get(f"http://{owner_ip}:{owner_port}/get_node_id").json()

        if int(owner_id) == node_id:
            continue

        for ip, port in peers:
            #owner_proxy.add_to_database(pieces_sha256, ip, port)
            requests.put(f"http://{owner_ip}:{owner_port}/add_to_database", params={'pieces_sha256':pieces_sha256, 'ip':ip, 'port':port})

        database.pop(pieces_sha256)

    successor_ip, successor_port = successor.split(':')
    predecessor_ip, predecessor_port = predecessor.split(':')
    
    #successor_proxy = self.connect_to(successor_ip, int(successor_port), 'tracker')
    #predecessor_proxy = self.connect_to(predecessor_ip, int(predecessor_port), 'tracker')

    succ_id = requests.get(f"http://{successor_ip}:{successor_port}/get_node_id").json()
    pred_id = requests.get(f"http://{predecessor_ip}:{predecessor_port}/get_node_id").json()
    
    if int(succ_id) < node_id:
        succ_database = requests.get(f"http://{successor_ip}:{successor_port}/get_database").json()
        for pieces_sha256, peers in succ_database.items():
            if int(pieces_sha256) <= node_id and int(pieces_sha256) > int(succ_id): #TODO: Este pieces_sha256 es un entero?
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
            if int(pieces_sha256) <= node_id or int(pieces_sha256) > int(succ_id): #Aqui si lo tengo que convertir xq el numero grandisimo del hash fastapi lo pasa como string
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

                #successor_proxy.remove_key_from_database(pieces_sha256)
                requests.delete(f"http://{successor_ip}:{successor_port}/remove_key_from_database", params={'key':int(pieces_sha256)})

        print(node_id)
        print('mi database')
        print(database)
        print('la otra id')

        print(requests.get(f"http://{'127.0.0.1'}:{'6203'}/get_node_id").json())
        print("La otra database")
        print(requests.get(f"http://{'127.0.0.1'}:{'6203'}/get_database").json())
        #proxy_test = self.connect_to('127.0.0.1', 6200, 'tracker') #TODO: Que es esto
        #print(proxy_test.get_database())
    
    #updating replication_databases
    requests.delete(f"http://{predecessor_ip}:{predecessor_port}/clean_replication_database")
    for pieces_sha256, peers in database.items():
        for ip, port in peers:
            #owner_proxy.add_to_database(pieces_sha256, ip, port)
            requests.put(f"http://{predecessor_ip}:{predecessor_port}/add_to_replication_database", params={'pieces_sha256':pieces_sha256, 'ip':ip, 'port':port})
    
    
    clean_replication_database()
    succ_database = requests.get(f"http://{successor_ip}:{successor_port}/get_database").json()
    for pieces_sha256, peers in succ_database.items():
        for ip, port in peers:
            add_to_replication_database(int(pieces_sha256), ip, port)

# TODO: Probar este metodo.

            

def join(ip, port):
    global successor
    global predecessor
    # proxy_tracker = self.connect_to(ip, port, 'tracker')
    succ_of_entry = requests.get(f"http://{ip}:{port}/get_successor").json()
    if succ_of_entry == '':
        successor = requests.get(f"http://{ip}:{port}/get_ip_port").json()
        predecessor = requests.get(f"http://{ip}:{port}/get_ip_port").json()
        requests.put(f"http://{ip}:{port}/set_successor", params={'node': get_ip_port()})
        requests.put(f"http://{ip}:{port}/set_predecessor", params={'node': get_ip_port()})
        # proxy_tracker.set_successor(self.get_ip_port())
        # proxy_tracker.set_predecessor(self.get_ip_port())
    else:
        successor = requests.get(f"http://{ip}:{port}/find_successor", params={'key': node_id}).json()
        suc_ip, suc_port = successor.split(':') 
        #proxy_tracker = self.connect_to(suc_ip, int(suc_port))
        predecessor = requests.get(f"http://{suc_ip}:{suc_port}/get_predecessor").json()
        requests.put(f"http://{suc_ip}:{suc_port}/set_predecessor", params={'node': get_ip_port()})
        #proxy_tracker.set_predecessor(self.get_ip_port)
        pre_ip, pre_port = predecessor.split(':')
        requests.put(f"http://{pre_ip}:{pre_port}/set_successor", params={'node': get_ip_port()})
        # proxy_tracker = self.connect_to(pre_ip, int(pre_port))
        # proxy_tracker.set_successor(self.get_ip_port)
    distribute_information()
        
#TODO: Fix this method
def leave(self):
    successor = self.find_succesor(self.node_id)
    #connect to succesor
    tracker_proxy = self.connect_to(successor.split(":")[0], int(successor.split(":")[1]), 'tracker')
    
    for key, peers in self.database.items():
        for ip, port in peers:
            tracker_proxy.add_to_database(key, ip, int(port))
    
    predecessor = self.predecessor
    successor.set_predecessor(predecessor)
    #connect to predecesor
    tracker_proxy = self.connect_to(predecessor.split(":")[0], int(predecessor.split(":")[1]), 'tracker')
    tracker_proxy.set_succesor(predecessor)

    # maybe this is not necessary
    self.predecessor = ""
    self.sucessor = ""


@fastapi.put("/set_successor")
def set_successor(node:str):
    global successor
    successor = node


@fastapi.put("/set_predecessor")
def set_predecessor(node:str):
    global predecessor
    predecessor = node
            
@Pyro4.expose
def dummy_response(self):
    return "DUMMY RESPONSE"


# def connect_to(self, ip, port, type_of_peer):
#     ns = Pyro4.locateNS()
#     # by default all peers, including tracker are registered in the name server as type_of_peerIP:Port
#     uri = ns.lookup(f"{type_of_peer}{ip}:{port}")
#     proxy = Pyro4.Proxy(uri=uri)

#     # try:
#     #     tracker_proxy._pyroConnection.ping()
#     #     print(f"Succefuly connection with the TRACKER at {tracker_ip}:{tracker_port}")
#     # except Pyro4.errors.CommunicationError:
#     #     print("TRACKER Unreachable")

#     return proxy

if __name__ == '__main__':
    import argparse

    # Define los argumentos de línea de comandos
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, metavar='', help='Tu ip')
    parser.add_argument('--port', type=int, metavar='', help='Tu puerto')
    parser.add_argument('--join', type=str, metavar='', help='ip:port de la puerta de entrada al chord')

    # Procesa los argumentos de línea de comandos
    args = parser.parse_args()

    ip = args.ip
    port = args.port
    node_id = sha256_hash(ip + ':' + str(port))

    if args.join != None:
        node_ip, node_port = args.join.split(':')
        join(node_ip, node_port)
        print(f'predecesor: {predecessor}')
        print(f'successor: {successor}')
        print('Este es el predecesor del que me uni')
        print(requests.get(f"http://{node_ip}:{node_port}/get_predecessor").json())
        print('Este es el sucesor del que me uni')
        print(requests.get(f"http://{node_ip}:{node_port}/get_successor").json())

    uvicorn.run(fastapi, host=ip, port=port)


# tracker = Tracker("127.0.0.1", 6200)

# daemon = Pyro4.Daemon(host=tracker.ip, port= tracker.port)
# ns = Pyro4.locateNS()
# uri = daemon.register(tracker)
# ns.register(f"tracker{tracker.ip}:{tracker.port}", uri)
# print(f"TRACKER {tracker.ip}:{tracker.port} STARTED")
# daemon.requestLoop()
