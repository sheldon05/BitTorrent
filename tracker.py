import Pyro4

class Tracker(object):

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        # keys are the concatenation of sha1 hash of the pieces of the files, pieces key in .torrent
        # values ip and port of the peers that potentially have the piece  , list of tuples (ip,port)
        self.database = {}


    def get_peers(self, pieces_sha1):
        decoded_info_hash = int.from_bytes(pieces_sha1, byteorder="big")
        peers = self.database[decoded_info_hash]

        return peers

    @Pyro4.expose
    def add_to_database(self, pieces_sha1, ip, port):
        decoded_info_hash = int.from_bytes(pieces_sha1, byteorder="big")
        if decoded_info_hash in self.database.keys():
            print("llegue aqui")
            if not self.database[decoded_info_hash].contains((ip, port)):
                self.database[decoded_info_hash].append((ip, port))

        else:
            self.database[decoded_info_hash] = [(ip, port)]


    def remove_from_database(self, pieces_sha1, ip, port):
        decoded_info_hash = int.from_bytes(pieces_sha1, byteorder="big")
        if decoded_info_hash in self.database.keys():
            if self.database[decoded_info_hash].contains((ip, port)):
                self.database[decoded_info_hash].remove((ip, port))

    @Pyro4.expose
    def dummy_response(self):
        return "DUMMY RESPONSE"


tracker = Tracker("127.0.0.1", 6200)

daemon = Pyro4.Daemon(host=tracker.ip, port= tracker.port)
ns = Pyro4.locateNS()
uri = daemon.register(tracker)
ns.register(f"tracker{tracker.ip}:{tracker.port}", uri)
print(f"TRACKER {tracker.ip}:{tracker.port} STARTED")
daemon.requestLoop()
