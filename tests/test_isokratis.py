import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.isokratis import IsokratisLibrary


class IsokratisLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "isokratis").mkdir()
        (self.root / "prosomia").mkdir()
        (self.root / "isokratis" / "60.mp3").write_bytes(b"ison")
        (self.root / "isokratis" / "chant.mp3").write_bytes(b"not a numbered ison")
        (self.root / "prosomia" / "6-chant.mp3").write_bytes(b"mode six")
        (self.root / "prosomia" / "1-1.mp3").write_bytes(b"hidden setup recording")
        (self.root / "prosomia" / "2-stauros.mp3").write_bytes(b"hidden second tone recording")
        (self.root / "prosomia" / "2-poiois.mp3").write_bytes(b"another hidden second tone recording")
        (self.root / "prosomia" / "2-γυναίκες-ακουτίσθητε.mp3").write_bytes(b"hidden Greek second tone recording")
        (self.root / "prosomia" / "liturgy.mp3").write_bytes(b"other")
        (self.root / "prosomia" / "book.pdf").write_bytes(b"excluded")
        self.library = IsokratisLibrary(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_indexes_only_direct_mp3_media(self):
        self.assertEqual(self.library.ison_numbers, frozenset({60}))
        self.assertEqual(
            [(mode, len(tracks)) for mode, tracks in self.library.prosomia_by_mode()],
            [("6", 1), ("other", 1)],
        )
        self.assertIsNone(self.library.prosomia_path("1-1.mp3"))
        self.assertIsNone(self.library.prosomia_path("2-stauros.mp3"))
        self.assertIsNone(self.library.prosomia_path("2-poiois.mp3"))
        self.assertIsNone(self.library.prosomia_path("2-γυναίκες-ακουτίσθητε.mp3"))

    def test_catalog_membership_prevents_arbitrary_paths(self):
        self.assertEqual(self.library.ison_path(60), self.root / "isokratis" / "60.mp3")
        self.assertIsNone(self.library.ison_path(61))
        self.assertEqual(
            self.library.prosomia_path("6-chant.mp3"), self.root / "prosomia" / "6-chant.mp3"
        )
        self.assertIsNone(self.library.prosomia_path("book.pdf"))
        self.assertIsNone(self.library.prosomia_path("../isokratis/60.mp3"))
