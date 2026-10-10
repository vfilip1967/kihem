import unittest

from src.ez_phrase_review import EzPhraseReviewError, build_ez_phrase_review_sheet


def template():
    return {
        "purpose": "private-ez-to-neanes-mapping-template; no-byzx-generated",
        "source_label": "test source",
        "rows": [
            {
                "source": {
                    "pdf_font": "EZPsaltica",
                    "pdf_font_instance": "1:EZ",
                    "pdf_glyph_id": 7,
                    "pua_codepoint": "U+F031",
                    "keyboard_keys": ["1"],
                    "character_table_group": ["ascending"],
                },
                "source_definition": {"source_name": "oligon", "neanes_candidate": {"element_type": "quantitativeNeume", "value": "Oligon"}},
            }
        ],
    }


class EzPhraseReviewTests(unittest.TestCase):
    def test_groups_known_occurrences_by_staff_line_without_assigning_them_to_text(self):
        report = {
            "pages": [
                {
                    "number": 1,
                    "glyphs": [
                        {"font_instance": "1:EZ", "glyph_id": 7, "codepoint": "U+F031", "bbox": [10, 100, 20, 110], "origin": [10, 108], "sequence": 4},
                        {"font_instance": "1:EZ", "glyph_id": 7, "codepoint": "U+F031", "bbox": [30, 103, 40, 113], "origin": [30, 111], "sequence": 5},
                    ],
                    "spans": [{"font": "GreekText", "text": "συλλαβή", "bbox": [8, 114, 45, 126], "location": {"block": 1}}],
                }
            ]
        }
        result = build_ez_phrase_review_sheet(report, template())
        line = result["pages"][0]["lines"][0]
        self.assertEqual(result["notation_glyph_count"], 2)
        self.assertEqual(len(line["source_glyphs"]), 2)
        self.assertEqual(line["nearby_text_candidates"][0]["text"], "συλλαβή")
        self.assertEqual(line["review"]["status"], "unreviewed")
        self.assertEqual(line["review"]["note_events"], [])

    def test_rejects_non_ez_template(self):
        with self.assertRaisesRegex(EzPhraseReviewError, "έγκυρο EZ"):
            build_ez_phrase_review_sheet({"pages": []}, {"purpose": "wrong"})

    def test_keeps_gorgon_as_an_attachment_candidate_with_two_possible_bases(self):
        sheet = template()
        sheet["rows"].extend(
            [
                {
                    "source": {"pdf_font": "EZPsaltica", "pdf_font_instance": "1:EZ", "pdf_glyph_id": 8, "pua_codepoint": "U+F053", "keyboard_keys": ["S"], "character_table_group": ["time"]},
                    "source_definition": {"neanes_candidate": {"element_type": "gorgonNeume", "value": None}},
                },
                {
                    "source": {"pdf_font": "EZPsaltica", "pdf_font_instance": "1:EZ", "pdf_glyph_id": 9, "pua_codepoint": "U+F031", "keyboard_keys": ["1"], "character_table_group": ["ascending"]},
                    "source_definition": {"neanes_candidate": {"element_type": "quantitativeNeume", "value": "Oligon"}},
                },
            ]
        )
        report = {"pages": [{"number": 1, "glyphs": [
            {"font_instance": "1:EZ", "glyph_id": 7, "codepoint": "U+F031", "bbox": [10, 100, 20, 110], "origin": [10, 108]},
            {"font_instance": "1:EZ", "glyph_id": 8, "codepoint": "U+F053", "bbox": [21, 100, 22, 110], "origin": [21, 108]},
            {"font_instance": "1:EZ", "glyph_id": 9, "codepoint": "U+F031", "bbox": [25, 100, 35, 110], "origin": [25, 108]},
        ], "spans": []}]}
        candidate = build_ez_phrase_review_sheet(report, sheet)["pages"][0]["lines"][0]["attachment_candidates"][0]
        self.assertEqual(candidate["attachment_type"], "gorgonNeume")
        self.assertEqual(candidate["attachment_position"], 2)
        self.assertEqual(candidate["nearest_previous_base_position"], 1)
        self.assertEqual(candidate["nearest_following_base_position"], 3)
