from __future__ import annotations

import typing as t
from dataclasses import dataclass

from overrides import overrides

from facilitate.model.block import Block
from facilitate.model.node import Node
from facilitate.model.sequence import Sequence
from facilitate.util import quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True, eq=False)
class Program(Node):
    top_level_nodes: list[Sequence]

    def __hash__(self) -> int:
        return hash(self.id_)

    @overrides
    def is_valid(self) -> bool:
        if not all(isinstance(node, Sequence) for node in self.top_level_nodes):
            return False
        return all(node.is_valid() for node in self.top_level_nodes)

    @overrides
    def copy(self: t.Self) -> t.Self:
        return self.__class__(
            id_=self.id_,
            tags=self.tags.copy(),
            top_level_nodes=[node.copy() for node in self.top_level_nodes],
        )

    @classmethod
    def build(cls, top_level_nodes: list[Node]) -> Program:
        # ensure that every top-level node is a sequence
        wrapped_top_level_nodes: list[Sequence] = []
        for node in top_level_nodes:
            if isinstance(node, Sequence):
                wrapped_top_level_nodes.append(node)
            elif isinstance(node, Block):
                wrapped_top_level_nodes.append(Sequence.build([node]))
            else:
                message = f"invalid top-level node: {node}"
                raise TypeError(message)

        return cls(
            id_="PROGRAM",
            top_level_nodes=wrapped_top_level_nodes,
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

    def position_of_child(self, child: Node) -> int:
        assert isinstance(child, Sequence)
        return self.top_level_nodes.index(child)

    def child(self, index: int) -> Node:
        return self.top_level_nodes[index]

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from self.top_level_nodes

    @overrides
    def remove_child(self, child: Node) -> None:
        assert isinstance(child, Sequence)
        self.top_level_nodes.remove(child)
        child.parent = None

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        attributes = self._nx_node_attributes()
        graph.add_node(
            quote(self.id_),
            label="program",
            shape="plaintext",
            **attributes,
        )
        for child in self.children():
            child._add_to_nx_digraph(graph)
            graph.add_edge(quote(self.id_), quote(child.id_))
