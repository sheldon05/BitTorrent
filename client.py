import Pyro4
import os
from torrent_files_utils.torrent_creator import TorrentCreator
from torrent_files_utils.torrent_reader import TorrentReader
from torrent_files_utils.torrent_info import TorrentInfo
from piece_manager import PieceManager

actual_path = os.getcwd()

class BitTorrentClient:
    
    def __init__(self, ip, port):
        self.ip = ip 
        self.port = port
        self.peers = []

        #TODO:Put more trackers on .torrent 

           
    def upload_file(self, path, tracker_urls, private = False, comments = "unknow", source = "unknow" ):
        '''
        Upload a local file to the tracker
        '''
        tc = TorrentCreator(path, 1 << 18, private, tracker_urls, comments, source )
        sha1_hash = tc.get_hash_pieces()

        trackers = []

        for url in tracker_urls:
            ip, port = url.split(':')
            trackers.append((ip, int(port)))

        for tracker_ip, tracker_port in trackers:
            tracker_proxy = self.connect_to(tracker_ip, tracker_port, 'tracker')
            tracker_proxy.add_to_database(sha1_hash, self.ip, self.port)
            tracker_proxy._pyroRelease()

        tc.create_dottorrent_file('torrent_files')

    def get_peers_from_tracker(self, torrent_info):
        info = torrent_info
        peers = []
        trackers = info.__get_trackers()
        peers = []
        for tracker_ip, tracker_port in trackers:
            tracker_proxy = self.connect_to(tracker_ip, tracker_port, 'tracker')
            for peer in tracker_proxy.get_peers(info.metainfo['info']['pieces']):
                peers.append(peer)
        return peers
            # ahora tengo que conectarme al peers y preguntarle por las piezas que tiene
            #para elegir la mas rara para descargarla
            
        #TODO:Check this method
    def find_rarest_piece(self, peers, torrent_info : TorrentInfo):
        count_of_pieces = [0 for i in range(torrent_info.number_of_pieces)]
        for ip, port in peers:
            proxy = self.connect_to(ip, port, 'client')
            peer_bit_field = proxy.get_bit_field_of(torrent_info)
            for i in range(len(peer_bit_field)):
                if peer_bit_field[i]:
                    count_of_pieces[i] = count_of_pieces[i] + 1
        return count_of_pieces.index(max(count_of_pieces, lambda x:x)) 

    def dowload_file(self,dottorrent_file_path, save_at = '/client_files' ):
        '''
        Start dowload of a file from a local dottorrent file
        '''
        tr = TorrentReader(dottorrent_file_path)
        info = tr.build_torrent_info()
        peers = self.get_peers_from_tracker(info)
        piece_manager_inst = PieceManager(info, save_at)
        rarest_piece = self.find_rarest_piece(peers, info)

    def get_bit_field_of(self, torrent_info : TorrentInfo):
        piece_manager = PieceManager(torrent_info, '/client_files')
        return piece_manager.bitfield
            


    def connect_to(self, ip, port, type_of_peer):
        ns = Pyro4.locateNS()
        # by default all peers, including tracker are registered in the name server as type_of_peerIP:Port
        uri = ns.lookup(f"{type_of_peer}{ip}:{port}")
        proxy = Pyro4.Proxy(uri=uri)

        # try:
        #     tracker_proxy._pyroConnection.ping()
        #     print(f"Succefuly connection with the TRACKER at {tracker_ip}:{tracker_port}")
        # except Pyro4.errors.CommunicationError:
        #     print("TRACKER Unreachable")

        return proxy
    