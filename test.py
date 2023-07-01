from client import BitTorrentClient
from threading import Thread
import time

a = 'a' + 1

print(a)

def run(client):
    client.run()

print("inicio")
client1 = BitTorrentClient("127.0.0.1", 6200)
print("cree el cliente 1")
tr = Thread(target=run,args=[client1])
tr.start()
time.sleep(1)
print("medio")
client2 = BitTorrentClient("127.0.0.1", 6201)
client2.testing()
print("echa pila")