import tempfile
import unittest
from datetime import date

from src.anastasimatarion import enrich_service_html
from src.typesafe_decisions import MusicDecision, TypesafeDecisionService


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "model": "jev-1.13.0",
            "answers": {
                "score": {
                    "type": "choice",
                    "choice": "plagal4_timiotera",
                    "confidence": 0.99,
                    "probabilities": {
                        "plagal4_timiotera": 0.99,
                        "tone4_timiotera": 0.01,
                        "no_score": 0.0,
                    },
                }
            },
            "usage": {"input_tokens": 100, "output_tokens": 10},
        }


class _Session:
    def __init__(self):
        self.calls = 0

    def post(self, *args, **kwargs):
        self.calls += 1
        return _Response()


class _AinoiResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "model": "jev-1.13.0",
            "answers": {
                "style": {
                    "type": "choice",
                    "choice": "short_ainoi",
                    "confidence": 0.99,
                    "probabilities": {
                        "slow_ainoi": 0.01,
                        "short_ainoi": 0.99,
                        "no_score": 0.0,
                    },
                }
            },
        }


class _AinoiSession:
    def __init__(self):
        self.calls = 0

    def post(self, *args, **kwargs):
        self.calls += 1
        return _AinoiResponse()


class _RejectingReviewer:
    def review_timiotera(self, _instruction):
        return MusicDecision(
            choice="tone4_timiotera",
            confidence=0.99,
            probabilities={"tone4_timiotera": 0.99},
            model="test",
        )


class TypesafeDecisionTests(unittest.TestCase):
    def test_timiotera_decision_is_cached_after_its_first_jev_call(self):
        with tempfile.TemporaryDirectory() as directory:
            session = _Session()
            service = TypesafeDecisionService(
                directory, api_key="test-key", session=session
            )
            instruction = "και ψαλλεται η τιμιωτερα στον ιδιο ηχο του ειρμου ηχοσ πλ δ"

            first = service.review_timiotera(instruction)
            second = service.review_timiotera(instruction)

        self.assertEqual(first.choice, "plagal4_timiotera")
        self.assertEqual(second.choice, "plagal4_timiotera")
        self.assertEqual(session.calls, 1)

    def test_sunday_ainoi_style_is_closed_and_cached_per_tone(self):
        with tempfile.TemporaryDirectory() as directory:
            session = _AinoiSession()
            service = TypesafeDecisionService(
                directory, api_key="test-key", session=session
            )

            first = service.review_ainoi_style(
                weekly_tone=3, local_heading="δοξαστικον εωθινον"
            )
            second = service.review_ainoi_style(
                weekly_tone=3, local_heading="δοξαστικον εωθινον"
            )

        self.assertEqual(first.choice, "short_ainoi")
        self.assertEqual(second.choice, "short_ainoi")
        self.assertEqual(session.calls, 1)

    def test_high_confidence_jev_disagreement_blocks_an_unsafe_timiotera_score(self):
        refrain = (
            "Τὴν Τιμιωτέραν τῶν Χερουβείμ, καὶ ἐνδοξοτέραν ἀσυγκρίτως "
            "τῶν Σεραφείμ, τὴν ἀδιαφθόρως Θεὸν Λόγον τεκοῦσαν, "
            "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.<br>"
        )
        source = (
            "Καὶ ψάλλεται ἡ Τιμιωτέρα στον ίδιο ήχο του Ειρμού. Ἦχος πλ δ΄<br>"
            + refrain * 6
        )

        result = enrich_service_html(
            date(2026, 10, 3),
            "orthros",
            source,
            semantic_reviewer=_RejectingReviewer(),
        )

        self.assertNotIn('data-music-piece="plagal4-timiotera"', result.html)
