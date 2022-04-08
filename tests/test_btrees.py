from py_btrees.disk import DISK
from py_btrees.btree import BTree
from py_btrees.btree_node import BTreeNode, get_node

import pytest
from typing import Any

# This is a rewriting of all of the specifications that the handout provides,
# except it does not test the property that all leaf nodes reside at the same level.
# Note that fulfilling all of these requirements does NOT guarantee a working BTree.
def btree_properties_recurse(root_node_addr, node, M, L):

    assert sorted(node.keys) == node.keys # Keys should remain sorted so that a binary search is possible

    if node.is_leaf:
        # Leaf node general properties
        assert len(node.children_addrs) == 0
        assert len(node.keys) == len(node.data)
        assert len(node.data) <= L
    else:
        # Non-leaf node general properties
        assert len(node.data) == 0
        assert len(node.keys) == len(node.children_addrs) - 1
        assert len(node.children_addrs) <= M

    if node.my_addr == root_node_addr:
        # Root node properties
        assert node.parent_addr is None
        assert node.index_in_parent is None
        if not node.is_leaf:
            assert len(node.children_addrs) >= 2
    else:
        # Non-root node properties
        assert node.parent_addr is not None
        assert node.index_in_parent is not None
        if node.is_leaf:
            assert len(node.data) >= (L+1)//2
        else:
            assert len(node.children_addrs) >= (M+1)//2
        
    # Run the assertions on all children
    for child_addr in node.children_addrs:
        btree_properties_recurse(root_node_addr, DISK.read(child_addr), M, L)

def test_btree_properties() -> None:
    M = 5
    L = 3
    btree = BTree(M, L)
    for i in range(100):
        btree.insert(i, str(i))
    for i in range(0, -100):
        btree.insert(i, str(i))

    root_addr = btree.root_addr

    btree_properties_recurse(root_addr, DISK.read(root_addr), M, L)



# If you want to run tests with various parameters, lookup pytest fixtures
def test_insert_and_find_odd():
    M = 3
    L = 3
    btree = BTree(M, L)
    btree.insert(0, "0")
    btree.insert(1, "1")
    btree.insert(2, "2")
    btree.insert(3, "3") # SPLIT!
    btree.insert(4, "4")

    root = DISK.read(btree.root_addr)
    assert not root.is_leaf
    assert len(root.keys) == 1
    assert root.keys[0] in [1, 2] # the split must divide the data evenly, so the key will be 1 or 2 depending on how you represent the keys array
    assert len(root.children_addrs) == 2
    left_child = DISK.read(root.children_addrs[0])
    right_child = DISK.read(root.children_addrs[1])

    assert left_child.is_leaf
    assert right_child.is_leaf
    assert right_child.parent_addr == root.my_addr
    assert right_child.index_in_parent == 1
    for key in left_child.keys:
        assert key in [0, 1]
    for key in right_child.keys:
        assert key in [2, 3, 4]

    assert btree.find(0) == "0"
    assert btree.find(4) == "4"

def test_insert_and_find_even():
    M = 2
    L = 2
    btree = BTree(M, L)
    btree.insert(0, "0")
    btree.insert(1, "1")
    btree.insert(2, "2") # SPLIT!

    root = DISK.read(btree.root_addr)
    assert not root.is_leaf
    assert len(root.keys) == 1
    assert root.keys[0] in [0, 1, 2] # You can divide the data into [0] [1 2] or [0 1] [2], so since the keys representation could mean left or right, it can be 0, 1, or 2
    assert len(root.children_addrs) == 2
    left_child = DISK.read(root.children_addrs[0])
    right_child = DISK.read(root.children_addrs[1])

    assert left_child.is_leaf
    assert right_child.is_leaf
    for key in left_child.keys:
        assert key in [0, 1]
    for key in right_child.keys:
        assert key in [1, 2]

    assert btree.find(0) == "0"
    assert btree.find(2) == "2"

def test_insert_and_find_edge():
    M = 2
    L = 1
    btree = BTree(M, L)
    btree.insert(0, "0")
    btree.insert(1, "1") # SPLIT!

    root = DISK.read(btree.root_addr)
    assert not root.is_leaf
    assert len(root.keys) == 1
    assert root.keys[0] in [0, 1]
    assert len(root.children_addrs) == 2
    left_child = DISK.read(root.children_addrs[0])
    right_child = DISK.read(root.children_addrs[1])

    assert left_child.is_leaf
    assert right_child.is_leaf
    for key in left_child.keys:
        assert key in [0]
    for key in right_child.keys:
        assert key in [1]

    assert btree.find(0) == "0"
    assert btree.find(1) == "1"
