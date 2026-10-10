import unittest

from src.ez_font_mapping import build_ez_mapping_template


class EzFontMappingTests(unittest.TestCase):
    def test_creates_an_unconfirmed_row_without_generating_neanes_semantics(self):
        report = {
            "pages": [
                {
                    "glyphs": [
                        {
                            "font": "EZPsaltica",
                            "font_instance": "14:EZPsaltica",
                            "glyph_id": 76,
                            "codepoint": "U+F030",
                        }
                    ]
                }
            ]
        }
        inventory = {
            "EZPsaltica": {
                "font_file": "EZ Psaltica.TTF",
                "role": "base_or_precomposed_neume",
                "entries": {"U+F030": {"glyph_name": "uniF030", "glyph_id": 76, "keyboard_keys": ["0"]}},
            }
        }

        result = build_ez_mapping_template(report, inventory, source_label="official sample")

        self.assertEqual(result["row_count"], 1)
        row = result["rows"][0]
        self.assertTrue(row["source"]["glyph_id_matches_full_font"])
        self.assertEqual(row["source"]["keyboard_keys"], ["0"])
        self.assertEqual(row["source"]["character_table_group"], ["ascending"])
        self.assertEqual(row["neanes"]["status"], "unconfirmed")
        self.assertIsNone(row["neanes"]["value"])
        self.assertEqual(row["source_definition"]["neanes_candidate"]["value"], "Ison")
        self.assertIn("no-byzx-generated", result["purpose"])

    def test_keeps_a_glyph_id_mismatch_visible_for_review(self):
        report = {"pages": [{"glyphs": [{"font": "EZPsaltica", "font_instance": "x", "glyph_id": 7, "codepoint": "U+F030"}]}]}
        inventory = {"EZPsaltica": {"font_file": "EZ Psaltica.TTF", "role": "base", "entries": {"U+F030": {"glyph_name": "uniF030", "glyph_id": 76}}}}

        row = build_ez_mapping_template(report, inventory, source_label="official sample")["rows"][0]

        self.assertFalse(row["source"]["glyph_id_matches_full_font"])

    def test_adds_a_source_documented_candidate_without_approving_a_byzx_value(self):
        report = {"pages": [{"glyphs": [{"font": "EZPsaltica", "font_instance": "x", "glyph_id": 5, "codepoint": "U+F031"}]}]}
        inventory = {"EZPsaltica": {"font_file": "EZ Psaltica.TTF", "role": "base", "entries": {"U+F031": {"glyph_name": "uniF031", "glyph_id": 5}}}}

        row = build_ez_mapping_template(report, inventory, source_label="official sample")["rows"][0]

        self.assertEqual(row["source_definition"]["source_name"], "oligon (up one)")
        self.assertEqual(row["source_definition"]["neanes_candidate"]["value"], "Oligon")
        self.assertEqual(row["neanes"]["status"], "unconfirmed")

    def test_marks_non_keyboard_macro_glyphs_as_unclassified(self):
        report = {"pages": [{"glyphs": [{"font": "EZPsaltica", "font_instance": "x", "glyph_id": 9, "codepoint": "U+F0D0"}]}]}
        inventory = {"EZPsaltica": {"font_file": "EZ Psaltica.TTF", "role": "base", "entries": {"U+F0D0": {"glyph_name": "uniF0D0", "glyph_id": 9, "keyboard_keys": []}}}}

        row = build_ez_mapping_template(report, inventory, source_label="official sample")["rows"][0]

        self.assertEqual(row["source"]["character_table_group"], [])

    def test_skips_the_ez_font_space_character(self):
        report = {"pages": [{"glyphs": [{"font": "EZPsaltica", "font_instance": "x", "glyph_id": 3, "codepoint": "U+F020"}]}]}
        inventory = {"EZPsaltica": {"font_file": "EZ Psaltica.TTF", "role": "base", "entries": {"U+F020": {"glyph_name": "uniF020", "glyph_id": 3, "keyboard_keys": [" "]}}}}

        result = build_ez_mapping_template(report, inventory, source_label="official sample")

        self.assertEqual(result["row_count"], 0)

    def test_adds_documented_ez_special_isokratema_as_an_ison_candidate(self):
        report = {"pages": [{"glyphs": [{"font": "EZSpecial-II", "font_instance": "x", "glyph_id": 38, "codepoint": "U+F04E"}]}]}
        inventory = {"EZSpecial-II": {"font_file": "EZ Special-II.TTF", "role": "support", "entries": {"U+F04E": {"glyph_name": "uniF04E", "glyph_id": 38, "keyboard_keys": ["N"]}}}}

        row = build_ez_mapping_template(report, inventory, source_label="official sample")["rows"][0]

        self.assertEqual(row["source_definition"]["source_name"], "isokratema Ga (Γ)")
        self.assertEqual(row["source_definition"]["neanes_candidate"], {"element_type": "ison", "value": "Ison.Ga"})

    def test_adds_review_confirmed_vareia_as_a_non_timed_note_property(self):
        report = {"pages": [{"glyphs": [{"font": "EZPsaltica", "font_instance": "x", "glyph_id": 25, "codepoint": "U+F07A"}]}]}
        inventory = {"EZPsaltica": {"font_file": "EZ Psaltica.TTF", "role": "base", "entries": {"U+F07A": {"glyph_name": "uniF07A", "glyph_id": 25, "keyboard_keys": ["z"]}}}}

        row = build_ez_mapping_template(report, inventory, source_label="official sample")["rows"][0]

        self.assertEqual(row["source_definition"]["source_name"], "vareia (τροπικό, άχρονο)")
        self.assertEqual(row["source_definition"]["neanes_candidate"]["value"], True)

    def test_adds_review_confirmed_ison_variant(self):
        report = {"pages": [{"glyphs": [{"font": "EZPsaltica", "font_instance": "x", "glyph_id": 33, "codepoint": "U+F027"}]}]}
        inventory = {"EZPsaltica": {"font_file": "EZ Psaltica.TTF", "role": "base", "entries": {"U+F027": {"glyph_name": "uniF027", "glyph_id": 33, "keyboard_keys": ["'"]}}}}

        row = build_ez_mapping_template(report, inventory, source_label="official sample")["rows"][0]

        self.assertEqual(row["source_definition"]["source_name"], "ison (variant)")
        self.assertEqual(row["source_definition"]["neanes_candidate"]["value"], "Ison")

    def test_adds_review_confirmed_hapli_as_one_time_unit(self):
        report = {"pages": [{"glyphs": [{"font": "EZPsaltica", "font_instance": "x", "glyph_id": 68, "codepoint": "U+F03A"}]}]}
        inventory = {"EZPsaltica": {"font_file": "EZ Psaltica.TTF", "role": "base", "entries": {"U+F03A": {"glyph_name": "uniF03A", "glyph_id": 68, "keyboard_keys": [":"]}}}}

        row = build_ez_mapping_template(report, inventory, source_label="official sample")["rows"][0]

        self.assertEqual(row["source_definition"]["source_name"], "hapli / απλή χρονική (μία χρονική μονάδα)")
        self.assertEqual(row["source_definition"]["neanes_candidate"], {"element_type": "timeNeume", "value": "Hapli"})
