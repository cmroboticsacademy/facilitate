from __future__ import annotations

__all__ = ("Node", "TerminalNode")

import abc
import tempfile
import typing as t
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

import networkx as nx
import PIL.Image
from overrides import final, overrides


@dataclass(kw_only=True, eq=False)
class Node(abc.ABC):
    """Represents a node in the abstract syntax tree."""
    id_: str
    parent: Node | None = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for child in self.children():
            child.parent = self

    def add_tag_to_subtree(self, tag: str) -> None:
        """Adds a tag to all of the nodes in the subtree rooted at this node."""
        for node in self.nodes():
            node.tags.append(tag)

    @abc.abstractmethod
    def is_valid(self) -> bool:
        """Determines whether this node is valid."""
        ...

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

    @final
    def contains(self, node: Node) -> bool:
        """Determines whether the given node is a descendant of this node."""
        return node in self.descendants()

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
        children = list(self.children())
        for child in children:
            yield from child.postorder()
        yield self

    @abc.abstractmethod
    def remove_child(self, child: Node) -> None:
        """Removes a child from this node."""
        ...

    def _nx_node_attributes(self) -> dict[str, str]:
        """Returns the attributes of this node to be used in a NetworkX graph."""
        attributes: dict[str, str] = {}

        if "UPDATED" in self.tags:
            attributes["fillcolor"] = "blue"
            attributes["style"] = "filled"
            attributes["fontcolor"] = "white"
        if "DELETED" in self.tags:
            attributes["fillcolor"] = "red"
            attributes["style"] = "filled"
            attributes["fontcolor"] = "white"
        if "ADDED" in self.tags:
            attributes["fillcolor"] = "green"
            attributes["style"] = "filled"
            attributes["fontcolor"] = "black"
        if "MOVED" in self.tags:
            attributes["fillcolor"] = "purple"
            attributes["style"] = "filled"
            attributes["fontcolor"] = "white"

        return attributes

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

    def to_dot_pil_image(self) -> PIL.Image.Image:
        """Renders the graph rooted as this node to a PIL image."""
        png_filename = tempfile.mkstemp(suffix=".png")[1]
        png_path = Path(png_filename)
        try:
            self.to_dot_png(png_filename)
            return PIL.Image.open(png_filename)
        finally:
            png_path.unlink(missing_ok=True)

    def to_dot_png(self, filename: str) -> None:
        """Writes the graph rooted as this node to a PNG file."""
        graph = self.to_nx_digraph()
        nx.drawing.nx_pydot.to_pydot(graph).write_png(filename)  # type: ignore

    def to_dot_pdf(self, filename: str) -> None:
        """Writes the graph rooted as this node to a PDF file."""
        graph = self.to_nx_digraph()
        nx.drawing.nx_pydot.to_pydot(graph).write_pdf(filename)  # type: ignore


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
