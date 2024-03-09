from __future__ import annotations

import typing as t
from dataclasses import dataclass

from overrides import overrides

from facilitate.model.node import Node, TerminalNode
from facilitate.util import generate_id, quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True, eq=False)
class Field(TerminalNode):
    """Fields store specific values, options, or settings that customize the behavior or appearance of a block."""
    name: str
    value: str

    @classmethod
    def create(
        cls,
        name: str,
        value: str,
        *,
        id_: str | None = None,
    ) -> Field:
        if not id_:
            id_ = generate_id(f"field:{name}")
        return cls(id_=id_, name=name, value=value)

    def __hash__(self) -> int:
        return hash(self.id_)

    @overrides
    def copy(self: t.Self) -> t.Self:
        return self.__class__(
            id_=self.id_,
            tags=self.tags.copy(),
            name=self.name,
            value=self.value,
        )

    @overrides
    def surface_equivalent_to(self, other: Node) -> bool:
        if not isinstance(other, Field):
            return False
        if self.name != other.name:
            return False
        return self.value == other.value

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        label = f'"field:{self.name}={self.value}"'
        attributes = self._nx_node_attributes()
        graph.add_node(
            quote(self.id_),
            label=label,
            **attributes,
        )

