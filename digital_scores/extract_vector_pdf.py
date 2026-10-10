#!/usr/bin/env python3
"""Create a private layout report from a born-digital music PDF.

The report is evidence for an eventual explicit font-glyph map. It is not an
OCR result, a licence to republish the input PDF, or a ``.byzx`` score.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vector_pdf import (
    extract_vector_pdf,
    parse_page_spec,
    write_glyph_atlas,
    write_neanes_glyph_suggestions,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ιδιωτική ανάλυση διανυσματικού μουσικού PDF")
    parser.add_argument("pdf", type=Path, help="Τοπικό PDF που επιτρέπεται να αναλυθεί")
    parser.add_argument("--pages", help="Σελίδες PDF, π.χ. 11-13,19. Προεπιλογή: όλες.")
    parser.add_argument("--output", required=True, type=Path, help="Ιδιωτικό αρχείο JSON εξόδου")
    parser.add_argument(
        "--glyph-atlas-dir",
        type=Path,
        help="Προαιρετικός ιδιωτικός φάκελος με μία οπτική δειγματοληψία ανά font/glyph.",
    )
    parser.add_argument(
        "--font",
        action="append",
        default=[],
        help="Γραμματοσειρά προς άτλαντα (επαναλαμβάνεται). Χωρίς αυτό: όλες οι γραμματοσειρές.",
    )
    parser.add_argument("--neanes-font", type=Path, help="Επίσημο αρχείο Neanes .otf για οπτική σύγκριση")
    parser.add_argument("--neanes-glyph-names", type=Path, help="Επίσημο Neanes SBMuFL glyphnames.json")
    parser.add_argument("--suggestions-output", type=Path, help="Ιδιωτικό JSON με οπτικές υποψήφιες αντιστοιχίσεις")
    parser.add_argument(
        "--reference-glyph-limit",
        type=int,
        default=96,
        help="Πλήθος αρχικών glyph Neanes προς σύγκριση (προεπιλογή 96, για ασφαλή χρήση μνήμης).",
    )
    arguments = parser.parse_args()

    import pymupdf as fitz

    with fitz.open(arguments.pdf) as document:
        pages = parse_page_spec(arguments.pages, document.page_count)
    report = extract_vector_pdf(arguments.pdf, pages)

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    atlas_message = ""
    if arguments.glyph_atlas_dir:
        atlas = write_glyph_atlas(arguments.pdf, arguments.glyph_atlas_dir, pages, arguments.font)
        atlas_message = f" Δημιουργήθηκαν {len(atlas['samples'])} ιδιωτικά δείγματα glyph."
    suggestion_values = (arguments.neanes_font, arguments.neanes_glyph_names, arguments.suggestions_output)
    if any(suggestion_values) and not all(suggestion_values):
        parser.error("Οι --neanes-font, --neanes-glyph-names και --suggestions-output δίνονται μαζί.")
    if all(suggestion_values):
        suggestions = write_neanes_glyph_suggestions(
            arguments.pdf,
            arguments.suggestions_output,
            arguments.neanes_font,
            arguments.neanes_glyph_names,
            pages,
            arguments.font,
            reference_glyph_limit=arguments.reference_glyph_limit,
        )
        atlas_message += f" Δημιουργήθηκαν {len(suggestions['suggestions'])} οπτικές προτάσεις Neanes προς έλεγχο."
    print(
        f"Αναλύθηκαν {len(report['pages'])} σελίδες σε {arguments.output}. "
        f"Δεν έχει παραχθεί μουσική μεταγραφή ή .byzx.{atlas_message}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
