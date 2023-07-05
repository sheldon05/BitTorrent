import Pyro4
import os
import math
import random
import serpent
import base64
from fastapi import FastAPI, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_utils.tasks import repeat_every
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import json
from bclient_logger import logger
from torrent_files_utils.torrent_creator import TorrentCreator
from torrent_files_utils.torrent_reader import TorrentReader
from torrent_files_utils.torrent_info import TorrentInfo
from piece_manager import PieceManager
from data_structs.block import Block, BlockState, DEFAULT_BLOCK_SIZE
from schemas import BlockSchema


actual_path = os.getcwd()
fastapi = FastAPI()


ip = '' 
port = ''


#TODO:Put more trackers on .torrent 


def run():
    uvicorn.run(fastapi, host=ip, port=port)


def update_trackers(trackers, sha1, remove : bool = False):
    if remove:
        for tracker_ip, tracker_port in trackers:
            requests.delete(f"http://{tracker_ip}:{tracker_port}/remove_from_database", params= {'pieces_sha1': sha1, "ip": ip, "port": port})
            # tracker_proxy = self.connect_to(tracker_ip, tracker_port, 'tracker')
            # tracker_proxy.remove_from_database(sha1, self.ip, self.port)
    else:
        print('estoy haciendo update trackers')
        for tracker_ip, tracker_port in trackers:
            requests.put(f"http://{tracker_ip}:{tracker_port}/add_to_trackers", params= {'pieces_sha1': sha1, "ip": ip, "port": port})
            # tracker_proxy = self.connect_to(tracker_ip, tracker_port, 'tracker')
            # tracker_proxy.add_to_trackers(sha1, self.ip, self.port)
            

def upload_file(path, tracker_urls, private = False, comments = "unknow", source = "unknow" ):
    '''
    Upload a local file to the tracker
    '''
    tc = TorrentCreator(path, 1 << 18, private, tracker_urls, comments, source )
    sha1_hash = tc.get_hash_pieces()
    tc.create_dottorrent_file('torrent_files')

    trackers = []

    for url in tracker_urls:
        ip, port = url.split(':')
        trackers.append((ip, int(port)))
    print(type(trackers))
    print(trackers)
    print('vamos a llamar a update trackers')
    update_trackers(trackers, sha1_hash)


def get_peers_from_tracker(torrent_info):
    info = torrent_info
    peers = []
    trackers = info.get_trackers()
    peers = []
    for tracker_ip, tracker_port in trackers:
        #tracker_proxy = self.connect_to(tracker_ip, tracker_port, 'tracker')
        #TODO: Revisar en que formato se devuelven los peers
        peers_response = requests.get(f"http://{tracker_ip}:{tracker_port}/get_peers", params={"pieces_sha1":info.metainfo['info']['pieces']}).json()
        for peer in peers_response:
            peers.append(peer)
    return peers
        # ahora tengo que conectarme al peers y preguntarle por las piezas que tiene
        #para elegir la mas rara para descargarla
            

        #TODO:Check this method, and potential connection failures
def find_rarest_piece(peers, torrent_info : TorrentInfo, owned_pieces):
    count_of_pieces = [0 for i in range(torrent_info.number_of_pieces)]
    owners = [[] for i in range(torrent_info.number_of_pieces)]
    print(peers)
    for ip, port in peers:
        #proxy = self.connect_to(ip, port, 'client')
        print('voy a hacer get_bit_field')
        #peer_bit_field = proxy.get_bit_field_of(dict(torrent_info.metainfo['info']))
        peer_bit_field = requests.get(f"http://{ip}:{port}/get_bit_field_of", params={'info':torrent_info.metainfo['info']}).json()
        print('tengo el bitfield')
        print(peer_bit_field)
        for i in range(len(peer_bit_field)):
            if peer_bit_field[i]:
                count_of_pieces[i] = count_of_pieces[i] + 1
                owners[i].append((ip, port))
        rarest_piece = count_of_pieces.index(min(count_of_pieces))
        while(owned_pieces[rarest_piece]):
            count_of_pieces[rarest_piece] = math.inf
            rarest_piece = count_of_pieces.index(min(count_of_pieces, lambda x:x))
    return rarest_piece, owners[rarest_piece]


def dowload_piece_from_peer(self, peer, torrent_info : TorrentInfo, piece_index, piece_manager : PieceManager):
    try:
        proxy_peer = self.connect_to(peer[0], peer[1], 'client')
    except:
        logger.error("Connection failure")
        return
    piece_size = torrent_info.file_size % torrent_info.piece_size if piece_index == piece_manager.number_of_pieces - 1 else torrent_info.piece_size
    for i in range(int(math.ceil(float(piece_size) / DEFAULT_BLOCK_SIZE))):
        #received_block = proxy_peer.get_block_of_piece(dict(torrent_info.metainfo['info']), piece_index, i*DEFAULT_BLOCK_SIZE)
        received_block = requests.get(f"http://{peer[0]}:{peer[1]}/get_block_of_piece", params={'info':torrent_info.metainfo['info'], 'piece_index':piece_index, 'block_offset': i*DEFAULT_BLOCK_SIZE}).json()
        print('este es el bloque que me mandaron')
        print(received_block)
        raw_data = base64.b64decode(received_block['data']['data']) #TODO: No se si ahora esto es necesario
        piece_manager.receive_block_piece(piece_index, i*DEFAULT_BLOCK_SIZE, received_block['data'])


def dowload_file(dottorrent_file_path, save_at = 'client_files'):
    '''
    Start dowload of a file from a local dottorrent file
    '''
    tr = TorrentReader(dottorrent_file_path)
    info = tr.build_torrent_info()
    peers = get_peers_from_tracker(info)
    piece_manager_inst = PieceManager(info.metainfo['info'], save_at)
        
    update_trackers(info.get_trackers(), info.dottorrent_pieces)
        
    while not piece_manager_inst.completed:
        rarest_piece, owners = find_rarest_piece(peers, info, piece_manager_inst.bitfield)
        while len(owners)>0:
            print('tengo un owner')
            peer_for_download = owners[random.randint(0,len(owners)-1)]
            owners.remove(peer_for_download)
            #try:
            piece_manager_inst.clean_memory(rarest_piece)
            print('voy a tratar de descargar la pieza')
            dowload_piece_from_peer(peer_for_download, info, rarest_piece, piece_manager_inst)
            break
            # except:
            #     logger.error('Download error')
        if not len(owners):
            break
        
            
    #TODO: Check if the path must cointain /
@fastapi.get("/get_bit_field_of")
def get_bit_field_of(info):
    piece_manager = PieceManager(info, 'client_files')
    return piece_manager.bitfield

    #TODO: Check if the path must cointain /
@fastapi.get("/get_block_of_piece")
def get_block_of_piece(info, piece_index, block_offset):
    piece_manager = PieceManager(info, 'client_files')
    print('la pieza tiene estos bloques')
    print(piece_manager.pieces[piece_index].number_of_blocks)
    print(piece_manager.get_block_piece(piece_index, block_offset).data)
    block = piece_manager.get_block_piece(piece_index, block_offset)
    return BlockSchema(data=block.data, block_size=block.block_size, state=block.state)
    


if __name__ == '__main__':
    import argparse

    # Define los argumentos de línea de comandos
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, metavar='', help='Tu ip')
    parser.add_argument('--port', type=int, metavar='', help='Tu puerto')
    parser.add_argument('--archive', type=str, metavar='', help='Direccion del archivo')

    # Procesa los argumentos de línea de comandos
    args = parser.parse_args()

    ip = args.ip
    port = args.port

    if args.archive != None:
        actual_folder = os.getcwd()
        file_path = os.path.join(actual_folder, 'client_files', args.archive)
        upload_file(file_path, ['127.0.0.1:6200'])

    run()

    