import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.scripture_interpretations import ScriptureInterpretationService, extract_orthros_passages


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

    def test_reads_the_raw_responses_api_output_shape(self):
        with TemporaryDirectory() as directory:
            session = FakeSession()
            session.post = lambda *args, **kwargs: RawResponsesApiResponse()
            service = ScriptureInterpretationService(directory, api_key="test", session=session, background=False)
            result = service.get(extract_orthros_passages(SOURCE)[0])
            self.assertIn("Κείμενο", result)
