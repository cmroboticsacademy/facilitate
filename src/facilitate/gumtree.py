from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import product

from facilitate.model import Node

# NOTE change to a set?
NodeMappings = list[tuple[Node, Node]]


@dataclass
class HeightIndexedPriorityList:
    _height_to_nodes: dict[int, set[Node]] = field(default_factory=defaultdict)

    @property
    def max_height(self) -> int:
        """Returns the maximum height of a node in the list."""
        return self.peek_max()

    def peek_max(self) -> int:
        """Returns the maximum height of a node in the list."""
        if not self._height_to_nodes:
            return 0
        return max(height for height in self._height_to_nodes.keys())

    def push(self, node: Node) -> None:
        """Adds a node to the list."""
        self._height_to_nodes[node.height].add(node)

    def pop(self) -> set[Node]:
        """Removes and returns the set of nodes with maximal height."""
        max_height = self.peek_max()
        nodes = self._height_to_nodes[max_height]
        del self._height_to_nodes[max_height]
        return nodes

    def open(self, node: Node) -> None:
        """Inserts all children of given node into the list."""
        for child in node.children():
            self.push(child)


def dice(
    node_x: Node,
    node_y: Node,
    mappings: NodeMappings,
) -> float:
    """Computes ratio of common descendants between two nodes based on given mappings."""
    raise NotImplementedError


def _add_children_to_mappings(
    node_x: Node,
    node_y: Node,
    mappings: NodeMappings,
) -> None:
    """Adds all children of given nodes to the mappings."""
    children_x = list(node_x.children())
    children_y = list(node_y.children())

    for child_x, child_y in zip(
        children_x,
        children_y,
        strict=True,
    ):
        if (child_x, child_y) not in mappings:
            mappings.append((child_x, child_y))
            _add_children_to_mappings(child_x, child_y, mappings)


def _compute_topdown_mappings(
    root_x: Node,
    root_y: Node,
    *,
    min_height: int = 2,
) -> NodeMappings:
    mappings: NodeMappings = []
    candidates: NodeMappings = []

    hlist_x = HeightIndexedPriorityList()
    hlist_x.push(root_x)

    hlist_y = HeightIndexedPriorityList()
    hlist_y.push(root_y)

    nodes_x = list(root_x.nodes())
    nodes_y = list(root_y.nodes())

    while min(hlist_x.max_height, hlist_y.max_height) > min_height:
        if hlist_x.max_height > hlist_y.max_height:
            for node in hlist_x.pop():
                hlist_x.open(node)
        elif hlist_x.max_height < hlist_y.max_height:
            for node in hlist_y.pop():
                hlist_y.open(node)
        else:
            max_height_nodes_x = hlist_x.pop()
            max_height_nodes_y = hlist_y.pop()

            added_trees_x: set[Node] = set()
            added_trees_y: set[Node] = set()

            for node_x, node_y in product(max_height_nodes_x, max_height_nodes_y):
                if node_x.equivalent_to(node_y):
                    # NOTE this is where sim_matrix_count_subtree_occurrences is used
                    match_x = any(node.equivalent_to(node_y) and node != node_x for node in nodes_x)
                    match_y = any(node.equivalent_to(node_x) and node != node_y for node in nodes_y)

                    if match_x or match_y:
                        candidates.append((node_x, node_y))
                    else:
                        mappings.append((node_x, node_y))

                    added_trees_x.add(node_x)
                    added_trees_y.add(node_y)

            for node in max_height_nodes_x:
                if node not in added_trees_x:
                    hlist_x.open(node)

            for node in max_height_nodes_y:
                if node not in added_trees_y:
                    hlist_y.open(node)

    candidates.sort(key=lambda node_x, node_y: dice(node_x.parent, node_y.parent, mappings))

    while candidates:
        node_x, node_y = candidates.pop(0)
        mappings.append((node_x, node_y))
        candidates = [
            (from_x, to_y)
            for from_x, to_y in candidates
            if from_x != node_x and to_y != node_y
        ]

    # FIXME add all kids of node_x and node_y to mappings

    return mappings
