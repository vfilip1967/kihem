from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from unittest import mock

from src.dcs import DcsClient, DcsError, parse_document, render_blocks, tone_from_text

FIXTURE = """
<html><head><title>x</title><script>var bad = 1;</script></head><body>
<div class='agesMenu'><a href='#'>Menu</a></div>
<div class='content'><table><tbody>
<tr><td><p class='sb_cover1'><span class='kvp'>Ἀκολουθία τοῦ Ἑσπερινοῦ</span></p></td></tr>
<tr><td><p class='sb_cover3'><span class='kvp'>τῇ Κυριακῇ, τῆς 8ης Νοεμβρίου</span></p></td></tr>
<tr><td><p class='sb_cover4'><span class='kvp'>Ὀκτώηχος - Ἦχος πλ. βʹ.</span></p></td></tr>
<tr><td><p class='sb_cover5'><span class='kvp'>Μηναῖον - Τῌ Θʹ ΝΟΕΜΒΡΙΟΥ</span></p></td></tr>
<tr><td><p class='designation'><span class='kvp'>Ψαλμὸς ΡΓʹ (103).</span></p></td></tr>
<tr><td><p class='mode'><span class='kvp'>Ἦχος πλ. βʹ.</span></p></td></tr>
<tr><td><p>Π<span class='kvp'>ᾶσα πνοὴ αἰνεσάτω</span></p></td></tr>
<tr><td><span class='kvp'><div class='media-group'><a href='score.pdf'>c1013 - Score</a></div></span></td></tr>
<tr><td><p class='rubric'><span class='kvp'>Εἰς τὴν εἴσοδον.</span></p></td></tr>
<tr><td><p class='hymn'><span class='kvp'>Φῶς ἱλαρόν.</span></p></td></tr>
<tr><td><p class='bookmark'>bookmark</p></td></tr>
<tr><td><p class='verse'>Στίχ. ὁ Θεός.</p></td></tr>
<tr><td><p class='reading'>Ἀνάγνωσις.</p></td></tr>
<tr><td><p>Link to Vesperal Prayers</p></td></tr>
</tbody></table></div></body></html>
"""


class ParseTests(unittest.TestCase):
    def test_blocks_keep_only_liturgical_parts(self):
        blocks, cover = parse_document(FIXTURE)
        kinds = [block.kind for block in blocks]
        texts = [block.text for block in blocks]

        self.assertEqual(cover[0], "Ἀκολουθία τοῦ Ἑσπερινοῦ")
        self.assertIn("heading", kinds)
        self.assertIn("rubric", kinds)
        self.assertIn("hymn", kinds)
        self.assertIn("verse", kinds)
        self.assertIn("reading", kinds)
        self.assertNotIn("bookmark", texts)
        self.assertNotIn("Link to Vesperal Prayers", texts)
        self.assertFalse(any("c1013" in text for text in texts), "score dropdown must be dropped")

    def test_decorated_initial_is_merged_with_the_line(self):
        blocks, _ = parse_document(FIXTURE)
        self.assertIn("Πᾶσα πνοὴ αἰνεσάτω", [block.text for block in blocks])

    def test_render_escapes_markup(self):
        blocks, _ = parse_document(FIXTURE.replace("Φῶς ἱλαρόν.", "5 < 6 καὶ 7 > 3"))
        html = render_blocks(blocks)
        self.assertIn("&lt;", html)
        self.assertIn("&gt;", html)
        self.assertNotIn("5 < 6", html)

    def test_script_tags_are_removed_before_rendering(self):
        blocks, _ = parse_document(FIXTURE.replace("Φῶς ἱλαρόν.", "<script>alert(1)</script>Φῶς"))
        html = render_blocks(blocks)
        self.assertNotIn("script", html.lower())

    def test_tone_labels(self):
        self.assertEqual(tone_from_text("Ἦχος πλ. δʹ."), 8)
        self.assertEqual(tone_from_text("Ἦχος πλ. βʹ. Αὐτόμελον."), 6)
        self.assertEqual(tone_from_text("Ἦχος βαρύς."), 7)
        self.assertEqual(tone_from_text("Ἦχος αʹ."), 1)
        self.assertIsNone(tone_from_text("Ψαλμὸς ΡΓʹ"))


class _Response:
    def __init__(self, status_code: int, body: bytes):
        self.status_code = status_code
        self.content = body


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _client(self, responses):
        session = mock.Mock()
        session.get.side_effect = responses
        return DcsClient(self.tmp.name, session=session), session

    def test_falls_back_from_ve2_to_ve_and_caches(self):
        client, session = self._client([
            _Response(404, b""),
            _Response(200, FIXTURE.encode("utf-8")),
        ])
        document = client.fetch_service(date(2026, 11, 8))

        self.assertEqual(document.service, "esperinos")
        self.assertEqual(document.label, "Ἑσπερινός")
        self.assertIn("dcs-heading", document.service_html)
        self.assertEqual(document.tone, 6)
        self.assertIn("Ἦχος πλ. β΄", document.tone_label)
        self.assertEqual(session.get.call_count, 2)
        from pathlib import Path

        self.assertTrue(any(path.name.startswith("dcs-") for path in Path(self.tmp.name).iterdir()))

        # second call is served from the cache: no further HTTP traffic
        again = client.fetch_service(date(2026, 11, 8))
        self.assertEqual(session.get.call_count, 2)
        self.assertIn("Φῶς", again.service_html)

    def test_error_when_no_page_exists(self):
        client, _ = self._client([_Response(404, b""), _Response(404, b"")])
        with self.assertRaises(DcsError):
            client.fetch_service(date(2026, 11, 8))
