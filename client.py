import Pyro4
import os
from torrent_files_utils import torrent_creator, torrent_reader

class BitTorrentClient:
    
    def __init__(self, ip, port):
        self.ip = ip 
        self.port = port
        os.mkdir(os.path.join(os.getcwd(), 'client_files', f'{ip}:{port}downloads'))

    
        #TODO:Put more trackers on .torrent    
    def upload_file(self, path, tracker_url, private = false, comments = "unknow", source = "unknow" ):
        '''
        Upload a local file to the tracker
        '''
        tc = torrent_creator(path, 1 << 18, private, [tracker_url], comments, source )
        sha1_hash = tc.get_hash_pieces()
        #TODO:Let tracker now that this file is upload, this part is with pyro Chuchi
        tc.create_dottorrent_file('torrent_files')

    
    
    
    def dowload_file(self,dottorrent_file_path):
        '''
        Start dowload of a file from a local dottorrent file
        '''
        tr = torrent_reader(dottorrent_file_path)
        info = tr.build_torrent_info()

    
