

from facilitate.model.node import Node


def test_copy(good_tree: Node) -> None:
    copied_tree = good_tree.copy()
    assert copied_tree is not good_tree
    assert copied_tree.equivalent_to(good_tree)
    assert good_tree.equivalent_to(copied_tree)


def test_height(good_tree: Node) -> None:
    node = good_tree.find("0z(.tYRa{!SepmI$)#U,").find_input("DIRECTION")
    assert node is not None
    assert node.height == 3

    node = good_tree.find("0z(.tYRa{!SepmI$)#U,")
    assert node is not None
    assert node.height == 4


def test_has_children(good_tree: Node) -> None:
    node = good_tree.find("0z(.tYRa{!SepmI$)#U,").find_input("DIRECTION")
    assert node is not None
    assert node.has_children()

    node = good_tree.find("x:e}MT(JcdrCU9-b]!D?")
    assert node is not None
    assert node.has_children()

    node = good_tree.find("x:e}MT(JcdrCU9-b]!D?").find_field("SPIN_DIRECTIONS")
    assert node is not None
    assert not node.has_children()


def test_parent(good_tree: Node) -> None:
    assert good_tree.parent is None
    for node in good_tree.nodes():
        for child in node.children():
            assert child.parent == node


def test_size(good_tree: Node) -> None:
    node = good_tree.find("0z(.tYRa{!SepmI$)#U,")
    assert node.size() == 4
