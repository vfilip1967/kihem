#!/usr/bin/env python3
"""Create a private supervised alignment scaffold from a verified Neanes score."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.digital_scores import DigitalScoreCatalog
from src.reference_alignment import build_reference_ledger, record_phrase_anchors, write_reference_ledger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True, help="digital_scores.json")
    parser.add_argument("--storage", type=Path, required=True, help="ιδιωτικός φάκελος ψηφιακών αρχείων")
    parser.add_argument("--score-id", required=True, help="μόνο verified καταχώριση")
    parser.add_argument("--output", type=Path, required=True, help="ιδιωτικό JSON ledger")
    parser.add_argument(
        "--phrase-plan",
        type=Path,
        help="προαιρετικό JSON με φράσεις, εύρη σημείων, συλλαβές και τμήμα σάρωσης",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    catalog = DigitalScoreCatalog(args.catalog, args.storage)
    score = catalog.get(args.score_id)
    if score is None:
        raise SystemExit(f"Δεν βρέθηκε η παρτιτούρα: {args.score_id}")
    byzx_path = catalog.asset_path(score, "byzx")
    if byzx_path is None:
        raise SystemExit(f"Δεν βρέθηκε το τοπικό .byzx για: {args.score_id}")
    ledger = build_reference_ledger(score, byzx_path)
    if args.phrase_plan:
        try:
            groups = json.loads(args.phrase_plan.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Δεν διαβάζεται το JSON φράσεων: {args.phrase_plan}") from exc
        if not isinstance(groups, list):
            raise SystemExit("Το JSON φράσεων πρέπει να είναι λίστα.")
        ledger = record_phrase_anchors(ledger, groups)
    output = write_reference_ledger(args.output, ledger)
    phrase_count = len(ledger.get("phrase_anchors", []))
    print(
        f"Δημιουργήθηκε ιδιωτικό ledger {output} με {ledger['score']['note_count']} σημεία Neanes"
        f" και {phrase_count} φράσεις."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
