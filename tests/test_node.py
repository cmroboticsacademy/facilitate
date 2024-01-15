import pytest

from facilitate.model.node import Node


def test_height(good_tree: Node) -> None:
    node = good_tree.find(":input[DIRECTION]@0z(.tYRa{!SepmI$)#U,")
    assert node.height == 3

    node = good_tree.find("0z(.tYRa{!SepmI$)#U,")
    assert node.height == 4
