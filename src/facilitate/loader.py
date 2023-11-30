from __future__ import annotations

import typing as t
from dataclasses import dataclass

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
class _BlockDescriptionSequence:
    descriptions: list[_BlockDescription]


_ProgramDescription = t.MutableMapping[
    str,
    _BlockDescription,
]


def _toposort(
    id_to_description: _ProgramDescription,
) -> list[_BlockDescription]:
    depends_on: dict[str, set[str]] = {
        id_: set() for id_ in id_to_description
    }
    for id_, description in id_to_description.items():
        description["id_"] = id_
        if "parent" in description:
            parent_id = description["parent"]
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

    return [id_to_description[id_] for id_ in sorted_ids]


def load_program_from_block_descriptions(
    id_to_description: _ProgramDescription,
) -> Program:
    descriptions: list[_BlockDescription] = _toposort(id_to_description)
    print(descriptions)

    # TODO identify sequences
