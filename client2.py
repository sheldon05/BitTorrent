from client import BitTorrentClient
from torrent_files_utils.torrent_reader import TorrentReader
import os

actual_folder = os.getcwd()
torrent_file_path = os.path.join(actual_folder, 'torrent_files', 'archivo.torrent')

client_leecher = BitTorrentClient('127.0.0.1', 6202)

tr = TorrentReader(torrent_file_path)

torrent_info = tr.build_torrent_info()

peers = client_leecher.get_peers_from_tracker(torrent_info)

print(peers)