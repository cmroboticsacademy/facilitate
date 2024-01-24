from __future__ import annotations

import abc
import typing as t
from dataclasses import dataclass, field

from loguru import logger
from overrides import overrides

from facilitate.model.block import Block
from facilitate.model.field import Field
from facilitate.model.input import Input
from facilitate.model.literal import Literal
from facilitate.model.sequence import Sequence

if t.TYPE_CHECKING:
    from facilitate.model.node import Node


class Edit(abc.ABC):
    @abc.abstractmethod
    def apply(self, root: Node) -> Node | None:
        ...


class Addition(Edit):
    """Represents an additive edit."""


class Move(Edit):
    """Represents a move edit."""


@dataclass(frozen=True, kw_only=True)
class AddInputToBlock(Addition):
    """Inserts a (bare) named input into a block."""
    block_id: str
    name: str

    @overrides
    def apply(self, root: Node) -> Node | None:
        """Inserts and returns the given input."""
        parent = root.find(self.block_id)
        assert isinstance(parent, Block)
        return parent.add_input(self.name)


@dataclass(frozen=True, kw_only=True)
class AddLiteralToInput(Addition):
    """Inserts a literal into an input."""
    input_id: str
    value: str

    @overrides
    def apply(self, root: Node) -> Node | None:
        """Inserts and returns the given literal."""
        parent = root.find(self.input_id)
        assert isinstance(parent, Input)
        return parent.add_literal(self.value)


@dataclass(frozen=True, kw_only=True)
class AddBlockToSequence(Addition):
    """Inserts a block into a sequence."""
    sequence_id: str
    block_id: str
    position: int
    opcode: str
    is_shadow: bool

    @overrides
    def apply(self, root: Node) -> Node | None:
        """Inserts and returns the given block."""
        parent = root.find(self.sequence_id)
        assert isinstance(parent, Sequence)
        return parent.insert_block(
            id_=self.block_id,
            opcode=self.opcode,
            is_shadow=self.is_shadow,
            position=self.position,
        )


@dataclass(frozen=True, kw_only=True)
class AddBlockToInput(Addition):
    """Inserts a block into an input as an expression."""
    input_id: str
    block_id: str
    opcode: str
    is_shadow: bool

    @overrides
    def apply(self, root: Node) -> Node | None:
        """Inserts and returns the given block."""
        parent = root.find(self.input_id)
        assert isinstance(parent, Input)
        block = Block(
            id_=self.block_id,
            opcode=self.opcode,
            is_shadow=self.is_shadow,
        )
        block.parent = parent
        parent.expression = block
        return block


@dataclass(frozen=True, kw_only=True)
class AddFieldToBlock(Addition):
    """Inserts a named field into a block."""
    block_id: str
    name: str
    value: str

    @overrides
    def apply(self, root: Node) -> Node | None:
        """Inserts and returns the given field."""
        parent = root.find(self.block_id)
        assert isinstance(parent, Block)
        return parent.add_field(self.name, self.value)


@dataclass(frozen=True, kw_only=True)
class MoveFieldToBlock(Move):
    move_from_block_id: str
    move_to_block_id: str
    field_id: str

    @overrides
    def apply(self, root: Node) -> Node | None:
        move_from_block = root.find(self.move_from_block_id)
        assert isinstance(move_from_block, Block)
        move_to_block = root.find(self.move_to_block_id)
        assert isinstance(move_to_block, Block)

        field = root.find(self.field_id)
        assert field is not None
        assert isinstance(field, Field)

        move_from_block.remove_child(field)
        return move_to_block.add_child(field)


@dataclass(frozen=True, kw_only=True)
class MoveInputToBlock(Move):
    move_from_block_id: str
    move_to_block_id: str
    input_id: str

    @overrides
    def apply(self, root: Node) -> Node | None:
        move_from_block = root.find(self.move_from_block_id)
        assert isinstance(move_from_block, Block)
        move_to_block = root.find(self.move_to_block_id)
        assert isinstance(move_to_block, Block)

        input_ = root.find(self.input_id)
        assert input_ is not None
        assert isinstance(input_, Input)

        logger.debug(
            "moving input {} from {} to {}",
            input_.id_,
            move_from_block.id_,
            move_to_block.id_,
        )
        move_from_block.remove_child(input_)
        return move_to_block.add_child(input_)


@dataclass(frozen=True, kw_only=True)
class MoveBlockInSequence(Move):
    sequence_id: str
    block_id: str
    position: int

    @overrides
    def apply(self, root: Node) -> Node | None:
        """Moves the block to the given position in the sequence."""
        sequence = root.find(self.sequence_id)
        assert isinstance(sequence, Sequence)
        block = sequence.find(self.block_id)
        assert isinstance(block, Block)
        assert block.parent == sequence

        current_position = sequence.blocks.index(block)
        sequence.blocks.remove(block)

        new_position = self.position
        if new_position > current_position:
            new_position -= 1

        sequence.blocks.insert(new_position, block)
        return block


@dataclass(frozen=True, kw_only=True)
class Update(Edit):
    """Updates the value (or opcode) of a node in the tree.

    This operation can only be applied to blocks, fields, and literals.
    When applied to a block, the opcode is updated.
    When applied to a field, the value is updated.
    When applied to a literal, the value is updated.

    Attributes
    ----------
    node_id
        the id of the node to update
    value
        the new value or opcode for the node
    """
    node_id: str
    value: str

    @classmethod
    def compute(
        cls,
        node_from: Node,
        node_to: Node,
    ) -> Update | None:
        """Computes the update operation between two nodes or returns None if an update is not possible."""
        value_from: str
        value_to: str

        if isinstance(node_from, Block) and isinstance(node_to, Block):
            value_from = node_from.opcode
            value_to = node_to.opcode
        elif isinstance(node_from, Literal) and isinstance(node_to, Literal):
            value_from = node_from.value
            value_to = node_to.value
        elif isinstance(node_from, Field) and isinstance(node_to, Field):
            if node_to.name != node_from.name:
                return None
            value_from = node_from.value
            value_to = node_to.value
        else:
            return None

        if value_from == value_to:
            return None

        return Update(
            node_id=node_from.id_,
            value=value_to,
        )

    @overrides
    def apply(self, root: Node) -> None:
        node = root.find(self.node_id)
        if isinstance(node, Block):
            node.opcode = self.value
        elif isinstance(node, Field | Literal):
            node.value = self.value
        else:
            error = f"cannot update node of type {type(node)}"
            raise TypeError(error)


@dataclass(frozen=True, kw_only=True)
class Delete(Edit):
    """Deletes a leaf node from the tree.

    Attributes
    ----------
    node_id
        the id of the node to delete
    """
    node_id: str

    @overrides
    def apply(self, root: Node) -> None:
        node = root.find(self.node_id)
        if not node:
            error = f"cannot delete node {self.node_id}: not found."
            raise ValueError(error)

        if node.has_children():
            error = f"cannot delete node {self.node_id}: has children."
            print(f"kids: {[c.id_ for c in node.children()]}")
            raise ValueError(error)

        parent = node.parent

        if not parent:
            error = f"cannot delete node {self.node_id}: no parent."
            raise ValueError(error)

        parent.remove_child(node)


@dataclass
class EditScript(t.Iterable[Edit]):
    _edits: list[Edit] = field(default_factory=list)

    def __iter__(self) -> t.Iterator[Edit]:
        yield from self._edits

    def __len__(self) -> int:
        return len(self._edits)

    def append(self, edit: Edit) -> None:
        logger.debug("added edit to script: {}", edit)
        self._edits.append(edit)

    def apply(self, root: Node) -> Node:
        root = root.copy()
        for edit in self._edits:
            edit.apply(root)
        return root
