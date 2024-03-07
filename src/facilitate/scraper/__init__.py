from __future__ import annotations

import json
import typing as t
from pathlib import Path

import ijson
from loguru import logger

_Session = dict[str, t.Any]
_Frame = dict[str, t.Any]
_Block = dict[str, t.Any]
_Blocks = list[_Block]


def _extract_blocks_from_frame(
    level_id: str,
    user_id: str,
    frame_index: int,
    frame: _Frame,
    output_to: Path,
    *,
    log_version: str | None = None,
    require_consent: bool = False,
    require_assent: bool = False,
) -> _Blocks | None:
    # restrict attention to frames that change the program
    if frame.get("actor") != "programming_interface":
        return None

    frame_id = f"{level_id}/{user_id}/{frame_index}"

    if require_consent and not frame.get("consent", False):
        logger.debug(f"skipping frame [{frame_id}]: lacking consent")
        return None

    if require_assent and not frame.get("assent", False):
        logger.debug(f"skipping frame [{frame_id}]: lacking assent")
        return None

    # extract program from state_info
    if "state_info" not in frame:
        logger.debug(f"skipping frame [{frame_id}]: missing 'state_info'")
        return None

    state_info = frame["state_info"]
    program = state_info["program"]
    targets = program["targets"]
    if not targets:
        logger.debug(f"skipping frame [{frame_id}]: no targets")
        return None

    if len(targets) > 1:
        logger.warning(f"bad frame [{frame_id}]: multiple targets")
        return None

    target = program["targets"][0]
    blocks = target["blocks"]
    assert isinstance(blocks, list)
    return blocks


def _scrape_session(
    session: _Session,
    output_to: Path,
    *,
    require_consent: bool = False,
    require_assent: bool = False,
) -> None:
    if "_id" not in session:
        logger.debug("skipping session: missing '_id'")
        return

    session_id: str
    if isinstance(session["_id"], int | str):
        session_id = str(session["_id"])
    elif isinstance(session["_id"], dict) and "$oid" in session["_id"]:
        session_id = session["_id"]["$oid"]
    else:
        logger.debug("skipping session: invalid '_id'")
        return

    # extract frames
    if "frames" not in session:
        logger.debug(f"skipping session {session_id}: missing 'frames'")
        return

    def _load_frame(frame_dict_or_text: str | dict[str, t.Any]) -> _Frame:
        if isinstance(frame_dict_or_text, str):
            frame = json.loads(frame_dict_or_text)
            assert isinstance(frame, dict)
            return frame
        return frame_dict_or_text

    frames: list[_Frame] = [
        _load_frame(text_or_dict) for text_or_dict in session["frames"]
    ]

    if not frames:
        logger.debug(f"skipping session {session_id}: no frames")
        return

    # determine level_id
    level_id: str | None = None
    if "level_id" in session:
        level_id = str(session["level_id"])

    if not level_id:
        episode_started_frame: _Frame | None = next(
            (frame for frame in frames if frame["verb"] == "episode_started"),
            None,
        )
        if episode_started_frame and "object_name" in episode_started_frame:
            level_id = str(episode_started_frame["object_name"])

    if not level_id:
        logger.debug(f"skipping session {session_id}: failed to determine 'level_id'")
        return

    # determine user_id
    if "user_id" not in frames[0]:
        logger.debug(f"skipping session {session_id}: missing 'user_id' in first frame")
        return
    user_id = str(frames[0]["user_id"])

    # determine data format version used by session
    log_version: str | None = frames[0].get("context", {}).get("version")

    for index, frame in enumerate(frames):
        maybe_blocks: _Blocks | None = _extract_blocks_from_frame(
            level_id=level_id,
            user_id=user_id,
            frame_index=index,
            frame=frame,
            output_to=output_to,
            require_consent=require_consent,
            require_assent=require_assent,
            log_version=log_version,
        )
        if maybe_blocks:
            frame_filename = output_to / level_id / user_id / f"{index}.json"
            frame_filename.parent.mkdir(parents=True, exist_ok=True)
            with frame_filename.open("w") as file:
                json.dump(maybe_blocks, file, indent=2)


def scrape(
    dump_filename: str | Path,
    output_to: str | Path,
    *,
    require_consent: bool = False,
    require_assent: bool = False,
) -> None:
    if isinstance(dump_filename, str):
        dump_filename = Path(dump_filename)
    if isinstance(output_to, str):
        output_to = Path(output_to)

    with dump_filename.open("r") as file:
        for session in ijson.items(file, "item"):
            _scrape_session(
                session=session,
                output_to=output_to,
                require_assent=require_assent,
                require_consent=require_consent,
            )
