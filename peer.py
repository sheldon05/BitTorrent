class Peer:
    def __init__(self, ip, port, peer_id):
        self.has_handshaked = False
        self.last_call = 0.0
        self.ip = ip
        self.port = port
        self.read_buffer = b''
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        # self.socket.setblocking(False)
        self.healthy = False
        self.bitfield: bitstring.BitArray = None
        self.unreachable = False
        self.connected = False
        self.handshaked = False
        self.peer_id = peer_id
        self.choking = False # this peer is choking the client
        self.interested = False # this peer is interested in the client