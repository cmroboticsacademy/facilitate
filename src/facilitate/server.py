from __future__ import annotations

import json
import typing as t

import flask
import flask_cors
from apiflask import APIFlask, Schema
from apiflask.fields import (
    Boolean,
    DateTime,
    Dict,
    Float,
    Integer,
    List,
    Nested,
    String,
)

from facilitate.diff import compute_edit_script
from facilitate.distance import compute_edit_script_and_distance
from facilitate.loader import load_program_from_block_descriptions

app = APIFlask(__name__)
flask_cors.CORS(app)


class Block(Schema):
    opcode = String(required=True)
    next_ = String(
        allow_none=True,
        data_key="next",
        attribute="next",
    )
    parent = String(allow_none=True)
    inputs = Dict(keys=String())
    fields_ = Dict(
        keys=String(),
        data_key="fields",
        attribute="fields",
    )
    shadow = Boolean(required=True)
    top_level = Boolean(
        required=True,
        data_key="topLevel",
    )
    x = Integer(required=False)
    y = Integer(required=False)


class Solution(Schema):
    id_ = Integer(
        attribute="id",
        data_key="id",
        required=True,
        strict=True,
    )
    cmra_blocks_element_id = Integer(
        required=True,
        strict=True,
    )
    weight = Float(strict=True)
    program = String(required=True)
    created_at = DateTime(required=False)
    updated_at = DateTime(required=False)


class DiffRequest(Schema):
    from_program = Dict(
        keys=String(),
        values=Nested(Block()),
        required=True,
        data_key="from",
    )
    to_program = Dict(
        keys=String(),
        values=Nested(Block()),
        required=True,
        data_key="to",
    )


class ProgressRequest(Schema):
    user_program = String()
    solutions = List(
        Nested(Solution()),
        required=True,
    )


@app.put("/diff")  # type: ignore
@app.input(DiffRequest, location="json")
def diff(json_data: dict[str, t.Any]) -> flask.Response:
    jsn_from_program = json_data["from_program"]
    jsn_to_program = json_data["to_program"]

    from_program = load_program_from_block_descriptions(jsn_from_program)
    to_program = load_program_from_block_descriptions(jsn_to_program)

    edit_script = compute_edit_script(from_program, to_program)
    response = flask.jsonify(edit_script.to_dict())
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.put("/distance")  # type: ignore
@app.input(DiffRequest, location="json")
def distance(json_data: dict[str, t.Any]) -> flask.Response:
    jsn_from_program = json_data["from_program"]
    jsn_to_program = json_data["to_program"]

    from_program = load_program_from_block_descriptions(jsn_from_program)
    to_program = load_program_from_block_descriptions(jsn_to_program)

    edit_script, distance = compute_edit_script_and_distance(from_program, to_program)
    response = flask.jsonify({
        "edits": edit_script.to_dict(),
        "distance": distance,
    })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.put("/progress")  # type: ignore
@app.input(ProgressRequest, location="json")
def progress(json_data: dict[str, t.Any]) -> flask.Response:
    jsn_user_program = json.loads(json_data["user_program"])
    jsn_user_blocks = jsn_user_program["targets"][0]["blocks"]
    user_program = load_program_from_block_descriptions(jsn_user_blocks)

    solution_distances: list[dict[str, t.Any]] = []

    solutions = json_data["solutions"]
    for solution in solutions:
        jsn_solution_program = json.loads(solution["program"])
        jsn_solution_blocks = jsn_solution_program["targets"][0]["blocks"]
        solution_program = load_program_from_block_descriptions(jsn_solution_blocks)
        edit_script, distance = compute_edit_script_and_distance(
            tree_from=user_program,
            tree_to=solution_program,
        )
        solution_distances.append({
            "id": solution["id"],
            "distance": distance,
            "edits": edit_script.to_dict(),
        })

    response = flask.jsonify(solution_distances)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
