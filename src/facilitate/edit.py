from __future__ import annotations

import abc
import typing as t
from dataclasses import dataclass, field

from loguru import logger

from facilitate.model.block import Block
from facilitate.model.field import Field
from facilitate.model.literal import Literal

if t.TYPE_CHECKING:
    from facilitate.model.node import Node


class Edit(abc.ABC):
    @abc.abstractmethod
    def apply(self, root: Node) -> None:
        ...


@dataclass(frozen=True, kw_only=True)
class InsertField(Edit):
    """Inserts a named field into a block."""
    block_id: str
    name: str


@dataclass(frozen=True, kw_only=True)
class InsertInput(Edit):
    """Inserts an input into a block.

    Attributes
    ----------
    block_id
        the id of the block to insert the input into
    created_id
        the id of the input to create
    name
        the name of the input to create
    """
    block_id: str
    created_id: str
    name: str

    def apply(self, root: Node) -> None:
        parent = root.find(self.block_id)
        assert isinstance(parent, Block)


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
            value_from = node_to.opcode
            value_to = node_from.opcode
        elif isinstance(node_from, Literal) and isinstance(node_to, Literal):
            value_from = node_to.value
            value_to = node_from.value
        elif isinstance(node_from, Field) and isinstance(node_to, Field):
            if node_to.name != node_from.name:
                return None
            value_from = node_to.value
            value_to = node_from.value
        else:
            return None

        if value_from == value_to:
            return None

        return Update(
            node_id=node_from.id_,
            value=value_to,
        )

    def apply(self, root: Node) -> None:
        raise NotImplementedError


@dataclass(frozen=True, kw_only=True)
class Delete(Edit):
    """Deletes a node from the tree.

    Attributes
    ----------
    node_id
        the id of the node to delete
    """
    node_id: str

    def apply(self, root: Node) -> None:
        # TODO locate node
        # TODO find parent of node [node.parent]
        ...


@dataclass
class EditScript(t.Iterable[Edit]):
    _edits: list[Edit] = field(default_factory=list)

    def __iter__(self) -> t.Iterator[Edit]:
        yield from self._edits

    def __len__(self) -> int:
        return len(self._edits)

    def append(self, edit: Edit) -> None:
        logger.trace("added edit to script: {}", edit)
        self._edits.append(edit)

    def apply(self, root: Node) -> Node:
        root = root.copy()
        for edit in self._edits:
            edit.apply(root)
        return root
