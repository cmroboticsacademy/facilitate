from __future__ import annotations

import functools
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import product

from facilitate.model import Node

# NOTE change to a set?
NodeMappings = list[tuple[Node, Node]]


@dataclass
class HeightIndexedPriorityList:
    _height_to_nodes: dict[int, set[Node]] = field(
        default_factory=functools.partial(defaultdict, set),
    )

    @property
    def max_height(self) -> int:
        """Returns the maximum height of a node in the list."""
        return self.peek_max()

    def peek_max(self) -> int:
        """Returns the maximum height of a node in the list."""
        if not self._height_to_nodes:
            return 0
        return max(height for height in self._height_to_nodes)

    def push(self, node: Node) -> None:
        """Adds a node to the list."""
        self._height_to_nodes[node.height].add(node)

    def pop(self) -> set[Node]:
        """Removes and returns the set of nodes with maximal height."""
        max_height = self.peek_max()
        nodes = self._height_to_nodes[max_height]
        del self._height_to_nodes[max_height]
        return nodes

    def add_children(self, node: Node) -> None:
        """Inserts all children of given node into the list."""
        for child in node.children():
            self.push(child)


# FIXME this doesn't look quite right; original paper contains an error in formula
# TODO write some tests for this method
def dice(
    root_x: Node,
    root_y: Node,
    mappings: NodeMappings,
) -> float:
    """Computes ratio of common descendants between two nodes based on given mappings."""
    descendants_x = set(root_x.descendants())
    descendants_y = set(root_y.descendants())

    contained_mappings: NodeMappings = []

    for (node_x, node_y) in mappings:
        contains_x = any(node.equivalent_to(node_x) for node in descendants_x)
        contains_y = any(node.equivalent_to(node_y) for node in descendants_y)
        if contains_x and contains_y:
            contained_mappings.append((node_x, node_y))

    # NOTE Leo's code had an extra multiplication by 2 (if root_x and root_y have the same block ID) here
    numerator = 2 * len(contained_mappings)
    denominator = len(descendants_x) + len(descendants_y)
    return numerator / denominator


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


def compute_topdown_mappings(
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
                hlist_x.add_children(node)
        elif hlist_x.max_height < hlist_y.max_height:
            for node in hlist_y.pop():
                hlist_y.add_children(node)
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
                    hlist_x.add_children(node)

            for node in max_height_nodes_y:
                if node not in added_trees_y:
                    hlist_y.add_children(node)

    def sort_key(map_entry: tuple[Node, Node]) -> float:
        node_x, node_y = map_entry
        return dice(node_x, node_y, mappings)

    candidates.sort(key=sort_key)

    while candidates:
        node_x, node_y = candidates.pop(0)
        mappings.append((node_x, node_y))
        candidates = [
            (from_x, to_y)
            for from_x, to_y in candidates
            if from_x != node_x and to_y != node_y
        ]

    # FIXME we shouldn't be able to mutate mappings while we're iterating over it!
    for node_x, node_y in mappings:
        _add_children_to_mappings(node_x, node_y, mappings)

    return mappings


def compute_bottom_up_mappings(
    root_x: Node,
    root_y: Node,
    mappings: NodeMappings,
    *,
    min_dice: float = 0.5,
) -> NodeMappings:
    mappings = mappings.copy()
    matched_x = [node_x for node_x, _ in mappings]
    matched_y = [node_y for _, node_y in mappings]

    def visit(node: Node) -> None:
        if node in matched_x:
            return

        if not any(child in matched_x for child in node.descendants()):
            return

        candidates: list[Node] = [
            node_y
            for node_y in root_y.nodes()
            if node_y not in matched_y and node.surface_equivalent_to(node_y)
        ]

        if not candidates:
            return

        candidates.sort(
            key=lambda node_y: dice(node, node_y, mappings),
            reverse=True,
        )
        top_candidate = candidates[0]

        if dice(node, top_candidate, mappings) > min_dice:
            mappings.append((node, top_candidate))

    for node in root_x.postorder():
        visit(node)

    # NOTE original GumTree algo uses RTED algorithm to find edit script
    # without move actions; possibly unnecessary given small size of trees

    return mappings


def compute_gumtree_mappings(
    root_x: Node,
    root_y: Node,
    *,
    min_height: int = 2,
    min_dice: float = 0.5,
) -> NodeMappings:
    """Uses the GumTree algorithm to map nodes between two trees."""
    mappings = compute_topdown_mappings(root_x, root_y, min_height=min_height)
    return compute_bottom_up_mappings(root_x, root_y, mappings, min_dice=min_dice)
