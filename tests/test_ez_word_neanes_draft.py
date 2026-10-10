import unittest

from src.ez_word_neanes_draft import EzWordPhrasePlanError, compile_confirmed_ez_word_phrase_plan


def report():
    return {
        "purpose": "private-ez-word-font-run-report; source-font-confirmed; no-byzx-generated",
        "source_label": "test Word source",
        "source_filename": "formula.doc",
        "runs": [{"pua_occurrences": [
            {"word_occurrence": 1, "pua_codepoint": "U+F031", "status": "source-font-confirmed; no-neanes-event", "source_definition": {"neanes_candidate": {"element_type": "quantitativeNeume", "value": "Oligon"}}},
            {"word_occurrence": 2, "pua_codepoint": "U+F021", "status": "source-font-confirmed; no-neanes-event", "source_definition": {"neanes_candidate": {"element_type": "quantitativeNeume", "value": "Apostrophos"}}},
        ]}],
    }


class EzWordNeanesDraftTests(unittest.TestCase):
    def test_compiles_exact_word_occurrences(self):
        result = compile_confirmed_ez_word_phrase_plan(report(), {"schema": 1, "reviewer": "ψάλτης", "events": [
            {"confirmed": True, "source_anchors": [{"word_occurrence": 1, "pua_codepoint": "U+F031"}], "resolution": {"quantitativeNeume": "Oligon"}},
            {"confirmed": True, "source_anchors": [{"word_occurrence": 2, "pua_codepoint": "U+F021"}], "resolution": {"quantitativeNeume": "Apostrophos"}},
        ]})
        self.assertEqual([event["quantitativeNeume"] for event in result["events"]], ["Oligon", "Apostrophos"])

    def test_rejects_unconfirmed_word_event(self):
        with self.assertRaisesRegex(EzWordPhrasePlanError, "confirmed"):
            compile_confirmed_ez_word_phrase_plan(report(), {"schema": 1, "reviewer": "ψάλτης", "events": [
                {"confirmed": False, "source_anchors": [], "resolution": {"quantitativeNeume": "Oligon"}},
            ]})

    def test_keeps_a_separately_confirmed_opening_martyria(self):
        result = compile_confirmed_ez_word_phrase_plan(report(), {"schema": 1, "reviewer": "ψάλτης", "events": [
            {"confirmed": True, "source_anchors": [{"word_occurrence": 1, "pua_codepoint": "U+F031"}], "resolution": {"quantitativeNeume": "Oligon"}},
        ], "opening_martyria": {
            "confirmed": True,
            "source_evidence": {"reference": "ιδιωτική οπτική επιβεβαίωση, αρχική μαρτυρία"},
            "note": "Pa", "rootSign": "Alpha", "scale": "Diatonic",
        }})
        self.assertEqual(result["opening_martyria"], {"note": "Pa", "rootSign": "Alpha", "scale": "Diatonic"})

    def test_rejects_an_opening_martyria_without_source_evidence(self):
        with self.assertRaisesRegex(EzWordPhrasePlanError, "source_evidence"):
            compile_confirmed_ez_word_phrase_plan(report(), {"schema": 1, "reviewer": "ψάλτης", "events": [
                {"confirmed": True, "source_anchors": [{"word_occurrence": 1, "pua_codepoint": "U+F031"}], "resolution": {"quantitativeNeume": "Oligon"}},
            ], "opening_martyria": {
                "confirmed": True, "note": "Pa", "rootSign": "Alpha", "scale": "Diatonic",
            }})
