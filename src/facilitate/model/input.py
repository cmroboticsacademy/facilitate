from __future__ import annotations

__all__ = ("Input",)

import typing as t
from dataclasses import dataclass, field

from overrides import overrides

from facilitate.model.node import Node
from facilitate.util import generate_id, quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True, eq=False)
class Input(Node):
    name: str
    _children: list[Node] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        name: str,
        expression: Node | None,
        *,
        id_: str | None = None,
    ) -> Input:
        if not id_:
            id_ = generate_id(f"input:{name}")
        children = [expression] if expression is not None else []
        return cls(id_=id_, name=name, _children=children)

    def __hash__(self) -> int:
        return hash(self.id_)

    @property
    def expression(self) -> Node | None:
        if self._children:
            return self._children[0]
        return None

    @overrides
    def is_valid(self) -> bool:
        if len(self._children) > 1:
            return False
        return all(child.is_valid() for child in self.children())

    def add_child(self, child: Node) -> None:
        assert child not in self._children
        child.parent = self
        self._children.append(child)

    @classmethod
    def determine_id(cls, block_id: str, input_name: str) -> str:
        return f":input[{input_name}]@{block_id}"

    @overrides
    def copy(self: t.Self) -> t.Self:
        return self.__class__(
            id_=self.id_,
            tags=self.tags.copy(),
            name=self.name,
            _children=[child.copy() for child in self._children],
        )

    @overrides
    def surface_equivalent_to(self, other: Node) -> bool:
        return isinstance(other, Input) and self.name == other.name

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        if not self.surface_equivalent_to(other):
            return False
        assert isinstance(other, Input)

        if len(self._children) != len(other._children):
            return False

        return all(
            child.equivalent_to(other_child)
            for child, other_child
            in zip(self._children, other._children, strict=True)
        )

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from self._children

    @overrides
    def remove_child(self, child: Node) -> None:
        if child not in self._children:
            error = f"cannot remove child {child.id_}: does not belong to parent {self.id_}"
            raise ValueError(error)
        child.parent = None
        self._children.remove(child)

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        label = f'"input:{self.name}"'
        attributes = self._nx_node_attributes()
        graph.add_node(
            quote(self.id_),
            label=label,
            **attributes,
        )

        for expression in self.children():
            expression._add_to_nx_digraph(graph)
            graph.add_edge(quote(self.id_), quote(expression.id_))


