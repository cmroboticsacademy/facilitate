import pytest

from facilitate.gumtree import dice
from facilitate.mappings import NodeMappings
from facilitate.model.node import Node


@pytest.mark.xfail(reason="bug in gumtree implementation")
def test_dice(good_tree: Node, bad_tree: Node) -> None:
    mappings = NodeMappings()
    tree_to = good_tree
    tree_from = bad_tree

    input_to = good_tree.find(":input[DIRECTION]@0z(.tYRa{!SepmI$)#U,")
    input_from = bad_tree.find(":input[DIRECTION]@tJ6ev+AvtHAf*PZbI}7i")

    mappings.add_with_descendants(input_from, input_to)

    score = dice(tree_from, tree_to, mappings)

    assert score == pytest.approx(1.0)
