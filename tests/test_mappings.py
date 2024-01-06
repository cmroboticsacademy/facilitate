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


def test_add_nodes_with_different_types(tree_before: Node, tree_after: Node) -> None:
    node_before = tree_before.find(":input[RATE]@f7NN)mvnvpU?d$C(PZTk")
    node_after = tree_after.find(":field[SPIN_DIRECTIONS]@;UXN^kcB}()L,w3LFgoL")

    mappings = NodeMappings()

    with pytest.raises(TypeError):
        mappings.add(node_before, node_after)
