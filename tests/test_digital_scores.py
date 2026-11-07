import json
import unicodedata
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from src import digital_scores as digital_scores_module
from src.digital_scores import DigitalScoreCatalog, DigitalScoreReviewStore, parallage_label


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

    def test_public_draft_is_public_but_never_verified(self):
        self.write_catalog([self.score(public_draft=True), self.score(id="other-score")])
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        draft = catalog.get("lithou-sfragisthentos-tone1")
        self.assertTrue(draft.is_public)
        self.assertFalse(draft.is_verified)
        self.assertEqual([s.score_id for s in catalog.public_scores()], ["lithou-sfragisthentos-tone1"])
        self.assertEqual(catalog.verified_scores(), ())

    def test_public_draft_must_be_needs_review(self):
        self.write_catalog([self.score(public_draft=True, review_state="draft")])
        with self.assertRaises(ValueError):
            DigitalScoreCatalog(self.catalog_path, self.storage).scores()

    def test_parallage_labels_name_the_note_and_its_octave(self):
        self.assertEqual(parallage_label("Pa"), "Πα")
        self.assertEqual(parallage_label("Thi"), "Δι")
        self.assertEqual(parallage_label("ZoLow"), "Ζω κάτω")
        self.assertEqual(parallage_label("KeHigh"), "Κε άνω")
        self.assertIsNone(parallage_label("Unknown"))

    def test_note_labels_come_from_the_optional_private_sidecar(self):
        self.write_catalog([self.score()])
        (self.storage / "lithou-sfragisthentos-tone1.byzx").write_text("{}", encoding="utf-8")
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        score = catalog.get("lithou-sfragisthentos-tone1")
        self.assertIsNone(catalog.note_labels(score))
        sidecar = self.storage / "lithou-sfragisthentos-tone1.notes.json"
        sidecar.write_text(
            json.dumps({"schema": 1, "elements": {"1": ["Pa"], "2": ["Ni", "Pa"], "x": ["Pa"], "3": ["Bogus"]}}),
            encoding="utf-8",
        )
        self.assertEqual(catalog.note_labels(score), {"1": ["Πα"], "2": ["Νη", "Πα"]})
        sidecar.write_text("not json", encoding="utf-8")
        self.assertIsNone(catalog.note_labels(score))

    def test_hidden_elements_come_from_the_optional_private_sidecar(self):
        self.write_catalog([self.score()])
        (self.storage / "lithou-sfragisthentos-tone1.byzx").write_text("{}", encoding="utf-8")
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        score = catalog.get("lithou-sfragisthentos-tone1")
        self.assertEqual(catalog.hidden_elements(score), [])
        sidecar = self.storage / "lithou-sfragisthentos-tone1.notes.json"
        sidecar.write_text(json.dumps({"schema": 1, "elements": {}, "hidden": [12, 3, 3, -1, "x", True]}), encoding="utf-8")
        self.assertEqual(catalog.hidden_elements(score), [3, 12])
        sidecar.write_text("not json", encoding="utf-8")
        self.assertEqual(catalog.hidden_elements(score), [])

    def test_ison_marks_come_from_the_private_byzx(self):
        self.write_catalog([self.score()])
        byzx = self.storage / "lithou-sfragisthentos-tone1.byzx"
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        score = catalog.get("lithou-sfragisthentos-tone1")

        self.assertEqual(catalog.ison_marks(score), [])
        byzx.write_text(
            json.dumps(
                {
                    "staff": {
                        "elements": [
                            {"elementType": "Martyria", "note": "Pa"},
                            {"elementType": "Note", "ison": "Ison.Pa"},
                            {"elementType": "Note"},
                            {"elementType": "Empty"},
                            {"elementType": "Note", "ison": "Ison.Thi"},
                            {"elementType": "Note", "ison": "Ison.Unison"},
                            "not an object",
                            {"elementType": "Note", "ison": 7},
                            {"elementType": "Note", "ison": "  "},
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            catalog.ison_marks(score),
            [[1, "Ison.Pa"], [4, "Ison.Thi"], [5, "Ison.Unison"]],
        )

        byzx.write_text("not json", encoding="utf-8")
        self.assertEqual(catalog.ison_marks(score), [])
        byzx.write_text(json.dumps({"staff": {}}), encoding="utf-8")
        self.assertEqual(catalog.ison_marks(score), [])
        byzx.unlink()
        self.assertEqual(catalog.ison_marks(score), [])

    def test_auto_ison_marks_use_the_mode_default_and_never_override_real_marks(self):
        self.write_catalog([self.score(), self.score(id="with-real-marks")])
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        score = catalog.get("lithou-sfragisthentos-tone1")
        byzx = self.storage / "lithou-sfragisthentos-tone1.byzx"
        byzx.write_text(
            json.dumps(
                {
                    "staff": {
                        "elements": [
                            {"elementType": "Martyria", "note": "Pa"},
                            {"elementType": "Note"},
                            {"elementType": "Note"},
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(catalog.auto_ison_marks(score), [[1, "Ison.Pa"]])

        byzx.write_text(
            json.dumps(
                {
                    "staff": {
                        "elements": [
                            {"elementType": "Martyria", "note": "Pa"},
                            {"elementType": "Note", "ison": "Ison.Pa"},
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(catalog.auto_ison_marks(score), [])

    def test_auto_ison_marks_switch_to_di_on_a_high_segment_and_back(self):
        self.write_catalog([self.score()])
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        score = catalog.get("lithou-sfragisthentos-tone1")
        byzx = self.storage / "lithou-sfragisthentos-tone1.byzx"
        elements = [{"elementType": "Martyria", "note": "Pa"}]
        elements += [{"elementType": "Note"} for _ in range(3)]
        elements += [{"elementType": "Martyria", "note": "Pa"}]
        elements += [{"elementType": "Note"} for _ in range(3)]
        elements += [{"elementType": "Martyria", "note": "Pa"}]
        elements += [{"elementType": "Note"} for _ in range(3)]
        byzx.write_text(json.dumps({"staff": {"elements": elements}}), encoding="utf-8")
        byzx.with_suffix(".notes.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "physical": {
                        "1": ["Pa"],
                        "2": ["Vou"],
                        "3": ["Ga"],
                        "5": ["NiHigh"],
                        "6": ["PaHigh"],
                        "7": ["ZoHigh"],
                        "9": ["Pa"],
                        "10": ["Ni"],
                        "11": ["Pa"],
                    },
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            catalog.auto_ison_marks(score),
            [[1, "Ison.Pa"], [5, "Ison.Thi"], [9, "Ison.Pa"]],
        )

    def test_auto_ison_marks_do_not_raise_without_a_sidecar_or_for_unknown_modes(self):
        self.write_catalog([self.score(), self.score(id="unknown-tone", tone_label="Δεν δηλώνεται ήχος")])
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        byzx = self.storage / "lithou-sfragisthentos-tone1.byzx"
        byzx.write_text(
            json.dumps({"staff": {"elements": [{"elementType": "Note"}, {"elementType": "Note"}]}}),
            encoding="utf-8",
        )
        score = catalog.get("lithou-sfragisthentos-tone1")
        self.assertEqual(catalog.auto_ison_marks(score), [[0, "Ison.Pa"]])
        byzx.with_suffix(".notes.json").write_text("not json", encoding="utf-8")
        self.assertEqual(catalog.auto_ison_marks(score), [[0, "Ison.Pa"]])
        self.assertEqual(catalog.auto_ison_marks(catalog.get("unknown-tone")), [])

    def test_auto_ison_marks_do_not_replace_a_default_already_at_or_above_di(self):
        self.write_catalog([self.score(id="tone-two", tone_label="Ἦχος β΄")])
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        score = catalog.get("tone-two")
        byzx = self.storage / "lithou-sfragisthentos-tone1.byzx"
        byzx.write_text(
            json.dumps(
                {
                    "staff": {
                        "elements": [
                            {"elementType": "Martyria", "note": "Thi"},
                            {"elementType": "Note"},
                            {"elementType": "Martyria", "note": "Thi"},
                            {"elementType": "Note"},
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )
        byzx.with_suffix(".notes.json").write_text(
            json.dumps({"schema": 1, "physical": {"1": ["Pa"], "3": ["PaHigh"]}}),
            encoding="utf-8",
        )
        self.assertEqual(catalog.auto_ison_marks(score), [[1, "Ison.Thi"]])

    def test_auto_ison_marks_use_the_genus_data_for_ambiguous_modes(self):
        cases = (
            ("papline-cher-pl2-gregorios-private-draft", "Ἦχος β΄", "Ison.Pa"),
            ("papline-kat-kyrap-s-α-private-draft", "Ἦχος β΄", "Ison.Thi"),
            ("papline-kat-megsab-s-α-private-draft", "Ἦχος πλ. β΄", "Ison.Thi"),
            ("papline-kat-pent-s-α-private-draft", "Ἦχος βαρύς", "Ison.Ga"),
            ("papline-kat-sabva-s-α-private-draft", "Ἦχος πλ. δ΄", "Ison.Ga"),
            ("not-in-genus", "Ἦχος πλ. δ΄", "Ison.Ni"),
        )
        self.write_catalog([self.score(id=score_id, tone_label=label) for score_id, label, _ in cases])
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        byzx = self.storage / "lithou-sfragisthentos-tone1.byzx"
        byzx.write_text(
            json.dumps({"staff": {"elements": [{"elementType": "Note"}]}}),
            encoding="utf-8",
        )
        for score_id, label, expected in cases:
            with self.subTest(score_id=score_id, label=label):
                self.assertEqual(catalog.auto_ison_marks(catalog.get(score_id)), [[0, expected]])

    def test_hard_chromatic_pa_default_still_switches_to_di_above_di(self):
        self.write_catalog(
            [self.score(id="papline-cher-pl2-gregorios-private-draft", tone_label="Ἦχος β΄")]
        )
        catalog = DigitalScoreCatalog(self.catalog_path, self.storage)
        score = catalog.get("papline-cher-pl2-gregorios-private-draft")
        byzx = self.storage / "lithou-sfragisthentos-tone1.byzx"
        elements = [{"elementType": "Martyria", "note": "Pa"}]
        elements += [{"elementType": "Note"} for _ in range(3)]
        elements += [{"elementType": "Martyria", "note": "Pa"}]
        elements += [{"elementType": "Note"} for _ in range(3)]
        byzx.write_text(json.dumps({"staff": {"elements": elements}}), encoding="utf-8")
        byzx.with_suffix(".notes.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "physical": {
                        "1": ["Pa"],
                        "2": ["Vou"],
                        "3": ["Ga"],
                        "5": ["NiHigh"],
                        "6": ["PaHigh"],
                        "7": ["ZoHigh"],
                    },
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            catalog.auto_ison_marks(score),
            [[1, "Ison.Pa"], [5, "Ison.Thi"]],
        )

    def test_genus_loader_never_raises_for_an_absent_file(self):
        digital_scores_module.ison_genus_table.cache_clear()
        try:
            with mock.patch.object(
                digital_scores_module,
                "ISON_GENUS_PATH",
                self.root / "missing-ison-genus.json",
            ):
                self.assertEqual(digital_scores_module.ison_genus_table(), {})
        finally:
            digital_scores_module.ison_genus_table.cache_clear()

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

    def test_playback_speed_defaults_to_normal_and_is_bounded(self):
        self.write_catalog([self.score(), self.score(id="slow", playback_speed=0.6)])
        scores = DigitalScoreCatalog(self.catalog_path, self.storage).scores()
        self.assertEqual([score.playback_speed for score in scores], [1.0, 0.6])
        for invalid in (0, 5, "0.6", True):
            self.write_catalog([self.score(playback_speed=invalid)])
            with self.assertRaisesRegex(ValueError, "playback_speed"):
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
            [
                "lithou-sfragisthentos-tone1",
                "formula1p-ez-word-varys-ga-diatonic-pilot",
                "ananas-line7-pdf-private-draft",
                "papline-cherubikon-lambadarios-full-private-draft",
                "papline-koinonikon-aineite-lambadarios-full-private-draft",
                "papline-koinonikon-aineite-2-lambadarios-full-private-draft",
                "papline-koinonikon-aineite-3-lambadarios-full-private-draft",
                "papline-doxologia-manuel1-tone4-private-draft",
                "papline-ainoi-lambadarios-tone4-private-draft",
                "papline-doxastikon-eothinon10-lambadarios-private-draft",
            ],
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

    def test_short_katavasies_data_exists_in_the_catalogue_with_unique_incipits(self):
        project_root = Path(__file__).resolve().parents[1]
        catalogue = json.loads(
            (project_root / "src" / "data" / "digital_scores.json").read_text(encoding="utf-8")
        )["scores"]
        catalogue_ids = {score["id"] for score in catalogue}
        entries = json.loads(
            (project_root / "src" / "data" / "katavasies.json").read_text(encoding="utf-8")
        )
        self.assertTrue(entries)

        def normalized(value):
            value = unicodedata.normalize("NFD", value.casefold())
            cleaned = "".join(
                ch
                for ch in value
                if unicodedata.category(ch)
                not in {"Mn", "Pc", "Pd", "Pe", "Pf", "Pi", "Po", "Ps"}
            )
            return " ".join(cleaned.split())

        for entry in entries:
            self.assertIn(entry["id"], catalogue_ids)
            for field in ("set", "ode", "incipit", "first_incipit", "feast", "composer", "tone", "title"):
                self.assertTrue(entry[field], f"{entry['id']} has no {field}")
            self.assertGreaterEqual(
                len(normalized(entry["incipit"]).split()),
                3,
                f"{entry['id']} has a short ode incipit",
            )
            self.assertGreaterEqual(
                len(normalized(entry["first_incipit"]).split()),
                3,
                f"{entry['id']} has a short first incipit",
            )
        incipits = [normalized(entry["incipit"]) for entry in entries]
        self.assertEqual(len(incipits), len(set(incipits)))
