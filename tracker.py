import Pyro4
import hashlib
from threading import Timer

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
        peers = self.database[pieces_sha1]

        return peers
    
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
    def add_to_database(self, pieces_sha1, ip, port):
        print(type(pieces_sha1))
        if pieces_sha1 in self.database.keys():
            print("llegue aqui")
            if not (ip,port) in self.database[pieces_sha1]:
                self.database[pieces_sha1].append((ip, port))

        else:
            self.database[pieces_sha1] = [(ip, port)]


    def remove_from_database(self, pieces_sha1, ip, port):
        if pieces_sha1 in self.database.keys():
            if not (ip,port) in self.database[pieces_sha1]:
                self.database[pieces_sha1].remove((ip, port))


    def add_to_trackers(self, pieces_sha1, ip, port):
        pieces_sha256 = sha256_hash(pieces_sha1)
        if self.successor == '':
            self.add_to_database(pieces_sha256, ip, port)


    
    def distribute_information(self):
        for pieces_sha256, ip, port in self.database.items():
            owner_ip, owner_port = self.find_successor(pieces_sha256).split(':')
            owner_proxy = self.connect_to(owner_ip, int(owner_port), 'tracker')
            owner_proxy.add_to_database(pieces_sha256, ip, port)


    def find_successor(self, key):
        if (key < self.node_id):
            ip_next, port_next = proxy_tracker.get_predecessor().split(':')
            proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
            while(key < proxy_tracker.node_id):
                actual_node_id = proxy_tracker.node_id
                ip_next, port_next = proxy_tracker.get_predecessor().split(':')
                proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
                if proxy_tracker.node_id > actual_node_id:
                    return proxy_tracker.get_succesor()
            return proxy_tracker.get_succesor()
        else:
            ip_next, port_next = proxy_tracker.get_successor().split(':')
            proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
            while(key > proxy_tracker.node_id):
                actual_node_id = proxy_tracker.node_id
                ip_next, port_next = proxy_tracker.get_successor().split(':')
                proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
                if proxy_tracker.node_id < actual_node_id:
                    return proxy_tracker.get_ip_port()
            return proxy_tracker.get_ip_port()
            
    def join(self, ip, port):
        pass

    def leave(self):
        successor = self.find_succesor(self.node_id)
        #connect to succesor
        tracker_proxy = self.connect_to(successor.split(":")[0], int(successor.split(":")[1]))
        database_successor = tracker_proxy.get_data()
        for key, peers in self.database.items():
            if key in database_successor.keys():
                database_successor[key] += [i for i in peers if i not in database_successor[key]]
            else:
                database_successor[key] = peers
       
        predecessor = self.predecessor
        successor.set_predecessor(predecessor)
        #connect to predecesor
        tracker_proxy = self.connect_to(predecessor.split(":")[0], int(predecessor.split(":")[1]))
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
               
    def chord_neighbors_update(self, ip, port, is_predecessor : bool = True):
        pass
    
    
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
