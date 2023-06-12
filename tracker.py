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
        self.sucessor = '' # 'IP:PORT'
        self.predecessor = '' # 'IP:PORT'
        # keys are the concatenation of sha1 hash of the pieces of the files, pieces key in .torrent
        # values ip and port of the peers that potentially have the piece  , list of tuples (ip,port)
        self.database = {}

    @Pyro4.expose
    def get_peers(self, pieces_sha1):
        peers = self.database[pieces_sha1]

        return peers

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
        if self.sucessor == '':
            self.add_to_database(pieces_sha256, ip, port)

    def join(self, ip, port):
        proxy_tracker = self.connect_to(ip, port, 'tracker')
        start_tracker_id = proxy_tracker.node_id
        if (start_tracker_id > self.node_id):
           while(proxy_tracker.node_id > self.node_id):
               actual_node_id = proxy_tracker.node_id
               
               ip_next, port_next = proxy_tracker.predecessor.split(':')
               proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
               if proxy_tracker.node_id>actual_node_id:
                   self.chord_neighbors_update(ip_next, port_next)
        else:
            while(proxy_tracker.node_id < self.node_id):
                actual_node_id = proxy_tracker.node_id
                
                ip_next, port_next = proxy_tracker.sucessor.split(':')
                proxy_tracker = self.connect_to(ip_next, int(port_next), 'tracker')
                if proxy_tracker.node_id<actual_node_id:
                    self.chord_neighbors_update(ip_next, port_next, is_predecessor= False)
               
               
    def chord_neighbors_update(self, ip, port, is_predecessor : bool = True):
        if 
    
    
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
