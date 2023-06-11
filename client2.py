from client import BitTorrentClient
from torrent_files_utils.torrent_reader import TorrentReader
import os
from torrent_files_utils.torrent_reader import TorrentReader
from testing import Prueba
import serpent

actual_folder = os.getcwd()
torrent_file_path = os.path.join(actual_folder, 'torrent_files', 'archivo.torrent')

client_leecher = BitTorrentClient('127.0.0.1', 6202)

tr = TorrentReader(torrent_file_path)

torrent_info = tr.build_torrent_info()

print(torrent_info.metainfo)

client_leecher.dowload_file(torrent_file_path, save_at='test')
