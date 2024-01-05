from __future__ import annotations

import abc
import enum
import typing as t
from dataclasses import dataclass
from functools import cached_property

import networkx as nx
from overrides import final, overrides

from facilitate.util import quote


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
    @cached_property
    def height(self) -> int:
        """The height of the subtree rooted at this node."""
        max_child_height = 0
        for child in self.children():
            max_child_height = max(max_child_height, child.height)
        return max_child_height + 1

    @abc.abstractmethod
    def equivalent_to(self, other: Node) -> bool:
        """Determines whether this node is equivalent to another."""
        raise NotImplementedError

    @abc.abstractmethod
    def children(self) -> t.Iterator[Node]:
        """Iterates over all children of this node."""
        raise NotImplementedError

    @final
    def descendants(self) -> t.Iterator[Node]:
        """Iterates over all descendants of this node."""
        for child in self.children():
            yield child
            yield from child.descendants()

    @final
    def nodes(self) -> t.Iterator[Node]:
        """Iterates over all nodes within the subtree rooted at this node."""
        yield self
        yield from self.descendants()

    @final
    def postorder(self) -> t.Iterator[Node]:
        """Iterates over all nodes within the subtree rooted at this node in postorder."""
        for child in self.children():
            yield from child.postorder()
        yield self

    @abc.abstractmethod
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        """Adds the subtree rooted as this node to a digraph."""
        raise NotImplementedError

    @final
    def to_nx_digraph(self) -> nx.DiGraph:
        """Converts the graph rooted as this node to an NetworkX DiGraph."""
        graph = nx.DiGraph()
        self._add_to_nx_digraph(graph)
        return graph

    def to_dot(self, filename: str) -> None:
        """Writes the graph rooted as this node to a DOT file."""
        graph = self.to_nx_digraph()
        nx.drawing.nx_pydot.write_dot(graph, filename)

    def to_dot_png(self, filename: str) -> None:
        """Writes the graph rooted as this node to a PNG file."""
        graph = self.to_nx_digraph()
        nx.drawing.nx_pydot.to_pydot(graph).write_png(filename)


class TerminalNode(Node, abc.ABC):
    """Represents a node in the abstract syntax tree that has no children."""
    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from []


@dataclass
class Field(TerminalNode):
    """Fields store specific values, options, or settings that customize the behavior or appearance of a block."""
    id_: str
    name: str
    value: str

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        if not isinstance(other, Field):
            return False
        if self.name != other.name:
            return False
        return self.value == other.value

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        label = f'"field:{self.name}={self.value}"'
        graph.add_node(
            quote(self.id_),
            label=label,
        )


@dataclass
class Literal(TerminalNode):
    """Represents a literal value within the AST."""
    id_: str
    value: str

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        return isinstance(other, Literal) and self.value == other.value

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        label = f'"literal:{self.value}"'
        graph.add_node(
            quote(self.id_),
            label=label,
            shape="hexagon",
        )


@dataclass
class Input(Node):
    id_: str
    name: str
    expression: Node

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        if not isinstance(other, Input):
            return False
        if self.name != other.name:
            return False
        return self.expression.equivalent_to(other.expression)

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield self.expression

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        label = f'"input:{self.name}"'
        graph.add_node(
            quote(self.id_),
            label=label,
        )
        self.expression._add_to_nx_digraph(graph)
        graph.add_edge(quote(self.id_), quote(self.expression.id_))


@dataclass
class Sequence(Node):
    """Represents a sequence of blocks."""
    id_: str
    parent: Node | None
    blocks: list[Block]

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        if not isinstance(other, Sequence):
            return False
        if len(self.blocks) != len(other.blocks):
            return False
        for block, other_block in zip(
            self.blocks,
            other.blocks,
            strict=True,
        ):
            if not block.equivalent_to(other_block):
                return False
        return True

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from self.blocks

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        graph.add_node(
            quote(self.id_),
            label="sequence",
            shape="plaintext",
        )
        for block in self.blocks:
            block._add_to_nx_digraph(graph)
            graph.add_edge(quote(self.id_), quote(block.id_))


@dataclass
class Block(Node):
    id_: str
    opcode: str
    parent: Block | None
    fields: list[Field]
    inputs: list[Input]
    is_shadow: bool

    def _fields_are_equivalent(self, other: Block) -> bool:
        """Determines whether the fields of this block are equivalent to those of another."""
        if len(self.fields) != len(other.fields):
            return False
        for field, other_field in zip(
            self.fields,
            other.fields,
            strict=True,
        ):
            if not field.equivalent_to(other_field):
                return False
        return True

    def _inputs_are_equivalent(self, other: Block) -> bool:
        """Determines whether the inputs of this block are equivalent to those of another."""
        if len(self.inputs) != len(other.inputs):
            return False
        for input_, other_input in zip(
            self.inputs,
            other.inputs,
            strict=True,
        ):
            if not input_.equivalent_to(other_input):
                return False
        return True

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        """Determines whether this block is equivalent to another."""
        if not isinstance(other, Block):
            return False

        if self.opcode != other.opcode:
            return False

        if not self._fields_are_equivalent(other):
            return False

        return self._inputs_are_equivalent(other)

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

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        label = f'"block:{self.opcode}"'
        graph.add_node(
            quote(self.id_),
            label=label,
            opcode=self.opcode,
            shape="box",
        )
        for child in self.children():
            child._add_to_nx_digraph(graph)
            graph.add_edge(quote(self.id_), quote(child.id_))


@dataclass
class Program(Node):
    top_level_blocks: list[Block]

    @property
    def id_(self) -> str:
        return "PROGRAM"

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        if not isinstance(other, Program):
            return False
        if len(self.top_level_blocks) != len(other.top_level_blocks):
            return False
        for block, other_block in zip(
            self.top_level_blocks,
            other.top_level_blocks,
            strict=True,
        ):
            if not block.equivalent_to(other_block):
                return False
        return True

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from self.top_level_blocks

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        graph.add_node(
            quote(self.id_),
            label="program",
            shape="plaintext",
        )
        for child in self.children():
            child._add_to_nx_digraph(graph)
            graph.add_edge(quote(self.id_), quote(child.id_))
