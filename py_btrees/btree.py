# Modified by Nhi Cmerek 4/11/2022
# In Collaboration with Avinash and Izaak Thompson

import bisect
from typing import Any, List, Optional, Tuple, Union, Dict, Generic, TypeVar, cast, NewType
from py_btrees.disk import DISK, Address
from py_btrees.btree_node import BTreeNode, KT, VT, get_node

"""
----------------------- Starter code for your B-Tree -----------------------

Helpful Tips (You will need these):
1. Your tree should be composed of BTreeNode objects, where each node has:
    - the disk block address of its parent node
    - the disk block addresses of its children nodes (if non-leaf)
    - the data items inside (if leaf)
    - a flag indicating whether it is a leaf

------------- THE ONLY DATA STORED IN THE `BTree` OBJECT SHOULD BE THE `M` & `L` VALUES AND THE ADDRESS OF THE ROOT NODE -------------
-------------              THIS IS BECAUSE THE POINT IS TO STORE THE ENTIRE TREE ON DISK AT ALL TIMES                    -------------

2. Create helper methods:
    - get a node's parent with DISK.read(parent_address)
    - get a node's children with DISK.read(child_address)
    - write a node back to disk with DISK.write(self)
    - check the health of your tree (makes debugging a piece of cake)
        - go through the entire tree recursively and check that children point to their parents, etc.
        - now call this method after every insertion in your testing and you will find out where things are going wrong
3. Don't fall for these common bugs:
    - Forgetting to update a node's parent address when its parent splits
        - Remember that when a node splits, some of its children no longer have the same parent
    - Forgetting that the leaf and the root are edge cases
    - FORGETTING TO WRITE BACK TO THE DISK AFTER MODIFYING / CREATING A NODE
    - Forgetting to test odd / even M values
    - Forgetting to update the KEYS of a node who just gained a child
    - Forgetting to redistribute keys or children of a node who just split
    - Nesting nodes inside of each other instead of using disk addresses to reference them
        - This may seem to work but will fail our grader's stress tests
4. USE THE DEBUGGER
5. USE ASSERT STATEMENTS AS MUCH AS POSSIBLE
    - e.g. `assert node.parent != None or node == self.root` <- if this fails, something is very wrong

--------------------------- BEST OF LUCK ---------------------------
"""


# Complete both the find and insert methods to earn full credit
class BTree:
    def __init__(self, M: int, L: int):
        """
        Initialize a new BTree.
        You do not need to edit this method, nor should you.
        """
        self.root_addr: Address = DISK.new() # Remember, this is the ADDRESS of the root node
        # DO NOT RENAME THE ROOT MEMBER -- LEAVE IT AS self.root_addr
        DISK.write(self.root_addr, BTreeNode(self.root_addr, None, None, True))
        self.M = M  # M will fall in the range 2 to 99999
        self.L = L  # L will fall in the range 1 to 99999

    def insert(self, key: KT, value: VT) -> None:
        """
        Insert the key-value pair into your tree.
        It will probably be useful to have an internal
        _find_node() method that searches for the node
        that should be our parent (or finds the leaf
        if the key is already present).

        Overwrite old values if the key exists in the BTree.

        Make sure to write back all changes to the disk!
        """
        root_node = get_node(self.root_addr)

        if root_node.is_leaf:
            # insert data first
            root_node.insert_data(key, value)
            self._check_split_node(root_node, True, root_node)
        else:
            # insert data first into leaf node
            leaf_node = self._find_leaf_node(key, root_node)
            leaf_node.insert_data(key, value)
            self._check_split_node(leaf_node, False, root_node)

    # function to check if need to split a node or not after insertion
    # write to disk if doesn't
    def _check_split_node(self, current_node: BTreeNode, is_root: bool = True, root_node: BTreeNode = None):
        # if leaf node and have more data than allowed
        # shouldn't be greater than here but just in case
        if current_node.is_leaf and len(current_node.data) > self.L:
            # need to make new leaf node
            # get parent first
            if not is_root:
                parent = get_node(current_node.parent_addr)
                assert parent is not None
                # check for sibling first
                # TBD
                # else split nodes
                _split_nodes(current_node, parent)
                # recursively goes up the tree
                self._check_split_node(parent, parent.my_addr == self.root_addr, root_node)
            else:
                if root_node is None:
                    old_root = get_node(self.root_addr)
                else:
                    old_root = root_node
                _split_root_keys(old_root)

        # if not leaf node and have more keys than allowed
        # shouldn't be greater than here but just in case
        elif not current_node.is_leaf and len(current_node.children_addrs) > self.M:
            # if current node is root, make new root node:
            if is_root:
                _split_root_keys(current_node)
            else:
                parent = get_node(current_node.parent_addr)
                assert parent is not None
                # check for sibling first
                # TBD
                # else split nodes
                _split_nodes(current_node, parent)
                # recursively goes up the tree
                self._check_split_node(parent, parent.my_addr == self.root_addr, root_node)
        else:
            # nothing to do here, just write to disk
            current_node.write_back()

    # recursively go down the tree until finding the correct leaf node
    def _find_leaf_node(self, key: KT, current_node: BTreeNode = None) -> BTreeNode:
        if current_node is None:
            return None

        # if leaf node, return it
        if current_node.is_leaf:
            return current_node
        # else recursively find next node
        else:
            child_index = current_node.find_idx(key)
            assert len(current_node.children_addrs) > child_index
            child_address = current_node.children_addrs[child_index]
            return self._find_leaf_node(key, get_node(child_address))
        return None

    def find(self, key: KT) -> Optional[VT]:
        """
        Find a key and return the value associated with it.
        If it is not in the BTree, return None.

        This should be implemented with a logarithmic search
        in the node.keys array, not a linear search. Look at the
        BTreeNode.find_idx() method for an example of using
        the builtin bisect library to search for a number in 
        a sorted array in logarithmic time.
        """
        found_node = self._find_leaf_node(key, get_node(self.root_addr))
        if found_node is None:
            return None
        else:
            return found_node.find_data(key)

    def delete(self, key: KT) -> None:
        raise NotImplementedError("Karma method delete()")

    def __str__(self) -> str:
        return self._print_btree(get_node(self.root_addr))

    # debugging function
    def _print_btree(self, node, level: int = 0):
        if node is None:
            return ""
        else:
            return_str = str(level) + "\t" * level + f" Leaf: {node.is_leaf}, My Addr: {node.my_addr}," \
                                                     f" Index: {node.index_in_parent}, " \
                                                     f" Keys: {node.keys}, Children: {node.children_addrs}," \
                                                     f" Data: {node.data}"
            for i in range(len(node.children_addrs)):
                return_str = return_str + "\r\n" + self._print_btree(node.get_child(i), level + 1)
            return return_str


# Insert new key into the correct spot
def _insert_key(new_key, current_node: BTreeNode):
        assert current_node is not None
        new_index = current_node.find_idx(new_key)
        current_node.keys.insert(new_index, new_key)


def _split_root_keys(root: BTreeNode) -> None:
    [split_index, new_key] = _find_new_key(root)
    # create 2 new nodes
    left_node_addr: Address = DISK.new()
    right_node_addr: Address = DISK.new()
    left_node = BTreeNode(left_node_addr, root.my_addr, 0, root.is_leaf)
    right_node = BTreeNode(right_node_addr, root.my_addr, 1, root.is_leaf)
    _make_new_nodes(left_node, right_node, root, split_index)

    # update root
    if root.is_leaf:
        root.is_leaf = False
        root.data = []
    root.children_addrs = [left_node_addr, right_node_addr]
    root.keys = [new_key]
    root.write_back()


def _split_nodes(current_node: BTreeNode, parent_node: BTreeNode):
    [split_index, new_key] = _find_new_key(current_node)
    _insert_key(new_key, parent_node)
    index_in_parent = current_node.index_in_parent + 1
    # make new node
    new_node_addr: Address = DISK.new()
    new_node = BTreeNode(new_node_addr, parent_node.my_addr, index_in_parent, current_node.is_leaf)
    _make_new_nodes(current_node, new_node, current_node, split_index)
    # update index_in_parent for all siblings to the right
    _update_child_nodes_index(range(index_in_parent + 1, len(parent_node.children_addrs)), parent_node)

    # update parent node
    parent_node.children_addrs.insert(index_in_parent, new_node_addr)
    # parent_node.write_back()


# left is same as current if not making 2 new nodes
def _make_new_nodes(left_node: BTreeNode, right_node: BTreeNode, current_node: BTreeNode, split_index: int):
    right_node.keys = current_node.keys[split_index:]
    left_node.keys = current_node.keys[:split_index]

    if current_node.is_leaf:
        right_node.data = current_node.data[split_index:]
        left_node.data = current_node.data[:split_index]
    else:
        right_node.children_addrs = current_node.children_addrs[split_index:]
        left_node.children_addrs = current_node.children_addrs[:split_index]
        left_node.keys = _key_reduce(left_node.keys, left_node.children_addrs)
        right_node.keys = _key_reduce(right_node.keys, right_node.children_addrs)
        _update_child_nodes_index(range(len(left_node.children_addrs)), left_node)
        _update_child_nodes_index(range(len(right_node.children_addrs)), right_node)
    # save to memory
    left_node.write_back()
    right_node.write_back()


def _find_new_key(node: BTreeNode):
    if node.is_leaf:
        length = len(node.data)
    else:
        length = len(node.children_addrs)

    index = length // 2
    if length % 2 == 0:
        key = node.keys[index - 1]
    else:
        key = node.keys[index]
    return [index, key]


# Remove right-most key, only need to do for interior (non-leaf) nodes
def _key_reduce(key_list: List, node_list):
    if len(key_list) == len(node_list):
        key_list = key_list[:len(key_list) - 1]
    return key_list


# Update the children index_in_parent after key update for interior (non-leaf) nodes
def _update_child_nodes_index(range_list: List, parent_node: BTreeNode):
    for i in range_list:
        child_node = get_node(parent_node.children_addrs[i])
        assert child_node is not None
        child_node.index_in_parent = i
        child_node.parent_addr = parent_node.my_addr
        child_node.write_back()

# M = 2
# L = 1
# btree = BTree(M, L)
# for i in range(5):
#     btree.insert(i, str(i))
#
# print(btree)
# print(btree.find(1))


