from facilitate.gumtree import dice
from facilitate.mappings import NodeMappings
from facilitate.model.node import Node


def test_dice(good_tree: Node, bad_tree: Node) -> None:
    mappings = NodeMappings()

    input_to = good_tree.find(":input[DIRECTION]@0z(.tYRa{!SepmI$)#U,")
    input_from = bad_tree.find(":input[DIRECTION]@tJ6ev+AvtHAf*PZbI}7i")

    mappings.add_with_descendants(input_from, input_to)

    score = dice(input_from, input_to, mappings)
    assert score == 1.0
