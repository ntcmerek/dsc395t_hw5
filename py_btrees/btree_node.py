from __future__ import annotations
import typing
import bisect
from typing import Any, List, Optional, Tuple, Union, Dict, Generic, TypeVar, cast, NewType
from py_btrees.disk import DISK, Address
from py_btrees.comparable import Comparable

KT = TypeVar("KT", bound=Comparable)  # Key Type for generics
VT = TypeVar("VT", bound=Any)  # Value Type for generics

class BTreeNode(Generic[KT, VT]):
    def __init__(self, my_addr: Address, parent_addr: Optional[Address], index_in_parent: Optional[int], is_leaf: bool):
        """
        Create a new BTreeNode. You do not need to edit this class at all, but you can. Be sure to leave the following attributes:

        * my_addr stores the address of this object (self)
          In other words, given a node address a, a == get_node(a).my_addr.

        * parent_addr stores the address of the parent node.

        * index_in_parent stores the location of this node in the parent's key list
          For example, if the parent has children [c1, c2, c3], then c1 should have
          index_in_parent == 0, c2 should have it 1, etc.

        * is_leaf keeps track of if this node is a leaf node or not.

        * keys stores the keys that this node uses to index, sorted ascending.
          If self.is_leaf, then foreach index i over range(len(keys)),
        * self.data[i] contains the data element for a key keys[i]
        * Likewise, if not self.is_leaf, then self.children_addrs[i]
          contains the address of a child node whose keys fall between
          keys[i] and keys[i+1] according to BTree rules.
          You can have each key represent either the max value of the left child
          or the min value of the right child.
        """
        self.my_addr = my_addr
        self.parent_addr = parent_addr
        self.index_in_parent = index_in_parent
        self.is_leaf = is_leaf
        self.keys: List[KT] = []
        self.children_addrs: List[Address] = [] # for use when self.is_leaf == False. Otherwise it should be empty.
        self.data: List[VT] = []                # for use when self.is_leaf == True. Otherwise it should be empty.

    def get_child(self, idx: int) -> BTreeNode:
        return DISK.read(self.children_addrs[idx])

    def get_parent(self) -> BTreeNode:
        return DISK.read(self.parent_addr)

    def write_back(self):
        DISK.write(self.my_addr, self)

    def find_idx(self, key: KT) -> Optional[int]:
        """
        Finds the index in self.keys where `key`
        should go, if it were inserted into the keys list.
        
        Assumes the keys array is sorted. Works in logarithmic time.
        """
        # Get index of key
        return bisect.bisect_left(self.keys, key)

    def find_data(self, key: KT) -> Optional[VT]:
        """
        Given a key, retrieve the data associated with that key.
        Returns None if key is not present in self.keys.
        Only valid on leaf nodes.

        Works in logarithmic time using find_idx.
        """
        assert self.is_leaf
        idx = self.find_idx(key)
        # We can use the index we would insert at, and check if that entry has the key we need
        if idx < len(self.keys) and self.keys[idx] == key:
            return self.data[idx]
        return None

    def insert_data(self, key: KT, value: VT):
        """
        Insert the (key, value) pair into this leaf node.
        Preserves self.keys being sorted.
        Overwrites existing values with the same key.
        """
        assert self.is_leaf
        idx = self.find_idx(key)
        if idx < len(self.keys) and self.keys[idx] == key:
            self.data[idx] = value
        else:
            self.keys.insert(idx, key)
            self.data.insert(idx, value)


# You may find this helper function useful
def get_node(addr: Address) -> BTreeNode:
    return DISK.read(addr)

