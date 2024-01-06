from __future__ import annotations

import typing as t

from loguru import logger

from facilitate.edit import (
    EditScript,
    Update,
)
from facilitate.gumtree import compute_gumtree_mappings
from facilitate.model.sequence import Sequence

if t.TYPE_CHECKING:
    from facilitate.model.node import Node


def compute_edit_script(
    tree_from: Node,
    tree_to: Node,
) -> EditScript:
    """Computes an edit script to transform one tree into another."""
    script = EditScript()
    new_mappings = compute_gumtree_mappings(tree_from, tree_to)
    mappings = new_mappings.as_tuples()

    nodes_from = set(tree_from.nodes())
    matched_nodes_from = {node_from for node_from, _ in mappings}
    _unmatched_nodes_from = nodes_from - matched_nodes_from

    nodes_to = set(tree_to.nodes())
    matched_nodes_to = {node_to for _, node_to in mappings}
    unmatched_nodes_to = nodes_to - matched_nodes_to

    logger.trace(
        "matched nodes:\n{}",
        "\n".join(f"* {node_from.id_} -> {node_to.id_}" for (node_from, node_to) in mappings),
    )

    # update phase:
    # - look for pairs (x, y) where their values differ
    # - for each such pair, create an update edit: x -> y
    for (node_from, node_to) in mappings:
        maybe_update = Update.compute(node_from, node_to)
        if maybe_update:
            script.append(maybe_update)

    # align phase:
    # - check each pair (x, y) to see if their children are misaligned
    # - create a move edit to align them if so
    #
    # note that, within the context of Scratch, this is only possible for sequences
    #
    # children of x and y are misaligned if:
    # - x has matched children u and v
    # - u is to the left of v in x but the partner of u is to the right of the partner of v in y
    for (_node_from, _node_to) in mappings:
        if not isinstance(_node_from, Sequence):
            continue
        assert isinstance(_node_to, Sequence)

        _indexed_children_from = list(enumerate(_node_from.blocks))
        _indexed_children_to = list(enumerate(_node_to.blocks))

        raise NotImplementedError

    # (3) insert phase
    # look for nodes in tree_to that are unmatched but have a matched parent
    for node in unmatched_nodes_to:
        if node.parent not in matched_nodes_to:
            continue
        print(f"create Insert({node.__class__.__name__}) for {node.id_}")
        raise NotImplementedError

    # (4) move phase
    # - look for matched pairs (x, y) for which (p(x), p(y)) is not matched,
    #   where p(x) is the parent of x

    # (5) delete phase
    # - look for unmatched leaf nodes in tree_from
    for _node in tree_from.postorder():
        pass

    raise NotImplementedError

    # TODO ensure that edit script works!

    return script
