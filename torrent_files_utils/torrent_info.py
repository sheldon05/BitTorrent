import os
import hashlib
import math
import time
import bencode
import pickle

class TorrentInfo:
    def __init__(self, metainfo):
        '''
            Representation of the Torrent File
            to Download File
        '''
        self.metainfo = dict(metainfo)
        # print(type(self.metainfo))
        self.file_md5sum = self.metainfo['info']['md5sum']
        self.file_name = self.metainfo['info']['name']
        self.file_size = self.metainfo['info']['length']
        self.piece_size = self.metainfo['info']['piece length']
        self.number_of_pieces = math.ceil(self.file_size/self.piece_size)
        self.dottorrent_pieces = self.metainfo['info']['pieces']
        self.trackers = self.get_trackers()
        #  urlencoded 20-byte SHA1 hash of the value of the info key from the Metainfo file. Note that the value will be a bencoded dictionary, given the definition of the info key above.
        self.info_hash = hashlib.sha1(bencode.encode(self.metainfo['info'])).hexdigest()
        
        
    
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
    
    def __getstate__(self):
        dic = {
            'metainfo':self.metainfo,
            'file_md5sum':self.file_md5sum,
            'file_name':self.file_name,
            'file_size':self.file_size,
            'piece_size':self.piece_size,
            'number_of_pieces':self.number_of_pieces,
            'dottorrent_pieces':self.dottorrent_pieces,
            'trackers':self.trackers,
            'info_hash':self.info_hash
        }
        return dic
        
    def __setstate__(self, state):
        self.metainfo = state['metainfo']
        self.file_md5sum = state['file_md5sum']
        self.file_name = state['file_name']
        self.file_size = state['file_size']
        self.piece_size = state['piece_size']
        self.number_of_pieces = state['number_of_pieces']
        self.dottorrent_pieces = state['dottorrent_pieces']
        self.trackers = state['trackers']
        self.info_hash = state['info_hash']