import unittest

from src.ez_neanes_draft import EzPhrasePlanError, compile_confirmed_ez_phrase_plan


def row(instance, glyph_id, codepoint, candidate):
    return {
        "source": {
            "pdf_font_instance": instance,
            "pdf_glyph_id": glyph_id,
            "pua_codepoint": codepoint,
            "glyph_id_matches_full_font": True,
        },
        "source_definition": {"neanes_candidate": candidate},
    }


class EzNeanesDraftTests(unittest.TestCase):
    def setUp(self):
        self.template = {
            "purpose": "private-ez-to-neanes-mapping-template; no-byzx-generated",
            "source_label": "official public EZ sample",
            "rows": [
                row("1:EZ", 10, "U+F031", {"element_type": "quantitativeNeume", "value": "Oligon"}),
                row("1:EZ", 11, "U+F053", {"element_type": "gorgonNeume", "value": None, "context_required": "top-or-bottom attachment"}),
                row("1:EZ", 12, "U+F041", {"element_type": "timeNeume", "value": "Klasma_Top"}),
                row("1:EZ", 13, "U+F03F", {"element_type": "isonControl", "value": "Pause"}),
                row("1:EZ", 14, "U+F07A", {"element_type": "vareia", "value": True}),
            ],
        }

    def test_compiles_a_reviewer_confirmed_base_with_anchored_attachments(self):
        result = compile_confirmed_ez_phrase_plan(
            self.template,
            {
                "schema": 1,
                "events": [
                    {
                        "confirmed": True,
                        "source_anchors": [
                            {"pdf_font_instance": "1:EZ", "pdf_glyph_id": 10, "pua_codepoint": "U+F031"},
                            {"pdf_font_instance": "1:EZ", "pdf_glyph_id": 11, "pua_codepoint": "U+F053"},
                            {"pdf_font_instance": "1:EZ", "pdf_glyph_id": 12, "pua_codepoint": "U+F041"},
                        ],
                        "resolution": {
                            "quantitativeNeume": "Oligon",
                            "gorgonNeume": "Gorgon_Top",
                            "timeNeume": "Klasma_Top",
                            "lyrics": "δοκιμή",
                        },
                    }
                ],
            },
        )

        self.assertEqual(result["review_state"], "needs_score_and_auditory_review")
        self.assertEqual(
            result["events"],
            [{"elementType": "Note", "quantitativeNeume": "Oligon", "gorgonNeume": "Gorgon_Top", "timeNeume": "Klasma_Top", "lyrics": "δοκιμή"}],
        )

    def test_refuses_an_unconfirmed_event(self):
        plan = {
            "schema": 1,
            "events": [{"confirmed": False, "source_anchors": [], "resolution": {"quantitativeNeume": "Oligon"}}],
        }
        with self.assertRaisesRegex(EzPhrasePlanError, "ρητή επιβεβαίωση"):
            compile_confirmed_ez_phrase_plan(self.template, plan)

    def test_refuses_an_attachment_without_its_own_anchor(self):
        plan = {
            "schema": 1,
            "events": [
                {
                    "confirmed": True,
                    "source_anchors": [{"pdf_font_instance": "1:EZ", "pdf_glyph_id": 10, "pua_codepoint": "U+F031"}],
                    "resolution": {"quantitativeNeume": "Oligon", "gorgonNeume": "Gorgon_Top"},
                }
            ],
        }
        with self.assertRaisesRegex(EzPhrasePlanError, "χωρίς αντίστοιχο EZ glyph anchor"):
            compile_confirmed_ez_phrase_plan(self.template, plan)

    def test_refuses_a_glyph_id_mismatch(self):
        self.template["rows"][0]["source"]["glyph_id_matches_full_font"] = False
        plan = {
            "schema": 1,
            "events": [
                {
                    "confirmed": True,
                    "source_anchors": [{"pdf_font_instance": "1:EZ", "pdf_glyph_id": 10, "pua_codepoint": "U+F031"}],
                    "resolution": {"quantitativeNeume": "Oligon"},
                }
            ],
        }
        with self.assertRaisesRegex(EzPhrasePlanError, "δεν συμφωνεί"):
            compile_confirmed_ez_phrase_plan(self.template, plan)

    def test_refuses_a_template_row_without_a_source_definition(self):
        self.template["rows"][0]["source_definition"] = None
        plan = {
            "schema": 1,
            "events": [
                {
                    "confirmed": True,
                    "source_anchors": [{"pdf_font_instance": "1:EZ", "pdf_glyph_id": 10, "pua_codepoint": "U+F031"}],
                    "resolution": {"quantitativeNeume": "Oligon"},
                }
            ],
        }
        with self.assertRaisesRegex(EzPhrasePlanError, "δεν έχει τεκμηριωμένο ορισμό"):
            compile_confirmed_ez_phrase_plan(self.template, plan)

    def test_keeps_only_an_explicitly_confirmed_opening_martyria(self):
        result = compile_confirmed_ez_phrase_plan(
            self.template,
            {
                "schema": 1,
                "opening_martyria": {"confirmed": True, "note": "Pa", "rootSign": "Alpha", "scale": "Diatonic"},
                "events": [
                    {
                        "confirmed": True,
                        "source_anchors": [{"pdf_font_instance": "1:EZ", "pdf_glyph_id": 10, "pua_codepoint": "U+F031"}],
                        "resolution": {"quantitativeNeume": "Oligon"},
                    }
                ],
            },
        )
        self.assertEqual(result["opening_martyria"], {"note": "Pa", "rootSign": "Alpha", "scale": "Diatonic"})

    def test_keeps_a_confirmed_ison_pause_out_of_the_neanes_note(self):
        result = compile_confirmed_ez_phrase_plan(
            self.template,
            {
                "schema": 1,
                "events": [
                    {
                        "confirmed": True,
                        "source_anchors": [{"pdf_font_instance": "1:EZ", "pdf_glyph_id": 10, "pua_codepoint": "U+F031"}],
                        "resolution": {"quantitativeNeume": "Oligon"},
                    }
                ],
                "ison_controls": [
                    {
                        "confirmed": True,
                        "after_note_event": 1,
                        "source_anchors": [{"pdf_font_instance": "1:EZ", "pdf_glyph_id": 13, "pua_codepoint": "U+F03F"}],
                    }
                ],
            },
        )
        self.assertEqual(result["ison_controls"], [{"kind": "pause", "after_note_event": 1}])
        self.assertNotIn("ison", result["events"][0])

    def test_compiles_a_confirmed_vareia_on_the_following_note(self):
        result = compile_confirmed_ez_phrase_plan(
            self.template,
            {
                "schema": 1,
                "events": [
                    {
                        "confirmed": True,
                        "source_anchors": [
                            {"pdf_font_instance": "1:EZ", "pdf_glyph_id": 10, "pua_codepoint": "U+F031"},
                            {"pdf_font_instance": "1:EZ", "pdf_glyph_id": 14, "pua_codepoint": "U+F07A"},
                        ],
                        "resolution": {"quantitativeNeume": "Oligon", "vareia": True},
                    }
                ],
            },
        )
        self.assertTrue(result["events"][0]["vareia"])
