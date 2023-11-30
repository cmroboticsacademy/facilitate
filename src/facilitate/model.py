from __future__ import annotations

import abc
import enum
import typing as t
from dataclasses import dataclass


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
class VarRef(TerminalNode):
    """Represents a reference to a named variable."""
    variable: str


@dataclass
class Sequence(Node):
    """Represents a sequence of blocks."""
    blocks: list[Block]

    def children(self) -> t.Iterator[Node]:
        yield from self.blocks


@dataclass
class Block(Node):
    id_: str
    opcode: str
    parent: Block | None
    fields: list[Field]
    inputs: list[Node]
    is_shadow: bool

    # FIXME ensure that fields and inputs are ordered (postinit)

    @property
    def category(self) -> BlockCategory:
        return BlockCategory.from_opcode(self.opcode)

    def children(self) -> t.Iterator[Node]:
        yield from self.fields
        yield from self.inputs


@dataclass
class Program(Node):
    top_level_blocks: list[Block]

    def children(self) -> t.Iterator[Node]:
        yield from self.top_level_blocks