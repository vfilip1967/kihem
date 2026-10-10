import unittest
from pathlib import Path

from src.neanes_byzx_bridge import NeanesByzxBridgeError, _typescript_worker, write_private_byzx


def event_draft():
    return {
        "schema": 1,
        "purpose": "private-confirmed-ez-neanes-event-draft; not-a-complete-byzx-score",
        "review_state": "needs_score_and_auditory_review",
        "events": [{"elementType": "Note", "quantitativeNeume": "Oligon", "lyrics": "δοκιμή"}],
    }


class NeanesByzxBridgeTests(unittest.TestCase):
    def test_rejects_a_non_private_event_draft(self):
        with self.assertRaisesRegex(NeanesByzxBridgeError, "έγκυρο ιδιωτικό"):
            write_private_byzx({}, output_path="/tmp/ignored.byzx", title="x", neanes_source="/tmp/no-neanes")

    def test_generated_worker_uses_neanes_own_serializer_and_marks_the_draft_private(self):
        worker = _typescript_worker(event_draft(), Path("/tmp/private.byzx"), "Δοκιμή")
        self.assertIn("SaveService.SaveScoreToJson(score)", worker)
        self.assertIn("ιδιωτικό EZ draft", worker)
        self.assertIn("new EmptyElement()", worker)
        self.assertNotIn("source PDF", worker)

    def test_generated_worker_keeps_a_confirmed_martyria_manual_through_layout(self):
        draft = event_draft()
        draft["opening_martyria"] = {"note": "Ga", "rootSign": "Varys", "scale": "Diatonic"}
        worker = _typescript_worker(draft, Path("/tmp/private.byzx"), "Δοκιμή")
        self.assertIn("const element = new MartyriaElement()", worker)
        self.assertIn("element.auto = false", worker)
        self.assertIn("Object.assign(element, martyria)", worker)
        self.assertIn("element.rootSignOverride = element.rootSign", worker)
        self.assertIn("expect(reopenedMartyria!.auto).toBe(false)", worker)
        self.assertIn("expect(reopenedMartyria!.note).toBe(martyria.note)", worker)
        self.assertNotIn("ModeKeyElement.createFromTemplate", worker)
