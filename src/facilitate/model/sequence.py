from __future__ import annotations

import typing as t
from dataclasses import dataclass

from overrides import overrides

from facilitate.model.block import Block
from facilitate.model.node import Node
from facilitate.util import quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True)
class Sequence(Node):
    """Represents a sequence of blocks."""
    blocks: list[Block]

    def __hash__(self) -> int:
        return hash(self.id_)

    @overrides
    def copy(self: t.Self) -> t.Self:
        return self.__class__(
            id_=self.id_,
            blocks=[block.copy() for block in self.blocks],
        )

    @overrides
    def surface_equivalent_to(self, other: Node) -> bool:
        return isinstance(other, Sequence)

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        if not isinstance(other, Sequence):
            return False
        if len(self.blocks) != len(other.blocks):
            return False
        for block, other_block in zip(
            self.blocks,
            other.blocks,
            strict=True,
        ):
            if not block.equivalent_to(other_block):
                return False
        return True

    def position_of_block(self, block: Block) -> int:
        return self.blocks.index(block)

    def insert_block(
        self,
        id_: str,
        opcode: str,
        is_shadow: bool,
        position: int,
    ) -> Block:
        id_ = f"ADDED:{id_}"
        block = Block(
            id_=id_,
            opcode=opcode,
            is_shadow=is_shadow,
        )
        self.blocks.insert(position, block)
        block.parent = self
        return block

    @overrides
    def remove_child(self, child: Node) -> None:
        if not isinstance(child, Block):
            error = f"cannot remove child {child.id_}: not a block."
            raise TypeError(error)
        self.blocks.remove(child)
        child.parent = None

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from self.blocks

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        graph.add_node(
            quote(self.id_),
            label="sequence",
            shape="plaintext",
        )
        for block in self.blocks:
            block._add_to_nx_digraph(graph)
            graph.add_edge(quote(self.id_), quote(block.id_))

