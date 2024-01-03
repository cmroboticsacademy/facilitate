from __future__ import annotations

import abc
import enum
import typing as t
from dataclasses import dataclass
from typing import Iterator

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
    @abc.abstractmethod
    def children(self) -> t.Iterator[Node]:
        ...

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
        return


@dataclass
class Field(TerminalNode):
    """Fields store specific values, options, or settings that customize the behavior or appearance of a block."""
    id_: str
    name: str
    value: str

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
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        label = f'"literal:{self.value}"'
        graph.add_node(
            quote(self.id_),
            label=label,
        )


@dataclass
class Input(Node):
    id_: str
    name: str
    expression: Node

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

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        graph.add_node(
            quote(self.id_),
            label="sequence",
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
    def children(self) -> t.Iterator[Node]:
        yield from self.top_level_blocks

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        graph.add_node(
            quote(self.id_),
            label="program",
        )
        for child in self.children():
            child._add_to_nx_digraph(graph)
            graph.add_edge(quote(self.id_), quote(child.id_))
