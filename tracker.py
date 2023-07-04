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
# keys are the concatenation of sha1 hash of the pieces of the files, pieces key in .torrent
# values ip and port of the peers that potentially have the piece  , list of tuples (ip,port)
database = {}

def set_ip_port(incoming_ip, incoming_port):
    ip = incoming_ip
    port = incoming_port
    node_id = sha256_hash(self.ip + ':' + str(self.port))

@fastapi.get("/get_peers")
def get_peers(pieces_sha1):
    pieces_sha256 = sha256_hash(pieces_sha1)

    if successor != '':
        owner_ip, owner_port = find_successor(pieces_sha256).split(':')
        try:
            peers = requests.get(f"http://{owner_ip}:{owner_port}/get_database").json()[pieces_sha256]
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


@fastapi.get("/add_to_database")
def add_to_database(pieces_sha256, ip, port):
    print(type(pieces_sha256))
    if pieces_sha256 in database.keys():
        print("llegue aqui")
        if not (ip,port) in database[pieces_sha256]:
            database[pieces_sha256].append((ip, port))

    else:
        print(f'annadi la pieza a la database de {port}')
        database[pieces_sha256] = [(ip, port)]


@fastapi.delete("/remove_from_database")
def remove_from_database(pieces_sha1, ip, port):
    if pieces_sha1 in database.keys():
        if not (ip,port) in database[pieces_sha1]:
            database[pieces_sha1].remove((ip, port))


@fastapi.delete("/remove_key_from_database")
def remove_key_from_database(key):
    database.pop(key)


@fastapi.put("/add_to_trackers") #Check this, use of post, put or get
def add_to_trackers(pieces_sha1, ip, port):
    pieces_sha256 = sha256_hash(pieces_sha1)
    if successor == '':
        add_to_database(pieces_sha256, ip, port)
    else:
        tracker_ip, tracker_port = find_successor(pieces_sha256).split(':')
        requests.put()
        proxy_tracker = self.connect_to(tracker_ip, int(tracker_port), 'tracker')
        proxy_tracker.add_to_database(pieces_sha256, ip, port)
            

def distribute_information(self):
    print('voy a distribuir la info')
    for pieces_sha256, peers in self.database.items():
        owner_ip, owner_port = self.find_successor(pieces_sha256).split(':')
        owner_proxy = self.connect_to(owner_ip, int(owner_port), 'tracker')

        if owner_proxy.get_node_id() == self.node_id:
            continue

        for ip, port in peers:
            owner_proxy.add_to_database(pieces_sha256, ip, port)

        self.database.pop(pieces_sha256)

    successor_ip, successor_port = self.successor.split(':')
    predecessor_ip, predecessor_port = self.predecessor.split(':')
    
    successor_proxy = self.connect_to(successor_ip, int(successor_port), 'tracker')
    predecessor_proxy = self.connect_to(predecessor_ip, int(predecessor_port), 'tracker')
    
    if successor_proxy.get_node_id() < self.node_id:
        for pieces_sha256, peers in successor_proxy.get_database().items():
            if pieces_sha256 <= self.node_id and pieces_sha256 > successor_proxy.get_node_id():
                for ip, port in peers:
                    self.add_to_database(pieces_sha256, ip, port)
                    
    elif predecessor_proxy.get_node_id() > self.node_id:
        for pieces_sha256, peers in successor_proxy.get_database().items():
            if pieces_sha256 <= self.node_id or pieces_sha256 > successor_proxy.get_node_id():
                for ip, port in peers:
                    self.add_to_database(pieces_sha256, ip, port)
    else:
        print('voy a entrar al for')
        print(successor_proxy.get_database())
        for pieces_sha256, peers in successor_proxy.get_database().items():
            print(f'estoy revisando la pieza {pieces_sha256}')
            if pieces_sha256 <= self.node_id or (self.node_id<sha256_hash(successor_proxy.get_ip_port()) and pieces_sha256>sha256_hash(successor_proxy.get_ip_port()) and successor_proxy.get_successor()==self.get_ip_port()):
                print(f'la tenia que copiar para mi')
                for ip, port in peers:
                    print('voy a annadirla')
                    self.add_to_database(pieces_sha256, ip, port)

                successor_proxy.remove_key_from_database(pieces_sha256)
        print(self.node_id)
        print('mi database')
        print(self.database)
        print('la otra')
        proxy_test = self.connect_to('127.0.0.1', 6200, 'tracker')
        print(proxy_test.get_database())
            

# TODO: Probar este metodo.
@fastapi.get("/find_succesor")
def find_successor(key:int):
    if (key < self.node_id):
        ip_port_next = self.get_predecessor()
        ip_next, port_next = ip_port_next.split(':')
        node_id = requests.get(f"http://{ip_next}:{port_next}/get_node_id").json()
        #proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
        while(key < int(node_id)):
            actual_node_id = int(node_id)
            ip_port_next = requests.get(f"http://{ip_next}:{port_next}/get_predecessor").json()
            ip_next, port_next = ip_port_next.split(':')
            #proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
            node_id = requests.get(f"http://{ip_next}:{port_next}/get_node_id").json()
            if int(node_id) > actual_node_id:
                ip_port_succ = requests.get(f"http://{ip_next}:{port_next}/get_successor").json()
                return ip_port_succ
        
        ip_next, port_next = ip_port_next.split(':')
        return requests.get(f"http://{ip_next}:{port_next}/get_successor").json()

    else:
        ip_port_next = self.get_successor()
        ip_next, port_next = ip_port_next.split(':')
        node_id = requests.get(f"http://{ip_next}:{port_next}/get_node_id").json()
        #proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
        while(key > int(node_id)):
            actual_node_id = int(node_id)
            ip_port_next = requests.get(f"http://{ip_next}:{port_next}/get_successor").json()
            ip_next, port_next = ip_port_next.split(':')
            #proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
            node_id = requests.get(f"http://{ip_next}:{port_next}/get_node_id").json()
            if int(node_id) < actual_node_id:
                return requests.get(f"http://{ip_next}:{port_next}/get_ip_port").json()
        
        ip_next, port_next = ip_port_next.split(':')
        return requests.get(f"http://{ip_next}:{port_next}/get_ip_port").json()
            

def join(self, ip, port):
    proxy_tracker = self.connect_to(ip, port, 'tracker')
    if proxy_tracker.get_successor() == '':
        self.successor = proxy_tracker.get_ip_port()
        self.predecessor = proxy_tracker.get_ip_port()
        proxy_tracker.set_successor(self.get_ip_port())
        proxy_tracker.set_predecessor(self.get_ip_port())
    else:
        succesor = proxy_tracker.find_successor(self.node_id)
        self.successor = succesor
        suc_ip, suc_port = succesor.split(':') 
        proxy_tracker = self.connect_to(suc_ip, int(suc_port))
        self.predecessor = proxy_tracker.get_predecessor()
        proxy_tracker.set_predecessor(self.get_ip_port)
        pre_ip, pre_port = self.predecessor.split(':')
        proxy_tracker = self.connect_to(pre_ip, int(pre_port))
        proxy_tracker.set_successor(self.get_ip_port)
    self.distribute_information()
        
        


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


@Pyro4.expose
def set_successor(self,node):
    self.successor = node


@Pyro4.expose
def set_predecessor(self, node):
    self.predecessor = node
            
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

    # Procesa los argumentos de línea de comandos
    args = parser.parse_args()

    ip = args.ip
    port = args.port
    node_id = sha256_hash(self.ip + ':' + str(self.port))


# tracker = Tracker("127.0.0.1", 6200)

# daemon = Pyro4.Daemon(host=tracker.ip, port= tracker.port)
# ns = Pyro4.locateNS()
# uri = daemon.register(tracker)
# ns.register(f"tracker{tracker.ip}:{tracker.port}", uri)
# print(f"TRACKER {tracker.ip}:{tracker.port} STARTED")
# daemon.requestLoop()
