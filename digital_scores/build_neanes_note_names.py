#!/usr/bin/env python3
"""Create the private ``<score>.notes.json`` parallage sidecar for a ``.byzx``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neanes_byzx_bridge import NeanesByzxBridgeError, write_note_names  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("byzx", type=Path, help="Το .byzx του οποίου οι νότες θα καταγραφούν")
    parser.add_argument("--neanes-source", required=True, type=Path, help="Τοπικό checkout Neanes με node_modules")
    parser.add_argument("--output", type=Path, help="Προορισμός· προεπιλογή <byzx>.notes.json δίπλα στο .byzx")
    args = parser.parse_args()
    output = args.output or args.byzx.with_suffix(".notes.json")
    try:
        path = write_note_names(args.byzx, output_path=output, neanes_source=args.neanes_source)
    except NeanesByzxBridgeError as error:
        print(error, file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
