from __future__ import annotations

import unittest

from src.vespers_music import attach_music

HIT = """
<h3 class="dcs-heading">Ἀπολυτίκιον Ἀναστάσιμον.</h3>
<p class="dcs-mode">Ἦχος πλ. βʹ.</p>
<p class="dcs-hymn">Ἀγγελικαὶ Δυνάμεις ἐπὶ τὸ μνῆμά σου, καὶ οἱ φυλάσσοντες ἀπενεκρώθησαν.</p>
<h3 class="dcs-heading">Ἀπόστιχα.</h3>
<p class="dcs-hymn">Ἕτερόν τι.</p>
"""

DIALOG_ONLY = """
<h3 class="dcs-heading">Ἀπολυτίκιον.</h3>
<p class="dcs-dialog">ΧΟΡΟΣ: Κύριε, ἐλέησον.</p>
<p class="dcs-hymn">Ἄλλο ἀπολυτίκιον ἡμέρας, χωρὶς γνωστὸ μέλος.</p>
"""

MISS = """
<h3 class="dcs-heading">Ἀπολυτίκιον.</h3>
<p class="dcs-hymn">Ἄλλο ἀπολυτίκιον ἡμέρας.</p>
"""


DOXASTIKON = """
<h3 class="dcs-heading">Δοξαστικόν.</h3>
<p class="dcs-hymn">Αὕτη ἡ ἡμέρα Κυρίου, ἀγαλλιάσθε λαοί.</p>
"""

LITURGY_TEXT_IN_APOLYTIKION = """
<h3 class="dcs-heading">Ἀπολυτίκιον.</h3>
<p class="dcs-hymn">Πατέρα, Υἱὸν καὶ Ἅγιον Πνεῦμα, Τριάδα ὁμοούσιον.</p>
"""


class AttachTests(unittest.TestCase):
    def test_attaches_the_verified_apolytikion(self):
        html, bookmarks, pieces = attach_music(HIT)

        self.assertEqual(pieces, ["tone6-apolytikion"])
        self.assertIn('data-music-piece="tone6-apolytikion"', html)
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks[0]["anchor_id"], "music-tone6-apolytikion-1")
        self.assertIn(bookmarks[0]["anchor_id"], html)
        self.assertLess(html.index("Ἀγγελικαὶ"), html.index("data-music-piece"))

    def test_dialogue_responses_cannot_trigger_a_piece(self):
        html, bookmarks, pieces = attach_music(DIALOG_ONLY)

        self.assertNotIn("litourgia-kyrie-eleison-pandekti", pieces)
        self.assertNotIn("data-music-piece", html)

    def test_no_match_leaves_the_document_untouched(self):
        html, bookmarks, pieces = attach_music(MISS)

        self.assertEqual(pieces, [])
        self.assertEqual(bookmarks, [])
        self.assertNotIn("music-attachment", html)

    def test_instance_numbers_continue_across_documents(self):
        _, bookmarks, _ = attach_music(HIT, instance_start=4)

        self.assertEqual(bookmarks[0]["anchor_id"], "music-tone6-apolytikion-5")

    def test_doxastikon_family_attaches_under_its_own_section(self):
        html, bookmarks, pieces = attach_music(DOXASTIKON)

        self.assertEqual(pieces, ["kypseli-08-doxastikon"])
        self.assertEqual(bookmarks[0]["anchor_id"], "music-kypseli-08-doxastikon-1")

    def test_section_families_block_cross_service_pieces(self):
        # A Liturgy setting of the Trinitarian formula must never land in the
        # Apolytikion just because its incipit appears there.
        html, bookmarks, pieces = attach_music(LITURGY_TEXT_IN_APOLYTIKION)

        self.assertEqual(pieces, [])
        self.assertNotIn("data-music-piece", html)

    def test_empty_document_is_safe(self):
        self.assertEqual(attach_music(""), ("", [], []))
