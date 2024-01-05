from __future__ import annotations

import typing as t

from facilitate.edit import (
    EditScript,
    Update,
)
from facilitate.gumtree import compute_gumtree_mappings

if t.TYPE_CHECKING:
    from facilitate.model import Node


def compute_edit_script(
    tree_from: Node,
    tree_to: Node,
) -> EditScript:
    """Computes an edit script to transform one tree into another."""
    script = EditScript()
    mappings = compute_gumtree_mappings(tree_from, tree_to)

    nodes_from = set(tree_from.nodes())
    matched_nodes_from = {node_from for node_from, _ in mappings}
    unmatched_nodes_from = nodes_from - matched_nodes_from

    nodes_to = set(tree_to.nodes())
    matched_nodes_to = {node_to for _, node_to in mappings}
    unmatched_nodes_to = nodes_to - matched_nodes_to

    # update phase:
    # - look for pairs (x, y) where their values differ
    # - for each such pair, create an update edit: x -> y
    for (node_from, node_to) in mappings:

        print(f"considering {node_from.id_} -> {node_to.id_}")
        print(f"- {node_from.__class__.__name__} -> {node_to.__class__.__name__}")

        maybe_update = Update.compute(node_from, node_to)
        if maybe_update:
            print(f"created Update: {maybe_update}")
            script.append(maybe_update)

    # align phase:
    # - check each pair (x, y) to see if their children are misaligned
    # - create a move edit to align them if so
    #
    # FIXME children of x and y are misaligned if:
    # ...
    for (node_from, node_to) in mappings:
        # We say that the children of x and y are misaligned if x has matched children u and v
        # such that u is to the left of v in T1 but the partner of u is to the right of the partner of v in T2
        pass

    # (3) insert phase
    # look for nodes in tree_to that are unmatched but have a matched parent
    for node in unmatched_nodes_to:
        if node.parent not in matched_nodes_to:
            continue
        print(f"create Insert({node.__class__.__name__}) for {node.id_}")

    # (4) move phase
    # (5) delete phase

    raise NotImplementedError

    # TODO ensure that edit script works!

    return script
