#!/usr/bin/env python3
"""Create a private EZ glyph/line review sheet from a vector report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ez_phrase_review import EzPhraseReviewError, build_ez_phrase_review_sheet


def main() -> int:
    parser = argparse.ArgumentParser(description="Ιδιωτική καρτέλα ελέγχου φράσεων EZ")
    parser.add_argument("vector_report", type=Path, help="JSON από extract_vector_pdf.py")
    parser.add_argument("mapping_template", type=Path, help="Ιδιωτικό JSON από build_ez_mapping_template.py")
    parser.add_argument("--output", required=True, type=Path, help="Ιδιωτικό JSON καρτέλας")
    parser.add_argument("--line-tolerance", type=float, default=7.0, help="Ανοχή κατακόρυφης ομαδοποίησης σε PDF points")
    arguments = parser.parse_args()
    try:
        result = build_ez_phrase_review_sheet(
            json.loads(arguments.vector_report.read_text(encoding="utf-8")),
            json.loads(arguments.mapping_template.read_text(encoding="utf-8")),
            line_tolerance=arguments.line_tolerance,
        )
    except (EzPhraseReviewError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Δημιουργήθηκαν {result['notation_glyph_count']} ιδιωτικά glyph occurrences σε {sum(page['notation_line_count'] for page in result['pages'])} γραμμές ελέγχου.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
