from __future__ import annotations

import enum


class BlockCategory(enum.Enum):
    CONTROL = "control"
    CUSTOM = "custom"
    EVENT = "event"
    LOOKS = "looks"
    MOTION = "motion"
    OPERATORS = "operator"
    SENSING = "sensing"
    SOUND = "sound"
    UNKNOWN = "unknown"
    VARIABLES = "data"

    @classmethod
    def _missing_(cls, _value: object) -> BlockCategory:
        return cls.UNKNOWN

    @classmethod
    def from_opcode(cls, opcode: str) -> BlockCategory:
        if "_" not in opcode:
            msg = f"Invalid opcode [{opcode}]: must contain an underscore"
            raise ValueError(msg)

        prefix = opcode.split("_")[0]
        assert prefix.islower()
        return cls(prefix)

