# Bittorrent piece
import hashlib
from bclient_logger import logger
import math
import os
from block import Block, BlockState, DEFAULT_BLOCK_SIZE
from disk_io import DiskIO

class Piece:


    def __init__(self, piece_index: int, piece_offset, piece_size: int, piece_hash: str):
        """
        Initialize a piece
        """
        self.piece_index = piece_index
        self.piece_offset = piece_offset
        self.piece_size = piece_size
        self.piece_hash = piece_hash
        self.number_of_blocks: int = int(math.ceil(float(piece_size) / DEFAULT_BLOCK_SIZE))
        self.blocks: list['Block'] = self.__build_blocks()
        self.is_completed: bool = False 
        self.raw_data : bytes = b''
        # self.last_call = 0
    
    
    @property
    def in_memory(self):
        return self.raw_data != b''
    
    def put_data(self, data):
        self.raw_data = data
        self.is_completed = True
        
    @property
    def have_all_blocks(self):
        '''
            If all block of the piece succefully downloaded
        '''
        return all(block.state == BlockState.BLOCK_FULL for block in self.blocks) 
    
    def write_block(self, offset, data):
        block_index = offset//DEFAULT_BLOCK_SIZE

        #TODO: check if first condition is needed
        if not self.is_completed and not self.blocks[block_index].state == BlockState.BLOCK_FULL:
            self.blocks[block_index].data = data
            self.blocks[block_index].state = BlockState.BLOCK_FULL
        
        if self.have_all_blocks:
            self.__merge_all_blocks()
    
    def __build_blocks(self):
        blocks: list['Block'] = []

        for _ in range(self.number_of_blocks-1):
            blocks.append(Block(block_size = DEFAULT_BLOCK_SIZE))
        
        blocks.append(Block(block_size = self.piece_size%DEFAULT_BLOCK_SIZE))
        return blocks
    
    def __merge_blocks(self):
        raw_data = b''
        for block in self.blocks:
            raw_data += block.data
        return raw_data

    #TODO: Handler logger in piece manager 
    def __valid_blocks(self, raw_data):
        hash_raw_data = hashlib.sha1(raw_data).digest()
        
        if hash_raw_data == self.piece_hash:
            logger.debug(f"Piece Hash of Piece{self.piece_index} validated successfully")
            return True
        
        logger.warning(f'Error Piece Hash : {hash_raw_data} != {self.piece_hash} Piece{self.piece_index}')
        return False
    
    #TODO: Handler logger in piece manager 
    def __merge_all_blocks(self):
        raw_data = self.__merge_blocks()
        if self.__valid_blocks(raw_data):
            self.is_completed = True
            self.raw_data = raw_data
            logger.debug(f"Piece {self.piece_index} downloaded successfully")  
            
        else:
            self.blocks = self.__build_blocks()

    def __rebuild_blocks(self):

        for i in range(self.number_of_blocks-1):
            self.blocks[i].data = self.raw_data[i*DEFAULT_BLOCK_SIZE:(i+1)*DEFAULT_BLOCK_SIZE]
        self.blocks[self.number_of_blocks-1].data = self.raw_data[(self.number_of_blocks-1)*DEFAULT_BLOCK_SIZE:]

        
    def get_block(self, block_offset)-> 'Block':
        block_index = block_offset//DEFAULT_BLOCK_SIZE
        return self.blocks[block_index]

    def load_from_disk(self, filename: str):
        piece_data = DiskIO.read_from_disk(filename, self.piece_offset, self.piece_size)
        self.raw_data = piece_data
        self.__rebuild_blocks()

    def clean_memory(self):
        self.raw_data = b''
    
    #aqui se calcula el block offset
    def get_empty_block(self):
        if self.is_completed:
            return None
        
        for block_index, block in enumerate(self.blocks):
            if block.state == BlockState.BLOCK_FREE:
                self.blocks[block_index].state = BlockState.BLOCK_PENDING
                return block_index * DEFAULT_BLOCK_SIZE, self.blocks[block_index].block_size
        
        return None 
        