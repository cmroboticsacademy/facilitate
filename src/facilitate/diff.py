from __future__ import annotations

import typing as t

from loguru import logger

from facilitate.algorithms import breadth_first_search
from facilitate.edit import (
    AddBlockToInput,
    AddBlockToSequence,
    AddFieldToBlock,
    AddInputToBlock,
    Addition,
    AddLiteralToInput,
    AddSequenceToInput,
    AddSequenceToProgram,
    Delete,
    Edit,
    EditScript,
    MoveBlockInSequence,
    MoveBlockToSequence,
    MoveFieldToBlock,
    MoveInputToBlock,
    MoveNodeToInput,
    MoveSequenceInProgram,
    MoveSequenceToProgram,
    Update,
)
from facilitate.gumtree import compute_gumtree_mappings
from facilitate.model.block import Block
from facilitate.model.field import Field
from facilitate.model.input import Input
from facilitate.model.literal import Literal
from facilitate.model.program import Program
from facilitate.model.sequence import Sequence
from facilitate.util import longest_common_subsequence

if t.TYPE_CHECKING:
    from facilitate.mappings import NodeMappings
    from facilitate.model.node import Node


def _find_insertion_position(
    missing_node: Node,
    mappings: NodeMappings,
) -> int:
    logger.debug("finding insertion position for {}", missing_node.id_)

    parent_to = missing_node.parent
    assert parent_to is not None
    assert isinstance(parent_to, Program | Sequence)

    parent_from = mappings.destination_is_mapped_to(parent_to)
    assert parent_from is not None
    assert isinstance(parent_from, Program | Sequence)

    missing_node_position = parent_to.position_of_child(missing_node)

    if missing_node_position == 0:
        return 0

    logger.debug("missing node position: {}", missing_node_position)

    # it's possible that the node before the missing node hasn't been mapped,
    # so we need to work leftwards until we find a mapped node
    # if we fail to find a mapped node, we return zero as the index
    for node_before_position in range(missing_node_position - 1, -1, -1):
        node_before_missing = parent_to.child(node_before_position)
        insert_after_node = mappings.destination_is_mapped_to(node_before_missing)
        if insert_after_node is not None and insert_after_node.parent == parent_from:
            return parent_from.position_of_child(insert_after_node) + 1

    return 0


def _align_children(
    script: EditScript,
    tree_from: Node,
    parent_from: Sequence | Program,
    parent_to: Sequence | Program,
    mappings: NodeMappings,
) -> None:
    """Aligns the children of two nodes."""
    logger.debug("aligning children of {} and {}", parent_from.id_, parent_to.id_)

    def equals(x: Node, y: Node) -> bool:
        return (x, y) in mappings

    # sequence of children of (parent_from) whose partners are children of (parent_to)
    mapped_node_from_children = [
        child for child in parent_from.children() if mappings.source_is_mapped(child)
    ]
    mapped_node_from_children = [
        child for child in mapped_node_from_children if mappings.source_is_mapped_to(child).parent == parent_to  # type: ignore
    ]

    # sequence of children of (parent_to) whose partners are children of (parent_from)
    mapped_node_to_children = [
        child for child in parent_to.children() if mappings.destination_is_mapped(child)
    ]
    mapped_node_to_children = [
        child for child in mapped_node_to_children if mappings.destination_is_mapped_to(child).parent == parent_from  # type: ignore
    ]

    logger.debug(
        f"mapped node from children [{len(mapped_node_from_children)}]: "
        f"{', '.join(block.id_ for block in mapped_node_from_children)}",
    )
    logger.debug(
        f"mapped node to children [{len(mapped_node_to_children)}]: "
        f"{', '.join(block.id_ for block in mapped_node_to_children)}",
    )

    lcs: list[tuple[Node, Node]] = longest_common_subsequence(
        mapped_node_from_children,
        mapped_node_to_children,
        equals,
    )
    lcs_node_to: list[Node] = [y for (_, y) in lcs]
    logger.debug(f"lcs (node to) [{len(lcs_node_to)}]: {', '.join(child.id_ for child in lcs_node_to)}")

    for b in mapped_node_to_children:
        if b in lcs_node_to:
            continue

        a = mappings.destination_is_mapped_to(b)
        assert a is not None

        if a not in mapped_node_from_children:
            continue

        position = _find_insertion_position(
            missing_node=b,
            mappings=mappings,
        )

        move: Edit
        if isinstance(parent_to, Sequence):
            assert isinstance(a, Block)
            move = MoveBlockInSequence(
                sequence_id=parent_from.id_,
                block_id=a.id_,
                position=position,
            )
        elif isinstance(parent_to, Program):
            assert isinstance(a, Sequence)
            move = MoveSequenceInProgram(
                sequence_id=a.id_,
                position=position,
            )
        else:
            error = f"unexpected parent type: {parent_to.__class__.__name__}"
            raise TypeError(error)

        script.append(move)
        move.apply(tree_from)


def _compute_move_position(
    move_node: Node,
    move_to_parent: Program | Sequence,
    mappings: NodeMappings,
) -> int:
    position = 0
    partner = mappings.source_is_mapped_to(move_node)
    assert partner is not None
    partner_parent = partner.parent
    assert isinstance(partner_parent, Program | Sequence)

    move_to_parent_children = list(move_to_parent.children())

    partner_position = partner_parent.position_of_child(partner)
    partner_children = list(partner_parent.children())

    for partner_insert_at_position in range(partner_position - 1, -1, -1):
        partner_insert_after_node = partner_children[partner_insert_at_position]
        insert_after_node = mappings.destination_is_mapped_to(partner_insert_after_node)
        if insert_after_node is not None:
            position = move_to_parent_children.index(insert_after_node) + 1
            break

    return position


def _move_block_to_input(
    *,
    move_block: Block,
    move_to_parent: Input,
) -> MoveNodeToInput:
    parent_block = move_to_parent.parent
    assert isinstance(parent_block, Block)
    return MoveNodeToInput(
        node_id=move_block.id_,
        parent_block_id=parent_block.id_,
        input_name=move_to_parent.name,
    )


def _move_block(
    *,
    move_block: Block,
    move_block_partner: Block,
    move_block_partner_parent: Node,
    move_from_parent: Node,
    move_to_parent: Node,
    mappings: NodeMappings,
) -> Edit:
    if isinstance(move_to_parent, Input):
        return _move_block_to_input(
            move_block=move_block,
            move_to_parent=move_to_parent,
        )

    if isinstance(move_to_parent, Sequence):
        assert isinstance(move_to_parent, Sequence)
        assert isinstance(move_block_partner_parent, Sequence)

        position = 0
        partner_position = move_block_partner_parent.position_of_block(move_block_partner)

        for partner_insert_at_position in range(partner_position - 1, -1, -1):
            partner_insert_after_node = move_block_partner_parent.blocks[partner_insert_at_position]
            insert_after_node = mappings.destination_is_mapped_to(partner_insert_after_node)
            if insert_after_node is not None:
                assert isinstance(insert_after_node, Block)
                position = move_to_parent.position_of_block(insert_after_node) + 1
                break

        return MoveBlockToSequence(
            block_id=move_block.id_,
            sequence_id=move_to_parent.id_,
            position=position,
        )

    error = f"unexpected move of Block to parent: {move_to_parent.__class__.__name__}"
    raise ValueError(error)


def _move_input(
    *,
    move_input: Input,
    move_from_parent: Node,
    move_to_parent: Node,
) -> Edit:
    assert isinstance(move_from_parent, Block)
    assert isinstance(move_to_parent, Block)
    return MoveInputToBlock(
        move_from_block_id=move_from_parent.id_,
        move_to_block_id=move_to_parent.id_,
        # NOTE is this dangerous?
        input_id=move_input.id_,
    )


def _move_field(
    *,
    move_field: Field,
    move_from_parent: Node,
    move_to_parent: Node,
) -> Edit:
    assert isinstance(move_from_parent, Block)
    assert isinstance(move_to_parent, Block)
    return MoveFieldToBlock(
        move_from_block_id=move_from_parent.id_,
        move_to_block_id=move_to_parent.id_,
        # NOTE is this dangerous?
        field_id=move_field.id_,
    )


def _move_literal(
    *,
    move_literal: Literal,
    move_to_parent: Node,
) -> Edit:
    if isinstance(move_to_parent, Input):
        parent_block = move_to_parent.parent
        assert isinstance(parent_block, Block)
        return MoveNodeToInput(
            node_id=move_literal.id_,
            parent_block_id=parent_block.id_,
            input_name=move_to_parent.name,
        )

    error = f"unexpected move of Literal to parent: {move_to_parent.__class__.__name__}"
    raise ValueError(error)


def _move_sequence(
    *,
    move_sequence: Sequence,
    move_to_parent: Node,
    mappings: NodeMappings,
) -> Edit:
    if isinstance(move_to_parent, Input):
        parent_block = move_to_parent.parent
        assert isinstance(parent_block, Block)
        return MoveNodeToInput(
            node_id=move_sequence.id_,
            parent_block_id=parent_block.id_,
            input_name=move_to_parent.name,
        )

    if isinstance(move_to_parent, Program):
        if move_sequence.parent == move_to_parent:
            error = "sequence is already a child of the program"
            raise ValueError(error)

        position = _compute_move_position(
            move_node=move_sequence,
            move_to_parent=move_to_parent,
            mappings=mappings,
        )

        return MoveSequenceToProgram(
            sequence_id=move_sequence.id_,
            position=position,
        )

    error = f"unexpected move of Sequence to parent: {move_to_parent.__class__.__name__}"
    raise TypeError(error)


def _move_node(
    tree_from: Node,
    tree_to: Node,
    move_node: Node,
    move_node_partner: Node,
    mappings: NodeMappings,
) -> Edit:
    logger.debug("moving node: {} {}", move_node.id_, move_node.__class__.__name__)

    assert tree_from.contains(move_node)
    assert tree_to.contains(move_node_partner)

    move_from_parent = move_node.parent
    assert move_from_parent is not None
    logger.debug("moving from parent: {} {}", move_from_parent.id_, move_from_parent.__class__.__name__)

    move_node_partner_parent = move_node_partner.parent
    assert move_node_partner_parent is not None
    move_to_parent = mappings.destination_is_mapped_to(move_node_partner_parent)
    assert move_to_parent is not None
    logger.debug(f"moving to parent: {move_to_parent.id_} {move_to_parent.__class__.__name__}")

    if isinstance(move_node, Input):
        return _move_input(
            move_input=move_node,
            move_from_parent=move_from_parent,
            move_to_parent=move_to_parent,
        )

    if isinstance(move_node, Field):
        return _move_field(
            move_field=move_node,
            move_from_parent=move_from_parent,
            move_to_parent=move_to_parent,
        )

    if isinstance(move_node, Block):
        assert isinstance(move_node_partner, Block)
        return _move_block(
            move_block=move_node,
            move_block_partner=move_node_partner,
            move_block_partner_parent=move_node_partner_parent,
            move_from_parent=move_from_parent,
            move_to_parent=move_to_parent,
            mappings=mappings,
        )

    if isinstance(move_node, Sequence):
        assert isinstance(move_node_partner, Sequence)
        return _move_sequence(
            move_sequence=move_node,
            move_to_parent=move_to_parent,
            mappings=mappings,
        )

    if isinstance(move_node, Literal):
        assert isinstance(move_node_partner, Literal)
        return _move_literal(
            move_literal=move_node,
            move_to_parent=move_to_parent,
        )

    error = f"unexpected node type: {move_node.__class__.__name__}"
    raise ValueError(error)


def _insert_missing_node(
    tree_from: Node,
    tree_to: Node,
    missing_node: Node,
    mappings: NodeMappings,
) -> Addition:
    logger.debug(
        "inserting missing node: {} {}",
        missing_node.id_,
        missing_node.__class__.__name__,
    )
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
            missing_node=missing_node,
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
            opcode=missing_node.opcode,
            is_shadow=missing_node.is_shadow,
        )

    if isinstance(missing_node, Sequence) and isinstance(parent, Input):
        block = parent.parent
        assert isinstance(block, Block)
        return AddSequenceToInput(
            block_id=block.id_,
            input_name=parent.name,
        )

    if isinstance(missing_node, Sequence) and isinstance(parent, Program):
        position = _find_insertion_position(
            missing_node=missing_node,
            mappings=mappings,
        )
        return AddSequenceToProgram(
            position=position,
        )

    logger.error(
        "missing node: {}<{}>; parent: {}<{}>",
        missing_node.__class__.__name__,
        missing_node.id_,
        parent.__class__.__name__,
        parent.id_,
    )
    raise NotImplementedError


def delete_phase(
    script: EditScript,
    tree_from: Node,
    mappings: NodeMappings,
) -> EditScript:
    for node_ in tree_from.postorder():
        if not mappings.source_is_mapped(node_):
            edit = Delete(node_id=node_.id_)
            edit.apply(tree_from)
            script.append(edit)
    return script


def update_insert_align_move_phase(
    tree_from: Node,
    tree_to: Node,
    mappings: NodeMappings,
) -> EditScript:
    script = EditScript()

    for node_to in breadth_first_search(tree_to):
        logger.debug(f"processing node: {node_to.id_} {node_to.__class__.__name__}")

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
                update.apply(tree_from)
                script.append(update)

            parent_from = _maybe_node_from.parent
            parent_to = node_to.parent

            # move stage
            # - if the parents of the node and its partner are not mapped, move the node
            if parent_from is not None and parent_to is not None:  # noqa: SIM102
                if (parent_from, parent_to) not in mappings:
                    edit = _move_node(
                        tree_from=tree_from,
                        tree_to=tree_to,
                        move_node=_maybe_node_from,
                        move_node_partner=node_to,
                        mappings=mappings,
                    )
                    edit.apply(tree_from)
                    script.append(edit)

            # align stage
            if isinstance(_maybe_node_from, Sequence | Program):
                assert isinstance(node_to, Sequence | Program)
                _align_children(
                    script=script,
                    tree_from=tree_from,
                    parent_from=_maybe_node_from,
                    parent_to=node_to,
                    mappings=mappings,
                )

    return script


def compute_edit_script(
    tree_from: Node,
    tree_to: Node,
) -> EditScript:
    """Computes an edit script to transform one tree into another."""
    tree_from = tree_from.copy()
    tree_to = tree_to.copy()

    mappings = compute_gumtree_mappings(tree_from, tree_to)
    logger.debug("mappings: {}", mappings)

    script = update_insert_align_move_phase(tree_from, tree_to, mappings)
    delete_phase(
        script=script,
        tree_from=tree_from,
        mappings=mappings,
    )

    assert tree_from.equivalent_to(tree_to)

    return script
