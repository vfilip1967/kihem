import unittest

from src.pdf_font_forensics import parse_to_unicode_mappings


class PdfFontForensicsTests(unittest.TestCase):
    def test_reads_only_bfchar_mappings(self):
        source = """
        <0000> <FFFF>
        2 beginbfchar
        <0001> <03A0>
        <0002> <03B1>
        endbfchar
        """
        self.assertEqual(
            parse_to_unicode_mappings(source),
            [{"cid": "0x0001", "unicode": "Π"}, {"cid": "0x0002", "unicode": "α"}],
        )
