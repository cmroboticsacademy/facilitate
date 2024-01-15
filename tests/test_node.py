import pytest

from facilitate.model.node import Node


def test_height(good_tree: Node) -> None:
    node = good_tree.find(":input[DIRECTION]@0z(.tYRa{!SepmI$)#U,")
    assert node.height == 3

    node = good_tree.find("0z(.tYRa{!SepmI$)#U,")
    assert node.height == 4


def test_has_children(good_tree: Node) -> None:
    node = good_tree.find(":input[DIRECTION]@0z(.tYRa{!SepmI$)#U,")
    assert node.has_children()

    node = good_tree.find("x:e}MT(JcdrCU9-b]!D?")
    assert node.has_children()

    node = good_tree.find(":field[SPIN_DIRECTIONS]@x:e}MT(JcdrCU9-b]!D?")
    assert not node.has_children()
