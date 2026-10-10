#!/usr/bin/env python3
"""Write a private feasibility report for embedded fonts in a score PDF."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pdf_font_forensics import inspect_embedded_fonts
from src.vector_pdf import parse_page_spec


def main() -> int:
    parser = argparse.ArgumentParser(description="Ιδιωτική επιθεώρηση ενσωματωμένων PDF γραμματοσειρών")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", help="Σελίδες, π.χ. 11-12,19. Προεπιλογή: όλες.")
    parser.add_argument("--font-name", action="append", default=[], help="Μέρος ονόματος γραμματοσειράς.")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    import pymupdf as fitz

    with fitz.open(arguments.pdf) as document:
        pages = parse_page_spec(arguments.pages, document.page_count)
    report = inspect_embedded_fonts(arguments.pdf, pages, arguments.font_name)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    feasible = sum(bool(font["font_program"].get("direct_semantic_mapping_feasible")) for font in report["fonts"])
    print(f"Ελέγχθηκαν {len(report['fonts'])} font instances. Άμεσα αξιοποιήσιμα: {feasible}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
