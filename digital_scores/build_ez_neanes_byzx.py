#!/usr/bin/env python3
"""Write a private reviewed EZ phrase draft as a Neanes .byzx file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.neanes_byzx_bridge import NeanesByzxBridgeError, write_private_byzx


def main() -> int:
    parser = argparse.ArgumentParser(description="Ιδιωτικό EZ event draft → .byzx μέσω του επίσημου Neanes serializer")
    parser.add_argument("event_draft", type=Path, help="Ιδιωτικό JSON από build_ez_neanes_event_draft.py")
    parser.add_argument("--title", required=True, help="Τίτλος του ιδιωτικού draft")
    parser.add_argument("--neanes-source", required=True, type=Path, help="Τοπικό checkout Neanes με node_modules")
    parser.add_argument("--output", required=True, type=Path, help="Ιδιωτική διαδρομή .byzx εξόδου")
    arguments = parser.parse_args()
    try:
        output = write_private_byzx(
            json.loads(arguments.event_draft.read_text(encoding="utf-8")),
            output_path=arguments.output,
            title=arguments.title,
            neanes_source=arguments.neanes_source,
        )
    except (NeanesByzxBridgeError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(f"Δημιουργήθηκε ιδιωτικό .byzx προς έλεγχο: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
