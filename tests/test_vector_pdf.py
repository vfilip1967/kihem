import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf as fitz

from src.vector_pdf import (
    assess_visual_evidence,
    extract_vector_pdf,
    parse_page_spec,
    rank_shape_candidates,
    write_glyph_atlas,
)


class VectorPdfTests(unittest.TestCase):
    def test_ranks_a_same_shape_candidate_first(self):
        source = (1, 0, 1, 0)
        candidates = [
            {"glyph_name": "other", "signature": (0, 1, 0, 1), "aspect_ratio": 1.0},
            {"glyph_name": "same", "signature": source, "aspect_ratio": 1.0},
        ]
        ranked = rank_shape_candidates(source, 1.0, candidates)
        self.assertEqual(ranked[0]["glyph_name"], "same")
        self.assertEqual(ranked[0]["visual_similarity"], 1.0)
        self.assertEqual(assess_visual_evidence(ranked), "reviewable-shape-only")
        self.assertEqual(assess_visual_evidence([{**ranked[0], "visual_similarity": 0.7}]), "insufficient-shape-evidence")

    def test_parse_page_spec_is_one_based_and_deduplicated(self):
        self.assertEqual(parse_page_spec("2-3,1,2", 3), (2, 3, 1))
        with self.assertRaisesRegex(ValueError, "εκτός PDF"):
            parse_page_spec("4", 3)
        with self.assertRaisesRegex(ValueError, "Ανάστροφο"):
            parse_page_spec("3-2", 3)

    def test_extracts_vector_text_and_position_without_inferring_notes(self):
        with TemporaryDirectory() as temporary:
            source = Path(temporary) / "sample.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "Kyrie")
            document.save(source)
            document.close()

            report = extract_vector_pdf(source, (1,))
            self.assertEqual(report["schema"], 1)
            self.assertEqual(report["purpose"], "private-vector-pdf-analysis; no-note-semantics-inferred")
            self.assertEqual(report["document"]["page_count"], 1)
            page_report = report["pages"][0]
            self.assertEqual(page_report["image_count"], 0)
            self.assertEqual(page_report["glyphs"][0]["text"], "K")
            self.assertGreaterEqual(page_report["glyphs"][0]["glyph_id"], 0)
            self.assertGreater(page_report["fonts"][0]["distinct_glyph_ids"], 0)
            span = page_report["spans"][0]
            self.assertEqual(span["text"], "Kyrie")
            self.assertEqual(span["characters"][0]["codepoint"], "U+004B")
            self.assertEqual(len(span["bbox"]), 4)

            atlas = write_glyph_atlas(source, Path(temporary) / "atlas", (1,), ["Helvetica"])

            self.assertEqual(len(atlas["samples"]), 5)
            self.assertIn("glyph_id", atlas["samples"][0])
            self.assertTrue((Path(temporary) / "atlas" / "glyph-atlas.json").is_file())
            self.assertTrue((Path(temporary) / "atlas" / atlas["samples"][0]["file"]).is_file())
