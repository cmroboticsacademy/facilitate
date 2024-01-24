from __future__ import annotations

__all__ = ("Node", "TerminalNode")

import abc
import typing as t
from dataclasses import dataclass, field
from functools import cached_property

import networkx as nx
from overrides import final, overrides


@dataclass(kw_only=True)
class Node(abc.ABC):
    """Represents a node in the abstract syntax tree."""
    id_: str
    parent: Node | None = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for child in self.children():
            child.parent = self

    @abc.abstractmethod
    def copy(self: t.Self) -> t.Self:
        """Creates a deep copy of this node."""
        raise NotImplementedError

    @cached_property
    def height(self) -> int:
        """The height of the subtree rooted at this node."""
        max_child_height = 0
        for child in self.children():
            max_child_height = max(max_child_height, child.height)
        return max_child_height + 1

    def size(self) -> int:
        """The size of the subtree rooted at this node."""
        return sum(1 for _ in self.nodes())

    @abc.abstractmethod
    def equivalent_to(self, other: Node) -> bool:
        """Determines whether this node is equivalent to another."""
        raise NotImplementedError

    @abc.abstractmethod
    def surface_equivalent_to(self, other: Node) -> bool:
        """Determines whether the surface-level attributes of this node are equivalent to another.

        Does not check the children of the nodes.
        """
        raise NotImplementedError

    @final
    def has_children(self) -> bool:
        """Determines whether this node has any children."""
        for _ in self.children():
            return True
        return False

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

    def find(self, id_: str) -> Node | None:
        """Finds the node with the given ID within the subtree rooted at this node.

        Returns
        -------
        Node
            the node with the given ID if it exists, otherwise None
        """
        for node in self.nodes():
            if node.id_ == id_:
                return node
        return None

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
    def remove_child(self, child: Node) -> None:
        """Removes a child from this node."""
        ...

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
        nx.drawing.nx_pydot.to_pydot(graph).write_png(filename)  # type: ignore


class TerminalNode(Node, abc.ABC):
    """Represents a node in the abstract syntax tree that has no children."""
    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from []

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        return self.surface_equivalent_to(other)

    @overrides
    def remove_child(self, child: Node) -> None:
        error = f"cannot remove child {child.id_} from terminal node ({self.id_})"
        raise NotImplementedError(error)
