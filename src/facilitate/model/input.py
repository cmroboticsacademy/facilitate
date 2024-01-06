from __future__ import annotations

__all__ = ("Input",)

import typing as t
from dataclasses import dataclass

from overrides import overrides

from facilitate.model.node import Node
from facilitate.util import quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True)
class Input(Node):
    name: str
    expression: Node

    def __hash__(self) -> int:
        return hash(self.id_)

    @overrides
    def copy(self: t.Self) -> t.Self:
        return self.__class__(
            id_=self.id_,
            name=self.name,
            expression=self.expression.copy(),
        )

    @overrides
    def surface_equivalent_to(self, other: Node) -> bool:
        return isinstance(other, Input) and self.name == other.name

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        if not self.surface_equivalent_to(other):
            return False
        assert isinstance(other, Input)
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


