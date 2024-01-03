from __future__ import annotations

import abc
import typing as t
from dataclasses import dataclass
from pprint import pprint

from loguru import logger

if t.TYPE_CHECKING:
    from facilitate.program import Program


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


def _inject_parent_into_block_descriptions(
    id_to_node_description: dict[str, t.Any],
) -> dict[str, t.Any]:
    id_to_parent: t.Dict[str, str] = {}
    for id_, description in id_to_node_description.items():
        # remove ambiguous "parent" field:
        # can mean immediate parent or predecessor (i.e., previous block in sequence)
        if "parent" in description:
            description["parent"] = None

        # identify parenthood via "inputs" field
        for input_values in description["inputs"].values():
            if len(input_values) != 2:
                continue
            if not isinstance(input_values[1], str):
                continue
            if input_values[1] in id_to_node_description:
                id_to_parent[input_values[1]] = id_

    # inject actual parent ID into each block description
    for id_, parent_id in id_to_parent.items():
        id_to_node_description[id_]["parent"] = parent_id


def _extract_sequence_descriptions(
    id_to_node_description: dict[str, t.Any],
) -> list[dict[str, t.Any]]:
    sequences: list[list[str]] = []
    for id_, description in id_to_node_description.items():
        next_id = description["next"]
        if not next_id:
            continue
        for sequence in sequences:
            if sequence[-1] == id_:
                sequence.append(next_id)
                break
        else:
            sequences.append([id_, next_id])

    descriptions: list[dict[str, t.Any]] = []
    for sequence in sequences:
        starts_at = sequence[0]
        parent_id = id_to_node_description[starts_at]["parent"]
        for id_ in sequence[1:]:
            assert id_to_node_description[id_]["parent"] == parent_id
        description = {
            "type": "sequence",
            "id_": f":seq@{starts_at}",
            "blocks": sequence,
            "parent": parent_id,
        }
        descriptions.append(description)

    return descriptions


def _fix_input_block_references(
    sequence_descriptions: list[dict[str, t.Any]],
    id_to_node_description: dict[str, t.Any],
) -> None:
    input_block_id_to_sequence_id: dict[str, str] = {
        description["blocks"][0]: description["id_"]
        for description in sequence_descriptions
    }
    for description in id_to_node_description.values():
        if description["type"] != "block":
            continue
        for input_values in description["inputs"].values():
            if len(input_values) != 2:
                continue
            if not isinstance(input_values[1], str):
                continue
            if input_values[1] in input_block_id_to_sequence_id:
                input_values[1] = input_block_id_to_sequence_id[input_values[1]]


def load_program_from_block_descriptions(
    id_to_raw_description: t.Dict[str, t.Any],
) -> Program:
    # inject an ID into each block description and denote as a block
    id_to_node_description = {
        id_: {
            "id_": id_,
            "type": "block",
            "previous": None,
        } | description
        for id_, description in id_to_raw_description.items()
    }
    logger.trace("injected ID into block descriptions")
    logger.trace("program description contains {} blocks", len(id_to_node_description))

    _inject_parent_into_block_descriptions(id_to_node_description)
    logger.trace("injected corrected parent field into block descriptions")

    sequence_descriptions = _extract_sequence_descriptions(id_to_node_description)
    for description in sequence_descriptions:
        sequence_id = description["id_"]
        id_to_node_description[sequence_id] = description

        # update parent field for each block in sequence
        for block_id in description["blocks"]:
            id_to_node_description[block_id]["parent"] = sequence_id

    logger.trace("extracted {} sequences", len(sequence_descriptions))

    # update block reference in "inputs" fields for the start of each sequence
    _fix_input_block_references(sequence_descriptions, id_to_node_description)
    logger.trace("fixed input block references to account for sequences")

    pprint(id_to_node_description)

    raise NotImplementedError
