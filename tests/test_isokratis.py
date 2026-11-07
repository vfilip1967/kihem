import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.isokratis import (
    ISON_MARK_NUMBERS,
    ISON_NOTES,
    MODE_DEFAULT_ISON,
    IsokratisLibrary,
    mode_key_from_tone_label,
)


class IsokratisLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "isokratis").mkdir()
        (self.root / "prosomia").mkdir()
        (self.root / "isokratis" / "60.mp3").write_bytes(b"ison")
        (self.root / "isokratis" / "chant.mp3").write_bytes(b"not a numbered ison")
        (self.root / "prosomia" / "6-αγγελικαί δυνάμεις .mp3").write_bytes(b"mode six")
        (self.root / "prosomia" / "ηχος_πλ.β_θεος_κυριος.m4a").write_bytes(b"mode six m4a")
        (self.root / "prosomia" / "1-1.mp3").write_bytes(b"hidden setup recording")
        (self.root / "prosomia" / "2-stauros.mp3").write_bytes(b"unlisted duplicate recording")
        (self.root / "prosomia" / "liturgy.mp3").write_bytes(b"other")
        (self.root / "prosomia" / "book.pdf").write_bytes(b"excluded")
        self.library = IsokratisLibrary(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_indexes_only_direct_mp3_media(self):
        self.assertEqual(self.library.ison_numbers, frozenset({60}))
        self.assertEqual(
            [(mode, len(tracks)) for mode, tracks in self.library.prosomia_by_mode()],
            [("6", 2)],
        )
        self.assertIsNone(self.library.prosomia_path("1-1.mp3"))
        self.assertIsNone(self.library.prosomia_path("2-stauros.mp3"))
        self.assertIsNone(self.library.prosomia_path("liturgy.mp3"))

    def test_catalog_membership_prevents_arbitrary_paths(self):
        self.assertEqual(self.library.ison_path(60), self.root / "isokratis" / "60.mp3")
        self.assertIsNone(self.library.ison_path(61))
        self.assertEqual(
            self.library.prosomia_path("6-αγγελικαί δυνάμεις .mp3"),
            self.root / "prosomia" / "6-αγγελικαί δυνάμεις .mp3",
        )
        self.assertEqual(
            self.library.prosomia_path("ηχος_πλ.β_θεος_κυριος.m4a"),
            self.root / "prosomia" / "ηχος_πλ.β_θεος_κυριος.m4a",
        )
        self.assertIsNone(self.library.prosomia_path("book.pdf"))
        self.assertIsNone(self.library.prosomia_path("../isokratis/60.mp3"))


class ModeDefaultIsonTests(unittest.TestCase):
    def test_default_ison_table_covers_all_eight_modes(self):
        self.assertEqual(
            MODE_DEFAULT_ISON,
            {
                "1": "Ison.Pa",
                "2": "Ison.Thi",
                "3": "Ison.Ga",
                "4": "Ison.Vou",
                "5": "Ison.Pa",
                "6": "Ison.Pa",
                "7": "Ison.Ga",
                "8": "Ison.Ni",
            },
        )

    def test_tone_labels_are_parsed_including_plagal_and_barys(self):
        cases = {
            "Ἦχος α΄": "1",
            "Ἦχος β΄": "2",
            "Ἦχος γ΄": "3",
            "Ἦχος δ΄": "4",
            "Ἦχος πλ. α΄": "5",
            "Ἦχος πλ.β΄": "6",
            "Ἦχος βαρύς": "7",
            "Ἦχος πλ. δ΄": "8",
            "Ἦχος δ΄ · Vou · διατονικός": "4",
            "Ἦχος πλ.δ΄ · Ni · Diatonic": "8",
            "Ἦχος πλ. α΄ · Πα · διατονικός": "5",
            "Ἦχος βαρύς · Γα · διατονικός": "7",
            "Ἦχος β΄ · Δι · μαλακό χρωματικό": "2",
            "Ἦχος πλ. δ΄ (ἐκ τοῦ Γα) · Γα · διατονικός": "8",
            "Βαρύς · Γα · διατονικός": "7",
        }
        for label, expected in cases.items():
            with self.subTest(label=label):
                self.assertEqual(mode_key_from_tone_label(label), expected)
        self.assertIsNone(mode_key_from_tone_label("Δεν δηλώνεται μαρτυρία/ήχος στην απομονωμένη φόρμουλα"))
        self.assertIsNone(mode_key_from_tone_label(""))
        self.assertIsNone(mode_key_from_tone_label(None))


class IsonMarkMappingTests(unittest.TestCase):
    def test_mark_numbers_use_the_ison_bases_at_register_and_semitone_zero(self):
        bases = {note["label"]: note["base"] for note in ISON_NOTES}
        self.assertEqual(
            ISON_MARK_NUMBERS,
            {
                "Ison.Pa": bases["Πα"],
                "Ison.Ni": bases["Νη"],
                "Ison.Zo": bases["Ζω"],
                "Ison.Vou": bases["Βου"],
                "Ison.Ga": bases["Γα"],
                "Ison.Thi": bases["Δι"],
                "Ison.Ke": bases["Και"],
                "Ison.KeLow": bases["Κε"],
                "Ison.ThiLow": bases["Δη"],
            },
        )

    def test_every_mark_number_exists_in_the_installed_media_library(self):
        byz = Path(__file__).resolve().parents[1] / "byz"
        if not (byz / "isokratis").is_dir():
            self.skipTest("ison media library is not installed")
        library = IsokratisLibrary(byz)
        missing = {
            name: number
            for name, number in ISON_MARK_NUMBERS.items()
            if number not in library.ison_numbers
        }
        self.assertEqual(missing, {})
