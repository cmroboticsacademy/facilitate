from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

if t.TYPE_CHECKING:
    from facilitate.model.node import Node


@dataclass
class NodeMappings:
    _source_to_destination: dict[Node, Node] = field(default_factory=dict)
    _destination_to_source: dict[Node, Node] = field(default_factory=dict)

    def __contains__(self, mapping: tuple[Node, Node]) -> bool:
        source, _destination = mapping
        if source not in self._source_to_destination:
            return False
        return self._source_to_destination[source] == _destination

    def __iter__(self) -> t.Iterator[tuple[Node, Node]]:
        yield from self._source_to_destination.items()

    def __len__(self) -> int:
        return len(self._source_to_destination)

    def source_is_mapped_to(self, source: Node) -> Node:
        return self._source_to_destination[source]

    def destination_is_mapped_to(self, destination: Node) -> Node:
        return self._destination_to_source[destination]

    def add(self, source: Node, destination: Node) -> None:
        if type(source) != type(destination):
            error = "source and destination must be of the same type"
            raise TypeError(error)

        if source in self._source_to_destination:
            error = f"source node {source.id_} already has a mapping"
            raise ValueError(error)

        if destination in self._destination_to_source:
            error = f"destination node {destination.id_} already has a mapping"
            raise ValueError(error)

        self._source_to_destination[source] = destination
        self._destination_to_source[destination] = source
