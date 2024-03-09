from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from overrides import overrides

from facilitate.model.block import Block
from facilitate.model.node import Node
from facilitate.util import generate_id, quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True, eq=False)
class Sequence(Node):
    """Represents a sequence of blocks."""
    blocks: list[Block] = field(default_factory=list)

    @classmethod
    def create(cls) -> Sequence:
        """Creates a new empty sequence."""
        id_ = generate_id("seq")
        return cls(
            id_=id_,
            blocks=[],
        )

    @classmethod
    def build(cls, blocks: list[Block]) -> Sequence:
        return cls(
            id_=cls.determine_id(blocks[0].id_),
            blocks=blocks,
        )

    @classmethod
    def determine_id(cls, starts_at_id: str) -> str:
        return f":seq@{starts_at_id}"

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

    def position_of_child(self, child: Node) -> int:
        assert isinstance(child, Block)
        return self.position_of_block(child)

    def insert_block(
        self,
        opcode: str,
        is_shadow: bool,
        position: int,
        *,
        id_: str | None = None,
    ) -> Block:
        block = Block.create(
            opcode=opcode,
            is_shadow=is_shadow,
            id_=id_,
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

    def child(self, index: int) -> Node:
        return self.blocks[index]

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

