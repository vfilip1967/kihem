import json
from base64 import b64encode
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from src.app import create_app
from src.composer import ComposedService
from src.melodos import ServiceDocument


class FakeComposer:
    def compose(self, selected_date, services, refresh=False):
        documents = tuple(
            ServiceDocument(
                service=service,
                label="Όρθρος" if service == "orthros" else "Θεία Λειτουργία Ιωάννου Χρυσοστόμου",
                service_html=(
                    'Ήχος εβδομάδος πλ β΄.<br><span class="ep">Δοκιμαστικό κείμενο</span><br>'
                    "Ἀγγελικαὶ Δυνάμεις, ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.<br>"
                    '<span class="ep">ΑΠΟΣΤΟΛΟΣ</span><br>Πρὸς Ῥωμαίους 1:1-7<br>'
                    "Ἀδελφοί, τὸ εὐαγγέλιον τοῦ Χριστοῦ εἶναι δύναμις Θεοῦ καὶ κλήση σε πίστη, αγάπη και ελπίδα για κάθε άνθρωπο.<br>"
                    '<span class="ar">Ἀλληλούϊα</span><br><span class="ep">ΕΥΑΓΓΕΛΙΟΝ</span><br>Ἐκ τοῦ κατὰ Λουκᾶν 5:1-11<br>'
                    "Τῷ καιρῷ ἐκείνῳ, ἐδίδασκεν ὁ Ἰησοῦς τοὺς μαθητὰς καὶ ἐκάλεσεν αὐτοὺς νὰ τὸν ἀκολουθήσουν με πίστη και ταπείνωση.<br>"
                    '<span class="ep">Επόμενο μέρος</span>'
                ),
                plain_text="Δοκιμαστικό κείμενο — Ἀγγελικαὶ Δυνάμεις",
                tone=6,
                tone_label="Ἦχος πλ. β΄",
                fetched_at=datetime.now(timezone.utc),
                source_day_label=(
                    "Δευτέρα 14 Σεπτεμβρίου 2026"
                    if selected_date.day == 14
                    else "Κυριακή 13 Σεπτεμβρίου 2026"
                ),
                source_tone_label="Ήχος εβδομάδος πλ β΄.",
                day_title=("Δοκιμαστικός τίτλος Μελωδού" if selected_date.day == 13 else None),
            )
            for service in services
        )
        return ComposedService(selected_date=selected_date, documents=documents, tone=6)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        byz = Path(self.temporary.name) / "byz"
        (byz / "isokratis").mkdir(parents=True)
        (byz / "prosomia").mkdir()
        (byz / "isokratis" / "60.mp3").write_bytes(b"test-ison")
        (byz / "prosomia" / "1-ouraniwn.mp3").write_bytes(b"test-prosomia")
        (byz / "prosomia" / "ηχος_πλ.β_θεος_κυριος.m4a").write_bytes(b"test-prosomia-m4a")
        (byz / "prosomia" / "not-for-web.pdf").write_bytes(b"test-pdf")
        self.app = create_app(
            {
                "TESTING": True,
                "CACHE_DIR": self.temporary.name,
                "BYZ_DIR": str(byz),
                "COMPOSER": FakeComposer(),
                "DEFAULT_DATE": "2026-09-09",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temporary.cleanup()

    def test_index_renders_one_orthros_page_and_music_links(self):
        response = self.client.get("/?date=2026-09-13&services=orthros")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('href="static/app.css?v=20260929-reading-bookmarks"', text)
        self.assertIn("Όρθρος", text)
        self.assertIn("Θεία Λειτουργία", text)  # separate-page navigation
        self.assertIn('class="service-switch-link active" href="?date=2026-09-13&amp;services=orthros"', text)
        self.assertIn('class="service-switch-link " href="?date=2026-09-13&amp;services=litourgia"', text)
        self.assertIn("Δοκιμαστικός τίτλος Μελωδού", text)
        self.assertIn("Ήχος εβδομάδος πλ β΄.", text)
        self.assertNotIn("τοποθετήθηκαν κάτω από τα αντίστοιχα μέλη", text)
        self.assertIn("music/ioannis-protopsaltis-1905/tone6-apolytikion/1.png", text)
        self.assertIn('class="music-bookmarks-menu"', text)
        self.assertIn('class="reading-bookmarks-menu"', text)
        self.assertIn('class="reader-nav-row"', text)
        self.assertIn('<summary>Αναγνώσεις <span>2</span></summary>', text)
        self.assertIn('href="#reading-orthros-first-apostolos"', text)
        self.assertIn('href="#reading-orthros-first-evangelion"', text)
        self.assertIn('<summary>Μουσικά <span>1</span></summary>', text)
        self.assertNotIn('Μουσικά κείμενα', text)
        self.assertIn('href="#music-tone6-apolytikion-1"', text)
        self.assertNotIn('href="#music-tone6-apolytikion-2"', text)
        self.assertIn("link.closest('details').open = false", text)
        self.assertIn('data-scroll-controls', text)
        self.assertIn('data-scroll-toggle', text)
        self.assertIn('readerToolbar.append(isokratisPanel)', text)
        self.assertNotIn('data-scroll-slower', text)
        self.assertNotIn('data-scroll-faster', text)
        self.assertNotIn("kihem-scroll-level", text)
        self.assertNotIn("Μουσικό παράρτημα", text)
        self.assertIn('data-isokratis', text)
        self.assertIn("Ἴσον και προσόμοια", text)
        self.assertNotIn('data-ison-play', text)
        self.assertNotIn('data-ison-reset', text)
        self.assertNotIn('data-prosomia-play', text)
        self.assertNotIn('data-prosomia-pause', text)
        self.assertIn('data-prosomia-stop', text)
        self.assertIn('title="Διακοπή ισοκρατήματος">Ⅱ</button>', text)
        self.assertIn('title="Διακοπή ηχογράφησης">Ⅱ</button>', text)
        self.assertNotIn('>■ Διακοπή</button>', text)
        self.assertIn('data-register-down aria-label="Μείωση διαστήματος">−1', text)
        self.assertIn('data-register-up aria-label="Αύξηση διαστήματος">+1', text)
        self.assertIn('data-semitone-down aria-label="Μείωση ημιτονίου">−6', text)
        self.assertIn('data-semitone-up aria-label="Αύξηση ημιτονίου">+6', text)
        self.assertIn("Οὐρανίων ταγμάτων", text)
        self.assertIn('data-ison-url-template="isokratis/ison/__number__.mp3"', text)
        self.assertIn('value="isokratis/prosomia/1-ouraniwn.mp3"', text)
        self.assertIn("prosomiaGroup.addEventListener('change', () => setTracks(true))", text)
        self.assertNotIn("not-for-web.pdf", text)
        self.assertIn("melodos-audio?url=", text)

    def test_index_renders_litourgia_on_its_own_page(self):
        response = self.client.get("/?date=2026-09-13&services=litourgia")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("Θεία Λειτουργία", text)
        self.assertNotIn('id="orthros"', text)

    def test_legacy_both_query_opens_single_orthros_page(self):
        response = self.client.get("/?date=2026-09-13&services=both")
        text = response.get_data(as_text=True)
        self.assertIn('id="orthros"', text)
        self.assertNotIn('id="litourgia"', text)

    def test_configured_default_date_is_used_for_deterministic_testing(self):
        response = self.client.get("/")
        self.assertIn('value="2026-09-09"', response.get_data(as_text=True))

    def test_unconfigured_default_date_is_tomorrow_and_orthros(self):
        self.app.config["DEFAULT_DATE"] = None
        response = self.client.get("/")
        text = response.get_data(as_text=True)
        tomorrow = date.today() + timedelta(days=1)
        self.assertIn(f'value="{tomorrow.isoformat()}"', text)
        self.assertIn('id="orthros"', text)
        self.assertNotIn('id="litourgia"', text)

    def test_index_composes_non_sunday_instead_of_rejecting_it(self):
        response = self.client.get("/?date=2026-09-14")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("Δευτέρα 14 Σεπτεμβρίου 2026", text)
        self.assertNotIn("τοποθετήθηκαν κάτω από τα αντίστοιχα μέλη", text)
        self.assertNotIn("Η επόμενη Κυριακή", text)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.json["calendar"], "gregorian")

    def test_digital_score_endpoints_hide_unreviewed_transcriptions(self):
        digital_assets = Path(self.temporary.name) / "digital-scores"
        digital_assets.mkdir()
        catalog_path = Path(self.temporary.name) / "digital-scores.json"
        catalog_path.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "scores": [
                        {
                            "id": "draft-score",
                            "title": "Πρόχειρο μέλος",
                            "incipit": "Δοκιμή",
                            "tone_label": "Ἦχος α΄",
                            "source_description": "Πρωτότυπη σάρωση",
                            "source_reference": "Δοκιμαστική έντυπη πηγή · σ. 1",
                            "transcription_by": "Δοκιμή",
                            "review_state": "draft",
                            "byzx_filename": "draft-score.byzx",
                            "ocr_filename": "draft-score.byzocr",
                            "musicxml_filename": "draft-score.musicxml",
                            "preview_filename": "draft-score-preview.png",
                            "source_scan_filenames": ["draft-source-1.png"],
                        },
                        {
                            "id": "verified-score",
                            "title": "Ελεγμένο μέλος",
                            "incipit": "Δοκιμή ελεγμένη",
                            "tone_label": "Ἦχος α΄",
                            "source_description": "Πρωτότυπη σάρωση",
                            "transcription_by": "Δοκιμή",
                            "review_state": "verified",
                            "reviewed_by": "Πρωτοψάλτης δοκιμής",
                            "byzx_filename": "verified-score.byzx",
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (digital_assets / "draft-score.byzx").write_text("{}", encoding="utf-8")
        (digital_assets / "draft-score.byzocr").write_text("pages: []\n", encoding="utf-8")
        (digital_assets / "draft-score.musicxml").write_text("<score-partwise/>", encoding="utf-8")
        (digital_assets / "draft-score-preview.png").write_bytes(b"preview")
        (digital_assets / "draft-source-1.png").write_bytes(b"source")
        (digital_assets / "verified-score.byzx").write_text("{}", encoding="utf-8")
        neanes_web = Path(self.temporary.name) / "neanes-web"
        neanes_web.mkdir()
        (neanes_web / "index.html").write_text("<!doctype html><title>Neanes</title>", encoding="utf-8")
        (neanes_web / "app.js").write_text("window.neanes = true;", encoding="utf-8")
        app = create_app(
            {
                "TESTING": True,
                "CACHE_DIR": self.temporary.name,
                "BYZ_DIR": str(Path(self.temporary.name) / "byz"),
                "COMPOSER": FakeComposer(),
                "DIGITAL_SCORES_CATALOG": str(catalog_path),
                "DIGITAL_SCORES_DIR": str(digital_assets),
                "DIGITAL_SCORES_REVIEW_DIR": str(Path(self.temporary.name) / "review-notes"),
                "NEANES_WEB_DIR": str(neanes_web),
                "REVIEW_USERNAME": "reviewer",
                "REVIEW_PASSWORD": "test-secret",
            }
        )
        client = app.test_client()
        response = client.get("/digital-scores")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([score["id"] for score in response.json], ["verified-score"])
        self.assertEqual(response.json[0]["assets"]["byzx"], "/digital-scores/verified-score/byzx")
        public_list = client.get("/digital-scores", headers={"Accept": "text/html"})
        self.assertEqual(public_list.status_code, 200)
        self.assertIn("Επαληθευμένες ψηφιακές παρτιτούρες", public_list.get_data(as_text=True))
        public_score = client.get("/digital-scores/verified-score/")
        self.assertEqual(public_score.status_code, 200)
        self.assertEqual(public_score.headers["Cache-Control"], "no-store, max-age=0")
        self.assertIn("Ελεγμένο μέλος", public_score.get_data(as_text=True))
        self.assertIn("digital-scores/neanes/app", public_score.get_data(as_text=True))
        self.assertIn("reclaimReaderWidth", public_score.get_data(as_text=True))
        self.assertIn("useNeanesPageWidth", public_score.get_data(as_text=True))
        self.assertIn("Kihem public reader", public_score.get_data(as_text=True))
        self.assertIn(".dv-groupview:has", public_score.get_data(as_text=True))
        self.assertIn('id="speed-select"', public_score.get_data(as_text=True))
        self.assertIn('"kihem-speed-verified-score"', public_score.get_data(as_text=True))
        self.assertIn("const fallback = 1.0;", public_score.get_data(as_text=True))
        self.assertIn('id="practice-play"', public_score.get_data(as_text=True))
        self.assertIn(".contextual-toolbar-panel", public_score.get_data(as_text=True))
        public_neanes = client.get("/digital-scores/neanes/app/")
        self.assertEqual(public_neanes.status_code, 200)
        self.assertIn("Neanes", public_neanes.get_data(as_text=True))
        self.assertEqual(client.get("/digital-scores/draft-score/").status_code, 404)
        self.assertEqual(client.get("/digital-scores/draft-score/byzx").status_code, 404)
        download = client.get("/digital-scores/verified-score/byzx")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.mimetype, "application/json")
        download.close()

        review_path = "/review/digital-scores/draft-score"
        self.assertEqual(client.get(review_path).status_code, 401)
        authorization = {"Authorization": "Basic " + b64encode(b"reviewer:test-secret").decode()}
        review = client.get(
            review_path,
            headers={**authorization, "X-Forwarded-Prefix": "/kihem"},
        )
        self.assertEqual(review.status_code, 200)
        self.assertIn("Ιδιωτικός χώρος ελέγχου", review.get_data(as_text=True))
        review_html = review.get_data(as_text=True)
        self.assertIn(
            '/kihem/review/digital-scores/draft-score/asset/source?position=0',
            review_html,
        )
        self.assertIn("Πλήρης αρχική εικόνα Neanes", review_html)
        self.assertIn("Τεχνική ακρόαση", review_html)
        self.assertIn("Ενσωματωμένη ακρόαση Neanes", review_html)
        self.assertIn("Αποτέλεσμα OCR .byzocr", review_html)
        self.assertIn("Δοκιμαστική έντυπη πηγή · σ. 1", review_html)
        unpreviewed_review = client.get(
            "/review/digital-scores/verified-score",
            headers={**authorization, "X-Forwarded-Prefix": "/kihem"},
        )
        self.assertEqual(unpreviewed_review.status_code, 200)
        unpreviewed_html = unpreviewed_review.get_data(as_text=True)
        self.assertIn("Neanes · ενσωματωμένη προβολή εργασίας", unpreviewed_html)
        self.assertIn('class="review-inline-player"', unpreviewed_html)
        self.assertNotIn("MusicXML</a>", unpreviewed_html)
        playback = client.get(
            f"{review_path}/playback",
            headers={**authorization, "X-Forwarded-Prefix": "/kihem"},
        )
        self.assertEqual(playback.status_code, 200)
        playback_html = playback.get_data(as_text=True)
        self.assertIn('/kihem/review/neanes/app/', playback_html)
        self.assertIn('/kihem/review/digital-scores/draft-score/asset/byzx', playback_html)
        self.assertIn("reclaimReaderWidth", playback_html)
        self.assertIn("useNeanesPageWidth", playback_html)
        self.assertIn("kihem-neanes-reader-mode", playback_html)
        self.assertEqual(client.get("/review/neanes/app/").status_code, 401)
        neanes_index = client.get("/review/neanes/app/", headers=authorization)
        self.assertEqual(neanes_index.status_code, 200)
        self.assertIn("Neanes", neanes_index.get_data(as_text=True))
        neanes_index.close()
        source = client.get(f"{review_path}/asset/source?position=0", headers=authorization)
        self.assertEqual(source.status_code, 200)
        self.assertEqual(source.data, b"source")
        source.close()
        ocr = client.get(f"{review_path}/asset/ocr", headers=authorization)
        self.assertEqual(ocr.status_code, 200)
        self.assertEqual(ocr.mimetype, "application/yaml")
        ocr.close()
        saved = client.post(
            review_path,
            headers=authorization,
            data={"reviewer": "Δοκιμαστικός ψάλτης", "lyrics": "1", "notes": "Πρώτη σημείωση."},
        )
        self.assertEqual(saved.status_code, 200)
        self.assertIn("αποθηκεύτηκε", saved.get_data(as_text=True))
        note = json.loads((Path(self.temporary.name) / "review-notes" / "draft-score.json").read_text(encoding="utf-8"))
        self.assertTrue(note["checks"]["lyrics"])
        self.assertFalse(note["checks"]["neumes"])

    def test_isokratis_audio_routes_only_serve_catalogued_mp3_files(self):
        ison = self.client.get("/isokratis/ison/60.mp3")
        self.assertEqual(ison.status_code, 200)
        self.assertEqual(ison.mimetype, "audio/mpeg")
        self.assertEqual(ison.data, b"test-ison")
        ison.close()

        prosomia = self.client.get("/isokratis/prosomia/1-ouraniwn.mp3")
        self.assertEqual(prosomia.status_code, 200)
        self.assertEqual(prosomia.mimetype, "audio/mpeg")
        self.assertEqual(prosomia.data, b"test-prosomia")
        prosomia.close()
        prosomia_m4a = self.client.get("/isokratis/prosomia/ηχος_πλ.β_θεος_κυριος.m4a")
        self.assertEqual(prosomia_m4a.status_code, 200)
        self.assertEqual(prosomia_m4a.mimetype, "audio/mp4")
        self.assertEqual(prosomia_m4a.data, b"test-prosomia-m4a")
        prosomia_m4a.close()

        self.assertEqual(self.client.get("/isokratis/prosomia/not-for-web.pdf").status_code, 404)
        self.assertEqual(self.client.get("/isokratis/prosomia/../isokratis/60.mp3").status_code, 404)

    def test_melodos_audio_route_serves_cache_and_rejects_other_origins(self):
        source = "https://melodos.com/akolouthies/mousika/litourgia/example.mp3"
        cache = self.app.extensions["kihem_melodos_audio_cache"]
        cache._cache_path(source).write_bytes(b"cached-melodos-audio")

        response = self.client.get("/melodos-audio", query_string={"url": source})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/mpeg")
        self.assertEqual(response.data, b"cached-melodos-audio")
        response.close()

        rejected = self.client.get(
            "/melodos-audio",
            query_string={"url": "https://example.invalid/akolouthies/mousika/a.mp3"},
        )
        self.assertEqual(rejected.status_code, 400)
