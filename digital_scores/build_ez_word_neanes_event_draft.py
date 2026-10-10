#!/usr/bin/env python3
"""Compile a reviewer-confirmed direct-Word EZ phrase to private Note events."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ez_word_neanes_draft import EzWordPhrasePlanError, compile_confirmed_ez_word_phrase_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Ιδιωτικό direct-Word EZ→Neanes draft γεγονότων")
    parser.add_argument("word_report", type=Path)
    parser.add_argument("phrase_plan", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        result = compile_confirmed_ez_word_phrase_plan(
            json.loads(arguments.word_report.read_text(encoding="utf-8")),
            json.loads(arguments.phrase_plan.read_text(encoding="utf-8")),
        )
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (EzWordPhrasePlanError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(f"Δημιουργήθηκαν {len(result['events'])} ιδιωτικά Neanes Note events.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
