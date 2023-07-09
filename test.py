from torrent_files_utils.torrent_creator import TorrentCreator
import os

actual_folder = os.getcwd()
file_path = os.path.join(actual_folder, 'client_files', 'prueba2.txt')

tc = TorrentCreator(file_path, 1 << 18, False, ['192.20.0.7:8080'], 'unknow', 'unknow')
sha1_hash = tc.get_hash_pieces()
tc.create_dottorrent_file('torrent_files')

