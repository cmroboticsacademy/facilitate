from __future__ import annotations

import typing as t
from dataclasses import dataclass
from pprint import pprint

from loguru import logger

if t.TYPE_CHECKING:
    from facilitate.program import Program


class _BlockDescription(t.TypedDict):
    id_: str
    opcode: str
    next: str | None
    parent: str | None
    next: str | None
    inputs: dict[str, list[t.Any]]
    fields: dict[str, list[t.Any]]
    shadow: bool
    topLevel: bool
    x: int
    y: int


@dataclass
class _SequenceDescription:
    parent_id: str | None
    descriptions: list[_BlockDescription]

    @property
    def id_(self) -> str:
        """The ID of the sequence."""
        if self.parent_id is None:
            return f"toplevel_sequence_{self.start_id}_to_{self.end_id}"
        return f"{self.parent_id}_sequence_{self.start_id}_to_{self.end_id}"

    @property
    def start_id(self) -> str:
        """The ID of the first block in the sequence."""
        return self.descriptions[0]["id_"]

    @property
    def end_id(self) -> str:
        """The ID of the last block in the sequence."""
        return self.descriptions[-1]["id_"]

    def add(self, description: _BlockDescription) -> None:
        """Add a block to the end of the sequence."""
        assert description["parent"] == self.parent_id
        assert description["id_"] not in self.block_ids
        self.descriptions.append(description)


_NodeDescription = _BlockDescription | _SequenceDescription


_ProgramDescription = t.MutableMapping[
    str,
    _BlockDescription,
]


def _toposort(
    id_to_node_description: dict[str, _NodeDescription],
) -> list[_NodeDescription]:
    depends_on: dict[str, set[str]] = {
        id_: set() for id_ in id_to_node_description
    }
    for id_, description in id_to_node_description.items():
        parent_id: str | None = None
        if isinstance(description, _BlockDescription):
            parent_id = description["parent"]
        elif isinstance(description, _SequenceDescription):
            parent_id = description.parent_id
        if parent_id:
            depends_on[parent_id].add(id_)

    queue: list[str] = list(depends_on.keys())
    visited: set[str] = set()
    sorted_ids: list[str] = []
    while queue:
        next_id = queue.pop(0)
        if next_id in visited:
            continue
        queue.insert(0, *depends_on[next_id])
        sorted_ids.insert(0, next_id)
        visited[next_id] = True

    assert visited == set(depends_on.keys())

    return [id_to_node_description[id_] for id_ in sorted_ids]


def _extract_sequences(
    id_to_description: _ProgramDescription,
) -> list[_SequenceDescription]:
    sequences: list[_SequenceDescription] = []

    for from_id, from_description in id_to_description.items():
        if not from_description["next"]:
            continue

        parent_id = from_description["parent"]
        logger.trace("parent of {} is {}", from_id, parent_id)
        to_id = from_description["next"]
        to_description = id_to_description[to_id]

        logger.trace("identified sequence link: {} -> {}", from_id, to_id)

        # is there a sequence that ends with from_id?
        # if so, add block to the end of that sequence
        # if not, create a new sequence
        existing_sequence: _SequenceDescription | None = next(
            (sequence for sequence in sequences if sequence.end_id == from_id),
            None,
        )
        if existing_sequence:
            logger.trace("extending existing sequence: {}", existing_sequence.id_)
            existing_sequence.add(to_description)
        else:
            new_sequence = _SequenceDescription(
                parent_id,
                [from_description, to_description],
            )
            logger.trace("creating new sequence: {}", new_sequence.id_)
            sequences.append(new_sequence)

    return sequences


def load_program_from_block_descriptions(
    id_to_description: _ProgramDescription,
) -> Program:
    id_to_block_description = {
        id_: {"id_": id_} | description
        for id_, description in id_to_description.items()
    }
    logger.trace("injected ID into block descriptions")
    logger.trace("program description contains {} blocks", len(id_to_block_description))
    pprint(list(id_to_block_description.values()))

    sequences = _extract_sequences(id_to_block_description)
    logger.trace("extracted {} sequences", len(sequences))
    for sequence in sequences:
        for description in sequence.descriptions:
            description["parent"] = sequence.id_

    id_to_node_description = {
        **id_to_block_description,
        **{sequence.id_: sequence for sequence in sequences},
    }

    descriptions = _toposort(id_to_node_description)
    print(descriptions)


# FIXME fix handling of top-level blocks
