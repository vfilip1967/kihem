import json
import unittest

from src.ez_word_runs import build_ez_word_run_report, canonical_ez_font


class EzWordRunTests(unittest.TestCase):
    def test_normalizes_official_word_font_names(self):
        self.assertEqual(canonical_ez_font("EZ Psaltica"), "EZPsaltica")
        self.assertEqual(canonical_ez_font("EZ Special-II"), "EZSpecial-II")
        self.assertIsNone(canonical_ez_font("Times New Roman"))

    def test_preserves_exact_font_owner_for_each_pua_character(self):
        lines = "\n".join(
            [
                json.dumps({"run_index": 3, "font_name": "EZ Psaltica", "text": "\uf030\uf07a", "pua_codepoints": ["U+F030", "U+F07A"]}),
                json.dumps({"run_index": 4, "font_name": "EZ Special-II", "text": "\uf04e", "pua_codepoints": ["U+F04E"]}),
            ]
        )

        report = build_ez_word_run_report(lines, source_label="test", source_filename="formula.doc")

        self.assertEqual(report["source_ez_fonts"], ["EZPsaltica", "EZSpecial-II"])
        first = report["runs"][0]["pua_occurrences"]
        self.assertEqual(first[0]["source_font"], "EZPsaltica")
        self.assertEqual(first[0]["source_definition"]["neanes_candidate"]["value"], "Ison")
        self.assertEqual(first[1]["source_definition"]["neanes_candidate"]["value"], True)
        self.assertEqual(report["runs"][1]["pua_occurrences"][0]["source_font"], "EZSpecial-II")

    def test_excludes_private_characters_from_a_non_ez_font(self):
        lines = json.dumps(
            {"run_index": 5, "font_name": "SymbolGreek", "text": "\uf063", "pua_codepoints": ["U+F063"]}
        )

        report = build_ez_word_run_report(lines, source_label="test", source_filename="formula.doc")

        occurrence = report["runs"][0]["pua_occurrences"][0]
        self.assertIsNone(occurrence["source_font"])
        self.assertEqual(occurrence["status"], "non-ez-font; excluded-from-ez-conversion")
        self.assertEqual(report["non_ez_run_fonts"], ["SymbolGreek"])
