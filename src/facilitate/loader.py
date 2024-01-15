from __future__ import annotations

import json
import typing as t
from pathlib import Path

import networkx as nx
from loguru import logger

from facilitate.model.block import Block
from facilitate.model.field import Field
from facilitate.model.input import Input
from facilitate.model.literal import Literal
from facilitate.model.program import Program
from facilitate.model.sequence import Sequence

if t.TYPE_CHECKING:
    from facilitate.model.node import Node

_NodeDescription = dict[str, t.Any]

_INPUT_VALUE_ARRAY_LENGTH = 2


def _toposort(
    id_to_node_description: dict[str, _NodeDescription],
) -> list[_NodeDescription]:
    expected_num_nodes = len(id_to_node_description)
    graph = nx.DiGraph()
    for id_, description in id_to_node_description.items():
        if description["type"] == "sequence":
            logger.trace("skipping sequence {}", id_)
        parent_id: str | None = description["parent"]
        if parent_id:
            graph.add_edge(parent_id, id_)
    # NOTE networkx stubs are incorrect here; topological_sort returns a generator
    sorted_ids = list(nx.topological_sort(graph))  # type: ignore
    sorted_descriptions = [id_to_node_description[id_] for id_ in sorted_ids]
    actual_num_nodes = len(sorted_descriptions)
    assert actual_num_nodes == expected_num_nodes
    return sorted_descriptions


def _inject_parent_into_block_descriptions(
    id_to_node_description: dict[str, _NodeDescription],
) -> None:
    id_to_parent: dict[str, str] = {}
    for id_, description in id_to_node_description.items():
        # remove ambiguous "parent" field:
        # can mean immediate parent or predecessor (i.e., previous block in sequence)
        if "parent" in description:
            description["parent"] = None

        # identify parenthood via "inputs" field
        for input_values in description["inputs"].values():
            if len(input_values) != _INPUT_VALUE_ARRAY_LENGTH:
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

        sequence_id = f":seq@{starts_at}"
        description = {
            "type": "sequence",
            "id_": sequence_id,
            "blocks": sequence,
            "parent": parent_id,
        }

        # update child block descriptions to point to sequence
        for id_ in sequence:
            id_to_node_description[id_]["parent"] = sequence_id

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
            if len(input_values) != _INPUT_VALUE_ARRAY_LENGTH:
                continue
            if not isinstance(input_values[1], str):
                continue
            if input_values[1] in input_block_id_to_sequence_id:
                input_values[1] = input_block_id_to_sequence_id[input_values[1]]


def _build_program_from_node_descriptions(
    id_to_node_description: dict[str, _NodeDescription],
) -> Program:
    node_descriptions = _toposort(id_to_node_description)
    logger.trace("toposorted nodes for parsing (nodes: {})", len(node_descriptions))

    id_to_node: dict[str, Node] = {}
    for description in reversed(node_descriptions):
        id_ = description["id_"]
        node_type = description["type"]

        if node_type == "block":
            inputs: list[Input] = []
            for input_name, input_value_arr in description["inputs"].items():
                assert len(input_value_arr) == _INPUT_VALUE_ARRAY_LENGTH
                assert isinstance(input_value_arr[0], int)

                expression: Node
                if isinstance(input_value_arr[1], str):
                    expression = id_to_node[input_value_arr[1]]
                elif isinstance(input_value_arr[1], list):
                    assert len(input_value_arr[1]) == _INPUT_VALUE_ARRAY_LENGTH
                    literal_value = input_value_arr[1][1]
                    assert isinstance(literal_value, str)
                    literal_id = f":literal@input[{input_name}]@{id_}"
                    expression = Literal(
                        id_=literal_id,
                        value=literal_value,
                    )
                else:
                    error = f"invalid input value: {input_value_arr[1]}"
                    raise TypeError(error)

                input_ = Input(
                    id_=Input.determine_id(id_, input_name),
                    name=input_name,
                    expression=expression,
                )
                inputs.append(input_)

            fields: list[Field] = [
                Field(
                    id_=Field.determine_id(id_, name),
                    name=name,
                    value=value_arr[0],
                )
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
            blocks: list[Block] = []
            for block_id in description["blocks"]:
                node = id_to_node[block_id]
                assert isinstance(node, Block)
                blocks.append(node)

            sequence = Sequence(
                id_=id_,
                parent=None,
                blocks=blocks,
            )
            logger.trace("constructed sequence {}", sequence.id_)
            id_to_node[id_] = sequence

        else:
            error = f"invalid node type: {description['type']}"
            raise ValueError(error)

    top_level_nodes: list[Node] = [
        node for node in id_to_node.values() if node.parent is None
    ]
    return Program.build(top_level_nodes)


def load_program_from_block_descriptions(
    id_to_raw_description: dict[str, _NodeDescription],
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
        for block_id in description["blocks"]:
            block_parent_id = id_to_node_description[block_id]["parent"]
            assert block_parent_id == sequence_id

    # update block reference in "inputs" fields for the start of each sequence
    _fix_input_block_references(sequence_descriptions, id_to_node_description)
    logger.trace("fixed input block references to account for sequences")

    program = _build_program_from_node_descriptions(id_to_node_description)

    num_expected_sequences = len(sequence_descriptions)
    num_actual_sequences = sum(1 for node in program.nodes() if isinstance(node, Sequence))
    assert num_expected_sequences == num_actual_sequences

    return program


def load_from_file(filename_or_path: str | Path) -> Program:
    """Loads a Facilitate program from a file."""
    path = Path(filename_or_path)
    with path.open() as file:
        block_descriptions = json.load(file)
    return load_program_from_block_descriptions(block_descriptions)
