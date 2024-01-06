from __future__ import annotations

import functools
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import product

from loguru import logger

from facilitate.model.node import Node, TerminalNode

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


def _dice_coefficient(
    common_elements: int,
    elements_in_x: int,
    elements_in_y: int,
) -> float:
    """Computes the dice coefficient between two sets."""
    return 2 * common_elements / (elements_in_x + elements_in_y)


def dice(
    root_x: Node,
    root_y: Node,
    mappings: NodeMappings,
) -> float:
    """Measures the ratio of common descendants between two nodes given a set of mappings."""

    def get_y_for_x(node_x: Node) -> Node:
        for node_x_, node_y in mappings:
            if node_x_ == node_x:
                return node_y
        error = f"no mapping found for {node_x.id_}"
        raise ValueError(error)

    def coefficient(
        common_elements: int,
        elements_in_x: int,
        elements_in_y: int,
    ) -> float:
        return 2 * common_elements / (elements_in_x + elements_in_y)

    descendants_x = set(root_x.descendants())
    descendants_y = set(root_y.descendants())

    mapped_x = {node for node, _ in mappings}
    mapped_descendants = 0

    for node_x in descendants_x:
        if node_x in mapped_x:
            node_y = get_y_for_x(node_x)
            if node_y in descendants_y:
                mapped_descendants += 1

    return coefficient(
        mapped_descendants,
        len(descendants_x),
        len(descendants_y),
    )


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
    matched_x = {node_x for node_x, _ in mappings}
    matched_y = {node_y for _, node_y in mappings}

    # to find the container mappings, the nodes of T1 are processed in postorder
    # for each unmatched non-leaf node of T1, we extract a list of candidate nodes from T2
    def visit(node: Node) -> None:
        if node in matched_x:
            return

        if isinstance(node, TerminalNode):
            return

        # A node c ∈ T2 is a candidate for t1 if label(t1) = label(c), c is unmatched, and t1
        # and c have some matching descendants.
        candidates: list[Node] = [
            node_y
            for node_y in root_y.nodes()
            if node_y not in matched_y and type(node) == type(node_y)
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

    # When two nodes matches, we finally apply an optimal algorithm to search for
    # additional mappings (called recovery mappings) among their descendants.
    # - uses RTED without move actions

    return mappings


def sanity_check_mappings(
    mappings: NodeMappings,
) -> None:
    mapped_from: set[Node] = set()
    mapped_to: set[Node] = set()

    for (node_from, node_to) in mappings:
        # both nodes must have identical labels
        assert type(node_from) == type(node_to)

        if node_from in mapped_from:
            error = f"source node {node_from.__class__.__name__}({node_from.id_}) already mapped"
            raise ValueError(error)
        mapped_from.add(node_from)

        if node_to in mapped_to:
            error = f"destination node {node_to.__class__.__name__}({node_to.id_}) already mapped"
            raise ValueError(error)
        mapped_to.add(node_to)


def compute_gumtree_mappings(
    root_x: Node,
    root_y: Node,
    *,
    min_height: int = 2,
    min_dice: float = 0.5,
) -> NodeMappings:
    """Uses the GumTree algorithm to map nodes between two trees."""
    mappings = compute_topdown_mappings(root_x, root_y, min_height=min_height)
    logger.trace(
        "sanity checking top-down mappings:\n{}",
        "\n".join(f"* {node_from.id_} -> {node_to.id_}" for (node_from, node_to) in mappings),
    )
    sanity_check_mappings(mappings)

    mappings = compute_bottom_up_mappings(root_x, root_y, mappings, min_dice=min_dice)
    logger.trace(
        "sanity checking complete mappings:\n{}",
        "\n".join(f"* {node_from.id_} -> {node_to.id_}" for (node_from, node_to) in mappings),
    )
    sanity_check_mappings(mappings)

    return mappings
