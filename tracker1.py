from tracker import Tracker
from threading import Thread
import Pyro4
import time


def run_tracker_service(tracker):
    print(f"TRACKER {tracker.ip}:{tracker.port} STARTED")
    daemon.requestLoop()



tracker = Tracker("127.0.0.1", 6200)

daemon = Pyro4.Daemon(host=tracker.ip, port= tracker.port)
ns = Pyro4.locateNS()
uri = daemon.register(tracker)
ns.register(f"tracker{tracker.ip}:{tracker.port}", uri)

run_tracker_service(tracker)
