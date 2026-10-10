#!/usr/bin/env python3
"""Extract ordered EZ PUA characters directly from a legacy Word .doc file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ez_font_mapping import EZ_FONT_FILES
from src.ez_word import EzWordExtractionError, extract_ez_word_document


def main() -> int:
    parser = argparse.ArgumentParser(description="Ιδιωτική εξαγωγή χαρακτήρων EZ από παλαιό Word .doc")
    parser.add_argument("source", type=Path, help="Τοπικό .doc γραμμένο με EZ fonts")
    parser.add_argument("--source-label", required=True, help="Προέλευση και επιτρεπόμενος σκοπός χρήσης")
    parser.add_argument("--output", required=True, type=Path, help="Ιδιωτικό JSON report")
    parser.add_argument("--wvware", default="wvWare", help="Εκτελέσιμο wvWare (προεπιλογή: wvWare)")
    arguments = parser.parse_args()
    try:
        report = extract_ez_word_document(
            arguments.source,
            source_label=arguments.source_label,
            known_fonts=EZ_FONT_FILES,
            executable=arguments.wvware,
        )
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (EzWordExtractionError, OSError) as error:
        parser.error(str(error))
    print(
        f"Εξήχθησαν {report['pua_occurrence_count']} χαρακτήρες EZ σε "
        f"{report['paragraph_count_with_pua']} παραγράφους Word. Δεν δημιουργήθηκε .byzx."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
