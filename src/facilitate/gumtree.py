from __future__ import annotations

import functools
import typing as t
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import product

from loguru import logger

from facilitate.mappings import NodeMappings

if t.TYPE_CHECKING:
    from facilitate.model.node import Node


@dataclass
class HeightIndexedPriorityList:
    _height_to_nodes: dict[int, list[Node]] = field(
        default_factory=functools.partial(defaultdict, list),
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
        self._height_to_nodes[node.height].append(node)

    def pop(self) -> list[Node]:
        """Removes and returns the set of nodes with maximal height."""
        max_height = self.peek_max()
        nodes = self._height_to_nodes[max_height]
        del self._height_to_nodes[max_height]
        return nodes

    def add_children(self, node: Node) -> None:
        """Inserts all children of given node into the list."""
        for child in node.children():
            self.push(child)


def dice(
    root_x: Node,
    root_y: Node,
    mappings: NodeMappings,
) -> float:
    """Measures the ratio of common descendants between two nodes given a set of mappings."""
    def coefficient(
        common_elements: int,
        elements_in_x: int,
        elements_in_y: int,
    ) -> float:
        return 2 * common_elements / (elements_in_x + elements_in_y)

    descendants_x = set(root_x.descendants())
    descendants_y = set(root_y.descendants())

    mapped_descendants = 0

    for node_x in descendants_x:
        node_y = mappings.source_is_mapped_to(node_x)
        if node_y and node_y in descendants_y:
            mapped_descendants += 1

    num_descendants_x = len(descendants_x)
    num_descendants_y = len(descendants_y)
    num_descendants_total = num_descendants_x + num_descendants_y

    if num_descendants_total == 0:
        return 1 if root_x.id_ == root_y.id_ else 0

    score = coefficient(
        mapped_descendants,
        num_descendants_x,
        num_descendants_y,
    )

    # prefer nodes with the same ID
    if root_x.id_ == root_y.id_:
        score *= 2

    logger.trace(
        f"dice(common={mapped_descendants}, x={num_descendants_x}, y={num_descendants_y})"
        f" = {score:.2f} @ ({root_x.id_}, {root_y.id_})",
    )
    return score


def compute_topdown_mappings(
    root_x: Node,
    root_y: Node,
    *,
    min_height: int = 1,
) -> NodeMappings:
    mappings = NodeMappings()
    candidates: list[tuple[Node, Node]] = []

    hlist_x = HeightIndexedPriorityList()
    hlist_x.push(root_x)

    hlist_y = HeightIndexedPriorityList()
    hlist_y.push(root_y)

    nodes_x = list(root_x.nodes())
    nodes_y = list(root_y.nodes())

    while True:
        min_max_height = min(hlist_x.max_height, hlist_y.max_height)
        if min_max_height < min_height:
            break
        logger.debug(f"max height x vs. y: {hlist_x.max_height} vs. {hlist_y.max_height}")

        if hlist_x.max_height > hlist_y.max_height:
            for node in hlist_x.pop():
                hlist_x.add_children(node)
        elif hlist_x.max_height < hlist_y.max_height:
            for node in hlist_y.pop():
                hlist_y.add_children(node)
        else:
            max_height_nodes_x = hlist_x.pop()
            max_height_nodes_y = hlist_y.pop()

            logger.debug(
                f"max height nodes x: {", ".join(node.id_ for node in max_height_nodes_x)}",
            )
            logger.debug(
                f"max height nodes y: {", ".join(node.id_ for node in max_height_nodes_y)}",
            )

            added_trees_x: list[Node] = []
            added_trees_y: list[Node] = []

            for node_x, node_y in product(max_height_nodes_x, max_height_nodes_y):
                if node_x.equivalent_to(node_y):
                    logger.debug(f"equivalent: {node_x.id_} vs. {node_y.id_}")

                    # FIXME these queries can be cached
                    # is there more than one possible match for either node?
                    match_x = any(node.equivalent_to(node_y) and node != node_x for node in nodes_x)
                    match_y = any(node.equivalent_to(node_x) and node != node_y for node in nodes_y)

                    if match_x or match_y:
                        logger.debug(f"candidate match: {node_x.id_} vs. {node_y.id_}")
                        candidates.append((node_x, node_y))
                    else:
                        logger.debug(f"isolated match: {node_x.id_} vs. {node_y.id_}")
                        mappings.add(node_x, node_y)

                    added_trees_x.append(node_x)
                    added_trees_y.append(node_y)

            for node in max_height_nodes_x:
                if node not in added_trees_x:
                    hlist_x.add_children(node)

            for node in max_height_nodes_y:
                if node not in added_trees_y:
                    hlist_y.add_children(node)

    def sort_key(map_entry: tuple[Node, Node]) -> float:
        node_x, node_y = map_entry
        score = dice(node_x, node_y, mappings)
        logger.trace(f"score [{node_x.id_} -> {node_y.id_}]: {score}")
        return score

    candidates.sort(key=sort_key)

    logger.debug(
        "sorted candidates:\n{}",
        "\n".join(f"* {node_x.id_} -> {node_y.id_}" for (node_x, node_y) in candidates),
    )

    while candidates:
        node_x, node_y = candidates.pop(0)
        mappings.add_with_descendants(node_x, node_y)
        candidates = [
            (from_x, to_y)
            for from_x, to_y in candidates
            if from_x != node_x and to_y != node_y
        ]

    return mappings


def compute_bottom_up_mappings(
    root_x: Node,
    root_y: Node,
    mappings: NodeMappings,
    *,
    min_dice: float = 0.5,
) -> NodeMappings:
    # to find the container mappings, the nodes of T1 are processed in postorder
    # for each unmatched non-leaf node of T1, we extract a list of candidate nodes from T2
    def visit(node: Node) -> None:
        if mappings.source_is_mapped(node):
            return

        if not node.has_children():
            return

        # A node c ∈ T2 is a candidate for t1 if label(t1) = label(c), c is unmatched, and t1
        # and c have some matching descendants.
        candidates: list[Node] = [
            node_y
            for node_y in root_y.nodes()
            if not mappings.destination_is_mapped(node_y) and type(node) == type(node_y)
        ]

        if not candidates:
            return

        candidates.sort(
            key=lambda node_y: dice(node, node_y, mappings),
            reverse=True,
        )
        top_candidate = candidates[0]

        if dice(node, top_candidate, mappings) > min_dice:
            mappings.add(node, top_candidate)

    for node in root_x.postorder():
        visit(node)

    # When two nodes matches, we finally apply an optimal algorithm to search for
    # additional mappings (called recovery mappings) among their descendants.
    # - uses RTED without move actions

    return mappings


def compute_gumtree_mappings(
    root_x: Node,
    root_y: Node,
    *,
    min_height: int = 1,
    min_dice: float = 0.5,
) -> NodeMappings:
    """Uses the GumTree algorithm to map nodes between two trees."""
    mappings = compute_topdown_mappings(root_x, root_y, min_height=min_height)
    logger.trace(
        "sanity checking top-down mappings:\n{}",
        "\n".join(f"* {node_from.id_} -> {node_to.id_}" for (node_from, node_to) in mappings),
    )
    mappings.check()

    mappings = compute_bottom_up_mappings(root_x, root_y, mappings, min_dice=min_dice)
    logger.trace(
        "sanity checking complete mappings:\n{}",
        "\n".join(f"* {node_from.id_} -> {node_to.id_}" for (node_from, node_to) in mappings),
    )
    mappings.check()

    return mappings
