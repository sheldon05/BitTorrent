import Pyro4


class Tracker:

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port