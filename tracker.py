import Pyro4
import hashlib
from threading import Timer
from copy import copy

def sha256_hash(s):
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)

class Tracker(object):

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.node_id = sha256_hash(self.ip + ':' + str(self.port))
        self.successor = '' # 'IP:PORT'
        self.predecessor = '' # 'IP:PORT'
        # keys are the concatenation of sha1 hash of the pieces of the files, pieces key in .torrent
        # values ip and port of the peers that potentially have the piece  , list of tuples (ip,port)
        self.database = {}


    @Pyro4.expose
    def get_peers(self, pieces_sha1):
        pieces_sha256 = sha256_hash(pieces_sha1)

        if self.successor != '':
            owner_ip, owner_port = self.find_successor(pieces_sha256).split(':')
            owner_proxy = self.connect_to(owner_ip, int(owner_port), 'tracker')

            try:
                peers = owner_proxy.get_database()[pieces_sha256]
            except KeyError:
                print("Not exist the torrent file")
                peers = []
        else:
            try:
                peers = self.database[pieces_sha256]
            except KeyError:
                print("Not exist the torrent file")
                peers = []
        return peers

    @Pyro4.expose
    def get_database(self):
        return self.database

    @Pyro4.expose
    def get_ip_port(self):
        return f'{self.ip}:{str(self.port)}'    
    
    @Pyro4.expose
    def get_predecessor(self):
        return self.predecessor

    @Pyro4.expose
    def get_successor(self):
        return self.successor

    @Pyro4.expose
    def add_to_database(self, pieces_sha256, ip, port):
        print(type(pieces_sha256))
        if pieces_sha256 in self.database.keys():
            print("llegue aqui")
            if not (ip,port) in self.database[pieces_sha256]:
                self.database[pieces_sha256].append((ip, port))

        else:
            self.database[pieces_sha256] = [(ip, port)]

    @Pyro4.expose
    def remove_from_database(self, pieces_sha1, ip, port):
        if pieces_sha1 in self.database.keys():
            if not (ip,port) in self.database[pieces_sha1]:
                self.database[pieces_sha1].remove((ip, port))

    @Pyro4.expose
    def remove_key_from_database(self, key):
        self.database.pop(key)

    @Pyro4.expose
    def add_to_trackers(self, pieces_sha1, ip, port):
        pieces_sha256 = sha256_hash(pieces_sha1)
        if self.successor == '':
            self.add_to_database(pieces_sha256, ip, port)
        else:
            tracker_ip, tracker_port = self.find_successor(pieces_sha256).split(':')
            proxy_tracker = self.connect_to(tracker_ip, int(tracker_port, 'tracker'))
            proxy_tracker.add_to_database(pieces_sha256, ip, port)
            


    def distribute_information(self):
        print('voy a distribuir la info')
        for pieces_sha256, peers in self.database.items():
            owner_ip, owner_port = self.find_successor(pieces_sha256).split(':')
            owner_proxy = self.connect_to(owner_ip, int(owner_port), 'tracker')

            if owner_proxy.node_id == self.node_id:
                continue

            for ip, port in peers:
                owner_proxy.add_to_database(pieces_sha256, ip, port)

            self.database.pop(pieces_sha256)

        successor_ip, successor_port = self.successor.split(':')
        successor_proxy = self.connect_to(successor_ip, int(successor_port), 'tracker')

        for pieces_sha256, peers in successor_proxy.get_database().items():
            if pieces_sha256 <= self.node_id:
                for ip, port in peers:
                    self.add_to_database(pieces_sha256, ip, port)

                successor_proxy.remove_key_from_database(pieces_sha256)
        print(self.node_id)
        print(self.database)
    @Pyro4.expose
    def find_successor(self, key):
        if (key < self.node_id):
            ip_next, port_next = self.get_predecessor().split(':')
            proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
            while(key < proxy_tracker.node_id):
                actual_node_id = proxy_tracker.node_id
                ip_next, port_next = proxy_tracker.get_predecessor().split(':')
                proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
                if proxy_tracker.node_id > actual_node_id:
                    return proxy_tracker.get_succesor()
            return proxy_tracker.get_succesor()
        else:
            ip_next, port_next = self.get_successor().split(':')
            proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
            while(key > proxy_tracker.node_id):
                actual_node_id = proxy_tracker.node_id
                ip_next, port_next = proxy_tracker.get_successor().split(':')
                proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
                if proxy_tracker.node_id < actual_node_id:
                    return proxy_tracker.get_ip_port()
            return proxy_tracker.get_ip_port()
            
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

    
    def connect_to(self, ip, port, type_of_peer):
        ns = Pyro4.locateNS()
        # by default all peers, including tracker are registered in the name server as type_of_peerIP:Port
        uri = ns.lookup(f"{type_of_peer}{ip}:{port}")
        proxy = Pyro4.Proxy(uri=uri)

        # try:
        #     tracker_proxy._pyroConnection.ping()
        #     print(f"Succefuly connection with the TRACKER at {tracker_ip}:{tracker_port}")
        # except Pyro4.errors.CommunicationError:
        #     print("TRACKER Unreachable")

        return proxy


# tracker = Tracker("127.0.0.1", 6200)

# daemon = Pyro4.Daemon(host=tracker.ip, port= tracker.port)
# ns = Pyro4.locateNS()
# uri = daemon.register(tracker)
# ns.register(f"tracker{tracker.ip}:{tracker.port}", uri)
# print(f"TRACKER {tracker.ip}:{tracker.port} STARTED")
# daemon.requestLoop()
