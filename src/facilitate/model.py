from __future__ import annotations

import abc
import enum
import typing as t
from dataclasses import dataclass
from typing import Iterator

from overrides import overrides


class BlockCategory(enum.Enum):
    CONTROL = "control"
    CUSTOM = "custom"
    EVENT = "event"
    LOOKS = "looks"
    MOTION = "motion"
    OPERATORS = "operator"
    SENSING = "sensing"
    SOUND = "sound"
    UNKNOWN = "unknown"
    VARIABLES = "data"

    @classmethod
    def _missing_(cls, _value: object) -> BlockCategory:
        return cls.UNKNOWN

    @classmethod
    def from_opcode(cls, opcode: str) -> BlockCategory:
        if "_" not in opcode:
            msg = f"Invalid opcode [{opcode}]: must contain an underscore"
            raise ValueError(msg)

        prefix = opcode.split("_")[0]
        assert prefix.islower()
        return cls(prefix)


class Node(abc.ABC):
    """Represents a node in the abstract syntax tree."""
    @abc.abstractmethod
    def children(self) -> t.Iterator[Node]:
        ...


class TerminalNode(Node, abc.ABC):
    """Represents a node in the abstract syntax tree that has no children."""
    @overrides
    def children(self) -> t.Iterator[Node]:
        return


@dataclass
class Field(TerminalNode):
    """Fields store specific values, options, or settings that customize the behavior or appearance of a block."""
    name: str
    value: str


@dataclass
class Literal(TerminalNode):
    """Represents a literal value within the AST."""
    value: str


@dataclass
class Input(Node):
    name: str
    expression: Node

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield self.expression


@dataclass
class VarRef(TerminalNode):
    """Represents a reference to a named variable."""
    variable: str


@dataclass
class Sequence(Node):
    """Represents a sequence of blocks."""
    id_: str
    parent: Node | None
    blocks: list[Block]

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from self.blocks


@dataclass
class Block(Node):
    id_: str
    opcode: str
    parent: Block | None
    fields: list[Field]
    inputs: list[Input]
    is_shadow: bool

    def __post_init__(self) -> None:
        self.fields.sort(key=lambda field: field.name)
        self.inputs.sort(key=lambda input_: input_.name)

    @property
    def category(self) -> BlockCategory:
        return BlockCategory.from_opcode(self.opcode)

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from self.fields
        yield from self.inputs


@dataclass
class Program(Node):
    top_level_blocks: list[Block]

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from self.top_level_blocks
