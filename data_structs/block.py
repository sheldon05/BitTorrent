from enum import Enum

DEFAULT_BLOCK_SIZE = 1 << 14 # 16KB
class BlockState(Enum):
    BLOCK_FREE = 0
    BLOCK_PENDING = 1
    BLOCK_FULL = 2

class Block():
    
    def __init__(self,  data: bytes = b'', block_size: int = DEFAULT_BLOCK_SIZE, state: BlockState = BlockState.BLOCK_FREE):
        self.data = data
        self.block_size = block_size
        self.state: BlockState = state

    def update_block_status(self, new_state: BlockState):
        self.state = new_state
        