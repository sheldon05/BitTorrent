from tracker import Tracker
from threading import Thread
import Pyro4
import time


def run_tracker_service(tracker):
    daemon = Pyro4.Daemon(host=tracker.ip, port= tracker.port)
    ns = Pyro4.locateNS()
    uri = daemon.register(tracker)
    ns.register(f"tracker{tracker.ip}:{tracker.port}", uri)
    print(f"TRACKER {tracker.ip}:{tracker.port} STARTED")
    daemon.requestLoop()



tracker = Tracker("127.0.0.1", 6200)

t1 = Thread(target=run_tracker_service, args=[tracker])
time.sleep(10)
t2 = Thread(target=tracker.run_chord)
t1.start()
t2.start()
t1.join()
t2.join()
