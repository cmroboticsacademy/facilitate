from __future__ import annotations

import typing as t
from dataclasses import dataclass

from overrides import overrides

from facilitate.model.node import Node, TerminalNode
from facilitate.util import generate_id, quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True, eq=False)
class Literal(TerminalNode):
    """Represents a literal value within the AST."""
    value: str

    @classmethod
    def create(cls, value: str, *, id_: str | None = None) -> Literal:
        assert isinstance(value, str)
        if not id_:
            id_ = generate_id("literal")
        return cls(id_=id_, value=value)

    def __hash__(self) -> int:
        return hash(self.id_)

    def is_valid(self) -> bool:
        return True

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
        node_attributes = self._nx_node_attributes()
        graph.add_node(
            quote(self.id_),
            label=label,
            shape="hexagon",
            **node_attributes,
        )
