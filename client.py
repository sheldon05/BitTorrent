import os
import math
import random
import hashlib
from threading import Thread
from time import sleep
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

# To test locally host must be ip, to use it in docker host must be:'0.0.0.0'
def run():
    uvicorn.run(fastapi, host=ip, port=port)


def ping(ip, port):    
    try:
        requests.get(f'http://{ip}:{port}/active')
        return 200
    except:
        return 500
    
@fastapi.get("/active")
def active():
  return True


def update_trackers(trackers, sha1, remove : bool = False):
    if remove:
        for tracker_ip, tracker_port in trackers:
            requests.delete(f"http://{tracker_ip}:{tracker_port}/remove_from_database", params= {'pieces_sha1': sha1, "ip": ip, "port": port})

    else:
        print('INFO: Update Trackers in progress')
        for tracker_ip, tracker_port in trackers:
            requests.put(f"http://{tracker_ip}:{tracker_port}/add_to_trackers", params= {'pieces_sha1': sha1, "ip": ip, "port": port})
        print('INFO Update Trackers ended succefully')

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
    update_trackers(trackers, sha1_hash)


def get_peers_from_tracker(torrent_info):
    print('INFO: Getting peers from tracker')
    info = torrent_info
    peers = []
    trackers = info.get_trackers()
    peers = []
    for tracker_ip, tracker_port in trackers:
        peers_response = requests.get(f"http://{tracker_ip}:{tracker_port}/get_peers", params={"pieces_sha1":info.metainfo['info']['pieces']}).json()
        print(f'This are the peers received: {peers_response}')
        for peer in peers_response:
            peers.append(peer)
    return peers

            


def find_rarest_piece(peers, torrent_info : TorrentInfo, owned_pieces):
    count_of_pieces = [0 for i in range(torrent_info.number_of_pieces)]
    owners = [[] for i in range(torrent_info.number_of_pieces)]
    print(peers)
    for ip, port in peers:
        print(f'INFO: Asking to {ip}:{port} for the bitfield')
        info = dict(torrent_info.metainfo['info'])
        info['md5sum'] = hashlib.md5(info['md5sum']).hexdigest() 
        peer_bit_field = requests.get(f"http://{ip}:{port}/get_bit_field_of", json=info).json()
        print(f'This is the bitfield received: {peer_bit_field}')
        for i in range(len(peer_bit_field)):
            if peer_bit_field[i]:
                count_of_pieces[i] = count_of_pieces[i] + 1
                owners[i].append((ip, port))
        rarest_piece = count_of_pieces.index(min(count_of_pieces))
        while(owned_pieces[rarest_piece]):
            count_of_pieces[rarest_piece] = math.inf
            rarest_piece = count_of_pieces.index(min(count_of_pieces))
    return rarest_piece, owners[rarest_piece]


def dowload_piece_from_peer(peer, torrent_info : TorrentInfo, piece_index, piece_manager : PieceManager):
    print(f'INFO: Downloading a piece from peer {peer}')
    piece_size = torrent_info.file_size % torrent_info.piece_size if piece_index == piece_manager.number_of_pieces - 1 else torrent_info.piece_size
    for i in range(int(math.ceil(float(piece_size) / DEFAULT_BLOCK_SIZE))):
        info = dict(torrent_info.metainfo['info'])
        info['md5sum'] = hashlib.md5(info['md5sum']).hexdigest()
        received_block = requests.get(f"http://{peer[0]}:{peer[1]}/get_block_of_piece", params={'piece_index':piece_index, 'block_offset': i*DEFAULT_BLOCK_SIZE}, json=info).json()
        print(f'Block {i} received succefully')
        piece_manager.receive_block_piece(piece_index, i*DEFAULT_BLOCK_SIZE, received_block.encode('utf-8'))

#TODO: Check try-except logic
def dowload_file(dottorrent_file_path, save_at = 'test'):
    '''
    Start dowload of a file from a local dottorrent file
    '''
    print('INFO: Starting the download')
    tr = TorrentReader(dottorrent_file_path)
    info = tr.build_torrent_info()
    peers = get_peers_from_tracker(info)
    piece_manager_inst = PieceManager(info.metainfo['info'], save_at)
        
    update_trackers(info.get_trackers(), info.dottorrent_pieces)
    print('INFO: Updated trackers with my download')
    while not piece_manager_inst.completed:
        rarest_piece, owners = find_rarest_piece(peers, info, piece_manager_inst.bitfield)
        print(f'rarest piece:{rarest_piece}, owners{owners}')
        while len(owners)>0:
            peer_for_download = owners[random.randint(0,len(owners)-1)]
            owners.remove(peer_for_download)
            try:
                piece_manager_inst.clean_memory(rarest_piece)
                print('INFO: Trying to download the piece')
                dowload_piece_from_peer(peer_for_download, info, rarest_piece, piece_manager_inst)
                break
            except:
                logger.error('Download error')
                if not len(owners):
                    break
        
            

@fastapi.get("/get_bit_field_of")
def get_bit_field_of(info: dict):
    piece_manager = PieceManager(info, 'client_files')
    return piece_manager.bitfield

@fastapi.get("/get_block_of_piece")
def get_block_of_piece(info: dict, piece_index:int, block_offset:int):
    piece_manager = PieceManager(info, 'client_files')
    block = piece_manager.get_block_piece(piece_index, block_offset)
    return block.data
    


if __name__ == '__main__':
    import argparse

    # Define los argumentos de línea de comandos
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, metavar='', help='Tu ip')
    parser.add_argument('--port', type=int, metavar='', help='Tu puerto')
    parser.add_argument('--archive', type=str, metavar='', help='Direccion del archivo')
    parser.add_argument('--tracker', type=str, metavar='', help='Ip Port del tracker al que vas a subir el archivo')
    parser.add_argument('--download', type=str, metavar='', help='Direccion del .torrent a descargar')

    actual_folder = os.getcwd()
    
    def action_dispatcher(args):
        if args.archive != None and args.tracker != None:
            #TODO: Agregar el tracker al que le vas a subir por paramentros
            file_path = os.path.join(actual_folder, 'client_files', args.archive)
            upload_file(file_path, [args.tracker])

        if args.download != None:
            torrent_file_path = os.path.join(actual_folder, 'torrent_files', args.download)
            dowload_file(torrent_file_path)

    # Procesa los argumentos de línea de comandos
    args = parser.parse_args()

    ip = args.ip
    port = args.port

    t1 = Thread(target=run)
    t1.start()

    sleep(1)

    t2 = Thread(target=action_dispatcher, args=[args])
    t2.start()

    t1.join()
    t2.join()

