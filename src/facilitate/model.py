from __future__ import annotations

import enum


class OpcodeKind(enum.Enum):
    EVENT = "event"
    MOTION = "motion"
    SOUND = "sound"
    LOOKS = "looks"
    CONTROL = "control"
    SENSING = "sensing"
    OPERATORS = "operator"
    VARIABLES = "data"
    CUSTOM = "custom"

    @classmethod
    def _missing_(cls, _value: object) -> OpcodeKind:
        return cls.CUSTOM

    @classmethod
    def from_opcode(cls, opcode: str) -> OpcodeKind:
        if "_" not in opcode:
            msg = f"Invalid opcode [{opcode}]: must contain an underscore"
            raise ValueError(msg)

        prefix = opcode.split("_")[0]
        assert prefix.islower()

        if prefix in cls:
            return cls(prefix)

        return cls.CUSTOM

