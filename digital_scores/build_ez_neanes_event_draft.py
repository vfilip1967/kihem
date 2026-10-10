#!/usr/bin/env python3
"""Compile a privately reviewed EZ phrase plan to Neanes Note-event JSON.

The script is deliberately unable to create a complete .byzx score.  It
produces the small, auditable event payload that is handed to the Neanes
import/export step only after score-level review.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ez_neanes_draft import EzPhrasePlanError, compile_confirmed_ez_phrase_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Ιδιωτικό, ελεγμένο EZ→Neanes draft γεγονότων")
    parser.add_argument("mapping_template", type=Path, help="Ιδιωτικό JSON από build_ez_mapping_template.py")
    parser.add_argument("phrase_plan", type=Path, help="Ιδιωτικό JSON με επιβεβαιωμένα source anchors")
    parser.add_argument("--output", required=True, type=Path, help="Ιδιωτικό JSON εξόδου")
    arguments = parser.parse_args()

    try:
        result = compile_confirmed_ez_phrase_plan(
            json.loads(arguments.mapping_template.read_text(encoding="utf-8")),
            json.loads(arguments.phrase_plan.read_text(encoding="utf-8")),
        )
    except (EzPhrasePlanError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Δημιουργήθηκαν {len(result['events'])} ιδιωτικά Neanes Note events. Δεν δημιουργήθηκε .byzx.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
