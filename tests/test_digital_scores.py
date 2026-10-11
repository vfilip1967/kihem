import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.digital_scores import DigitalScoreCatalog, DigitalScoreReviewStore


class DigitalScoreCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.catalog_path = self.root / "catalog.json"
        self.storage = self.root / "assets"
        self.storage.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def write_catalog(self, scores):
        self.catalog_path.write_text(json.dumps({"schema": 1, "scores": scores}), encoding="utf-8")

    @staticmethod
    def score(**overrides):
        value = {
            "id": "lithou-sfragisthentos-tone1",
            "title": "Ἀναστάσιμον Ἀπολυτίκιον · ἦχος α΄",
            "incipit": "Τοῦ λίθου σφραγισθέντος",
            "tone_label": "Ἦχος α΄",
            "source_description": "Ελεγμένη πιλοτική μεταγραφή από έντυπη παρτιτούρα.",
            "source_reference": "Δοκιμαστική έντυπη πηγή · σ. 1",
            "source_url": "https://example.test/source",
            "transcription_by": "Πιλοτική ομάδα Kihem",
            "review_state": "needs_review",
            "byzx_filename": "lithou-sfragisthentos-tone1.byzx",
            "ocr_filename": "lithou-sfragisthentos-tone1.byzocr",
            "musicxml_filename": "lithou-sfragisthentos-tone1.musicxml",
            "source_scan_filenames": ["source-1.png"],
        }
        value.update(overrides)
        return value

    def test_loads_a_reviewable_score_and_resolves_only_local_assets(self):
        self.write_catalog([self.score()])
        (self.storage / "lithou-sfragisthentos-tone1.byzx").write_text("{}", encoding="utf-8")
        (self.storage / "lithou-sfragisthentos-tone1.byzocr").write_text("pages: []\n", encoding="utf-8")
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        score = catalog.get("lithou-sfragisthentos-tone1")
        self.assertIsNotNone(score)
        self.assertFalse(score.is_verified)
        self.assertEqual(score.source_reference, "Δοκιμαστική έντυπη πηγή · σ. 1")
        self.assertEqual(catalog.asset_path(score, "byzx"), self.storage / "lithou-sfragisthentos-tone1.byzx")
        self.assertEqual(catalog.asset_path(score, "ocr"), self.storage / "lithou-sfragisthentos-tone1.byzocr")
        self.assertIsNone(catalog.asset_path(score, "musicxml"))

    def test_source_scan_paths_are_catalogued_and_cannot_escape_storage(self):
        self.write_catalog([self.score()])
        (self.storage / "source-1.png").write_bytes(b"source")
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        score = catalog.get("lithou-sfragisthentos-tone1")
        self.assertEqual(catalog.source_scan_path(score, 0), self.storage / "source-1.png")
        self.assertIsNone(catalog.source_scan_path(score, 1))

    def test_private_review_store_preserves_notes_without_publishing_a_score(self):
        store = DigitalScoreReviewStore(self.root / "review-notes")
        saved = store.save(
            "lithou-sfragisthentos-tone1",
            "Δοκιμαστικός ψάλτης",
            {"lyrics": True, "neumes": False},
            "Χρειάζεται ακόμη ακουστικός έλεγχος.",
        )
        self.assertEqual(saved["reviewer"], "Δοκιμαστικός ψάλτης")
        self.assertTrue(store.read("lithou-sfragisthentos-tone1")["checks"]["lyrics"])

    def test_verified_score_requires_named_psaltis_reviewer(self):
        self.write_catalog([self.score(review_state="verified")])
        with self.assertRaisesRegex(ValueError, "απαιτεί όνομα ελεγκτή"):
            DigitalScoreCatalog(self.catalog_path, self.storage).scores()

    def test_catalog_rejects_traversal_in_asset_names(self):
        self.write_catalog([self.score(byzx_filename="../outside.byzx")])
        with self.assertRaisesRegex(ValueError, "Μη ασφαλές"):
            DigitalScoreCatalog(self.catalog_path, self.storage).scores()

    def test_verified_score_is_explicitly_marked(self):
        self.write_catalog([self.score(review_state="verified", reviewed_by="Πρωτοψάλτης δοκιμής")])
        score = DigitalScoreCatalog(self.catalog_path, self.storage).scores()[0]
        self.assertTrue(score.is_verified)

    def test_only_verified_scores_are_listed_for_publication(self):
        self.write_catalog(
            [
                self.score(id="draft", review_state="draft"),
                self.score(id="reviewed", review_state="verified", reviewed_by="Πρωτοψάλτης δοκιμής"),
            ]
        )
        scores = DigitalScoreCatalog(self.catalog_path, self.storage).verified_scores()
        self.assertEqual([score.score_id for score in scores], ["reviewed"])

    def test_repository_pilot_is_verified_by_a_named_reviewer(self):
        project_root = Path(__file__).resolve().parents[1]
        catalog = DigitalScoreCatalog(
            project_root / "src" / "data" / "digital_scores.json",
            self.storage,
        )
        score = catalog.get("lithou-sfragisthentos-tone1")
        self.assertIsNotNone(score)
        self.assertEqual(score.review_state, "verified")
        self.assertEqual(score.reviewed_by, "vfilip")
        self.assertEqual(score.byzx_filename, "lithou-sfragisthentos-tone1.byzx")
        self.assertEqual(
            [published.score_id for published in catalog.verified_scores()],
            ["lithou-sfragisthentos-tone1", "formula1p-ez-word-varys-ga-diatonic-pilot", "ananas-line7-pdf-private-draft"],
        )

    def test_second_tone_candidate_has_its_own_private_source_page(self):
        project_root = Path(__file__).resolve().parents[1]
        catalog = DigitalScoreCatalog(
            project_root / "src" / "data" / "digital_scores.json",
            self.storage,
        )
        score = catalog.get("ote-katilthes-tone2")
        self.assertIsNotNone(score)
        self.assertEqual(score.review_state, "needs_review")
        self.assertEqual(score.source_reference, "Ἀναστασιματάριον Ἰωάννου Πρωτοψάλτου (1905) · έντυπες σελ. 65–66")
        self.assertEqual(
            score.source_scan_filenames,
            ("ote-katilthes-tone2-source-1.png", "ote-katilthes-tone2-source-2.png"),
        )

    def test_ocr_draft_keeps_the_machine_result_private_and_traceable(self):
        project_root = Path(__file__).resolve().parents[1]
        catalog = DigitalScoreCatalog(
            project_root / "src" / "data" / "digital_scores.json",
            self.storage,
        )
        score = catalog.get("ote-katilthes-tone2-ocr-draft")
        self.assertIsNotNone(score)
        self.assertEqual(score.review_state, "draft")
        self.assertEqual(score.ocr_filename, "ote-katilthes-tone2-ocr.byzocr")
        self.assertNotIn(score, catalog.verified_scores())
