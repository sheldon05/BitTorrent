import os
import hashlib
import math
import time
import bencode

class TorrentInfo:
    def __init__(self, metainfo):
        '''
            Representation of the Torrent File
            to Download File
        '''
        self.metainfo = metainfo
        self.file_md5sum = self.metainfo['info']['md5sum']
        self.file_name = self.metainfo['info']['name']
        self.file_size = self.metainfo['info']['length']
        self.piece_size = self.metainfo['info']['piece length']
        self.number_of_pieces = math.ceil(self.file_size/self.piece_size)
        self.dottorrent_pieces = self.metainfo['info']['pieces']
        self.trackers = self.get_trackers()
        #  urlencoded 20-byte SHA1 hash of the value of the info key from the Metainfo file. Note that the value will be a bencoded dictionary, given the definition of the info key above.
        #self.info_hash = hashlib.sha1(bencode.encode(self.metainfo['info'])).hexdigest()
        
        
    
    def get_trackers(self):
        '''
            from 'IP: PORT' return  {
                'IP': 'IP',
                'PORT': 'PORT'
            }
        '''
        trackers = []
        for tracker in self.metainfo['announce-list']:
            splited = tracker.split(':')
            trackers.append((splited[0], int(splited[1])))
        return trackers