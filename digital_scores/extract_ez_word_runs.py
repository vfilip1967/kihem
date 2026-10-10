#!/usr/bin/env python3
"""Read legacy EZ Word font runs through the private Apache POI helper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ez_word_runs import EzWordRunExtractionError, extract_ez_word_font_runs


def main() -> int:
    parser = argparse.ArgumentParser(description="Ιδιωτική εξαγωγή exact EZ font-runs από παλαιό Word .doc")
    parser.add_argument("source", type=Path, help="Τοπικό Word .doc")
    parser.add_argument("--source-label", required=True, help="Προέλευση και επιτρεπόμενος σκοπός χρήσης")
    parser.add_argument("--importer-jar", required=True, type=Path, help="Shaded JAR του word_importer")
    parser.add_argument("--output", required=True, type=Path, help="Ιδιωτικό JSON report")
    arguments = parser.parse_args()
    try:
        report = extract_ez_word_font_runs(
            arguments.source,
            source_label=arguments.source_label,
            importer_jar=arguments.importer_jar,
        )
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (EzWordRunExtractionError, OSError) as error:
        parser.error(str(error))
    print(
        f"Εξήχθησαν {report['pua_occurrence_count']} χαρακτήρες από "
        f"{report['font_run_count_with_pua']} Word font-runs. Δεν δημιουργήθηκε .byzx."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
