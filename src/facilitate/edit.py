from __future__ import annotations

import abc
import inspect
import json
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger
from overrides import final, overrides

from facilitate.model.block import Block
from facilitate.model.field import Field
from facilitate.model.input import Input
from facilitate.model.literal import Literal
from facilitate.model.program import Program
from facilitate.model.sequence import Sequence

if t.TYPE_CHECKING:
    from PIL.Image import Image

    from facilitate.model.node import Node


class Edit(abc.ABC):
    _name_to_edit_class: t.ClassVar[dict[str, type[Edit]]] = {}

    @abc.abstractmethod
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:
        ...

    @abc.abstractmethod
    def to_dict(self) -> dict[str, t.Any]:
        ...

    @classmethod
    @final
    def from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        type_name: str = dict_["type"]
        type_cls = cls._name_to_edit_class[type_name]
        return type_cls._from_dict(dict_)

    @classmethod
    @abc.abstractmethod
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        ...

    @classmethod
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if inspect.isabstract(cls):
            return
        Edit._name_to_edit_class[cls.__name__] = cls


class Addition(Edit):
    """Represents an additive edit."""


class Move(Edit):
    """Represents a move edit."""


@dataclass(frozen=True, kw_only=True)
class AddSequenceToProgram(Addition):
    position: int

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        """Inserts and returns the given input."""
        assert isinstance(root, Program)
        added = Sequence.create()
        added.tags.append("ADDED")
        root.top_level_nodes.insert(self.position, added)
        return added

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "AddSequenceToProgram",
            "position": self.position,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "AddSequenceToProgram"
        position = dict_["position"]
        return AddSequenceToProgram(position=position)


@dataclass(frozen=True, kw_only=True)
class AddInputToBlock(Addition):
    """Inserts a (bare) named input into a block."""
    block_id: str
    name: str

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        """Inserts and returns the given input."""
        parent = root.find(self.block_id)
        assert isinstance(parent, Block)
        added = parent.add_input(self.name)
        added.tags.append("ADDED")
        return added

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "AddInputToBlock",
            "block-id": self.block_id,
            "name": self.name,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "AddInputToBlock"
        block_id = dict_["block-id"]
        name = dict_["name"]
        return AddInputToBlock(
            block_id=block_id,
            name=name,
        )


@dataclass(frozen=True, kw_only=True)
class AddLiteralToInput(Addition):
    """Inserts a literal into an input."""
    input_id: str
    value: str

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        """Inserts and returns the given literal."""
        parent = root.find(self.input_id)
        assert isinstance(parent, Input)
        added = parent.add_literal(self.value)
        added.tags.append("ADDED")
        return added

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "AddLiteralToInput",
            "input-id": self.input_id,
            "value": self.value,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "AddLiteralToInput"
        input_id = dict_["input-id"]
        value = dict_["value"]
        return AddLiteralToInput(
            input_id=input_id,
            value=value,
        )


@dataclass(frozen=True, kw_only=True)
class AddBlockToSequence(Addition):
    """Inserts a block into a sequence."""
    sequence_id: str
    block_id: str
    position: int
    opcode: str
    is_shadow: bool

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        """Inserts and returns the given block."""
        parent = root.find(self.sequence_id)
        assert isinstance(parent, Sequence)
        added = parent.insert_block(
            opcode=self.opcode,
            is_shadow=self.is_shadow,
            position=self.position,
        )
        added.tags.append("ADDED")
        return added

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "AddBlockToSequence",
            "sequence-id": self.sequence_id,
            "block-id": self.block_id,
            "position": self.position,
            "opcode": self.opcode,
            "is-shadow": self.is_shadow,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "AddBlockToSequence"
        sequence_id = dict_["sequence-id"]
        block_id = dict_["block-id"]
        position = dict_["position"]
        opcode = dict_["opcode"]
        is_shadow = dict_["is-shadow"]
        return AddBlockToSequence(
            sequence_id=sequence_id,
            block_id=block_id,
            position=position,
            opcode=opcode,
            is_shadow=is_shadow,
        )


@dataclass(frozen=True, kw_only=True)
class AddSequenceToInput(Addition):
    """Inserts an empty sequence into an input as an expression."""
    block_id: str
    input_name: str

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        """Inserts and returns the given sequence."""
        block = root.find(self.block_id)
        assert isinstance(block, Block)
        input_ = block.find_input(self.input_name)
        assert input_ is not None
        sequence = Sequence.create()
        sequence.parent = input_
        input_.expression = sequence
        return sequence

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "AddSequenceToInput",
            "block-id": self.block_id,
            "input-name": self.input_name,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "AddSequenceToInput"
        block_id = dict_["block-id"]
        input_name = dict_["input-name"]
        return AddSequenceToInput(
            block_id=block_id,
            input_name=input_name,
        )


@dataclass(frozen=True, kw_only=True)
class AddBlockToInput(Addition):
    """Inserts a block into an input as an expression."""
    input_id: str
    opcode: str
    is_shadow: bool

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        """Inserts and returns the given block."""
        parent = root.find(self.input_id)
        assert isinstance(parent, Input)
        block = Block.create(
            opcode=self.opcode,
            is_shadow=self.is_shadow,
        )
        block.parent = parent
        parent.expression = block
        block.tags.append("ADDED")
        return block

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "AddBlockToInput",
            "input-id": self.input_id,
            "opcode": self.opcode,
            "is-shadow": self.is_shadow,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "AddBlockToInput"
        input_id = dict_["input-id"]
        opcode = dict_["opcode"]
        is_shadow = dict_["is-shadow"]
        return AddBlockToInput(
            input_id=input_id,
            opcode=opcode,
            is_shadow=is_shadow,
        )


@dataclass(frozen=True, kw_only=True)
class AddFieldToBlock(Addition):
    """Inserts a named field into a block."""
    block_id: str
    name: str
    value: str

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        """Inserts and returns the given field."""
        parent = root.find(self.block_id)
        assert isinstance(parent, Block)
        added = parent.add_field(self.name, self.value)
        added.tags.append("ADDED")
        return added

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "AddFieldToBlock",
            "block-id": self.block_id,
            "name": self.name,
            "value": self.value,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "AddFieldToBlock"
        block_id = dict_["block-id"]
        name = dict_["name"]
        value = dict_["value"]
        return AddFieldToBlock(
            block_id=block_id,
            name=name,
            value=value,
        )


@dataclass(frozen=True, kw_only=True)
class MoveSequenceToProgram(Move):
    sequence_id: str
    position: int

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        assert isinstance(root, Program)
        sequence = root.find(self.sequence_id)
        assert isinstance(sequence, Sequence)
        assert sequence.parent is not None

        position = self.position

        # are we switching position of a top-level sequence?
        if sequence.parent == root:
            current_position = root.top_level_nodes.index(sequence)

            # if the sequence is already in the correct position, do nothing
            if position == current_position:
                logger.warning("sequence {} already in position {}", sequence.id_, position)
                return sequence

            # if we want to move sequence to a later position, we need to decrement its position
            # to account for the temporary removal of the sequence from the list
            if position > current_position:
                position -= 1

            root.top_level_nodes.remove(sequence)

        # or are we moving a sequence from elsewhere in the program?
        else:
            sequence.parent.remove_child(sequence)

        root.top_level_nodes.insert(position, sequence)
        return sequence

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "MoveSequenceToProgram",
            "sequence-id": self.sequence_id,
            "position": self.position,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "MoveSequenceToProgram"
        sequence_id = dict_["sequence-id"]
        position = dict_["position"]
        return MoveSequenceToProgram(
            sequence_id=sequence_id,
            position=position,
        )


@dataclass(frozen=True, kw_only=True)
class MoveFieldToBlock(Move):
    move_from_block_id: str
    move_to_block_id: str
    field_id: str

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        move_from_block = root.find(self.move_from_block_id)
        assert isinstance(move_from_block, Block)
        move_to_block = root.find(self.move_to_block_id)
        assert isinstance(move_to_block, Block)

        field = root.find(self.field_id)
        assert field is not None
        assert isinstance(field, Field)

        field.tags.append("MOVED")

        move_from_block.remove_child(field)
        return move_to_block.add_child(field)

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "MoveFieldToBlock",
            "move-from-block-id": self.move_from_block_id,
            "move-to-block-id": self.move_to_block_id,
            "field-id": self.field_id,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "MoveFieldToBlock"
        move_from_block_id = dict_["move-from-block-id"]
        move_to_block_id = dict_["move-to-block-id"]
        field_id = dict_["field-id"]
        return MoveFieldToBlock(
            move_from_block_id=move_from_block_id,
            move_to_block_id=move_to_block_id,
            field_id=field_id,
        )


@dataclass(frozen=True, kw_only=True)
class MoveInputToBlock(Move):
    move_from_block_id: str
    move_to_block_id: str
    input_id: str

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        move_from_block = root.find(self.move_from_block_id)
        assert isinstance(move_from_block, Block)
        move_to_block = root.find(self.move_to_block_id)
        assert isinstance(move_to_block, Block)

        input_ = root.find(self.input_id)
        assert input_ is not None
        assert isinstance(input_, Input)

        input_.tags.append("MOVED")

        logger.debug(
            "moving input {} from {} to {}",
            input_.id_,
            move_from_block.id_,
            move_to_block.id_,
        )
        move_from_block.remove_child(input_)
        return move_to_block.add_child(input_)

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "MoveInputToBlock",
            "move-from-block-id": self.move_from_block_id,
            "move-to-block-id": self.move_to_block_id,
            "input-id": self.input_id,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "MoveInputToBlock"
        move_from_block_id = dict_["move-from-block-id"]
        move_to_block_id = dict_["move-to-block-id"]
        input_id = dict_["input-id"]
        return MoveInputToBlock(
            move_from_block_id=move_from_block_id,
            move_to_block_id=move_to_block_id,
            input_id=input_id,
        )


@dataclass(frozen=True, kw_only=True)
class MoveBlockToSequence(Move):
    block_id: str
    sequence_id: str
    position: int

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        move_block = root.find(self.block_id)
        assert isinstance(move_block, Block)

        move_from_parent = move_block.parent
        assert move_from_parent is not None

        move_to_sequence = root.find(self.sequence_id)
        assert isinstance(move_to_sequence, Sequence)

        # FIXME what if we're changing position of node within the same sequence?
        if move_from_parent == move_to_sequence:
            raise NotImplementedError

        move_from_parent.remove_child(move_block)
        move_to_sequence.blocks.insert(self.position, move_block)
        move_block.parent = move_to_sequence
        return move_block

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "MoveBlockToSequence",
            "block-id": self.block_id,
            "sequence-id": self.sequence_id,
            "position": self.position,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "MoveBlockToSequence"
        block_id = dict_["block-id"]
        sequence_id = dict_["sequence-id"]
        position = dict_["position"]
        return MoveBlockToSequence(
            block_id=block_id,
            sequence_id=sequence_id,
            position=position,
        )


@dataclass(frozen=True, kw_only=True)
class MoveNodeToInput(Move):
    node_id: str
    parent_block_id: str
    input_name: str

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        node_to_move = root.find(self.node_id)
        assert node_to_move is not None

        move_to_block = root.find(self.parent_block_id)
        assert isinstance(move_to_block, Block)

        node_to_move_parent = node_to_move.parent
        assert node_to_move_parent is not None
        node_to_move_parent.remove_child(node_to_move)
        input_ = move_to_block.find_input(self.input_name)
        assert input_ is not None

        node_to_move.parent = input_
        input_.expression = node_to_move

        return node_to_move

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "MoveNodeToInput",
            "node-id": self.node_id,
            "move-to-block-id": self.parent_block_id,
            "input-name": self.input_name,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "MoveNodeToInput"
        node_id = dict_["node-id"]
        move_to_block_id = dict_["move-to-block-id"]
        input_name = dict_["input-name"]
        return MoveNodeToInput(
            node_id=node_id,
            parent_block_id=move_to_block_id,
            input_name=input_name,
        )


@dataclass(frozen=True, kw_only=True)
class MoveBlockInSequence(Move):
    sequence_id: str
    block_id: str
    position: int

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
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

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "MoveBlockInSequence",
            "sequence-id": self.sequence_id,
            "block-id": self.block_id,
            "position": self.position,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "MoveBlockInSequence"
        sequence_id = dict_["sequence-id"]
        block_id = dict_["block-id"]
        position = dict_["position"]
        return MoveBlockInSequence(
            sequence_id=sequence_id,
            block_id=block_id,
            position=position,
        )


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
        elif isinstance(node_from, Input) and isinstance(node_to, Input):
            value_from = node_from.name
            value_to = node_to.name
        else:
            return None

        if value_from == value_to:
            return None

        return Update(
            node_id=node_from.id_,
            value=value_to,
        )

    @overrides
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:  # noqa: ARG002
        node = root.find(self.node_id)

        if isinstance(node, Block):
            node.opcode = self.value
        elif isinstance(node, Field | Literal):
            node.value = self.value
        elif isinstance(node, Input):
            node.name = self.value
        else:
            error = f"cannot update node of type {type(node)}"
            raise TypeError(error)

        node.tags.append("UPDATED")
        return node

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "Update",
            "node-id": self.node_id,
            "value": self.value,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "Update"
        node_id = dict_["node-id"]
        value = dict_["value"]
        return Update(
            node_id=node_id,
            value=value,
        )


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
    def apply(self, root: Node, *, no_delete: bool = False) -> Node | None:
        node = root.find(self.node_id)
        if not node:
            error = f"cannot delete node {self.node_id}: not found."
            raise ValueError(error)

        if not no_delete and node.has_children():
            error = f"cannot delete node {self.node_id}: has children."
            print(f"kids: {[c.id_ for c in node.children()]}")
            raise ValueError(error)

        parent = node.parent

        if not parent:
            error = f"cannot delete node {self.node_id}: no parent."
            raise ValueError(error)

        if not no_delete:
            parent.remove_child(node)

        node.tags.append("DELETED")

        return None

    @overrides
    def to_dict(self) -> dict[str, t.Any]:
        return {
            "type": "Delete",
            "node-id": self.node_id,
        }

    @classmethod
    @overrides
    def _from_dict(cls, dict_: dict[str, t.Any]) -> Edit:
        assert dict_["type"] == "Delete"
        node_id = dict_["node-id"]
        return Delete(
            node_id=node_id,
        )


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

    def to_dict(self) -> dict[str, t.Any]:
        return {
            "edits": [edit.to_dict() for edit in self._edits],
        }

    @classmethod
    def from_dict(cls, dict_: dict[str, t.Any]) -> EditScript:
        assert "edits" in dict_
        edits = [Edit.from_dict(edit_dict) for edit_dict in dict_["edits"]]
        return EditScript(edits)

    @classmethod
    def load(cls, filename: Path | str) -> EditScript:
        if isinstance(filename, str):
            filename = Path(filename)
        with filename.open("r") as f:
            dict_ = json.load(f)
        return cls.from_dict(dict_)

    def save_to_dot_gif(
        self,
        filename: Path | str,
        tree_from: Node,
    ) -> None:
        if isinstance(filename, str):
            filename = Path(filename)

        tree = tree_from.copy()

        # create temporary directory to store intermediate PNGs
        frames: list[Image] = []

        # draw initial tree
        frames.append(tree.to_dot_pil_image())

        # draw state of tree after each edit
        for edit in self._edits:
            logger.debug(f"GIF: applying edit: {edit}")
            edit.apply(tree, no_delete=True)
            frames.append(tree.to_dot_pil_image())

        # convert frames to GIF
        frames[0].save(
            filename,
            append_images=frames[1:],
            save_all=True,
            optimize=False,
            loop=0,
            duration=1000,
        )

    def save_to_json(self, filename: Path | str) -> None:
        if isinstance(filename, str):
            filename = Path(filename)
        with filename.open("w") as f:
            json.dump(self.to_dict(), f, indent=2)
