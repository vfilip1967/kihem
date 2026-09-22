"""Safe cataloguing for the local Isokratis and prosomia audio collection.

The old Android app addressed drone files by number and loaded recordings by
filename.  This module keeps that convention, but only serves files that are
present in the two explicitly configured media directories.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ISON_NOTES: tuple[dict[str, int | str], ...] = (
    {"label": "Δη", "base": 60},
    {"label": "Κε", "base": 72},
    {"label": "Ζω β", "base": 77},
    {"label": "Ζω", "base": 82},
    {"label": "Νη", "base": 90},
    {"label": "Πα", "base": 102},
    {"label": "Βου", "base": 112},
    {"label": "Γα", "base": 120},
    {"label": "Γα♯", "base": 126},
    {"label": "Δι", "base": 132},
    {"label": "Και", "base": 144},
)

MODE_LABELS = {
    "1": "Α΄ ήχος",
    "2": "Β΄ ήχος",
    "3": "Γ΄ ήχος",
    "4": "Δ΄ ήχος",
    "5": "Πλ. α΄",
    "6": "Πλ. β΄",
    "7": "Βαρύς",
    "8": "Πλ. δ΄",
    "other": "Λοιπά μέλη",
}
MODE_ORDER = tuple(MODE_LABELS)
_NUMBERED_FILE = re.compile(r"^(\d+)\.mp3$", re.IGNORECASE)

# The VLC export is the curated source for the public prosomia menus.  Keep
# exact filenames here rather than exposing every uploaded MP3: uploads also
# contain old numbered trials and duplicate takes.  The listed order is the
# playlist order, and its first track is the automatic selection for a tone.
_PROSOMIA_CATALOG: tuple[tuple[str, str, str], ...] = (
    ("1", "Οὐρανίων ταγμάτων", "1-ouraniwn.mp3"),
    ("1", "Τοῦ λίθου σφραγισθέντος", "1-lithos.mp3"),
    ("1", "Πανεύθυμοι μάρτυρες", "1-paneythymoi.mp3"),
    ("1", "Ὢ παραδόξου", "1-w-paradoksou.mp3"),
    ("1", "Τὸν τάφον σου Σωτήρ", "1-tafon-sou-swtir.mp3"),
    ("2", "Γυναίκες ἀκουτίσθητε", "2-γυναίκες-ακουτίσθητε-s.mp3"),
    ("2", "Τῶν μαθητῶν ὁρώντων", "2-των-μαθητών-ορώντων-s.mp3"),
    ("2", "Τὰ ἄνω ζητῶν", "2-τα άνω ζητών τοις κάτω συναπτόμενος.mp3"),
    ("2", "Σταυρὸς ὁ φύλαξ", "2-stauros-1.mp3"),
    ("2", "Ποίοις εὐφημιῶν στέμμασι", "2-poiois-1.mp3"),
    ("2", "Τοῖς μαθηταῖς συνέλθωμεν", "2-τοίς-μαθητές-συνέλθωμεν.mp3"),
    ("2", "Μαθητῶν ὁρώντων", "2-των-μαθητών-ορώντων.mp3"),
    ("2", "Ὅτε κατῆλθες", "2-ote-katil8es.mp3"),
    ("2", "Γυναίκες ἀκουτίσθητε · β΄ ἐκτέλεση", "2-γυναικες ακουτίσθητε φωνής αγαλλιασεως.mp3"),
    ("2", "Οἶκος τοῦ Εὐφραθᾶ", "2-οίκος-ευφραθά.mp3"),
    ("2", "Ὅτε ἐκ τοῦ ξύλου σε νεκρόν", "2ote-1.mp3"),
    ("2", "Τοῖς μαθηταῖς συνέλθωμεν · β΄ ἐκτέλεση", "2-τοίς-μαθητές-συνέλθωμεν-s.mp3"),
    ("3", "Θείας πίστεως ομολογία", "3-θείας-πίστεως-ομολογία.mp3"),
    ("3", "Την ωραιότητα της παρθενίας", "3-την-ωραιότητα-της-παρθενίας.mp3"),
    ("3", "Η Παρθένος σήμερον", "3-η παρθένος σήμερον.mp3"),
    ("3", "Απόστολοι εκ περάτων", "3-απόστολοι εκ περάτων.mp3"),
    ("3", "Εν πνεύματι τω ιερώ", "3-εν πνεύματι τώ ιερώ.mp3"),
    ("3", "Επεσκέψατο υμάς εξ ύψους", "3-επεσκέψατο υμάς εξ ύψους.mp3"),
    ("3", "Ευφρενέσθω τα ουράνια", "3-ευφρενέσθω τα ουράνια.mp3"),
    ("3", "Ο ουρανών τοις άστροις", "3-ο ουρανών τοις άστροις.mp3"),
    ("3", "Τον ληστήν αυθημερόν", "3-τον ληστήν αυθημερόν.mp3"),
    ("3", "Τον νυμφώνα σου βλέπω", "3-τον νυμφώνα σου βλέπω.mp3"),
    ("4", "Ως γενναίον εν μάρτυσιν", "4-ως γενναίο εν μάρτυσιν.mp3"),
    ("4", "Έδωκας σημείωσιν", "4-έδωκας σημείωσιν.mp3"),
    ("4", "Ήθελον δακρύσιν εξαλείψαι", "4-ήθελον δακρύσιν εξαλείψαι.mp3"),
    ("4", "Ο εξ υψίστου κληθείς", "4-ο εξ υψίστου κληθείς ουκ υπ ανθρώπων.mp3"),
    ("4", "Ο υψωθείς εν τω σταυρώ", "4-ο υψωθείς εν τω σταυρώ εκουσίως.mp3"),
    ("4", "Κατεπλάγη Ιωσήφ", "4-κατεπλαγη ιωσηφ.mp3"),
    ("4", "Ταχύ προκατάλαβε", "4-ταχύ προκατάλαβε.mp3"),
    ("4", "Επεφάνης σήμερον", "4-επεφάνης σήμερον.mp3"),
    ("4", "Το φαιδρόν της Αναστάσεως", "4-το φαιδρόν της Αναστάσεως.mp3"),
    ("4", "Ανοίξω το στόμα μου", "4-ανοίξω το στόμα μου.m4a"),
    ("4", "Τους σους υμνολόγους Θεοτόκε", "4-τους σους υμνολόγους Θεοτόκε.m4a"),
    ("5", "Χαίρεις ασκητικών αληθώς", "5-χαίρεις ασκητικών αληθώς.mp3"),
    ("5", "Τον συνάναρχον Λόγον Πατρί", "5-τον συνάναρχον λόγον πατρί.mp3"),
    ("5", "Κανόνες πλ. Α΄ και Τελώνου–Φαρισαίου", "5-κανόνες πλ. Α και Τελώνου Φαρισαίου.m4a"),
    ("6", "Θεός Κύριος–Καθίσματα", "ηχος_πλ.β_θεος_κυριος.m4a"),
    ("6", "Αγγελικαί Δυνάμεις", "6-αγγελικαί δυνάμεις .mp3"),
    ("6", "Όλην αποθέμενοι εν ουρανοίς", "6-ολην αποθέμενοι εν ουρανοίς.mp3"),
    ("6", "Τριήμερος ανέστης Χριστέ", "6-τριήμερος Ανέστης Χριστέ.mp3"),
    ("6", "Αναβαθμοί πλ. β΄", "6-αναβαθμοί πλ β.mp3"),
    ("7", "Αναβαθμοί βαρέως ήχου (Θρασύβουλος Στανίτσας)", "7-αναβαθμοί-βαρέως.m4a"),
    ("7", "Κατέλυσας τω Σταυρώ σου τον θάνατο", "7-κατέλυσας τω Σταυρώ Σου τον θάνατο.mp3"),
    ("8", "Ο εν Εδέμ παράδεισος", "8-ο εν Εδέμ παράδεισος .mp3"),
    ("8", "Τι υμάς καλέσωμεν άγιοι", "8-3-τι υμάς καλέσωμεν αγιοι.mp3"),
    ("8", "Εξ ύψους κατήλθες ο εύσπλαγχνος", "8-εξ ύψους κατήλθες ο εύσπλαχνος.mp3"),
    ("8", "Το προσταχθέν μυστικώς λαβών", "8-το προσταχθέν μυστικώς λαβών εν γνώσει.mp3"),
    ("8", "Την σοφίαν και λόγον εν ση γαστρί", "8-την σοφίαν και λόγον .mp3"),
    ("8", "Ω του παραδόξου θαύματος", "8-3-ω του παραδόξου θαύματος.mp3"),
)


@dataclass(frozen=True)
class ProsomiaTrack:
    """One known recording, represented by its direct filename only."""

    filename: str
    label: str
    mode: str


class IsokratisLibrary:
    """Read-only index of the ison MP3 and curated prosomia audio folders."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self._ison_numbers = self._read_ison_numbers()
        self._prosomia_tracks = self._read_prosomia_tracks()
        self._prosomia_names = {track.filename for track in self._prosomia_tracks}

    def _files(self, directory: str) -> tuple[Path, ...]:
        folder = self.root / directory
        if not folder.is_dir():
            return ()
        return tuple(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".mp3")

    def _read_ison_numbers(self) -> frozenset[int]:
        values = set()
        for path in self._files("isokratis"):
            match = _NUMBERED_FILE.fullmatch(path.name)
            if match:
                values.add(int(match.group(1)))
        return frozenset(values)

    def _read_prosomia_tracks(self) -> tuple[ProsomiaTrack, ...]:
        folder = self.root / "prosomia"
        return tuple(
            ProsomiaTrack(filename, label, mode)
            for mode, label, filename in _PROSOMIA_CATALOG
            if (folder / filename).is_file()
        )

    @property
    def ison_numbers(self) -> frozenset[int]:
        return self._ison_numbers

    @property
    def prosomia_tracks(self) -> tuple[ProsomiaTrack, ...]:
        return self._prosomia_tracks

    def prosomia_by_mode(self) -> tuple[tuple[str, tuple[ProsomiaTrack, ...]], ...]:
        return tuple(
            (mode, tuple(track for track in self._prosomia_tracks if track.mode == mode))
            for mode in MODE_ORDER
            if any(track.mode == mode for track in self._prosomia_tracks)
        )

    def ison_path(self, number: int) -> Path | None:
        if number not in self._ison_numbers:
            return None
        return self.root / "isokratis" / f"{number}.mp3"

    def prosomia_path(self, filename: str) -> Path | None:
        # Membership in the catalog also rejects traversal, nested paths and
        # non-curated media such as the PDFs deliberately excluded from this UI.
        if filename not in self._prosomia_names:
            return None
        return self.root / "prosomia" / filename
