#!/usr/bin/env python3
"""Build a private EZ-font mapping template from an extracted vector-PDF report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ez_font_mapping import build_ez_font_inventory, build_ez_mapping_template


def main() -> int:
    parser = argparse.ArgumentParser(description="Ιδιωτικό template αντιστοίχισης EZ προς Neanes")
    parser.add_argument("vector_report", type=Path, help="JSON από extract_vector_pdf.py")
    parser.add_argument("--ez-font-dir", required=True, type=Path, help="Τοπικός φάκελος επίσημων EZ TTF")
    parser.add_argument("--output", required=True, type=Path, help="Ιδιωτικό JSON template εξόδου")
    parser.add_argument("--source-label", required=True, help="Ταυτοποίηση του επιτρεπτού δημόσιου δείγματος")
    parser.add_argument("--visual-candidates", type=Path, help="Προαιρετικό JSON από οπτικές προτάσεις")
    arguments = parser.parse_args()

    report = json.loads(arguments.vector_report.read_text(encoding="utf-8"))
    candidates: list[dict[str, object]] = []
    if arguments.visual_candidates:
        candidates = json.loads(arguments.visual_candidates.read_text(encoding="utf-8")).get("suggestions", [])
    template = build_ez_mapping_template(
        report,
        build_ez_font_inventory(arguments.ez_font_dir),
        source_label=arguments.source_label,
        visual_candidates=candidates,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Δημιουργήθηκαν {template['row_count']} ιδιωτικές γραμμές EZ προς έλεγχο. Δεν δημιουργήθηκε .byzx.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
