from __future__ import annotations

import typing as t

from apiflask import APIFlask, Schema
from apiflask.fields import (
    Boolean,
    Dict,
    Integer,
    Nested,
    String,
)
import flask
import flask_cors

from facilitate.diff import compute_edit_script
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


@app.put("/diff")  # type: ignore
@app.input(DiffRequest, location="json")
def diff(json_data: dict[str, t.Any]) -> dict[str, str]:
    jsn_from_program = json_data["from_program"]
    jsn_to_program = json_data["to_program"]

    from_program = load_program_from_block_descriptions(jsn_from_program)
    to_program = load_program_from_block_descriptions(jsn_to_program)

    edit_script = compute_edit_script(from_program, to_program)
    response = flask.jsonify(edit_script.to_dict())
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
