import unittest
from datetime import date, datetime, timezone
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
                    '<span class="ep">Δοκιμαστικό κείμενο</span><br>'
                    "Ἀγγελικαὶ Δυνάμεις, ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.<br>"
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
        (byz / "prosomia" / "1-example.mp3").write_bytes(b"test-prosomia")
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
        self.assertIn("Όρθρος", text)
        self.assertIn("Θεία Λειτουργία", text)  # separate-page navigation
        self.assertIn('class="service-switch-link active" href="?date=2026-09-13&amp;services=orthros"', text)
        self.assertIn('class="service-switch-link " href="?date=2026-09-13&amp;services=litourgia"', text)
        self.assertIn("Δοκιμαστικός τίτλος Μελωδού", text)
        self.assertIn("Ήχος εβδομάδος πλ β΄.", text)
        self.assertNotIn("τοποθετήθηκαν κάτω από τα αντίστοιχα μέλη", text)
        self.assertIn("music/ioannis-protopsaltis-1905/tone6-apolytikion/1.png", text)
        self.assertIn('class="music-bookmarks-menu"', text)
        self.assertIn('href="#music-tone6-apolytikion-1"', text)
        self.assertNotIn('href="#music-tone6-apolytikion-2"', text)
        self.assertIn("link.closest('.music-bookmarks-menu').open = false", text)
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
        self.assertIn("1-example", text)
        self.assertIn('data-ison-url-template="isokratis/ison/__number__.mp3"', text)
        self.assertIn('value="isokratis/prosomia/1-example.mp3"', text)
        self.assertNotIn("not-for-web.pdf", text)

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

    def test_unconfigured_default_date_is_today_and_orthros(self):
        self.app.config["DEFAULT_DATE"] = None
        response = self.client.get("/")
        text = response.get_data(as_text=True)
        self.assertIn(f'value="{date.today().isoformat()}"', text)
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

    def test_isokratis_audio_routes_only_serve_catalogued_mp3_files(self):
        ison = self.client.get("/isokratis/ison/60.mp3")
        self.assertEqual(ison.status_code, 200)
        self.assertEqual(ison.mimetype, "audio/mpeg")
        self.assertEqual(ison.data, b"test-ison")
        ison.close()

        prosomia = self.client.get("/isokratis/prosomia/1-example.mp3")
        self.assertEqual(prosomia.status_code, 200)
        self.assertEqual(prosomia.mimetype, "audio/mpeg")
        self.assertEqual(prosomia.data, b"test-prosomia")
        prosomia.close()

        self.assertEqual(self.client.get("/isokratis/prosomia/not-for-web.pdf").status_code, 404)
        self.assertEqual(self.client.get("/isokratis/prosomia/../isokratis/60.mp3").status_code, 404)
