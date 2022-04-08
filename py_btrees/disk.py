"""
Disk interace abstraction for the B-Tree
"""

import pickle
from typing import List, NewType

#NUM_BLOCKS = 20
#BLOCK_SIZE = 4096
LOGGING = False

Address = NewType("Address", int)  # Address type

class Disk:
    __frozen = False

    def __init__(self):
        self.memory: List[bytearray] = []
        self.__frozen = True

    def __setattr__(self, name: str, value) -> None:
        if self.__frozen:
            raise Exception("Internal error.")
        super.__setattr__(self, name, value)

    def verify(self):
        assert self == DISK, "Error. Did you override DISK?"

    def new(self) -> Address:
        self.verify()
        empty = bytearray(pickle.dumps(object()))
        self.memory.append(empty)
        if LOGGING:
            print(f"allocated block {len(self.memory) - 1}")
        return len(self.memory) - 1

    def read(self, addr: Address) -> "BTreeNode":
        self.verify()
        if (addr >= len(self.memory)):
            raise ValueError(f"Error: Memory address {addr} has not yet been allocated. You cannot read from it.")
        block = self.memory[addr]
        if LOGGING:
            print(f"read {pickle.loads(block)} at block {addr}")
        return pickle.loads(block)

    def write(self, addr: Address, data: "BTreeNode"):
        self.verify()
        if str(type(data)) != "<class 'py_btrees.btree_node.BTreeNode'>":
            raise ValueError(f"You can only write BTreeNodes to the disk, not {str(type(data))}.")
        if (addr >= len(self.memory)):
            raise ValueError(f"Error: Memory address {addr} has not yet been allocated. You cannot write to it.")
        block = pickle.dumps(data)
        #if len(block) > BLOCK_SIZE:
            #raise Exception(f"Data blob of size {len(block)} cannot fit in the block size of {BLOCK_SIZE}")
        if LOGGING:
            print(f"wrote {data} to block {addr}")
        self.memory[addr] = bytearray(block)

DISK = Disk()

__all__ = ["DISK", "LOGGING"]
