from __future__ import annotations

import typing as t
from dataclasses import dataclass

from overrides import overrides

from facilitate.model.node import Node
from facilitate.util import quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True)
class Program(Node):
    top_level_nodes: list[Node]

    def __hash__(self) -> int:
        return hash(self.id_)

    @overrides
    def copy(self: t.Self) -> t.Self:
        return self.__class__(
            id_=self.id_,
            top_level_nodes=[node.copy() for node in self.top_level_nodes],
        )

    @classmethod
    def build(cls, top_level_nodes: list[Node]) -> Program:
        return cls(
            id_="PROGRAM",
            top_level_nodes=top_level_nodes,
        )

    @overrides
    def surface_equivalent_to(self, other: Node) -> bool:
        return isinstance(other, Program)

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        if not isinstance(other, Program):
            return False
        if len(self.top_level_nodes) != len(other.top_level_nodes):
            return False
        for node, other_node in zip(
            self.top_level_nodes,
            other.top_level_nodes,
            strict=True,
        ):
            if not node.equivalent_to(other_node):
                return False
        return True

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from self.top_level_nodes

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