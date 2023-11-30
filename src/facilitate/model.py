from __future__ import annotations

import abc
import enum
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


class Value(abc.ABC):
    """Tagged interface to indicate an AST element that can be evaluated to a value."""


class Expression(Value):
    """Indicates that given block represents an expression."""


@dataclass
class Field:
    """Fields store specific values, options, or settings that customize the behavior or appearance of a block."""
    name: str
    value: str


@dataclass
class Literal(Value):
    value: str


@dataclass
class VarRef(Value):
    """A reference to a named, in-scope variable."""
    variable: str


@dataclass
class Sequence(Node):
    """Represents a sequence of blocks."""
    blocks: list[Block]


@dataclass
class SimpleBlock:
    id_: str
    opcode: str
    parent: Block | None
    fields: list[Field]
    inputs: list[Node]
    is_shadow: bool

    @property
    def category(self) -> BlockCategory:
        return BlockCategory.from_opcode(self.opcode)

    # TODO ensure that fields and inputs are ordered


@dataclass
class Program:
    top_level_blocks: list[Block]
