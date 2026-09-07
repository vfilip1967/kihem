import unittest
from datetime import date, datetime, timezone
from tempfile import TemporaryDirectory

from src.melodos import MelodosClient, MelodosError, parse_tone


SAMPLE_ORTHROS = """
<!doctype html><html><body>
<script>alert('outside')</script>
<div id="div1">
  <a href="https://example.invalid">remote link</a><br>
  <span style="color:green">Κυριακή 6 Σεπτεμβρίου 2026</span><br>
  Ήχος εβδομάδος πλ α΄.<br>
  <span class="ep" onclick="bad()">ΟΡΘΡΟΣ</span><br>
  <span class="ar">ΧΟΡΟΣ:</span> Ἀμήν.<br>
  <select><option>audio</option></select>
  <script>alert('inside')</script>
</div></body></html>
"""

POLYTONIC_SAMPLE = """
<div id="div1" style="text-align:center">
  <span style="color:green;">Κυριακή 13 Σεπτεμβρίου 2026</span><br>
  <span class="ar">Ἀ</span>π᾿ ἐμοῦ· τῷ ᾅδῃ, ᾠδὴν καὶ ῥῆμα.<br>
  <span class="ep">Ἦχος πλ. β΄</span><br>/////////////////////
</div>
"""


class MelodosTests(unittest.TestCase):
    def test_parse_tone_variants(self):
        self.assertEqual(parse_tone("Ήχος εβδομάδος πλ α΄."), 5)
        self.assertEqual(parse_tone("Ήχος εβδομάδος βαρύς."), 7)
        self.assertIsNone(parse_tone("χωρίς επικεφαλίδα"))

    def test_parser_keeps_roles_but_removes_remote_interactivity(self):
        document = MelodosClient.parse_document(
            SAMPLE_ORTHROS, "orthros", fetched_at=datetime(2026, 9, 6, tzinfo=timezone.utc)
        )
        self.assertEqual(document.tone, 5)
        self.assertIn("ΟΡΘΡΟΣ", document.service_html)
        self.assertIn('class="ar"', document.service_html)
        self.assertNotIn("script", document.service_html)
        self.assertNotIn("select", document.service_html)
        self.assertNotIn("onclick", document.service_html)
        self.assertNotIn("example.invalid", document.service_html)

    def test_polytonic_codepoints_and_source_color_marker_are_preserved(self):
        document = MelodosClient.parse_document(
            POLYTONIC_SAMPLE,
            "orthros",
            fetched_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
        )
        self.assertIn("Ἀ</span>π᾿ ἐμοῦ· τῷ ᾅδῃ, ᾠδὴν καὶ ῥῆμα", document.service_html)
        self.assertIn('class="melodos-green"', document.service_html)
        self.assertIn("Ἦχος πλ. β΄", document.service_html)
        self.assertIn("/////////////////////", document.service_html)

    def test_payload_is_new_calendar_and_correct_service_defaults(self):
        with TemporaryDirectory() as temporary:
            client = MelodosClient(cache_dir=temporary)
            orthros = client._payload(date(2026, 9, 6), "orthros")
            liturgy = client._payload(date(2026, 9, 6), "litourgia")
            self.assertEqual(orthros["palaio"], "0")
            self.assertEqual(orthros["odes_oles"], "0")
            self.assertEqual(liturgy["tipika"], "0")
            self.assertEqual(liturgy["tipos_akolouthias"], "litourgia")

    def test_client_accepts_non_sunday(self):
        with TemporaryDirectory() as temporary:
            client = MelodosClient(cache_dir=temporary)
            client._validate(date(2026, 9, 7), "orthros")

    def test_client_rejects_date_outside_melodos_selector(self):
        with TemporaryDirectory() as temporary:
            client = MelodosClient(cache_dir=temporary)
            with self.assertRaisesRegex(ValueError, "2015 έως το 2029"):
                client._validate(date(2030, 1, 6), "orthros")

    def test_source_date_window_error_is_reported_explicitly(self):
        limited = "<h2>Η αναζήτηση μπορεί να γίνει.<br>Επίλεξε λοιπόν ακολουθίες από 4 έως 13 Σεπτεμβρίου.</h2>"
        with self.assertRaisesRegex(MelodosError, "4 έως 13 Σεπτεμβρίου"):
            MelodosClient._assert_final_page(limited, "orthros")
