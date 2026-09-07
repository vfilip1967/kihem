import unittest
from datetime import date

from src.anastasimatarion import (
    BOOK_ID,
    PANDEKTI_BOOK_ID,
    catalog_books,
    catalog_pieces,
    enrich_service_html,
    get_piece,
)


class AnastasimatarionTests(unittest.TestCase):
    def test_pilot_catalog_uses_verified_pages(self):
        pieces = {piece.piece_id: piece for piece in catalog_pieces()}
        self.assertEqual(len(pieces), 12)
        self.assertEqual(
            [region.printed_page for region in pieces["eothinon-4"].regions],
            [198, 199, 200],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone6-great-doxology"].regions],
            [305, 306, 307, 308, 309, 310],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["plagal4-timiotera"].regions],
            [418, 419],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["resurrectional-evlogitaria"].regions],
            [17, 18, 19, 20],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["psalm-50-tone2"].regions],
            [490, 491, 492, 493, 494],
        )
        self.assertEqual(get_piece(BOOK_ID, "tone6-apolytikion").incipit, "Ἀγγελικαὶ Δυνάμεις")
        self.assertEqual(get_piece(PANDEKTI_BOOK_ID, "psalm-50-tone2").book_id, PANDEKTI_BOOK_ID)
        self.assertEqual(len(catalog_books()), 2)

    def test_matching_is_driven_by_content_not_weekday_or_date(self):
        source = "Ἀγγελικαὶ Δυνάμεις, ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.<br>"
        result = enrich_service_html(date(2026, 9, 14), "orthros", source)
        self.assertEqual(result.attachment_count, 1)

    def test_music_is_inserted_after_matching_hymn_not_as_an_appendix(self):
        source = (
            "<span>Ἀπολυτίκιον</span><br>"
            "Ἀγγελικαὶ Δυνάμεις, ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.<br>"
            '<span class="ep">Ἀπολυτίκιον τῶν Ἐγκαινίων.</span>'
        )
        result = enrich_service_html(date(2026, 9, 13), "orthros", source)
        self.assertEqual(result.attachment_count, 1)
        self.assertLess(result.html.index("Κύριε δόξα σοί"), result.html.index("music-attachment"))
        self.assertLess(result.html.index("music-attachment"), result.html.index("τῶν Ἐγκαινίων"))
        self.assertIn("music/ioannis-protopsaltis-1905/tone6-apolytikion/1.png", result.html)

    def test_repeated_liturgy_apolytikion_gets_an_attachment_each_time(self):
        line = "Ἀγγελικαὶ Δυνάμεις, ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.<br>"
        result = enrich_service_html(date(2026, 9, 13), "litourgia", line * 3)
        self.assertEqual(result.attachment_count, 3)
        self.assertEqual(result.html.count('class="music-attachment"'), 3)

    def test_great_doxology_requires_the_matching_tone_context(self):
        doxology_end = "γιος ὁ Θεός, Ἅγιος Ἰσχυρός, Ἅγιος Ἀθάνατος, ἐλέησον ἡμᾶς.<br>"
        without_tone = enrich_service_html(date(2026, 9, 8), "orthros", doxology_end)
        with_tone = enrich_service_html(
            date(2026, 9, 8), "orthros", "<span>Ἦχος πλ β΄</span><br>" + doxology_end
        )
        self.assertEqual(without_tone.attachment_count, 0)
        self.assertEqual(with_tone.attachment_count, 1)

    def test_plagal_fourth_timiotera_is_attached_after_sixth_refrain(self):
        refrain = (
            "Τὴν Τιμιωτέραν τῶν Χερουβείμ, καὶ ἐνδοξοτέραν ἀσυγκρίτως "
            "τῶν Σεραφείμ, τὴν ἀδιαφθόρως Θεὸν Λόγον τεκοῦσαν, "
            "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.<br>"
        )
        heading = (
            "Καὶ ψάλλεται ἡ Τιμιωτέρα στον ίδιο ήχο των καταβασιών. "
            "Ἦχος πλ δ΄ Ωδή της θεοτόκου<br>"
        )
        result = enrich_service_html(
            date(2026, 9, 13), "orthros", heading + refrain * 6 + "Θ΄ ᾠδή"
        )

        self.assertEqual(result.attachment_count, 1)
        self.assertNotIn("plagal4-timiotera", result.unmatched_piece_ids)
        self.assertEqual(result.html.count('data-music-piece="plagal4-timiotera"'), 1)
        self.assertLess(result.html.rindex("σὲ μεγαλύνομεν"), result.html.index("plagal4-timiotera"))
        self.assertLess(result.html.index("plagal4-timiotera"), result.html.index("Θ΄ ᾠδή"))

    def test_evlogitaria_are_attached_after_the_third_final_alleluia(self):
        ending = "λληλούϊα, Ἀλληλούϊα, Ἀλληλούϊα. Δόξα σοὶ ὁ Θεός.<br>"
        source = (
            "Ἐν συνεχεία ψάλλονται τά Ἀναστάσιμα εὐλογητάρια.<br>"
            + ending * 3
            + "Ἡ Ὑπακοή"
        )
        result = enrich_service_html(date(2026, 9, 13), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertEqual(result.html.count('data-music-piece="resurrectional-evlogitaria"'), 1)
        self.assertLess(result.html.rindex("Δόξα σοὶ ὁ Θεός"), result.html.index("resurrectional-evlogitaria"))
        self.assertLess(result.html.index("resurrectional-evlogitaria"), result.html.index("Ἡ Ὑπακοή"))

    def test_psalm_50_uses_the_pandekti_after_its_final_verse(self):
        source = (
            "Οι Χοροί, ψάλλουν σε ήχο β΄ τον Ν΄ Ψαλμόν, κατ’ αντιφωνίαν<br>"
            "Ἐλέησόν με, ὁ Θεός, κατὰ τὸ μέγα ἔλεός σου.<br>"
            "Τότε ἀνοίσουσιν ἐπὶ τὸ θυσιαστήριόν σου μόσχους.<br>"
            "Δόξα Πατρί"
        )
        result = enrich_service_html(date(2026, 9, 13), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertIn('data-music-piece="psalm-50-tone2"', result.html)
        self.assertIn("music/pandekti-orthrou-1851/psalm-50-tone2/1.png", result.html)
        self.assertIn("Μουσικὴ Πανδέκτη · Τόμος Β΄", result.html)
        self.assertLess(result.html.index("μόσχους"), result.html.index("psalm-50-tone2"))
        self.assertLess(result.html.index("psalm-50-tone2"), result.html.index("Δόξα Πατρί"))
