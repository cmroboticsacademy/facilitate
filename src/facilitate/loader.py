from __future__ import annotations

import typing as t

import networkx as nx
from loguru import logger

from facilitate.model import (
    Block,
    Field,
    Input,
    Literal,
    Node,
    Program,
    Sequence,
)

_NodeDescription = dict[str, t.Any]

_INPUT_VALUE_ARRAY_LENGTH = 2


def _extract_input_names_to_id(description: _NodeDescription) -> dict[str, str]:
    """Retrives a mapping from input names to block IDs."""
    name_to_id: dict[str, str] = {}

    if description["type"] != "block":
        return {}

    for name, input_values in description["inputs"].items():
       if len(input_values) != _INPUT_VALUE_ARRAY_LENGTH:
           continue
       if not isinstance(input_values[1], str):
           continue
       name_to_id[name] = input_values[1]

    return name_to_id


def _extract_input_ids(description: _NodeDescription) -> list[str]:
    """Retrieves a list of the IDs of all inputs to a block."""
    return list(_extract_input_names_to_id(description).values())


def _toposort(
    id_to_node_description: dict[str, _NodeDescription],
) -> list[_NodeDescription]:
    graph = nx.DiGraph()
    for id_, description in id_to_node_description.items():
        parent_id: str | None = description["parent"]
        if parent_id:
            graph.add_edge(parent_id, id_)
    sorted_ids = list(nx.topological_sort(graph))
    return [id_to_node_description[id_] for id_ in sorted_ids]


def _inject_parent_into_block_descriptions(
    id_to_node_description: dict[str, _NodeDescription],
) -> dict[str, t.Any]:
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
    logger.trace("toposorted blocks for parsing")

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

                input_id = f":input[{input_name}]@{id_}"
                input_ = Input(
                    id_=input_id,
                    name=input_name,
                    expression=expression,
                )
                inputs.append(input_)

            fields: list[Field] = [
                Field(
                    id_=f":field[{name}]@{id_}",
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
            sequence = Sequence(
                id_=id_,
                parent=None,
                blocks=[
                    id_to_node[block_id] for block_id in description["blocks"]
                ],
            )
            id_to_node[id_] = sequence

        else:
            error = f"invalid node type: {description['type']}"
            raise ValueError(error)

    # update each description with correct parent pointers
    for id_, description in id_to_node_description.items():
        parent_id: str | None = description["parent"]
        if parent_id:
            id_to_node[id_].parent = id_to_node[parent_id]

    top_level_nodes: list[Node] = [
        node for node in id_to_node.values() if node.parent is None
    ]
    return Program(top_level_nodes)


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

        # update parent field for each block in sequence
        for block_id in description["blocks"]:
            id_to_node_description[block_id]["parent"] = sequence_id

    logger.trace("extracted {} sequences", len(sequence_descriptions))

    # update block reference in "inputs" fields for the start of each sequence
    _fix_input_block_references(sequence_descriptions, id_to_node_description)
    logger.trace("fixed input block references to account for sequences")

    return _build_program_from_node_descriptions(id_to_node_description)
