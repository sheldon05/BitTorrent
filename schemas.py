from pydantic import BaseModel
from data_structs.block import BlockState


class BlockSchema(BaseModel):
    data : bytes
    block_size: int
    state: BlockState