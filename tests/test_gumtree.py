import functools

import pytest

from facilitate.gumtree import (
    compute_topdown_mappings,
    dice,
)
from facilitate.mappings import NodeMappings
from facilitate.model.node import Node


def test_dice(good_tree: Node, bad_tree: Node) -> None:
    mappings = NodeMappings()

    input_to = good_tree.find(":input[DIRECTION]@0z(.tYRa{!SepmI$)#U,")
    input_from = bad_tree.find(":input[DIRECTION]@tJ6ev+AvtHAf*PZbI}7i")

    mappings.add_with_descendants(input_from, input_to)

    assert dice(input_from, input_to, mappings) == 1.0


# FIXME fails non-deterministically!
@pytest.mark.xfail(reason="non-deterministic behavior")
def test_topdown_mappings(good_tree: Node, bad_tree: Node) -> None:
    tree_from = bad_tree
    tree_to = good_tree

    nx = tree_from.find
    ny = tree_to.find

    mappings = compute_topdown_mappings(tree_from, tree_to)

    x = nx("ON]Ie`,s9aYllf=Ko6pI")
    y = ny("jR#!l0]kqB%K}fB9a_{O")

    assert x.equivalent_to(y)
    assert dice(x, y, mappings) == 1.0
    assert (x, y) in mappings
