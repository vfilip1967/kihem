"""Safe cataloguing for the local Isokratis and prosomia audio collection.

The old Android app addressed drone files by number and loaded recordings by
filename.  This module keeps that convention, but only serves files that are
present in the two explicitly configured media directories.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata


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

# Ison marks written in a digital score (Neanes ``Ison.*`` values) map to the
# same numbered MP3 files as the manual note buttons, at register 0 and
# semitone 0.  ``Ison.Unison`` is not a pitch: it keeps the current drone.
# Unknown marks are ignored.  Kept here so the mapping is tested together with
# the media catalogue instead of being duplicated in the browser.
ISON_MARK_NUMBERS: dict[str, int] = {
    "Ison.Pa": 102,
    "Ison.Ni": 90,
    "Ison.Zo": 82,
    "Ison.Vou": 112,
    "Ison.Ga": 120,
    "Ison.Thi": 132,
    "Ison.Ke": 144,
    "Ison.KeLow": 72,
    "Ison.ThiLow": 60,
}
ISON_UNISON = "Ison.Unison"

# Chosen default ison for a score that carries no ison marks.  This is an
# editorial default, not a rule encoded by Neanes (which has no mode->ison
# table).  The main note of each mode is consistent in the sources summarised
# in the local ison research: byzantinechant.org's *Reading Psalmodia*
# (Melling), analogion.com's *Isokratema*, *IsonSecondMode*,
# *EnharmonicPlagalFirstMode* and *Barys*, and kelfar.net's *byzmusic.pdf*.
# This table is the fallback when ``src/data/ison_genus.json`` has no genus
# for a score; ``default_ison_for`` refines the ambiguous modes from it:
#   * mode 2 uses the soft-chromatic base Δι and the hard-chromatic Πα;
#   * mode 6 (πλ. β΄) uses the soft-chromatic Δι and the hard-chromatic Πα;
#   * mode 7 uses the enharmonic Γα and the diatonic Ζω;
#   * mode 8 (πλ. δ΄) uses Νη unless the piece is «ἐκ τοῦ Γα».
# The optional plurals (πλ. α΄/δ΄) keep the same basis as their modes.
MODE_DEFAULT_ISON: dict[str, str] = {
    "1": "Ison.Pa",
    "2": "Ison.Thi",
    "3": "Ison.Ga",
    "4": "Ison.Vou",
    "5": "Ison.Pa",
    "6": "Ison.Pa",
    "7": "Ison.Ga",
    "8": "Ison.Ni",
}

# Modes whose automatic ison may follow a melody segment whose median written
# note is above Δι.  Checked against the 22 real-marked papline scores
# (5109 notes): the «segment mostly above Δι -> Ison.Thi» rule raised
# agreement with the PDF's real isons in mode 4 (0.15->0.44, 0.19->0.52) and
# πλ. δ΄ (0.17->0.22, 0.20->0.41), but lowered it in πλ. α΄ (0.83->0.61,
# 0.69->0.58) and πλ. β΄ (0.66->0.51), where the real ison stays on Πα in
# high segments.  Modes 1, 2, 3, 5, 6 and 7 therefore keep the plain
# mode/genus default for the whole piece (a single mark at the first note).
DI_RULE_MODES: tuple[str, ...] = ("4", "8")

# Genus labels recorded beside a score's opening martyria in
# ``src/data/ison_genus.json``.
ISON_GENUS_VALUES: frozenset[str] = frozenset(
    {"diatonic", "soft-chromatic", "hard-chromatic", "enharmonic", "unknown"}
)

_NUMERAL_MODES = {"α": "1", "β": "2", "γ": "3", "δ": "4"}
_PLAGAL_MODES = {"α": "5", "β": "6", "δ": "8"}


def _without_accents(value: str) -> str:
    text = unicodedata.normalize("NFD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.lower().replace("ς", "σ")


def _is_ek_tou_ga(label: str | None) -> bool:
    """True when a tone label says the piece is «ἐκ τοῦ Γα».

    Accents, punctuation, spacing and the Latin spelling ``Ga`` are tolerated.
    """

    if not isinstance(label, str):
        return False
    text = _without_accents(label)
    text = re.sub(r"[\u0384\u00b4'’.,()/·\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return bool(re.search(r"εκ\s*του\s*(?:γα|ga)(?![α-ωa-z])", text))


def _start_is_ga(start: str | None) -> bool:
    if not isinstance(start, str):
        return False
    return _without_accents(start).strip() in {"ga", "γα"}


def mode_key_from_tone_label(label: str | None) -> str | None:
    """Return the eight-mode catalogue key for a Greek ``tone_label``.

    Examples such as ``Ἦχος δ΄ · Vou · διατονικός``, ``Ἦχος πλ.δ΄ · Ni``,
    ``Ἦχος πλ. α΄``, ``Ἦχος βαρύς · Γα`` and ``Ἦχος β΄ · Δι`` are recognised.
    Plagal labels are checked before the plain tones.  Accents, the Greek
    keraia and spacing are tolerated; an unknown or mode-less label yields
    ``None`` rather than a guess.
    """

    if not isinstance(label, str):
        return None
    text = unicodedata.normalize("NFD", label)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower().replace("ς", "σ")
    text = re.sub(r"[\u0384\u00b4'’.,()/·\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if "βαρυ" in text:
        return "7"
    plagal = re.search(r"πλ\s*([αβγδ])", text)
    if plagal:
        return _PLAGAL_MODES.get(plagal.group(1))
    plain = re.search(r"ηχοσ\s*([αβγδ])", text)
    if plain:
        return _NUMERAL_MODES.get(plain.group(1))
    return None


def default_ison_for(
    mode_key: str | None,
    genus: str | None,
    tone_label: str | None,
    start: str | None,
) -> str | None:
    """Return the editorial automatic ison for one digital score.

    ``mode_key`` comes from :func:`mode_key_from_tone_label`; ``genus`` and
    ``start`` come from ``src/data/ison_genus.json`` when the catalogue has
    them.  Modes 1/3/4/5 keep their fixed basis.  The ambiguous modes use the
    genus of the piece:

    * β΄ and πλ. β΄: hard-chromatic → Πα, soft-chromatic → Δι;
    * βαρύς: enharmonic → Γα, diatonic → Ζω;
    * πλ. δ΄: Νη, unless the label says «ἐκ τοῦ Γα» or the start is Γα.

    Without usable genus information the old mode defaults apply.  An unknown
    or mode-less score yields ``None`` rather than a guess.
    """

    if mode_key not in MODE_DEFAULT_ISON:
        return None
    genus_key = genus.strip().lower() if isinstance(genus, str) else None
    if mode_key in {"2", "6"}:
        if genus_key == "hard-chromatic":
            return "Ison.Pa"
        if genus_key == "soft-chromatic":
            return "Ison.Thi"
        return MODE_DEFAULT_ISON[mode_key]
    if mode_key == "7":
        if genus_key == "diatonic":
            return "Ison.Zo"
        return "Ison.Ga"
    if mode_key == "8":
        if _start_is_ga(start) or _is_ek_tou_ga(tone_label):
            return "Ison.Ga"
        return "Ison.Ni"
    return MODE_DEFAULT_ISON[mode_key]


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
