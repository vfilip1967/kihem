import unittest
from datetime import date

from src.anastasimatarion import (
    BOOK_ID,
    IRMOLOGION_BOOK_ID,
    KYPSELI_BOOK_ID,
    MusicBookmark,
    PANDEKTI_LITOURGIA_BOOK_ID,
    PANDEKTI_BOOK_ID,
    catalog_books,
    catalog_pieces,
    enrich_service_html,
    get_piece,
)


class AnastasimatarionTests(unittest.TestCase):
    def test_pilot_catalog_uses_verified_pages(self):
        pieces = {piece.piece_id: piece for piece in catalog_pieces()}
        self.assertEqual(len(pieces), 133)
        self.assertEqual(
            [region.printed_page for region in pieces["eothinon-4"].regions],
            [198, 199, 200],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone6-great-doxology"].regions],
            [305, 306, 307, 308, 309, 310],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone1-ainoi"].regions],
            [39, 40, 41, 42, 43],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone2-ainoi"].regions],
            [86, 87, 88, 89, 90, 91],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone3-ainoi"].regions],
            [138, 139, 140, 141, 142, 143, 144, 145],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone4-ainoi"].regions],
            [193, 194, 195, 196, 197, 198],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone5-ainoi"].regions],
            [244, 245, 246, 247, 248, 249, 250, 251],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone6-ainoi"].regions],
            [298, 299, 300, 301, 302, 303, 304],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone7-ainoi"].regions],
            [360, 361, 362, 363, 364, 365],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["eothinon-7"].regions],
            [365, 366],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone1-great-doxology"].regions],
            [45, 46, 47, 48],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["plagal4-timiotera"].regions],
            [418, 419],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone4-timiotera"].regions],
            [191, 192],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone4-anavathmoi-first-antiphon"].regions],
            [176, 177],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["resurrectional-evlogitaria"].regions],
            [17, 18, 19, 20],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["psalm-50-tone2"].regions],
            [490, 491, 492, 493, 494],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["cross-katavasies"].regions],
            [225, 226, 227, 227, 228, 228, 229, 230, 231, 232, 233, 234, 235],
        )
        self.assertEqual(get_piece(BOOK_ID, "tone6-apolytikion").incipit, "Ἀγγελικαὶ Δυνάμεις")
        self.assertEqual(get_piece(PANDEKTI_BOOK_ID, "psalm-50-tone2").book_id, PANDEKTI_BOOK_ID)
        self.assertEqual(get_piece(IRMOLOGION_BOOK_ID, "cross-katavasies").book_id, IRMOLOGION_BOOK_ID)
        self.assertEqual(len(catalog_books()), 16)
        self.assertEqual(
            get_piece(PANDEKTI_LITOURGIA_BOOK_ID, "litourgia-eisodikon-pandekti").book_id,
            PANDEKTI_LITOURGIA_BOOK_ID,
        )
        self.assertEqual(
            [region.printed_page for region in pieces["litourgia-eisodikon-pandekti"].regions],
            [41],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["litourgia-patera-pandekti"].regions],
            [255],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["litourgia-agapiso-pandekti"].regions],
            [251, 252],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["litourgia-trisagion-argon-pandekti"].regions],
            [43, 44, 45],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["litourgia-tone-1-amin-se-ymnoumen"].regions],
            [11, 12],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["litourgia-tone-1-axion-estin"].regions],
            [12, 13, 14],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["litourgia-tone-6-eis-mnimosynon"].regions],
            [72, 73, 74, 75],
        )
        self.assertEqual(
            [region.printed_page for region in pieces["kypseli-09-doxastikon"].regions],
            [57, 58],
        )
        self.assertEqual(
            get_piece(KYPSELI_BOOK_ID, "kypseli-08-apolytikion").book_id,
            KYPSELI_BOOK_ID,
        )

    def test_matching_is_driven_by_content_not_weekday_or_date(self):
        source = (
            "Ήχος εβδομάδος πλ β΄.<br>"
            "Ἀγγελικαὶ Δυνάμεις, ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.<br>"
        )
        result = enrich_service_html(date(2026, 9, 14), "orthros", source)
        self.assertEqual(result.attachment_count, 1)

    def test_music_is_inserted_after_matching_hymn_not_as_an_appendix(self):
        source = (
            "Ήχος εβδομάδος πλ β΄.<br><span>Ἀπολυτίκιον</span><br>"
            "Ἀγγελικαὶ Δυνάμεις, ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.<br>"
            '<span class="ep">Ἀπολυτίκιον τῶν Ἐγκαινίων.</span>'
        )
        result = enrich_service_html(date(2026, 9, 13), "orthros", source)
        self.assertEqual(result.attachment_count, 1)
        self.assertLess(result.html.index("Κύριε δόξα σοί"), result.html.index("music-attachment"))
        self.assertLess(result.html.index("music-attachment"), result.html.index("τῶν Ἐγκαινίων"))
        self.assertIn("music/ioannis-protopsaltis-1905/tone6-apolytikion/1.png", result.html)
        self.assertIn('id="music-tone6-apolytikion-1"', result.html)
        self.assertIn('href="#music-tone6-apolytikion-1"', result.html)
        self.assertIn("Σελιδοδείκτης · Ἀναστάσιμον Ἀπολυτίκιον", result.html)

    def test_repeated_liturgy_apolytikion_gets_an_attachment_each_time(self):
        line = "Ἀγγελικαὶ Δυνάμεις, ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.<br>"
        result = enrich_service_html(date(2026, 9, 13), "litourgia", line * 3)
        self.assertEqual(result.attachment_count, 3)
        self.assertEqual(result.html.count('class="music-attachment"'), 3)

    def test_bookmarks_keep_unique_ids_when_services_are_combined(self):
        source = "Ἀγγελικαὶ Δυνάμεις, ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.<br>"
        result = enrich_service_html(
            date(2026, 9, 13), "litourgia", source, instance_offset=11
        )

        self.assertEqual(result.bookmarks[0].anchor_id, "music-tone6-apolytikion-12")
        self.assertIn('id="music-tone6-apolytikion-12"', result.html)

    def test_bookmarks_follow_excerpt_order_in_the_finished_litourgia(self):
        # The matching rules are intentionally not the display order.  The
        # menu must follow the inserted excerpts in the returned document.
        source = (
            "ψάλλονται σε ήχο πλ β΄.<br>"
            "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες.<br>"
            "Κύριε, ἐλέησον.<br>"
            "Μονογενὴς Υἱὸς καὶ Λόγος.<br>"
            "Χριστιανὰ τὰ τέλη τῆς ζωῆς ἡμῶν.<br>"
            "Παράσχου Κύριε.<br>"
            "Ποτήριον σωτηρίου λήψομαι, καὶ τὸ ὄνομα Κυρίου ἐπικαλέσομαι.<br>"
        )
        result = enrich_service_html(date(2026, 9, 8), "litourgia", source)

        self.assertEqual(
            [bookmark.title for bookmark in result.bookmarks],
            [
                "Χερουβικὸν · σύντομον · ἦχος πλ. β΄ · Μελωδός",
                "Κύριε ἐλέησον · σύντομα · Μουσικὴ Πανδέκτη",
                "Ὁ Μονογενὴς Υἱὸς καὶ Λόγος · Μουσικὴ Πανδέκτη",
                "Κύριε ἐλέησον καὶ Παράσχου Κύριε · ἦχος πλ. β΄ · Μελωδός",
            ],
        )

    def test_great_doxology_requires_the_matching_tone_context(self):
        doxology_end = "γιος ὁ Θεός, Ἅγιος Ἰσχυρός, Ἅγιος Ἀθάνατος, ἐλέησον ἡμᾶς.<br>"
        without_tone = enrich_service_html(date(2026, 9, 8), "orthros", doxology_end)
        with_tone = enrich_service_html(
            date(2026, 9, 8),
            "orthros",
            "Ήχος εβδομάδος πλ β΄.<br>"
            "Σύμφωνα με το άγραφο τυπικό, η δοξολογία σήμερα ψάλλεται στον ήχο του δοξαστικού.<br>"
            "<span>Ἦχος πλ β΄</span><br>"
            "ἐν τῷ φωτί σου ὀψόμεθα φῶς.<br>" + doxology_end,
        )
        self.assertEqual(without_tone.attachment_count, 0)
        self.assertEqual(with_tone.attachment_count, 1)

    def test_great_doxology_does_not_attach_to_the_opening_trisagion(self):
        trisagion = "γιος ὁ Θεός, Ἅγιος Ἰσχυρός, Ἅγιος Ἀθάνατος, ἐλέησον ἡμᾶς.<br>"
        late_marker = "ἐν τῷ φωτί σου ὀψόμεθα φῶς.<br>"
        result = enrich_service_html(
            date(2026, 9, 8),
            "orthros",
            "Ήχος εβδομάδος πλ β΄.<br>"
            "Σύμφωνα με το άγραφο τυπικό, η δοξολογία σήμερα ψάλλεται στον ήχο του δοξαστικού.<br>"
            "<span>Ἦχος πλ β΄</span><br>"
            + trisagion + "Μεσότητα του Όρθρου<br>" + late_marker + trisagion,
        )

        self.assertEqual(result.attachment_count, 1)
        self.assertLess(result.html.index(late_marker[:-4]), result.html.index('data-music-piece="tone6-great-doxology"'))

    def test_local_plagal_second_doxology_overrides_a_different_weekly_tone(self):
        source = (
            "Ήχος εβδομάδος α΄.<br>"
            "Σύμφωνα με το άγραφο τυπικό, η δοξολογία σήμερα ψάλλεται στον ήχο του δοξαστικού.<br>"
            "Ἦχος πλ β΄<br>ΜΕΓΑΛΗ ΔΟΞΟΛΟΓΙΑ<br>"
            "Ὅτι παρὰ σοὶ πηγὴ ζωῆς, ἐν τῷ φωτί σου ὀψόμεθα φῶς.<br>"
            "Παράτεινον τὸ ἔλεός σου τοῖς γινώσκουσί σε.<br>"
            "Ἅγιος ὁ Θεός, Ἅγιος Ἰσχυρός, Ἅγιος Ἀθάνατος, ἐλέησον ἡμᾶς.<br>"
            "Ἀπολυτίκιον."
        )
        result = enrich_service_html(date(2026, 9, 28), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertIn('data-music-piece="tone6-great-doxology"', result.html)
        self.assertLess(
            result.html.index("Ἅγιος ὁ Θεός"),
            result.html.index('data-music-piece="tone6-great-doxology"'),
        )
        self.assertLess(
            result.html.index('data-music-piece="tone6-great-doxology"'),
            result.html.index("Ἀπολυτίκιον"),
        )

    def test_plagal_fourth_great_doxology_is_attached_from_its_local_melodos_tone(self):
        source = (
            '<span class="melodos-audio-context">Μουσικό απόσπασμα Μεγάλης Δοξολογίας · '
            'Ἦχος πλ. δ΄</span><select class="melodos-audio-picker"><option>Χορός</option></select><br>'
            '<span class="ep">ΜΕΓΑΛΗ ΔΟΞΟΛΟΓΙΑ</span><br>Δόξα σοι τῷ δείξαντι τὸ φῶς.<br>'
            'Ὅτι παρὰ σοὶ πηγὴ ζωῆς, ἐν τῷ φωτί σου ὀψόμεθα φῶς.<br>'
            '<span class="ar">Π</span>αράτεινον τὸ ἔλεός σου τοὶς γινώσκουσί σε.<br>'
            '<span class="ar">Ἅ</span>γιος ὁ Θεός.'
        )
        result = enrich_service_html(date(2026, 9, 26), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertIn('data-music-piece="plagal4-great-doxology"', result.html)
        self.assertLess(
            result.html.index("αράτεινον τὸ ἔλεός σου τοὶς γινώσκουσί σε."),
            result.html.index('data-music-piece="plagal4-great-doxology"'),
        )
        self.assertLess(
            result.html.index('data-music-piece="plagal4-great-doxology"'),
            result.html.index("γιος ὁ Θεός."),
        )
        self.assertEqual(
            result.bookmarks,
            (MusicBookmark("music-plagal4-great-doxology-1", "Μεγάλη Δοξολογία, πλ. δ΄ · Μανουὴλ Πρωτοψάλτου"),),
        )

    def test_first_tone_great_doxology_is_attached_from_melodos_local_selector(self):
        source = (
            '<span class="melodos-audio-context">Μουσικό απόσπασμα Μεγάλης Δοξολογίας · '
            'Ἦχος α΄</span><select class="melodos-audio-picker"><option>Χορός</option></select><br>'
            '<span class="ep">ΜΕΓΑΛΗ ΔΟΞΟΛΟΓΙΑ</span><br>Δόξα σοι τῷ δείξαντι τὸ φῶς.<br>'
            'Ὅτι παρὰ σοὶ πηγὴ ζωῆς, ἐν τῷ φωτί σου ὀψόμεθα φῶς.<br>'
            '<span class="ar">Π</span>αράτεινον τὸ ἔλεός σου τοὶς γινώσκουσί σε.<br>'
            '<span class="ar">Ἅ</span>γιος ὁ Θεός.<br>Σήμερον σωτηρία τῷ κόσμῳ γέγονεν.'
        )
        result = enrich_service_html(date(2026, 10, 4), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertIn('data-music-piece="tone1-great-doxology"', result.html)
        self.assertLess(
            result.html.index("αράτεινον τὸ ἔλεός σου τοὶς γινώσκουσί σε."),
            result.html.index('data-music-piece="tone1-great-doxology"'),
        )
        self.assertLess(
            result.html.index('data-music-piece="tone1-great-doxology"'),
            result.html.index("Σήμερον σωτηρία"),
        )
        self.assertEqual(
            result.bookmarks,
            (MusicBookmark("music-tone1-great-doxology-1", "Μεγάλη Δοξολογία, ἦχος α΄ · Μανουὴλ Πρωτοψάλτου"),),
        )

    def test_plagal_fourth_ainoi_follow_their_final_sticheron(self):
        source = (
            "Ήχος εβδομάδος πλ δ΄.<br>Αἶνοι<br>Στιχηρὰ Ἀναστάσιμα Ἦχος πλ δ΄<br>"
            "Πᾶσα πνοὴ αἰνεσάτω τὸν Κύριον. Αἰνεῖτε τὸν Κύριον ἐκ τῶν οὐρανῶν.<br>"
            "Κύριε, εἰ καὶ κριτηρίῳ παρέστης, ὑπὸ Πιλάτου κρινόμενος.<br>"
            "Παντοδύναμε Σωτὴρ ἐλέησον ἡμᾶς.<br>"
            "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ ΣΤ'"
        )
        result = enrich_service_html(date(2026, 9, 27), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertIn('data-music-piece="tone8-ainoi"', result.html)
        self.assertLess(
            result.html.index("Παντοδύναμε Σωτὴρ ἐλέησον ἡμᾶς."),
            result.html.index('data-music-piece="tone8-ainoi"'),
        )
        self.assertLess(
            result.html.index('data-music-piece="tone8-ainoi"'),
            result.html.index("ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ ΣΤ'"),
        )

    def test_sunday_ainoi_always_use_the_verified_slow_or_short_setting(self):
        expected = (
            ("α΄", "tone1-ainoi", "slow"),
            ("β΄", "tone2-ainoi", "slow"),
            ("γ΄", "tone3-ainoi", "short"),
            ("δ΄", "tone4-ainoi", "short"),
            ("πλ α΄", "tone5-ainoi", "slow"),
            ("πλ β΄", "tone6-ainoi", "slow"),
            ("βαρύς", "tone7-ainoi", "short"),
            ("πλ δ΄", "tone8-ainoi", "short"),
        )
        for tone, piece_id, form in expected:
            with self.subTest(tone=tone):
                source = (
                    f"Ήχος εβδομάδος {tone}.<br>"
                    f"Στιχηρὰ Ἀναστάσιμα Ἦχος {tone}<br>"
                    "Πᾶσα πνοὴ αἰνεσάτω τὸν Κύριον.<br>"
                    "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ"
                )
                result = enrich_service_html(date(2026, 10, 4), "orthros", source)

                self.assertEqual(result.attachment_count, 1)
                self.assertIn(f'data-music-piece="{piece_id}"', result.html)
                self.assertIn(f"μέλος {('ἀργόν' if form == 'slow' else 'σύντομον')}", result.html)
                self.assertLess(
                    result.html.index(f'data-music-piece="{piece_id}"'),
                    result.html.index("ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ"),
                )

    def test_sixth_eothinon_is_attached_only_after_its_own_doxastikon(self):
        source = (
            "Κύριε δόξα σοι.<br>"
            "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ ΣΤ'<br>Ἦχος πλ β' Ἰδιόμελον<br>"
            "Ἡ ὄντως εἰρήνη σὺ Χριστέ.<br>Κύριε δόξα σοι.<br>"
            "Ὑπερευλογημένη ὑπάρχεις, Θεοτόκε Παρθένε."
        )
        result = enrich_service_html(date(2026, 9, 27), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertIn('data-music-piece="eothinon-6"', result.html)
        self.assertLess(
            result.html.rindex("Κύριε δόξα σοι."),
            result.html.index('data-music-piece="eothinon-6"'),
        )
        self.assertLess(
            result.html.index('data-music-piece="eothinon-6"'),
            result.html.index("Ὑπερευλογημένη"),
        )

    def test_plagal_fourth_kathismata_and_anavathmoi_keep_their_openings(self):
        pieces = {piece.piece_id: piece for piece in catalog_pieces()}
        self.assertEqual(
            [region.printed_page for region in pieces["tone8-kathismata"].regions],
            [396, 397, 398, 399],
        )
        self.assertEqual(pieces["tone8-kathismata"].regions[0].clip[1], .10)
        self.assertEqual(
            [region.printed_page for region in pieces["tone8-anavathmoi"].regions],
            [399, 400, 401, 402],
        )
        self.assertEqual(pieces["tone8-anavathmoi"].regions[0].clip[1], .57)

    def test_plagal_fourth_first_ode_keeps_armaitilatin_and_follows_its_text(self):
        source = (
            "Ήχος εβδομάδος πλ δ΄.<br>ΩΔΗ Α΄ ΚΑΝΟΝΩΝ<br>"
            "Κανὼν Ἀναστάσιμος<br>Ἁρματηλάτην Φαραὼ ἐβύθισε.<br>"
            "τὴν μετὰ Θεὸν προστασίαν ἡμῶν.<br>"
            "Κανόνας τοῦ Ἁγίου Καλλιστράτου."
        )
        result = enrich_service_html(date(2026, 9, 27), "orthros", source)
        pieces = {piece.piece_id: piece for piece in catalog_pieces()}

        self.assertIn('data-music-piece="tone8-canon-ode-1"', result.html)
        self.assertLess(
            result.html.index("τὴν μετὰ Θεὸν προστασίαν ἡμῶν."),
            result.html.index('data-music-piece="tone8-canon-ode-1"'),
        )
        self.assertLess(
            result.html.index('data-music-piece="tone8-canon-ode-1"'),
            result.html.index("Κανόνας τοῦ Ἁγίου Καλλιστράτου."),
        )
        self.assertEqual(pieces["tone8-canon-ode-1"].regions[0].clip[1], .08)

    def test_plagal_fourth_third_ode_is_complete_and_precedes_the_feast_canon(self):
        source = (
            "Ήχος εβδομάδος πλ δ΄.<br>ΩΔΗ Γ΄ ΚΑΝΟΝΩΝ<br>"
            "Κανὼν Ἀναστάσιμος<br>Ὁ στερεώσας κατ’ ἀρχάς.<br>"
            "ὕμνοις ἀεὶ μακαρίζομεν.<br>"
            "Κανόνας τοῦ Ἁγίου Καλλιστράτου.<br>Ἦχος πλ δ΄<br>"
            "Ὁ Εἱρμός. (Ο ειρμός δεν ψάλλεται)"
        )
        result = enrich_service_html(date(2026, 9, 27), "orthros", source)
        pieces = {piece.piece_id: piece for piece in catalog_pieces()}

        self.assertIn('data-music-piece="tone8-canon-ode-3"', result.html)
        self.assertLess(
            result.html.index('data-music-piece="tone8-canon-ode-3"'),
            result.html.index("Κανόνας τοῦ Ἁγίου Καλλιστράτου."),
        )
        self.assertEqual(
            [region.printed_page for region in pieces["tone8-canon-ode-3"].regions],
            [405, 406, 407],
        )
        self.assertEqual(pieces["tone8-canon-ode-3"].regions[0].clip[1], .24)

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

    def test_fourth_tone_timiotera_is_attached_after_sixth_refrain(self):
        refrain = (
            "Τὴν Τιμιωτέραν τῶν Χερουβείμ, καὶ ἐνδοξοτέραν ἀσυγκρίτως "
            "τῶν Σεραφείμ, τὴν ἀδιαφθόρως Θεὸν Λόγον τεκοῦσαν, "
            "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.<br>"
        )
        heading = "Καὶ ψάλλεται ἡ Τιμιωτέρα στον ίδιο ήχο του Ειρμού. Ἦχος δ΄<br>"
        result = enrich_service_html(
            date(2026, 9, 22), "orthros", heading + refrain * 6 + "Εἰρμός θ΄ ᾠδής"
        )

        self.assertEqual(result.html.count('data-music-piece="tone4-timiotera"'), 1)
        self.assertLess(result.html.rindex("σὲ μεγαλύνομεν"), result.html.index("tone4-timiotera"))
        self.assertLess(result.html.index("tone4-timiotera"), result.html.index("Εἰρμός θ΄"))

    def test_plagal_fourth_timiotera_uses_its_local_eirmos_tone_not_an_earlier_fourth_tone(self):
        refrain = (
            "Τὴν Τιμιωτέραν τῶν Χερουβείμ, καὶ ἐνδοξοτέραν ἀσυγκρίτως "
            "τῶν Σεραφείμ, τὴν ἀδιαφθόρως Θεὸν Λόγον τεκοῦσαν, "
            "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.<br>"
        )
        source = (
            "Ἦχος δ΄ από προηγούμενο μέλος.<br>"
            "Καὶ ψάλλεται ἡ Τιμιωτέρα στον ίδιο ήχο του Ειρμού. "
            "Ἦχος πλ δ΄<br>"
            + refrain * 6
            + "Εἰρμός θ΄ ᾠδής"
        )
        result = enrich_service_html(date(2026, 10, 3), "orthros", source)

        self.assertIn('data-music-piece="plagal4-timiotera"', result.html)
        self.assertNotIn('data-music-piece="tone4-timiotera"', result.html)

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

    def test_sunday_core_members_follow_the_weekly_tone_without_feast_tone_leakage(self):
        source = (
            "Ήχος εβδομάδος Βαρύς.<br>"
            "Οἱ Ἀναβαθμοὶ Ἦχος βαρύς<br>"
            "Προκείμενον Ἦχος βαρύς<br>"
            "ΚΑΝΟΝΕΣ<br>ΩΔΗ Α΄ ΚΑΝΟΝΩΝ<br>Κανὼν Ἀναστάσιμος<br>"
            "ΩΔΗ Γ΄ ΚΑΝΟΝΩΝ<br>"
            "Ἐν συνεχεία ψάλλονται τά Ἀναστάσιμα εὐλογητάρια.<br>"
        )
        result = enrich_service_html(date(2026, 9, 20), "orthros", source)

        self.assertIn('data-music-piece="tone7-kathismata"', result.html)
        self.assertIn('data-music-piece="tone7-anavathmoi"', result.html)
        self.assertIn('data-music-piece="tone7-canon-ode-1"', result.html)
        self.assertIn('data-music-piece="tone7-canon-ode-3"', result.html)
        self.assertNotIn('data-music-piece="tone8-kathismata"', result.html)
        self.assertLess(result.html.index("tone7-kathismata"), result.html.index("Ἀναστάσιμα εὐλογητάρια"))

    def test_weekday_prokeimenon_does_not_receive_sunday_anavathmoi(self):
        source = "Ήχος εβδομάδος Βαρύς.<br>Προκείμενον Ἦχος βαρύς<br>Καθημερινός Όρθρος"
        result = enrich_service_html(date(2026, 9, 22), "orthros", source)

        self.assertNotIn('data-music-piece="tone7-anavathmoi"', result.html)

    def test_tone_fourth_first_antiphon_is_attached_for_the_feast_day_orthros(self):
        source = (
            "Ἀναβαθμοί τὸ α΄ Ἀντίφωνον τοῦ δ΄ Ἤχου<br>"
            "Ἐκ νεότητός μου πολλὰ πολεμεῖ με πάθη.<br>"
            "Οἱ μισοῦντες Σιών, αἰσχύνθητε ἀπὸ τοῦ Κυρίου.<br>"
            "Ἁγίῳ Πνεύματι, ἀναβλύζει τὰ τῆς χάριτος ῥεῖθρα, "
            "ἀρδεύοντα ἅπασαν τὴν κτίσιν, πρὸς ζωογονίαν.<br>"
            "Προκείμενον Ἦχος δ΄"
        )
        result = enrich_service_html(date(2026, 9, 8), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertIn('data-music-piece="tone4-anavathmoi-first-antiphon"', result.html)
        self.assertIn("Ἀναβαθμοί · α΄ Ἀντίφωνον δ΄ ἤχου", result.html)
        self.assertIn("music/ioannis-protopsaltis-1905/tone4-anavathmoi-first-antiphon/1.png", result.html)
        self.assertLess(result.html.index("ζωογονίαν"), result.html.index("tone4-anavathmoi-first-antiphon"))
        self.assertLess(result.html.index("tone4-anavathmoi-first-antiphon"), result.html.index("Προκείμενον"))

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

    def test_ypereulogimeni_uses_its_fixed_second_tone_setting(self):
        source = (
            "Υπερευλογημένη ψάλλεται πάντοτε σε ήχο β΄.<br>"
            "Υπερευλογημένη υπάρχεις, Θεοτόκε Παρθένε.<br>"
            "Εὐλογητὸς Χριστὸς ὁ Θεὸς ἡμῶν, ὁ οὕτως εὐδοκήσας, δόξα σοι.<br>"
            "Δόξα σοι τῷ δείξαντι τὸ φῶς."
        )
        result = enrich_service_html(date(2026, 9, 16), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertIn('data-music-piece="ypereulogimeni-tone2"', result.html)
        self.assertIn("music/ypereulogimeni-tone2-pemptousia/ypereulogimeni-tone2/1.png", result.html)

    def test_cross_katavasies_are_inserted_before_timiotera_and_ninth_ode(self):
        source = (
            "Καταβασίες τῆς Ὑψώσεως τοῦ Τιμίου Σταυροῦ<br>"
            "Σταυρὸν χαράξας Μωσῆς.<br>"
            "ἣν πᾶσαι αἱ Δυνάμεις, τῶν οὐρανῶν μεγαλύνουσι.<br>"
            "Καὶ ψάλλεται ἡ Τιμιωτέρα στον ίδιο ήχο των καταβασιών.<br>"
            "Τὴν Τιμιωτέραν τῶν Χερουβείμ.<br>"
            "Κατόπιν ψάλλεται ἡ θ΄ Ωδή των καταβασιών<br>"
            "Ὠδὴ θ΄. Ἦχος πλ. δ΄<br>"
            "Μετὰ τὴν καταβασίαν τῆς θ΄ ᾠδῆς"
        )
        result = enrich_service_html(date(2026, 9, 13), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertIn('data-music-piece="cross-katavasies"', result.html)
        self.assertIn(
            "music/ioannis-protopsaltis-eirmologion-1903/cross-katavasies/1.png",
            result.html,
        )
        self.assertIn("Σύντομες Καταβασίαι", result.html)
        self.assertIn("Εἱρμολόγιον Καταβασιῶν Ἰωάννου Πρωτοψάλτου", result.html)
        self.assertLess(result.html.index("cross-katavasies"), result.html.index("Καὶ ψάλλεται"))
        self.assertLess(result.html.index("cross-katavasies"), result.html.index("Ὠδὴ θ΄"))

    def test_tone_fourth_theotokos_katavasies_precede_timiotera(self):
        refrain = "Τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.<br>"
        source = (
            "Καταβασίες Τῆς Θεοτόκου<br>Ἦχος δ΄.<br>"
            "Ἀνοίξω τὸ στόμα μου, καὶ πληρωθήσεται Πνεύματος.<br>"
            "Τὴν Θεοτόκον καὶ Μητέρα τοῦ Φωτός, ἐν ὕμνοις τιμῶντες μεγαλύνωμεν.<br>"
            "Καὶ ψάλλεται ἡ Τιμιωτέρα στον ίδιο ήχο των καταβασιών.<br>"
            "Ἦχος δ΄<br>" + refrain * 6 +
            "Κατόπιν ψάλλεται ἡ θ΄ Ωδή των καταβασιών"
        )
        result = enrich_service_html(date(2026, 9, 26), "orthros", source)
        self.assertEqual(result.attachment_count, 2)
        self.assertIn('data-music-piece="theotokos-katavasies-tone4"', result.html)
        self.assertIn('data-music-piece="tone4-timiotera"', result.html)
        self.assertNotIn('data-music-piece="plagal4-timiotera"', result.html)
        self.assertIn("music/ioannis-protopsaltis-eirmologion-1903/theotokos-katavasies-tone4/1.png", result.html)
        self.assertLess(result.html.index("theotokos-katavasies-tone4"), result.html.index("Τὴν Θεοτόκον"))
        self.assertLess(result.html.index("theotokos-katavasies-tone4"), result.html.index("θ΄ Ωδή"))

    def test_cross_katavasies_precede_the_feast_ninth_ode_when_timiotera_is_omitted(self):
        source = (
            "Καταβασίες τῆς Ὑψώσεως τοῦ Τιμίου Σταυροῦ<br>"
            "Σταυρὸν χαράξας Μωσῆς.<br>"
            "Ἡ Τιμιωτέρα δεν στιχολογεῖται αλλά ψάλλομε την θ΄ Ωδή "
            "των κανόνων της εορτής στον ήχο τους.<br>"
            "Ὠδὴ θ΄. Ἦχος πλ. δ΄"
        )
        result = enrich_service_html(date(2026, 9, 8), "orthros", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertLess(result.html.index("cross-katavasies"), result.html.index("Ἡ Τιμιωτέρα"))
        self.assertLess(result.html.index("cross-katavasies"), result.html.index("Ὠδὴ θ΄"))

    def test_litourgia_gets_pandekti_eisodikon_and_trisagion(self):
        source = (
            "Δεῦτε προσκυνήσωμεν καὶ προσπέσωμεν Χριστῷ.<br>"
            + ("Ἅγιος ὁ Θεός, ἅγιος ἰσχυρός, ἅγιος ἀθάνατος, ἐλέησον ἡμᾶς.<br>" * 3)
            + "Δύναμις.<br>"
            + "Ἅγιος ὁ Θεός, ἅγιος ἰσχυρός, ἅγιος ἀθάνατος, ἐλέησον ἡμᾶς.<br>"
            + "Πρόσχωμεν."
        )
        result = enrich_service_html(date(2026, 9, 8), "litourgia", source)

        self.assertEqual(result.attachment_count, 2)
        self.assertIn('data-music-piece="litourgia-eisodikon-pandekti"', result.html)
        self.assertIn('data-music-piece="litourgia-trisagion-argon-pandekti"', result.html)
        self.assertIn("music/pandekti-litourgia-1851/litourgia-eisodikon-pandekti/1.png", result.html)
        self.assertIn("music/pandekti-litourgia-1851/litourgia-trisagion-argon-pandekti/1.png", result.html)
        self.assertIn("music/pandekti-litourgia-1851/litourgia-trisagion-argon-pandekti/3.png", result.html)
        self.assertLess(result.html.index("litourgia-trisagion-argon-pandekti"), result.html.index("Δύναμις"))

    def test_antiphon_scores_follow_the_completed_first_and_second_antiphons(self):
        tais = "Ταῖς πρεσβείαις τῆς Θεοτόκου, Σῶτερ, σῶσον ἡμᾶς."
        soson = "Σῶσον ἡμᾶς Υἱὲ Θεοῦ, ὁ ἀναστὰς ἐκ νεκρῶν ψάλλοντάς σοι, Ἀλληλούϊα."
        source = (
            "Στίχ. α΄. Εὐλόγει ἡ ψυχή μου, τὸν Κύριον.<br>"
            + tais
            + "<br>Στίχ. β΄. Εὐλόγει, ἡ ψυχή μου, τὸν Κύριον καὶ μὴ ἐπιλανθάνου πάσας τὰς ἀνταποδόσεις αὐτοῦ.<br>"
            + tais
            + "<br>Στίχ. γ΄. Κύριος ἐν τῷ οὐρανῷ ἡτοίμασε τὸν θρόνον αὐτοῦ, καὶ ἡ βασιλεία αὐτοῦ πάντων δεσπόζει.<br>"
            + tais
            + "<br>Δόξα... Καὶ νῦν...<br>"
            + tais
            + "<br>Στίχ. α΄. Αἴνει ἡ ψυχή μου, τὸν Κύριον.<br>"
            + soson
            + "<br>Στίχ. β΄. Μακάριος οὗ ὁ Θεὸς Ἰακὼβ βοηθὸς αὐτοῦ, ἡ ἐλπὶς αὐτοῦ ἐπὶ Κύριον τὸν Θεὸν αὐτοῦ.<br>"
            + soson
            + "<br>Στίχ. γ΄. Βασιλεύσει Κύριος εἰς τὸν αἰῶνα, ὁ Θεός σου, Σιών, εἰς γενεὰν καὶ γενεάν.<br>"
            + soson
            + "<br>Δόξα... Καὶ νῦν...<br>Ἀκολουθεῖ τὸ Ὁ Μονογενής"
        )

        result = enrich_service_html(date(2026, 9, 27), "litourgia", source)

        self.assertEqual(result.attachment_count, 2)
        self.assertEqual(result.html.count('data-music-piece="litourgia-tais-presveiais-pandekti"'), 1)
        self.assertEqual(result.html.count('data-music-piece="litourgia-soson-yie-pandekti"'), 1)
        self.assertLess(
            result.html.rindex(tais),
            result.html.index('data-music-piece="litourgia-tais-presveiais-pandekti"'),
        )
        self.assertLess(
            result.html.index('data-music-piece="litourgia-soson-yie-pandekti"'),
            result.html.index("Ἀκολουθεῖ"),
        )

        weekday_result = enrich_service_html(date(2026, 9, 30), "litourgia", source)
        self.assertEqual(weekday_result.attachment_count, 2)
        self.assertIn('data-music-piece="litourgia-tais-presveiais-pandekti"', weekday_result.html)
        self.assertIn('data-music-piece="litourgia-soson-yie-pandekti"', weekday_result.html)

    def test_weekday_antiphons_get_the_same_two_score_insertions(self):
        source = (
            "Στίχ. α΄. Ἀγαθὸν τὸ ἐξομολογεῖσθαι τῷ Κυρίῳ.<br>"
            "Ταῖς πρεσβείαις τῆς Θεοτόκου, Σῶτερ, σῶσον ἡμᾶς.<br>"
            "Στίχ. β΄. Τοῦ ἀναγγέλλειν τὸ πρωῒ τὸ ἔλεός σου.<br>"
            "Ταῖς πρεσβείαις τῆς Θεοτόκου...<br>"
            "Στίχ. γ΄. Ὅτι εὐθὺς Κύριος ὁ Θεὸς ἡμῶν.<br>"
            "Ταῖς πρεσβείαις τῆς Θεοτόκου...<br>Δόξα... Καὶ νῦν...<br>"
            "Ταῖς πρεσβείαις τῆς Θεοτόκου...<br>"
            "Πρεσβείαις τῶν ἁγίων σου, σῶσον ἡμᾶς, Κύριε.<br>"
            "Πρεσβείαις τῶν ἁγίων σου, σῶσον ἡμᾶς, Κύριε.<br>"
            "Καὶ νῦν...<br>"
            "Ὁ Μονογενὴς Υἱὸς καὶ Λόγος τοῦ Θεοῦ"
        )

        result = enrich_service_html(date(2026, 9, 30), "litourgia", source)

        self.assertEqual(result.attachment_count, 3)
        self.assertEqual(result.html.count('data-music-piece="litourgia-tais-presveiais-pandekti"'), 1)
        self.assertEqual(result.html.count('data-music-piece="litourgia-soson-yie-pandekti"'), 1)
        self.assertLess(
            result.html.index('data-music-piece="litourgia-soson-yie-pandekti"'),
            result.html.index("Ὁ Μονογενὴς"),
        )

    def test_theotokos_feast_adds_fourth_tone_liturgy_music(self):
        note = (
            "Σύμφωνα με το άγραφο Τυπικό της Μεγάλης του Χριστου Εκκλησίας, "
            "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, "
            "Θεομητορική εορτή, ψάλλονται σε ήχο δ΄ άγια.<br>"
        )
        source = (
            note
            + "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες, καὶ τῇ ζωοποιῷ "
            "Τριάδι τὸν τρισάγιον ὕμνον προσᾴδοντες.<br>"
            + "Ἅγιος, ἅγιος, ἅγιος Κύριος Σαβαώθ· πλήρης ὁ οὐρανὸς καὶ ἡ γῆ "
            + "τῆς δόξης σου, ὡσαννὰ ἐν τοῖς ὑψίστοις. Εὐλογημένος ὁ ἐρχόμενος "
            + "ἐν ὀνόματι Κυρίου. Ὡσαννὰ ὁ ἐν τοῖς ὑψίστοις.<br>"
            + "Ποτήριον σωτηρίου λήψομαι, καὶ τὸ ὄνομα Κυρίου ἐπικαλέσομαι.<br>"
        )
        result = enrich_service_html(date(2026, 9, 8), "litourgia", source)

        self.assertEqual(result.attachment_count, 3)
        self.assertIn('data-music-piece="litourgia-cherouvikon-pandekti"', result.html)
        self.assertIn('data-music-piece="litourgia-koinonikon-pandekti"', result.html)
        self.assertIn('data-music-piece="litourgia-axion-tone4-pandekti"', result.html)
        self.assertIn("music/pandekti-litourgia-1851/litourgia-cherouvikon-pandekti/1.png", result.html)
        self.assertIn("music/pandekti-litourgia-1851/litourgia-koinonikon-pandekti/1.png", result.html)

    def test_september_ninth_orthros_uses_fixed_feast_excerpts(self):
        source = (
            "Ἀπολυτίκιον των Γενεθλίων<br>"
            "Ἡ γέννησίς σου Θεοτόκε, χαρὰν ἐμήνυσε πάσῃ τῇ οἰκουμένῃ· "
            "καὶ καταργήσας τὸν θάνατον, ἐδωρήσατο ἡμῖν ζωὴν τὴν αἰώνιον.<br>"
            "Σήμερον ἡ πανάμωμος Ἁγνὴ προῆλθεν ἐκ τῆς στείρας· "
            "Ἡμεῖς δὲ δοξολογοῦντες βοῶμεν· Δόξα ἐν ὑψίστοις Θεῷ, "
            "καὶ ἐπὶ γῆς εἰρήνη, ἐν ἀνθρώποις εὐδοκία.<br>"
        )
        result = enrich_service_html(date(2026, 9, 9), "orthros", source)

        self.assertEqual(result.attachment_count, 2)
        self.assertIn('data-music-piece="kypseli-08-apolytikion"', result.html)
        self.assertIn('data-music-piece="kypseli-09-doxastikon"', result.html)
        self.assertNotIn('data-music-piece="kypseli-08-doxastikon"', result.html)
        self.assertLess(
            result.html.index("kypseli-08-apolytikion"),
            result.html.index("kypseli-09-doxastikon"),
        )

    def test_september_ninth_liturgy_uses_the_day_tone_and_previous_feast_text(self):
        note = (
            "Σύμφωνα με το άγραφο Τυπικό της Μεγάλης του Χριστου Εκκλησίας, "
            "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, απλή Τετάρτη, "
            "ψάλλονται σε ήχο δ΄ άγια.<br>"
        )
        source = (
            note
            + "Ἡ γέννησίς σου Θεοτόκε, χαρὰν ἐμήνυσε πάσῃ τῇ οἰκουμένῃ· "
            + "καὶ καταργήσας τὸν θάνατον, ἐδωρήσατο ἡμῖν ζωὴν τὴν αἰώνιον.<br>"
            + "Ἰωακεὶμ καὶ Ἄννα ὀνειδισμοῦ ἀτεκνίας, καὶ Ἀδὰμ καὶ Εὔα, "
            + "Ἡ στεῖρα τίκτει τὴν Θεοτόκον, καὶ τροφὸν τῆς ζωῆς ἡμῶν.<br>"
            + "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες.<br>"
        )
        result = enrich_service_html(date(2026, 9, 9), "litourgia", source)

        self.assertIn('data-music-piece="kypseli-08-apolytikion"', result.html)
        self.assertIn('data-music-piece="kypseli-08-kontakion"', result.html)
        self.assertIn('data-music-piece="litourgia-cherouvikon-pandekti"', result.html)

    def test_litourgia_axion_is_one_excerpt_after_the_full_sanctus(self):
        note = (
            "Σύμφωνα με το άγραφο Τυπικό της Μεγάλης του Χριστου Εκκλησίας, "
            "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, "
            "Θεομητορική εορτή, ψάλλονται σε ήχο δ΄ άγια.<br>"
        )
        sanctus = (
            "Ἅγιος, ἅγιος, ἅγιος Κύριος Σαβαώθ· πλήρης ὁ οὐρανὸς καὶ ἡ γῆ "
            "τῆς δόξης σου, ὡσαννὰ ἐν τοῖς ὑψίστοις. Εὐλογημένος ὁ ἐρχόμενος "
            "ἐν ὀνόματι Κυρίου. Ὡσαννὰ ὁ ἐν τοῖς ὑψίστοις."
        )
        result = enrich_service_html(
            date(2026, 9, 8),
            "litourgia",
            note + "Ἔλεον εἰρήνης, θυσίαν αἰνέσεως.<br>" + sanctus + "<br>Σὲ ὑμνοῦμεν.",
        )

        self.assertEqual(result.attachment_count, 1)
        self.assertEqual(len(result.bookmarks), 1)
        self.assertIn('data-music-piece="litourgia-axion-tone4-pandekti"', result.html)
        self.assertIn("σελ. 7", result.html)
        self.assertLess(result.html.index(sanctus), result.html.index("litourgia-axion-tone4-pandekti"))
        self.assertLess(result.html.index("litourgia-axion-tone4-pandekti"), result.html.index("Σὲ ὑμνοῦμεν"))

    def test_litourgia_two_amens_and_se_ymnoumen_follow_the_full_response(self):
        note = (
            "Σύμφωνα με το άγραφο Τυπικό της Μεγάλης του Χριστου Εκκλησίας, "
            "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, "
            "Θεομητορική εορτή, ψάλλονται σε ήχο δ΄ άγια.<br>"
        )
        response = (
            "Σὲ ὑμνοῦμεν, σὲ εὐλογοῦμεν, σοὶ εὐχαριστοῦμεν, Κύριε, "
            "καὶ δεόμεθά σου, ὁ Θεὸς ἡμῶν."
        )
        result = enrich_service_html(
            date(2026, 9, 8),
            "litourgia",
            note + response + "<br>Μετὰ τούτων καὶ ἡμεῖς.",
        )

        self.assertEqual(result.attachment_count, 1)
        self.assertEqual(len(result.bookmarks), 1)
        self.assertIn('data-music-piece="litourgia-amin-se-ymnoumen-pandekti"', result.html)
        self.assertIn("σελ. 256, 257", result.html)
        self.assertLess(result.html.index(response), result.html.index("litourgia-amin-se-ymnoumen-pandekti"))
        self.assertLess(
            result.html.index("litourgia-amin-se-ymnoumen-pandekti"),
            result.html.index("Μετὰ τούτων"),
        )

    def test_litourgia_beginning_gets_kyrie_and_antiphon_music(self):
        source = (
            "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες.<br>"
            "Κύριε, ἐλέησον.<br>"
            "Ταῖς πρεσβείαις τῆς Θεοτόκου, Σῶτερ, σῶσον ἡμᾶς.<br>"
            "Σῶσον ἡμᾶς Υἱὲ Θεοῦ, ὁ ἐν Ἁγίοις θαυμαστός ψάλλοντάς σοι, "
            "Ἀλληλούϊα.<br>"
            "Ὁ Μονογενὴς Υἱὸς καὶ Λόγος τοῦ Θεοῦ, ... σῶσον ἡμᾶς.<br>"
        )
        result = enrich_service_html(date(2026, 9, 8), "litourgia", source)

        self.assertEqual(result.attachment_count, 4)
        for piece_id in (
            "litourgia-kyrie-eleison-pandekti",
            "litourgia-tais-presveiais-pandekti",
            "litourgia-soson-yie-pandekti",
            "litourgia-monogenis-pandekti",
        ):
            self.assertIn(f'data-music-piece="{piece_id}"', result.html)
        self.assertNotIn("litourgia-leitourgika-pandekti", result.html)

    def test_sunday_liturgy_accepts_melodos_day_tone_wording_and_resurrection_soson(self):
        source = (
            "Σῶσον ἡμᾶς Υἱὲ Θεοῦ, ὁ ἀναστὰς ἐκ νεκρῶν ψάλλοντάς σοι, Ἀλληλούϊα.<br>"
            "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, ψάλλονται στον "
            "κύριο ήχο της ημέρας, ήχο πλ δ΄.<br>"
            "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες.<br>"
            "Χριστιανὰ τὰ τέλη τῆς ζωῆς ἡμῶν.<br>Παράσχου Κύριε.<br>"
            "Σὲ ὑμνοῦμεν, σὲ εὐλογοῦμεν, σοὶ εὐχαριστοῦμεν, Κύριε, καὶ δεόμεθά σου, "
            "ὁ Θεὸς ἡμῶν.<br>"
            "Ἅγιος, ἅγιος, ἅγιος Κύριος Σαβαώθ· πλήρης ὁ οὐρανὸς καὶ ἡ γῆ τῆς "
            "δόξης σου, ὡσαννὰ ἐν τοῖς ὑψίστοις. Εὐλογημένος ὁ ἐρχόμενος ἐν "
            "ὀνόματι Κυρίου. Ὡσαννὰ ὁ ἐν τοῖς ὑψίστοις.<br>"
            "Τῇ Κυριακῇ ψάλλεται το Κοινωνικόν.<br>Αἰνεῖτε τὸν Κύριον ἐκ τῶν οὐρανῶν"
        )
        result = enrich_service_html(date(2026, 9, 27), "litourgia", source)

        for piece_id in (
            "litourgia-soson-yie-pandekti",
            "litourgia-tone-8-cherouvikon",
            "litourgia-tone-8-kyrie-paraschou",
            "litourgia-tone-8-amin-se-ymnoumen",
            "litourgia-tone-8-axion-kai-dikaion",
            "litourgia-tone-8-koinonikon",
        ):
            self.assertIn(f'data-music-piece="{piece_id}"', result.html)

    def test_sunday_liturgy_first_tone_accepts_the_same_melodos_day_tone_wording(self):
        source = (
            "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, ψάλλονται στον "
            "κύριο ήχο της ημέρας, ήχο α΄.<br>"
            "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες.<br>"
            "Χριστιανὰ τὰ τέλη τῆς ζωῆς ἡμῶν.<br>Παράσχου Κύριε.<br>"
            "Σὲ ὑμνοῦμεν, σὲ εὐλογοῦμεν, σοὶ εὐχαριστοῦμεν, Κύριε, καὶ δεόμεθά σου, "
            "ὁ Θεὸς ἡμῶν.<br>"
            "Ἅγιος, ἅγιος, ἅγιος Κύριος Σαβαώθ· πλήρης ὁ οὐρανὸς καὶ ἡ γῆ τῆς "
            "δόξης σου, ὡσαννὰ ἐν τοῖς ὑψίστοις. Εὐλογημένος ὁ ἐρχόμενος ἐν "
            "ὀνόματι Κυρίου. Ὡσαννὰ ὁ ἐν τοῖς ὑψίστοις.<br>"
            "Τῇ Κυριακῇ ψάλλεται το Κοινωνικόν.<br>Αἰνεῖτε τὸν Κύριον ἐκ τῶν οὐρανῶν"
        )
        result = enrich_service_html(date(2026, 10, 4), "litourgia", source)

        for piece_id in (
            "litourgia-tone-1-cherouvikon",
            "litourgia-tone-1-kyrie-paraschou",
            "litourgia-tone-1-amin-se-ymnoumen",
            "litourgia-tone-1-axion-kai-dikaion",
            "litourgia-tone-1-koinonikon",
        ):
            self.assertIn(f'data-music-piece="{piece_id}"', result.html)

    def test_litourgia_opening_kyrie_is_first_bookmark_and_is_tone_independent(self):
        opening = (
            "Εὐλογημένη ἡ βασιλεία τοῦ Πατρὸς καὶ τοῦ Υἱοῦ καὶ τοῦ Ἁγίου Πνεύματος.<br>"
            "Ἀμήν.<br>"
            + ("Κύριε, ἐλέησον.<br>" * 12)
            + "Σύμφωνα με το άγραφο Τυπικό της Μεγάλης του Χριστου Εκκλησίας, "
            + "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, "
            + "Θεομητορική εορτή, ψάλλονται σε ήχο δ΄ άγια.<br>"
            + "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες.<br>"
            + "Κύριε, ἐλέησον.<br>"
        )
        result = enrich_service_html(date(2026, 9, 8), "litourgia", opening)

        self.assertEqual(result.attachment_count, 2)
        self.assertEqual(result.bookmarks[0].anchor_id, "music-litourgia-kyrie-eleison-pandekti-1")
        self.assertEqual(result.bookmarks[1].anchor_id, "music-litourgia-cherouvikon-pandekti-2")
        self.assertEqual(result.html.count('data-music-piece="litourgia-kyrie-eleison-pandekti"'), 1)
        self.assertLess(
            result.html.index("music-litourgia-kyrie-eleison-pandekti-1"),
            result.html.index("music-litourgia-cherouvikon-pandekti-2"),
        )

    def test_post_cherouvikon_kyrie_and_paraschou_are_attached_in_order(self):
        note = (
            "Σύμφωνα με το άγραφο Τυπικό της Μεγάλης του Χριστου Εκκλησίας, "
            "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, "
            "Θεομητορική εορτή, ψάλλονται σε ήχο δ΄ άγια.<br>"
        )
        source = (
            "Κύριε, ἐλέησον.<br>"
            + note
            + "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες.<br>"
            + "Κύριε, ἐλέησον.<br>"
            + "Χριστιανὰ τὰ τέλη τῆς ζωῆς ἡμῶν.<br>"
            + "Παράσχου Κύριε.<br>"
        )
        result = enrich_service_html(date(2026, 9, 8), "litourgia", source)

        self.assertEqual(
            [bookmark.anchor_id for bookmark in result.bookmarks],
            [
                "music-litourgia-kyrie-eleison-pandekti-1",
                "music-litourgia-cherouvikon-pandekti-2",
                "music-litourgia-tone-4-kyrie-paraschou-3",
            ],
        )

    def test_litourgia_gets_paraschou_and_agapiso_responses(self):
        source = (
            "Σύμφωνα με το άγραφο Τυπικό της Μεγάλης του Χριστου Εκκλησίας, "
            "ψάλλονται σε ήχο δ΄ άγια.<br>"
            "Χριστιανὰ τὰ τέλη τῆς ζωῆς ἡμῶν.<br>"
            "Παράσχου Κύριε.<br>"
            "Πατέρα, Υἱὸν καὶ Ἅγιον Πνεῦμα, Τριάδα ὁμοούσιον καὶ ἀχώριστον.<br>"
            "Ἀγαπήσω σε, Κύριε, ἡ ἰσχύς μου, Κύριος στερέωμά μου.<br>"
        )
        result = enrich_service_html(date(2026, 9, 8), "litourgia", source)

        self.assertEqual(result.attachment_count, 3)
        self.assertIn('data-music-piece="litourgia-tone-4-kyrie-paraschou"', result.html)
        self.assertIn('data-music-piece="litourgia-patera-pandekti"', result.html)
        self.assertIn('data-music-piece="litourgia-agapiso-pandekti"', result.html)

    def test_every_weekly_tone_gets_tone_specific_core_members(self):
        sanctus = (
            "Ἅγιος, ἅγιος, ἅγιος Κύριος Σαβαώθ· πλήρης ὁ οὐρανὸς καὶ ἡ γῆ "
            "τῆς δόξης σου, ὡσαννὰ ἐν τοῖς ὑψίστοις. Εὐλογημένος ὁ ἐρχόμενος "
            "ἐν ὀνόματι Κυρίου. Ὡσαννὰ ὁ ἐν τοῖς ὑψίστοις."
        )
        notes = {
            1: "ψάλλονται σε ήχο α΄",
            2: "ψάλλονται σε ήχο β΄",
            3: "ψάλλονται σε ήχο γ΄",
            4: "ψάλλονται σε ήχο δ΄",
            5: "ψάλλονται σε ήχο πλ α΄",
            6: "ψάλλονται σε ήχο πλ β΄",
            7: "ψάλλονται σε ήχο βαρύ",
            8: "ψάλλονται σε ήχο πλ δ΄",
        }
        for tone, note in notes.items():
            source = (
                f"{note}<br>Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες.<br>"
                "Χριστιανὰ τὰ τέλη τῆς ζωῆς ἡμῶν.<br>Παράσχου Κύριε.<br>"
                f"{sanctus}<br>Σὲ ὑμνοῦμεν, σὲ εὐλογοῦμεν, σοὶ εὐχαριστοῦμεν, "
                "Κύριε, καὶ δεόμεθά σου, ὁ Θεὸς ἡμῶν.<br>"
                "Ἄξιόν ἐστιν ὡς ἀληθῶς μακαρίζειν σε τὴν Θεοτόκον, τὴν "
                "ἀειμακάριστον καὶ παναμώμητον καὶ μητέρα τοῦ Θεοῦ ἡμῶν. Τὴν "
                "τιμιωτέραν τῶν Χερουβεὶμ καὶ ἐνδοξοτέραν ἀσυγκρίτως τῶν Σεραφείμ· "
                "τὴν ἀδιαφθόρως Θεὸν Λόγον τεκοῦσαν, τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν."
            )
            result = enrich_service_html(date(2026, 9, 10), "litourgia", source)
            self.assertEqual(result.attachment_count, 5, tone)
            for member in (
                "cherouvikon",
                "kyrie-paraschou",
                "axion-kai-dikaion",
                "amin-se-ymnoumen",
                "axion-estin",
            ):
                self.assertIn(f'data-music-piece="litourgia-tone-{tone}-{member}"', result.html)

    def test_tenth_september_adds_plagal_fourth_thursday_social(self):
        source = (
            "ψάλλονται σε ήχο πλ δ΄.<br>"
            "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες.<br>"
            "Ἅγιος, ἅγιος, ἅγιος Κύριος Σαβαώθ· πλήρης ὁ οὐρανὸς καὶ ἡ γῆ "
            "τῆς δόξης σου, ὡσαννὰ ἐν τοῖς ὑψίστοις. Εὐλογημένος ὁ ἐρχόμενος "
            "ἐν ὀνόματι Κυρίου. Ὡσαννὰ ὁ ἐν τοῖς ὑψίστοις.<br>"
            "Το κοινωνικὸν συνήθως ψάλλεται εἰς τὸν ἦχον τοῦ Χερουβικοῦ.<br>"
            "Εἰς πᾶσαν τὴν γῆν ἐξῆλθεν ὁ φθόγγος αὐτῶν."
        )
        result = enrich_service_html(date(2026, 9, 10), "litourgia", source)
        self.assertEqual(result.attachment_count, 3)
        self.assertIn('data-music-piece="litourgia-tone-8-cherouvikon"', result.html)
        self.assertIn('data-music-piece="litourgia-tone-8-axion-kai-dikaion"', result.html)
        self.assertIn('data-music-piece="litourgia-koinonikon-thursday-pandekti"', result.html)

    def test_sunday_koinonikon_does_not_leak_from_alleluia_instructions(self):
        source = (
            "ψάλλονται σε ήχο πλ α΄.<br>"
            "ΑΛΛΗΛΟΥΑΡΙΟΝ 1ου ΕΥΑΓΓΕΛΙΟΥ.<br>"
            "Αἰνεῖτε τὸν Κύριον ἐκ τῶν οὐρανῶν.<br>"
            "Στίχ. 2 Αἰνεῖτε αὐτὸν, πάντες οἱ ἄγγελοι αὐτοῦ.<br>"
        )
        result = enrich_service_html(date(2026, 9, 10), "litourgia", source)
        self.assertEqual(result.attachment_count, 0)
        self.assertNotIn("litourgia-tone-5-koinonikon", result.html)

    def test_tuesday_koinonikon_uses_melodos_recommended_tone(self):
        source = (
            "Το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα "
            "ψάλλονται στον κύριο ήχο της ημέρας, ήχο πλ β΄.<br>"
            "Το κοινωνικὸν συνήθως ψάλλεται εἰς τὸν ἦχον εἰς ὃν "
            "ἐψάλη καὶ τὸ Χερουβικόν.<br>"
            "Εἰς μνημόσυνον αἰώνιον ἔσται Δίκαιος. Ἀλληλούια."
        )
        result = enrich_service_html(date(2026, 9, 16), "litourgia", source)

        self.assertEqual(result.attachment_count, 1)
        self.assertIn('data-music-piece="litourgia-tone-6-eis-mnimosynon"', result.html)
        self.assertNotIn("litourgia-tone-7-eis-mnimosynon", result.html)

    def test_post_communion_and_dismissal_hymns_get_music(self):
        source = (
            "Εἰς ἄφεσιν ἁμαρτιῶν καὶ εἰς ζωὴν αἰώνιον.<br>"
            "Πληρωθήτω τὸ στόμα ἡμῶν αἰνέσεως Κύριε, ὅπως ἀνυμνήσωμεν.<br>"
            "Εἴη τὸ ὄνομα Κυρίου εὐλογημένον ἀπὸ τοῦ νῦν καὶ ἕως τοῦ αἰῶνος."
        )
        result = enrich_service_html(date(2026, 9, 16), "litourgia", source)

        self.assertEqual(result.attachment_count, 2)
        self.assertIn('data-music-piece="litourgia-plirothito-melodos"', result.html)
        self.assertIn('data-music-piece="litourgia-eie-to-onoma-pandekti"', result.html)

    def test_fourth_tone_agia_uses_the_feast_setting_without_regular_tone_duplicates(self):
        note = "ψάλλονται σε ήχο δ΄ άγια.<br>"
        source = (
            note
            + "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες.<br>"
            + "Ἅγιος, ἅγιος, ἅγιος Κύριος Σαβαώθ· πλήρης ὁ οὐρανὸς καὶ ἡ γῆ "
            + "τῆς δόξης σου, ὡσαννὰ ἐν τοῖς ὑψίστοις. Εὐλογημένος ὁ ἐρχόμενος "
            + "ἐν ὀνόματι Κυρίου. Ὡσαννὰ ὁ ἐν τοῖς ὑψίστοις.<br>"
            + "Ἄξιον καὶ δίκαιον.<br>"
        )
        result = enrich_service_html(date(2026, 9, 8), "litourgia", source)
        self.assertIn('data-music-piece="litourgia-cherouvikon-pandekti"', result.html)
        self.assertIn('data-music-piece="litourgia-axion-tone4-pandekti"', result.html)
        self.assertNotIn('data-music-piece="litourgia-tone-4-cherouvikon"', result.html)
        self.assertNotIn('data-music-piece="litourgia-tone-4-leitourgika"', result.html)

    def test_menaia_pages_never_leak_from_a_neighbouring_date(self):
        # 10 September is not represented in the verified Kypseli catalogue.
        # Even if the Melodos text repeats a nearby feast's wording, its pages
        # must stay unattached until the exact date is catalogued.
        source = (
            "Ἡ γέννησίς σου Θεοτόκε, χαρὰν ἐμήνυσε πάσῃ τῇ οἰκουμένῃ· "
            "καὶ καταργήσας τὸν θάνατον, ἐδωρήσατο ἡμῖν ζωὴν τὴν αἰώνιον.<br>"
            "Σήμερον ἡ πανάμωμος Ἁγνὴ προῆλθεν ἐκ τῆς στείρας· "
            "Ἡμεῖς δὲ δοξολογοῦντες βοῶμεν· Δόξα ἐν ὑψίστοις Θεῷ.<br>"
        )
        result = enrich_service_html(date(2026, 9, 10), "orthros", source)

        self.assertNotIn("data-music-piece=\"kypseli-", result.html)
