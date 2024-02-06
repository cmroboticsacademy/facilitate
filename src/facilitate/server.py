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

app = APIFlask(__name__)


class Block(Schema):
    opcode = String(required=True)
    next_ = String(
        allow_none=True,
        data_key="next",
    )
    parent = String(allow_none=True)
    inputs = Dict(keys=String())
    fields = Dict(keys=String())
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


@app.get("/diff")
@app.input(DiffRequest, location="json")
def diff(json_data: dict[str, t.Any]) -> dict[str, str]:
    print(json_data)
    return {
        "todo": "implement",
    }
