from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

if t.TYPE_CHECKING:
    from facilitate.model.node import Node


@dataclass
class NodeMappings:
    _source_to_destination: dict[Node, Node] = field(default_factory=dict)
    _destination_to_source: dict[Node, Node] = field(default_factory=dict)

    @classmethod
    def from_tuples(cls, mappings: set[tuple[Node, Node]]) -> NodeMappings:
        output = NodeMappings()
        for source, destination in mappings:
            output.add(source, destination)
        return output

    def __contains__(self, mapping: tuple[Node, Node]) -> bool:
        source, _destination = mapping
        if source not in self._source_to_destination:
            return False
        return self._source_to_destination[source] == _destination

    def __iter__(self) -> t.Iterator[tuple[Node, Node]]:
        yield from self._source_to_destination.items()

    def __len__(self) -> int:
        return len(self._source_to_destination)

    def copy(self) -> NodeMappings:
        return NodeMappings(
            _source_to_destination=self._source_to_destination.copy(),
            _destination_to_source=self._destination_to_source.copy(),
        )

    def as_tuples(self) -> set[tuple[Node, Node]]:
        return set(self._source_to_destination.items())

    def sources(self) -> t.Iterator[Node]:
        yield from self._source_to_destination.keys()

    def destinations(self) -> t.Iterator[Node]:
        yield from self._destination_to_source.keys()

    def source_is_mapped(self, source: Node) -> bool:
        return source in self._source_to_destination

    def source_is_mapped_to(self, source: Node) -> Node | None:
        return self._source_to_destination.get(source)

    def destination_is_mapped(self, destination: Node) -> bool:
        return destination in self._destination_to_source

    def destination_is_mapped_to(self, destination: Node) -> Node | None:
        return self._destination_to_source.get(destination)

    def check(self) -> None:
        mapped_from: set[Node] = set()
        mapped_to: set[Node] = set()

        for (node_from, node_to) in self:
            if type(node_from) != type(node_to):
                error = "source and destination must be of the same type"
                raise TypeError(error)

            if node_from in mapped_from:
                error = f"source node {node_from.__class__.__name__}({node_from.id_}) already mapped"
                raise ValueError(error)
            mapped_from.add(node_from)

            if node_to in mapped_to:
                error = f"destination node {node_to.__class__.__name__}({node_to.id_}) already mapped"
                raise ValueError(error)
            mapped_to.add(node_to)

    def add(self, source: Node, destination: Node) -> None:
        if type(source) != type(destination):
            error = "source and destination must be of the same type"
            raise TypeError(error)

        self._source_to_destination[source] = destination
        self._destination_to_source[destination] = source

    def add_with_descendants(self, source: Node, destination: Node) -> None:
        for node_source, node_destination in zip(
            source.nodes(),
            destination.nodes(),
            strict=True,
        ):
            self.add(node_source, node_destination)

    def __str__(self) -> str:
        description = "\n".join(f" {before.id_} -> {after.id_}" for (before, after) in self)
        return f"NodeMappings(\n{description}\n)"
