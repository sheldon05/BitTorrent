from client import BitTorrentClient
import os
import Pyro4

actual_folder = os.getcwd()
file_path = os.path.join(actual_folder, 'client_files', 'archivo.txt')

client_seeder = BitTorrentClient('127.0.0.1', 6201)

client_seeder.upload_file(file_path, ['127.0.0.1:6200'])

daemon = Pyro4.Daemon(host=client_seeder.ip, port= client_seeder.port)
ns = Pyro4.locateNS()
uri = daemon.register(client_seeder)
ns.register(f"client{client_seeder.ip}:{client_seeder.port}", uri)
print(f"PEER {client_seeder.ip}:{client_seeder.port} ONLINE")
daemon.requestLoop()