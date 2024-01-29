from __future__ import annotations

import bisect
import dataclasses
import typing as t
from dataclasses import dataclass

from overrides import overrides

from facilitate.model.block_category import BlockCategory
from facilitate.model.field import Field
from facilitate.model.input import Input
from facilitate.model.node import Node
from facilitate.util import quote

if t.TYPE_CHECKING:
    import networkx as nx


@dataclass(kw_only=True, eq=False)
class Block(Node):
    opcode: str
    fields: list[Field] = dataclasses.field(default_factory=list)
    inputs: list[Input] = dataclasses.field(default_factory=list)
    is_shadow: bool

    def __hash__(self) -> int:
        return hash(self.id_)

    @overrides
    def copy(self: t.Self) -> t.Self:
        return self.__class__(
            id_=self.id_,
            opcode=self.opcode,
            tags=self.tags.copy(),
            fields=[field.copy() for field in self.fields],
            inputs=[input_.copy() for input_ in self.inputs],
            is_shadow=self.is_shadow,
        )

    def _fields_are_equivalent(self, other: Block) -> bool:
        """Determines whether the fields of this block are equivalent to those of another."""
        if len(self.fields) != len(other.fields):
            return False
        for field, other_field in zip(
            self.fields,
            other.fields,
            strict=True,
        ):
            if not field.equivalent_to(other_field):
                return False
        return True

    def _inputs_are_equivalent(self, other: Block) -> bool:
        """Determines whether the inputs of this block are equivalent to those of another."""
        if len(self.inputs) != len(other.inputs):
            return False
        for input_, other_input in zip(
            self.inputs,
            other.inputs,
            strict=True,
        ):
            if not input_.equivalent_to(other_input):
                return False
        return True

    @overrides
    def surface_equivalent_to(self, other: Node) -> bool:
        return isinstance(other, Block) and self.opcode == other.opcode

    @overrides
    def equivalent_to(self, other: Node) -> bool:
        """Determines whether this block is equivalent to another."""
        if not self.surface_equivalent_to(other):
            return False

        assert isinstance(other, Block)

        if not self._fields_are_equivalent(other):
            return False

        return self._inputs_are_equivalent(other)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.fields.sort(key=lambda field: field.name)
        self.inputs.sort(key=lambda input_: input_.name)

    @property
    def category(self) -> BlockCategory:
        return BlockCategory.from_opcode(self.opcode)

    def add_field(self, name: str, value: str) -> Field:
        id_ = Field.determine_id(self.id_, name)
        id_ = f"ADDED:{id_}"
        field = Field(
            id_=id_,
            name=name,
            value=value,
        )
        field.parent = self

        # insert field in alphabetical order
        bisect.insort(self.fields, field, key=lambda field: field.name)
        return field

    def add_input(self, name: str) -> Input:
        id_ = Input.determine_id(self.id_, name)
        id_ = f"ADDED:{id_}"
        input_ = Input(
            id_=id_,
            name=name,
            expression=None,
        )
        input_.parent = self

        # insert input in alphabetical order
        bisect.insort(self.inputs, input_, key=lambda input_: input_.name)
        return input_

    def add_child(self, child: Node) -> Node:
        child.parent = self

        if isinstance(child, Field):
            bisect.insort(self.fields, child, key=lambda field: field.name)
        elif isinstance(child, Input):
            bisect.insort(self.inputs, child, key=lambda input_: input_.name)
        else:
            error = f"cannot add child {child.id_}: not field or input"
            raise TypeError(error)

        return child

    @overrides
    def remove_child(self, child: Node) -> None:
        if isinstance(child, Field):
            self.fields.remove(child)
        elif isinstance(child, Input):
            self.inputs.remove(child)
        else:
            error = f"cannot remove child {child.id_}: not field or input of {self.id_}."
            raise TypeError(error)

        child.parent = None

    @overrides
    def children(self) -> t.Iterator[Node]:
        yield from self.fields
        yield from self.inputs

    @overrides
    def _add_to_nx_digraph(self, graph: nx.DiGraph) -> None:
        label = f'"block:{self.opcode}\n{self.id_}"'
        attributes = self._nx_node_attributes()
        graph.add_node(
            quote(self.id_),
            label=label,
            opcode=self.opcode,
            shape="box",
            **attributes,
        )
        for child in self.children():
            child._add_to_nx_digraph(graph)
            graph.add_edge(quote(self.id_), quote(child.id_))
