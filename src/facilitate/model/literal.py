from __future__ import annotations

import typing as t
from dataclasses import dataclass

from overrides import overrides

from facilitate.model.node import Node, TerminalNode
from facilitate.util import quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True)
class Literal(TerminalNode):
    """Represents a literal value within the AST."""
    value: str

    def __hash__(self) -> int:
        return hash(self.id_)

    @classmethod
    def determine_id(cls, parent_id: str) -> str:
        return f":literal@{parent_id}"

    @overrides
    def copy(self: t.Self) -> t.Self:
        return self.__class__(
            id_=self.id_,
            tags=self.tags.copy(),
            value=self.value,
        )

    @overrides
    def surface_equivalent_to(self, other: Node) -> bool:
        return isinstance(other, Literal) and self.value == other.value

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        label = f'"literal:{self.value}"'
        graph.add_node(
            quote(self.id_),
            label=label,
            shape="hexagon",
        )
