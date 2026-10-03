import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.scripture_interpretations import (
    ScriptureInterpretationService,
    add_reading_bookmarks,
    extract_litourgia_passages,
    extract_orthros_passages,
)


SOURCE = """
<br><span class='ie'>Ἐκ τοῦ κατὰ Λουκᾶν ἁγίου Εὐαγγελίου τὸ ἀνάγνωσμα.</span>
<br><span class='ep'>Ε΄ Ἑωθινόν Κεφ. 24:12-35</span>
<br><span class='ie'>Τῷ καιρῷ ἐκείνῳ, ὁ Πέτρος ἀναστὰς ἔδραμεν ἐπὶ τὸ μνημεῖον.</span>
<br><span class='ar'>ΧΟΡΟΣ:</span><br>Δόξα σοι.
<br><span class='ep'>ΑΠΟΣΤΟΛΟΣ</span><br>Πρὸς Γαλάτας Ἐπιστολῆς Παύλου τὸ Ἀνάγνωσμα
<br><span class='ep'>2:16-20</span><br>Ἀδελφοί, εἰδότες ὅτι οὐ δικαιοῦται ἄνθρωπος ἐξ ἔργων νόμου.
<br><span class='ep'>ΕΥΑΓΓΕΛΙΟΝ</span><br>Ἐκ τοῦ κατὰ Μᾶρκον<br><span class='ep'>η΄ 34 - θ΄ 1</span>
<br>Εἶπεν ὁ Κύριος· Ὃστις θέλει ὀπίσω μου ἐλθεῖν.
<br><span class='ep'>ΕΚΤΕΝΗΣ ΔΕΗΣΗ</span>
"""

SOURCE_WITH_SECOND_APOSTOLOS = """
<br><span class='ep'>ΑΠΟΣΤΟΛΟΣ</span><br>Πρὸς Ἐφεσίους 2:19-22
<br>Ἀδελφοί, ἄρα οὖν οὐκέτι ἐστὲ ξένοι καὶ πάροικοι.
<br><span class='ep'>ΑΠΟΣΤΟΛΟΣ 2ος</span><br>Πρὸς Ἑβραίους 11:33-40
<br>Ἀδελφοί, οἳ διὰ πίστεως κατηγωνίσαντο βασιλείας.
<br><span class='ep'>ΕΥΑΓΓΕΛΙΟΝ</span><br>Ἐκ τοῦ κατὰ Λουκᾶν 10:16-21
<br>Εἶπεν ὁ Κύριος τοῖς μαθηταῖς αὐτοῦ.
"""

SOURCE_WITH_OPTIONAL_READINGS = """
<span class='ep'>ΑΠΟΣΤΟΛΟΣ</span><br>Πρὸς Φιλιππησίους 2:5-11
<br>Ἀδελφοί, τοῦτο φρονείσθω ἐν ὑμῖν ὃ καὶ ἐν Χριστῷ ᾿Ιησοῦ, ὃς ἐν μορφῇ Θεοῦ ὑπάρχων ἑαυτὸν ἐκένωσε μορφὴν δούλου λαβών.
<br><span class='ar'>Ἀλληλούϊα</span><br>Πρὸς Τιμόθεον Β΄ 3:10-15
<br>Τέκνον Τιμόθεε, παρηκολούθηκάς μου τῇ διδασκαλίᾳ.
<br><span class='ep'>ΕΥΑΓΓΕΛΙΟΝ</span><br>Ἐκ τοῦ κατὰ Ματθαῖον 25:1-13
<br>Εἶπεν ὁ Κύριος τὴν παραβολὴν ταύτην· ὡμοιώθη ἡ βασιλεία τῶν οὐρανῶν δέκα παρθένοις, αἵτινες λαβοῦσαι τὰς λαμπάδας ἑαυτῶν ἐξῆλθον εἰς ἀπάντησιν τοῦ νυμφίου.
<span class='ep'>ΑΛΛΗΛΟΥΑΡΙΟΝ 2ου ΕΥΑΓΓΕΛΙΟΥ</span><br>Ἐκ τοῦ κατὰ Λουκᾶν 4:16-22
<br>Τῷ καιρῷ ἐκείνῳ, ἦλθεν ὁ Ἰησοῦς εἰς τὴν Ναζαρέτ.
"""

SOURCE_WITH_UNLABELLED_ORTHROS_GOSPEL = """
<span>Σοφία. Ὀρθοί, ἀκούσωμεν τοῦ ἁγίου Εὐαγγελίου.</span><br>
<span>Ἐκ τοῦ κατὰ Ἰωάννην ἁγίου Εὐαγγελίου τὸ ἀνάγνωσμα.</span><br>
<span>Κεφ. 21:14-25</span><br>
<span>Τῷ καιρῷ ἐκείνῳ, ἐφανέρωσεν ἑαυτὸν ὁ Ἰησοῦς τοῖς Μαθηταῖς αὐτοῦ, ἐγερθεὶς ἐκ νεκρῶν, καὶ λέγει τῷ Σίμωνι Πέτρῳ· Σίμων Ἰωνᾶ, ἀγαπᾷς με πλεῖον τούτων; Λέγει αὐτῷ· Ναί, Κύριε, σὺ οἶδας ὅτι φιλῶ σε.</span><br>
<span>ΧΟΡΟΣ:</span><br>Δόξα σοι, Κύριε.
"""


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"output_text": "## Μετάφραση\nΤο κείμενο σε νέα ελληνικά.\n\n## Μηνύματα\n- Πίστη (24:12)"}


class RawResponsesApiResponse(FakeResponse):
    def json(self):
        return {
            "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "## Ερμηνεία\nΚείμενο."}]}
            ]
        }


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return FakeResponse()


class ScriptureInterpretationTests(unittest.TestCase):
    def test_extracts_all_three_orthros_readings(self):
        passages = extract_orthros_passages(SOURCE)
        self.assertEqual([passage.kind for passage in passages], ["eothinon", "apostolos", "evangelion"])
        self.assertIn("24:12-35", passages[0].reference)
        self.assertIn("Γαλάτας", passages[1].text)
        self.assertIn("Μᾶρκον", passages[2].text)

    def test_extracts_from_a_full_html_document_too(self):
        passages = extract_orthros_passages(f"<html><body>{SOURCE}</body></html>")
        self.assertEqual([passage.kind for passage in passages], ["eothinon", "apostolos", "evangelion"])

    def test_first_apostolos_ends_before_second_apostolos_heading(self):
        passages = extract_orthros_passages(SOURCE_WITH_SECOND_APOSTOLOS)
        apostolos = next(passage for passage in passages if passage.kind == "apostolos")
        self.assertIn("Ἐφεσίους", apostolos.text)
        self.assertNotIn("Ἑβραίους", apostolos.text)
        self.assertNotIn("ΑΠΟΣΤΟΛΟΣ 2ος", apostolos.text)

    def test_only_the_first_optional_apostle_and_gospel_are_interpreted(self):
        passages = extract_orthros_passages(SOURCE_WITH_OPTIONAL_READINGS)
        apostolos = next(passage for passage in passages if passage.kind == "apostolos")
        evangelion = next(passage for passage in passages if passage.kind == "evangelion")
        self.assertIn("Φιλιππησίους", apostolos.text)
        self.assertNotIn("Τιμόθεον", apostolos.text)
        self.assertIn("Ματθαῖον", evangelion.text)
        self.assertNotIn("Λουκᾶν", evangelion.text)

    def test_apostle_does_not_end_on_the_word_allilous(self):
        source = """
        <span class='ep'>ΑΠΟΣΤΟΛΟΣ</span><br>Καθολικῆς Α’ Ἐπιστολῆς Ἰωάννου 4:12-19
        <br>Θεὸν οὐδεὶς πώποτε τεθέαται· ἐὰν ἀγαπῶμεν ἀλλήλους, ὁ Θεὸς ἐν ἡμῖν μένει καὶ ἡ ἀγάπη αὐτοῦ τετελειωμένη ἐστὶν ἐν ἡμῖν.
        <br><span class='ar'>Ἀλληλούϊα</span>
        <br><span class='ep'>ΕΥΑΓΓΕΛΙΟΝ</span><br>Ἐκ τοῦ κατὰ Ἰωάννην 19:25-27
        <br>Τῷ καιρῷ ἐκείνῳ, εἱστήκεισαν παρὰ τῷ σταυρῷ τοῦ Ἰησοῦ ἡ μήτηρ αὐτοῦ καὶ ὁ μαθητὴς ὃν ἠγάπα.
        """
        apostolos = next(passage for passage in extract_orthros_passages(source) if passage.kind == "apostolos")
        self.assertIn("ἀλλήλους", apostolos.text)
        self.assertIn("τετελειωμένη", apostolos.text)

    def test_extracts_an_orthros_gospel_without_an_eothinon_label(self):
        passages = extract_orthros_passages(SOURCE_WITH_UNLABELLED_ORTHROS_GOSPEL)
        eothinon = next(passage for passage in passages if passage.kind == "eothinon")
        self.assertIn("21:14-25", eothinon.reference)
        self.assertIn("Σίμων", eothinon.text)
        self.assertNotIn("Δόξα σοι", eothinon.text)

    def test_extracts_the_first_liturgy_apostle_and_gospel_without_an_eothinon(self):
        passages = extract_litourgia_passages(SOURCE)
        self.assertEqual([passage.kind for passage in passages], ["apostolos", "evangelion"])
        self.assertIn("Γαλάτας", passages[0].text)
        self.assertIn("Μᾶρκον", passages[1].text)

    def test_adds_primary_reading_bookmarks_for_orthros_and_liturgy(self):
        orthros, orthros_bookmarks = add_reading_bookmarks(SOURCE, service="orthros")
        litourgia, litourgia_bookmarks = add_reading_bookmarks(SOURCE, service="litourgia")
        self.assertEqual([bookmark.label for bookmark in orthros_bookmarks], ["1ος Απόστολος", "Ευαγγέλιο"])
        self.assertIn('id="reading-orthros-first-apostolos"', orthros)
        self.assertIn('id="reading-orthros-first-evangelion"', orthros)
        self.assertEqual([bookmark.label for bookmark in litourgia_bookmarks], ["1ος Απόστολος", "Ευαγγέλιο"])
        self.assertIn('id="reading-litourgia-first-apostolos"', litourgia)
        self.assertIn('id="reading-litourgia-first-evangelion"', litourgia)

    def test_uses_unlabelled_orthros_gospel_as_the_gospel_bookmark(self):
        rendered, bookmarks = add_reading_bookmarks(SOURCE_WITH_UNLABELLED_ORTHROS_GOSPEL, service="orthros")
        self.assertEqual([bookmark.label for bookmark in bookmarks], ["Ευαγγέλιο"])
        self.assertIn('id="reading-orthros-first-evangelion"', rendered)

    def test_generates_once_and_uses_disk_cache_afterwards(self):
        with TemporaryDirectory() as directory:
            session = FakeSession()
            service = ScriptureInterpretationService(directory, api_key="test", session=session, background=False)
            for passage in extract_orthros_passages(SOURCE):
                service.get(passage)
            first = service.enrich_orthros_html(SOURCE)
            second = service.enrich_orthros_html(SOURCE)
            self.assertEqual(len(session.calls), 3)
            self.assertEqual(first.count("Ερμηνεία αναγνώσματος"), 3)
            self.assertEqual(second.count("Ερμηνεία αναγνώσματος"), 3)
            cache_files = list((Path(directory) / "scripture-interpretations").glob("*.json"))
            self.assertEqual(len(cache_files), 3)
            self.assertEqual(json.loads(cache_files[0].read_text(encoding="utf-8"))["model"], "gpt-5.6-luna")

    def test_does_not_make_a_call_without_an_api_key(self):
        with TemporaryDirectory() as directory:
            session = FakeSession()
            service = ScriptureInterpretationService(directory, api_key="", session=session)
            self.assertNotIn("Ερμηνεία αναγνώσματος", service.enrich_orthros_html(SOURCE))
            self.assertEqual(session.calls, [])

    def test_liturgy_readings_use_the_same_cached_interpretation_flow(self):
        with TemporaryDirectory() as directory:
            session = FakeSession()
            service = ScriptureInterpretationService(directory, api_key="test", session=session, background=False)
            for passage in extract_litourgia_passages(SOURCE):
                service.get(passage)
            rendered = service.enrich_service_html(SOURCE, service="litourgia")
            self.assertEqual(len(session.calls), 2)
            self.assertEqual(rendered.count("Ερμηνεία αναγνώσματος"), 2)

    def test_reads_the_raw_responses_api_output_shape(self):
        with TemporaryDirectory() as directory:
            session = FakeSession()
            session.post = lambda *args, **kwargs: RawResponsesApiResponse()
            service = ScriptureInterpretationService(directory, api_key="test", session=session, background=False)
            result = service.get(extract_orthros_passages(SOURCE)[0])
            self.assertIn("Κείμενο", result)

    def test_prompt_reserves_a_mandatory_theological_messages_section(self):
        prompt = ScriptureInterpretationService._prompt(extract_orthros_passages(SOURCE)[2])
        self.assertIn("Θεολογικά μηνύματα", prompt)
        self.assertIn("final list is mandatory", prompt)
