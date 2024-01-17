from __future__ import annotations

import typing as t

from facilitate.algorithms import breadth_first_search
from facilitate.edit import (
    AddBlockToInput,
    AddBlockToSequence,
    AddFieldToBlock,
    AddInputToBlock,
    Addition,
    AddLiteralToInput,
    Delete,
    EditScript,
    Update,
)
from facilitate.gumtree import compute_gumtree_mappings
from facilitate.model.block import Block
from facilitate.model.field import Field
from facilitate.model.input import Input
from facilitate.model.literal import Literal
from facilitate.model.sequence import Sequence

if t.TYPE_CHECKING:
    from facilitate.mappings import NodeMappings
    from facilitate.model.node import Node


def _find_insertion_position(
    tree_from: Node,
    tree_to: Node,
    missing_block: Block,
    mappings: NodeMappings,
) -> int:
    parent_to = missing_block.parent
    assert parent_to is not None
    parent_from = mappings.destination_is_mapped_to(parent_to)
    assert parent_from is not None
    assert isinstance(parent_from, Sequence)
    assert isinstance(parent_to, Sequence)

    missing_block_position = parent_to.position_of_block(missing_block)

    if missing_block_position == 0:
        return 0

    node_before_missing_block = parent_to.blocks[missing_block_position - 1]
    insert_after_node = mappings.destination_is_mapped_to(node_before_missing_block)
    assert insert_after_node is not None
    assert isinstance(insert_after_node, Block)
    return parent_from.position_of_block(insert_after_node) + 1


def _insert_missing_node(
    tree_from: Node,
    tree_to: Node,
    missing_node: Node,
    mappings: NodeMappings,
) -> Addition:
    assert missing_node.parent is not None
    parent = mappings.destination_is_mapped_to(missing_node.parent)
    assert parent is not None

    if isinstance(missing_node, Input):
        assert isinstance(parent, Block)
        return AddInputToBlock(
            block_id=parent.id_,
            name=missing_node.name,
        )

    if isinstance(missing_node, Field):
        assert isinstance(parent, Block)
        return AddFieldToBlock(
            block_id=parent.id_,
            name=missing_node.name,
            value=missing_node.value,
        )

    if isinstance(missing_node, Literal) and isinstance(parent, Input):
        return AddLiteralToInput(
            input_id=parent.id_,
            value=missing_node.value,
        )

    if isinstance(missing_node, Block) and isinstance(parent, Sequence):
        position = _find_insertion_position(
            tree_from=tree_from,
            tree_to=tree_to,
            missing_block=missing_node,
            mappings=mappings,
        )
        return AddBlockToSequence(
            sequence_id=parent.id_,
            block_id=missing_node.id_,
            position=position,
            opcode=missing_node.opcode,
            is_shadow=missing_node.is_shadow,
        )

    if isinstance(missing_node, Block) and isinstance(parent, Input):
        return AddBlockToInput(
            input_id=parent.id_,
            block_id=missing_node.id_,
            opcode=missing_node.opcode,
            is_shadow=missing_node.is_shadow,
        )

    raise NotImplementedError


def update_insert_align_move_phase(
    tree_from: Node,
    tree_to: Node,
    mappings: NodeMappings,
) -> EditScript:
    script = EditScript()

    for node_to in breadth_first_search(tree_to):
        _maybe_node_from = mappings.destination_is_mapped_to(node_to)

        if not _maybe_node_from:
            insertion = _insert_missing_node(
                tree_from=tree_from,
                tree_to=tree_to,
                missing_node=node_to,
                mappings=mappings,
            )
            added_node = insertion.apply(tree_from)
            assert added_node is not None
            script.append(insertion)
            mappings.add(added_node, node_to)

        else:
            if not _maybe_node_from.surface_equivalent_to(node_to):
                update = Update.compute(_maybe_node_from, node_to)
                assert update is not None
                script.append(update)

            parent_from = _maybe_node_from.parent
            parent_to = node_to.parent
            if parent_from is None or parent_to is None:
                continue

            # move stage
            if (parent_from, parent_to) not in mappings:
                print("TODO create move")

        # align stage

    return script



def compute_edit_script(
    tree_from: Node,
    tree_to: Node,
) -> EditScript:
    """Computes an edit script to transform one tree into another."""
    script = EditScript()
    mappings = compute_gumtree_mappings(tree_from, tree_to)

    update_insert_align_move_phase(tree_from, tree_to, mappings)

    return script

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

    # delete phase
    for node_ in tree_from.postorder():
        if not mappings.source_is_mapped(node_):
            edit = Delete(node_id=node_.id_)
            edit.apply(tree_from)
            script.append(edit)

    # TODO ensure that edit script works!

    return script
