import json
import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from src.digital_scores import DigitalScore
from src.reference_alignment import build_reference_ledger, record_phrase_anchors, write_reference_ledger


class ReferenceAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.byzx = self.root / "reference.byzx"
        self.byzx.write_text(
            json.dumps(
                {
                    "staff": {
                        "elements": [
                            {"id": 1, "elementType": "TextBox", "content": "Τίτλος"},
                            {"id": 2, "elementType": "Note", "quantitativeNeume": "Ison", "lyrics": "Του"},
                            {
                                "id": 3,
                                "elementType": "Note",
                                "quantitativeNeume": "Oligon",
                                "gorgonNeume": "GorgonAbove",
                                "lyrics": "λι",
                            },
                        ]
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def score(**overrides):
        values = dict(
            score_id="reference-score",
            title="Δοκιμαστικό μέλος",
            incipit="Τοῦ λίθου",
            tone_label="Ἦχος α΄",
            source_description="Εξωτερικό Neanes δείγμα",
            source_reference="Έντυπη πηγή · σ. 1",
            source_url=None,
            transcription_by="Neanes",
            review_state="verified",
            reviewed_by="vfilip",
            notes=None,
            byzx_filename="reference.byzx",
            ocr_filename=None,
            musicxml_filename=None,
            preview_filename=None,
            source_scan_filenames=("source-1.png",),
        )
        values.update(overrides)
        return DigitalScore(**values)

    def test_builds_unconfirmed_human_alignment_scaffold(self):
        ledger = build_reference_ledger(
            self.score(),
            self.byzx,
            generated_at=datetime(2026, 10, 10, tzinfo=UTC),
        )
        self.assertEqual(ledger["status"], "awaiting_phrase_alignment")
        self.assertEqual(ledger["score"]["note_count"], 2)
        self.assertEqual(ledger["notes"][0]["notation"], {"quantitativeNeume": "Ison"})
        self.assertEqual(ledger["notes"][1]["notation"]["gorgonNeume"], "GorgonAbove")
        self.assertIsNone(ledger["notes"][0]["source_anchor"])
        self.assertFalse(ledger["notes"][0]["confirmed"])
        self.assertTrue(ledger["rules"]["do_not_generate_byzx"])

    def test_refuses_an_unreviewed_score_as_reference(self):
        with self.assertRaisesRegex(ValueError, "Μόνο επαληθευμένη"):
            build_reference_ledger(self.score(review_state="needs_review", reviewed_by=None), self.byzx)

    def test_writes_json_without_copying_scans(self):
        ledger = build_reference_ledger(self.score(), self.byzx)
        target = write_reference_ledger(self.root / "private" / "ledger.json", ledger)
        self.assertTrue(target.is_file())
        saved = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(saved["source"]["scan_filenames"], ["source-1.png"])

    def test_records_only_contiguous_phrase_ranges_pending_visual_check(self):
        ledger = build_reference_ledger(self.score(), self.byzx)
        annotated = record_phrase_anchors(
            ledger,
            [
                {
                    "id": "opening",
                    "sequence_start": 1,
                    "sequence_end": 2,
                    "text": "Τοῦ λίθου",
                    "syllables": ["Του", "λι"],
                    "source_scan_part": 1,
                }
            ],
        )
        self.assertEqual(annotated["status"], "phrase_anchors_recorded_pending_visual_check")
        self.assertEqual(annotated["phrase_anchors"][0]["visual_status"], "pending_line_check")
        self.assertFalse(annotated["phrase_anchors"][0]["individual_glyphs_confirmed"])

    def test_refuses_non_contiguous_or_wrong_phrase_syllables(self):
        ledger = build_reference_ledger(self.score(), self.byzx)
        with self.assertRaisesRegex(ValueError, "δεν συμφωνούν"):
            record_phrase_anchors(
                ledger,
                [
                    {
                        "id": "opening",
                        "sequence_start": 1,
                        "sequence_end": 2,
                        "text": "Λάθος",
                        "syllables": ["λά", "θος"],
                        "source_scan_part": 1,
                    }
                ],
            )
