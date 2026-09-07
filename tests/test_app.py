import unittest
from datetime import datetime, timezone
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
            )
            for service in services
        )
        return ComposedService(selected_date=selected_date, documents=documents, tone=6)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.app = create_app(
            {"TESTING": True, "CACHE_DIR": self.temporary.name, "COMPOSER": FakeComposer()}
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temporary.cleanup()

    def test_index_renders_both_services_and_music_links(self):
        response = self.client.get("/?date=2026-09-13&services=both")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("Όρθρος", text)
        self.assertIn("Θεία Λειτουργία", text)
        self.assertIn("2 μουσικές ενθέσεις", text)
        self.assertIn("music/ioannis-protopsaltis-1905/tone6-apolytikion/1.png", text)
        self.assertIn('class="music-bookmarks-menu"', text)
        self.assertIn('href="#music-tone6-apolytikion-1"', text)
        self.assertIn('href="#music-tone6-apolytikion-2"', text)
        self.assertIn("link.closest('.music-bookmarks-menu').open = false", text)
        self.assertNotIn("Μουσικό παράρτημα", text)

    def test_default_date_is_initial_pilot_date(self):
        response = self.client.get("/")
        self.assertIn('value="2026-09-13"', response.get_data(as_text=True))

    def test_index_composes_non_sunday_instead_of_rejecting_it(self):
        response = self.client.get("/?date=2026-09-14")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("Δευτέρα 14 Σεπτεμβρίου 2026", text)
        self.assertIn("2 μουσικές ενθέσεις", text)
        self.assertNotIn("Η επόμενη Κυριακή", text)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.json["calendar"], "gregorian")
