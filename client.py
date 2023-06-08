import Pyro4
import os
from torrent_files_utils.torrent_creator import TorrentCreator
from torrent_files_utils.torrent_reader import TorrentReader

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

    def get_peers_from_tracker(self, dottorrent_file_path):
        tr = TorrentReader(dottorrent_file_path)
        info = tr.build_torrent_info()
        trackers = info.__get_trackers()
        for tracker_ip, tracker_port in trackers:
            tracker_proxy = self.connect_to_tracker(tracker_ip, tracker_port)
            peers = tracker_proxy.get_peers(info.metainfo['info']['pieces'])
            for ip, port in peers:
                pass
            # ahora tengo que conectarme al peers y preguntarle por las piezas que tiene
            #para elegir la mas rara para descargarla
           
        

    def dowload_file(self,dottorrent_file_path):
        '''
        Start dowload of a file from a local dottorrent file
        '''
        tr = TorrentReader(dottorrent_file_path)
        info = tr.build_torrent_info()


    def connect_to_tracker(self, tracker_ip, tracker_port):
        #by default all the trackers have the service name tracker
        uri = f"PYRO:tracker@{tracker_ip}:{tracker_port}"
        tracker_proxy = Pyro4.Proxy(uri)

        try:
            tracker_proxy._pyroConnection.ping()
            print("El servidor Pyro está activo.")
        except Pyro4.errors.CommunicationError:
            print("Error: El servidor Pyro no está activo.")

        return tracker_proxy
