from client import BitTorrentClient
import os

actual_folder = os.getcwd()
torrent_file_path = os.path.join(actual_folder, 'client_files', 'archivo.txt')

client_seeder = BitTorrentClient('127.0.0.1', 6201)

client_seeder.upload_file(torrent_file_path, ['127.0.0.1:6200'])

