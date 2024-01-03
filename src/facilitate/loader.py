from __future__ import annotations

import abc
import typing as t
from dataclasses import dataclass
from pprint import pprint

from loguru import logger
import networkx as nx

from facilitate.model import Block, Field, Node, Sequence

if t.TYPE_CHECKING:
    from facilitate.program import Program


_NodeDescription = dict[str, t.Any]


def _extract_input_ids(description: _NodeDescription) -> list[str]:
    """Retrieves a list of the IDs of all inputs to a block."""
    if description["type"] != "block":
        return []
    input_ids: list[str] = []
    for input_values in description["inputs"].values():
        if len(input_values) != 2:
            continue
        if not isinstance(input_values[1], str):
            continue
        input_ids.append(input_values[1])
    return input_ids


def _toposort(
    id_to_node_description: dict[str, _NodeDescription],
) -> list[_NodeDescription]:
    graph = nx.DiGraph()
    depends_on: dict[str, set[str]] = {
        id_: set() for id_ in id_to_node_description
    }
    for id_, description in id_to_node_description.items():
        parent_id: str | None = description["parent"]
        if parent_id:
            graph.add_edge(parent_id, id_)
    sorted_ids = list(nx.topological_sort(graph))
    return [id_to_node_description[id_] for id_ in sorted_ids]


def _inject_parent_into_block_descriptions(
    id_to_node_description: dict[str, _NodeDescription],
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
    id_to_node_description: dict[str, _NodeDescription],
) -> list[_NodeDescription]:
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

    descriptions: list[_NodeDescription] = []
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
    sequence_descriptions: list[_NodeDescription],
    id_to_node_description: dict[str, _NodeDescription],
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
    id_to_raw_description: t.Dict[str, _NodeDescription],
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

    # toposort the descriptions
    node_descriptions = _toposort(id_to_node_description)
    logger.trace("toposorted blocks for parsing")

    # build the nodes in reverse order
    id_to_node: dict[str, Node] = {}
    for description in reversed(node_descriptions):
        id_ = description["id_"]
        node_type = description["type"]

        if node_type == "block":
            # fetch inputs (should already have been built!)
            inputs: list[Node] = [
                id_to_node[input_id]
                for input_id in _extract_input_ids(description)
            ]

            # build fields
            fields: list[Field] = [
                Field(name=name, value=value_arr[0])
                for name, value_arr in description["fields"].items()
            ]

            block = Block(
                id_=id_,
                opcode=description["opcode"],
                parent=None,
                fields=fields,
                inputs=inputs,
                is_shadow=description["shadow"],
            )
            logger.trace("constructed block {}", block.id_)
            id_to_node[id_] = block

        elif node_type == "sequence":
            sequence = Sequence(
                id_=id_,
                parent=None,
                blocks=[
                    id_to_node[block_id] for block_id in description["blocks"]
                ],
            )
            id_to_node[id_] = sequence

        else:
            raise ValueError(f"invalid node type: {description['type']}")

    # update each description with correct parent pointers
    for id_, description in id_to_node_description.items():
        parent_id: str | None = description["parent"]
        if parent_id:
            id_to_node[id_].parent = id_to_node[parent_id]

    pprint(id_to_node)

    raise NotImplementedError
