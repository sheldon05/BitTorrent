import Pyro4
import os
from torrent_files_utils.torrent_creator import TorrentCreator
from torrent_files_utils.torrent_reader import TorrentReader
from piece_manager import PieceManager

actual_path = os.getcwd()

class BitTorrentClient:
    
    def __init__(self, ip, port):
        self.ip = ip 
        self.port = port
        self.peers = []
        os.mkdir(os.path.join(os.getcwd(), 'client_files', f'{ip}:{port}downloads'))

        #TODO:Put more trackers on .torrent 

           
    def upload_file(self, path, tracker_url, private = False, comments = "unknow", source = "unknow" ):
        '''
        Upload a local file to the tracker
        '''
        tc = TorrentCreator(path, 1 << 18, private, [tracker_url], comments, source )
        sha1_hash = tc.get_hash_pieces()

        #TODO:Let tracker now that this file is upload, this part is with pyro Chuchi
        tc.create_dottorrent_file('torrent_files')

    def get_peers_from_tracker(self, torrent_info):
        info = torrent_info
        trackers = info.__get_trackers()
        for tracker_ip, tracker_port in trackers:
            tracker_proxy = self.connect_to_tracker(tracker_ip, tracker_port)
            peers = tracker_proxy.get_peers(info.metainfo['info']['pieces'])
            for ip, port in peers:
                pass
            # ahora tengo que conectarme al peers y preguntarle por las piezas que tiene
            #para elegir la mas rara para descargarla
           
        

    def dowload_file(self,dottorrent_file_path, save_at = '/client_files' ):
        '''
        Start dowload of a file from a local dottorrent file
        '''
        tr = TorrentReader(dottorrent_file_path)
        info = tr.build_torrent_info()
        peers = get_peers_from_tracker(info)
        piece_manager_inst = PieceManager(torrent_info, save_at)


    def connect_to_tracker(self, tracker_ip, tracker_port):
        #by default all the trackers have the service name tracker
        uri = f"PYRO:obj_4e01749f627a40a9b7049d91079fc309@{tracker_ip}:{tracker_port}"
        tracker_proxy = Pyro4.Proxy(uri)
        tracker_proxy.dummy_response()

        try:
            tracker_proxy._pyroConnection.ping()
            print("El servidor Pyro está activo.")
        except Pyro4.errors.CommunicationError:
            print("Error: El servidor Pyro no está activo.")

        return tracker_proxy

client = BitTorrentClient('127.0.0.1', 6201)

proxy = client.connect_to_tracker('127.0.0.1', 6200)

print(proxy.dummy_response())