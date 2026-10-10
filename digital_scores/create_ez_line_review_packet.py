#!/usr/bin/env python3
"""Create a private visual-review packet for one EZ notation line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ez_review_packet import EzReviewPacketError, create_ez_line_review_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Ιδιωτικό πακέτο οπτικού ελέγχου γραμμής EZ")
    parser.add_argument("review_sheet", type=Path, help="Ιδιωτικό JSON από build_ez_phrase_review_sheet.py")
    parser.add_argument("--line", required=True, dest="line_id", help="id γραμμής, π.χ. page-1-line-7")
    parser.add_argument("--source-pdf", required=True, type=Path, help="Τοπικό PDF πηγής")
    parser.add_argument("--output-dir", required=True, type=Path, help="Ιδιωτικός φάκελος πακέτου")
    arguments = parser.parse_args()
    try:
        output = create_ez_line_review_packet(
            json.loads(arguments.review_sheet.read_text(encoding="utf-8")),
            line_id=arguments.line_id,
            source_pdf=arguments.source_pdf,
            output_directory=arguments.output_dir,
        )
    except (EzReviewPacketError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print("Δημιουργήθηκε ιδιωτικό πακέτο ελέγχου:")
    for name, path in output.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
