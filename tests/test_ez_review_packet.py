import json
import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz

from src.ez_review_packet import EzReviewPacketError, create_ez_line_review_packet


def review_sheet():
    return {
        "purpose": "private-ez-phrase-review-sheet; no-musical-meaning-inferred",
        "source_label": "test source",
        "pages": [
            {
                "number": 1,
                "lines": [
                    {
                        "id": "page-1-line-1",
                        "bbox": [10, 10, 50, 30],
                        "source_glyphs": [
                            {
                                "source_anchor": {"pdf_font_instance": "1:EZ", "pdf_glyph_id": 7, "pua_codepoint": "U+F031"},
                                "source_definition": {"source_name": "oligon"},
                            }
                        ],
                        "nearby_text_candidates": [{"text": "δοκιμή"}],
                    }
                ],
            }
        ],
    }


class EzReviewPacketTests(unittest.TestCase):
    def test_writes_private_crop_checklist_and_empty_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "source.pdf"
            document = fitz.open()
            document.new_page(width=100, height=100)
            document.save(pdf)
            document.close()
            output = create_ez_line_review_packet(
                review_sheet(), line_id="page-1-line-1", source_pdf=pdf, output_directory=root / "packet"
            )
            self.assertTrue(output["crop"].is_file())
            self.assertIn("Οπτικός έλεγχος", output["checklist"].read_text(encoding="utf-8"))
            plan = json.loads(output["phrase_plan"].read_text(encoding="utf-8"))
            self.assertFalse(plan["confirmed"])
            self.assertEqual(plan["events"], [])
            self.assertEqual(plan["unassigned_source_anchors"][0]["pua_codepoint"], "U+F031")

    def test_records_existing_reviewer_readings_in_the_checklist(self):
        sheet = review_sheet()
        sheet["pages"][0]["lines"][0]["source_glyphs"] = [
            {
                "source_anchor": {"pdf_font_instance": "1:EZ+EZPsaltica", "pdf_glyph_id": 68, "pua_codepoint": "U+F03A"},
                "source_definition": {"source_name": "hapli"},
            }
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "source.pdf"
            document = fitz.open()
            document.new_page(width=100, height=100)
            document.save(pdf)
            document.close()
            output = create_ez_line_review_packet(sheet, line_id="page-1-line-1", source_pdf=pdf, output_directory=root / "packet")

            checklist = output["checklist"].read_text(encoding="utf-8")
            self.assertIn("Όσα έχουν ήδη επιβεβαιωθεί από τον ψάλτη", checklist)
            self.assertIn("απλή χρονική: προσθέτει μία χρονική μονάδα", checklist)

    def test_rejects_missing_line(self):
        with self.assertRaisesRegex(EzReviewPacketError, "Δεν βρέθηκε γραμμή"):
            create_ez_line_review_packet(review_sheet(), line_id="missing", source_pdf="/missing.pdf", output_directory="/tmp/x")
