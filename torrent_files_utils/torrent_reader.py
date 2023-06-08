import bencode
from torrent_info import TorrentInfo

class TorrentReader:
    
    def __init__(self, dottorrent_path):
        self.dottorrent_path = dottorrent_path
        self.metainfo = self.__read()
    
    def __read(self):
        dottorrent_f =  open(self.dottorrent_path, 'rb')
        contents = dottorrent_f.read()
        metainfo = bencode.decode(contents) 
        dottorrent_f.close()
        return metainfo
    
    def build_torrent_info(self):
        return TorrentInfo(self.metainfo)
