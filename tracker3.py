from tracker import Tracker
from threading import Thread
import Pyro4
import time

def run_tracker_service(tracker):
    
    print(f"TRACKER {tracker.ip}:{tracker.port} STARTED")
    daemon.requestLoop()


tracker = Tracker("127.0.0.1", 6205)

daemon = Pyro4.Daemon(host=tracker.ip, port= tracker.port)
ns = Pyro4.locateNS()
uri = daemon.register(tracker)
ns.register(f"tracker{tracker.ip}:{tracker.port}", uri)

t1 = Thread(target=run_tracker_service, args=[tracker])
t1.start()
time.sleep(1)

t2 = Thread(target=tracker.join, args=('127.0.0.1', 6204))
t2.start()
time.sleep(1)

t3 = Thread(target=tracker.run_chord())

t3.start()
t1.join()
t2.join()
t3.join()