from __future__ import annotations

import pytest

from facilitate.mappings import NodeMappings
from facilitate.model.node import Node


@pytest.fixture
def tree_before(bad_tree) -> Node:
    return bad_tree


@pytest.fixture
def tree_after(good_tree) -> Node:
    return good_tree


def test_sources_and_destinations(tree_before: Node, tree_after: Node) -> None:
    mappings = NodeMappings()

    n1_before = tree_before.find(":input[DIRECTION]@0z(.tYRa{!SepmI$)#U,")
    n1_after = tree_after.find(":input[DIRECTION]@tJ6ev+AvtHAf*PZbI}7i")

    mappings.add(n1_before, n1_after)

    sources = set(mappings.sources())
    assert len(sources) == 1
    assert n1_before in sources
    assert mappings.source_is_mapped(n1_before)
    assert mappings.source_is_mapped_to(n1_before) == n1_after

    destinations = set(mappings.destinations())
    assert len(destinations) == 1
    assert n1_after in destinations
    assert mappings.destination_is_mapped(n1_after)
    assert mappings.destination_is_mapped_to(n1_after) == n1_before


def test_add_nodes_with_different_types(tree_before: Node, tree_after: Node) -> None:
    node_before = tree_before.find(":input[RATE]@f7NN)mvnvpU?d$C(PZTk")
    node_after = tree_after.find(":field[SPIN_DIRECTIONS]@;UXN^kcB}()L,w3LFgoL")

    mappings = NodeMappings()

    with pytest.raises(TypeError):
        mappings.add(node_before, node_after)
