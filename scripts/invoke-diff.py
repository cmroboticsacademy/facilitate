#!/usr/bin/env python
from pathlib import Path
import json

import requests

DIR_SCRIPTS = Path(__file__).resolve().parent
DIR_REPO = DIR_SCRIPTS.parent
DIR_EXAMPLES = DIR_REPO / "examples"

FILE_BAD_EXAMPLE = DIR_EXAMPLES / "bad.json"
FILE_GOOD_EXAMPLE = DIR_EXAMPLES / "good.json"

URL_API = "http://127.0.0.1:5000/diff"


def main() -> None:
    with FILE_BAD_EXAMPLE.open() as fh:
        bad = json.load(fh)

    with FILE_GOOD_EXAMPLE.open() as fh:
        good = json.load(fh)

    request = {
        "from": bad,
        "to": good,
    }

    response = requests.get(URL_API, json=request)
    jsn = response.json()
    print(jsn)


if __name__ == "__main__":
    main()
