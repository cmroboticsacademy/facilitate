"""Computes weighted distances from edit scripts."""
from __future__ import annotations

from facilitate.diff import compute_edit_script
from facilitate.edit import (
    AddBlockToInput,
    AddBlockToSequence,
    AddFieldToBlock,
    AddInputToBlock,
    Addition,
    AddSequenceToInput,
    AddSequenceToProgram,
    Delete,
    EditScript,
    Move,
    MoveBlockInSequence,
    MoveBlockToSequence,
    MoveFieldToBlock,
    MoveInputToBlock,
    MoveNodeToInput,
    MoveSequenceInProgram,
    MoveSequenceToProgram,
    Update,
)
from facilitate.model.block import Block
from facilitate.model.field import Field
from facilitate.model.input import Input
from facilitate.model.literal import Literal
from facilitate.model.program import Program
from facilitate.model.sequence import Sequence

DELETE_BLOCK_COST = 0.5
DELETE_FIELD_COST = 0.0
DELETE_INPUT_COST = 0.0
DELETE_LITERAL_COST = 0.5
DELETE_SEQUENCE_COST = 0.5

INSERT_BLOCK_COST = 1.0
INSERT_SEQUENCE_COST = 1.0
INSERT_FIELD_COST = 0.0
INSERT_INPUT_COST = 0.0

MOVE_BLOCK_IN_SEQUENCE_COST = 0.5
MOVE_BLOCK_TO_SEQUENCE_COST = 1.0
MOVE_FIELD_TO_BLOCK_COST = 0.0
MOVE_INPUT_TO_BLOCK_COST = 0.0
MOVE_NODE_TO_INPUT_COST = 0.5
MOVE_SEQUENCE_IN_PROGRAM_COST = 0.5
MOVE_SEQUENCE_TO_PROGRAM_COST = 1.0
MOVE_OTHER_COST = 0.5

UPDATE_LITERAL_COST = 0.5
UPDATE_BLOCK_COST = 1.0


def _compute_update_costs(
    tree_from: Program,
    edit_script: EditScript,
) -> float:
    """Computes the cost of all updates within a given edit script."""
    cost = 0.0

    updates: list[Update] = [edit for edit in edit_script if isinstance(edit, Update)]
    for update in updates:
        node = tree_from.find(update.node_id)
        assert node is not None

        match node:
            case Block():
                cost += UPDATE_BLOCK_COST
            case Literal():
                cost += UPDATE_LITERAL_COST

    return cost


def _compute_move_costs(edit_script: EditScript) -> float:
    cost = 0.0

    for edit in edit_script:
        match edit:
            case MoveBlockInSequence():
                cost += MOVE_BLOCK_IN_SEQUENCE_COST
            case MoveBlockToSequence():
                cost += MOVE_BLOCK_TO_SEQUENCE_COST
            case MoveFieldToBlock():
                cost += MOVE_FIELD_TO_BLOCK_COST
            case MoveInputToBlock():
                cost += MOVE_INPUT_TO_BLOCK_COST
            case MoveNodeToInput():
                cost += MOVE_NODE_TO_INPUT_COST
            case MoveSequenceInProgram():
                cost += MOVE_SEQUENCE_IN_PROGRAM_COST
            case MoveSequenceToProgram():
                cost += MOVE_SEQUENCE_TO_PROGRAM_COST
            case Move():
                cost += MOVE_OTHER_COST

    return cost


def _compute_deletion_costs(
    tree_from: Program,
    edit_script: EditScript,
) -> float:
    """Computes the cost of all deletions within a given edit script."""
    cost = 0.0

    deletions: list[Delete] = [edit for edit in edit_script if isinstance(edit, Delete)]
    for deletion in deletions:
        node = tree_from.find(deletion.node_id)
        assert node is not None

        match node:
            case Block():
                cost += DELETE_BLOCK_COST
            case Sequence():
                cost += DELETE_SEQUENCE_COST
            case Literal():
                cost += DELETE_LITERAL_COST
            case Field():
                cost += DELETE_FIELD_COST
            case Input():
                cost += DELETE_INPUT_COST

    return cost


def _compute_insertion_costs(
    edit_script: EditScript,
) -> float:
    """Computes the cost of all insertions within a given edit script."""
    cost = 0.0

    insertions: list[Addition] = [edit for edit in edit_script if isinstance(edit, Addition)]
    for insertion in insertions:
        match insertion:
            case AddSequenceToProgram() | AddSequenceToInput():
                cost += INSERT_SEQUENCE_COST
            case AddBlockToInput() | AddBlockToSequence():
                cost += INSERT_BLOCK_COST
            case AddFieldToBlock():
                cost += INSERT_FIELD_COST
            case AddInputToBlock():
                cost += INSERT_INPUT_COST

    return cost


def compute_distance(
    *,
    tree_from: Program,
    edit_script: EditScript,
    tree_to: Program | None = None,
) -> float:
    """Computes the weighted distance of an edit script."""
    if tree_to is None:
        edited_tree = edit_script.apply(tree_from)
        assert isinstance(edited_tree, Program)
        tree_to = edited_tree
    assert tree_to is not None

    deletion_costs = _compute_deletion_costs(
        tree_from,
        edit_script,
    )
    insertion_costs = _compute_insertion_costs(edit_script)
    move_costs = _compute_move_costs(edit_script)
    update_costs = _compute_update_costs(
        tree_from,
        edit_script,
    )

    return deletion_costs + insertion_costs + update_costs + move_costs


def compute_edit_script_and_distance(
    tree_from: Program,
    tree_to: Program,
) -> tuple[EditScript, float]:
    """Computes the edit script and weighted distance between two trees."""
    edit_script = compute_edit_script(tree_from, tree_to)
    distance = compute_distance(
        tree_from=tree_from,
        tree_to=tree_to,
        edit_script=edit_script,
    )
    return edit_script, distance
