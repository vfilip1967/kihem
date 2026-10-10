import unittest

from src.ez_word import build_ez_word_report, declared_ez_fonts_from_table


class EzWordTests(unittest.TestCase):
    def test_finds_ez_font_names_in_a_word_table_stream(self):
        table = "Arial\x00EZ Psaltica\x00EZ Special-II\x00".encode("utf-16le")

        self.assertEqual(
            declared_ez_fonts_from_table(table, ["EZPsaltica", "EZ Special-II", "EZ Psaltica"]),
            ["EZPsaltica", "EZ Special-II"],
        )

    def test_keeps_word_pua_font_ownership_unresolved(self):
        xml = "<doc><p>κειμενο \uf030\uf04e</p></doc>"

        report = build_ez_word_report(
            xml,
            source_label="official test",
            source_filename="formula.doc",
            declared_fonts=["EZPsaltica", "EZSpecial-II"],
        )

        self.assertEqual(report["pua_occurrence_count"], 2)
        first = report["paragraphs"][0]["pua_occurrences"][0]
        self.assertEqual(first["pua_codepoint"], "U+F030")
        self.assertEqual(first["status"], "font-run-unresolved; no-neanes-event")
        self.assertEqual([entry["font"] for entry in first["font_candidates"]], ["EZPsaltica", "EZSpecial-II"])
        self.assertIn("κειμενο", report["paragraphs"][0]["nearby_text"])
