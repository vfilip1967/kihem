from __future__ import annotations

import html
import json
import logging
import os
import threading
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from collections.abc import Collection
from typing import TYPE_CHECKING, Final, Literal

import pymupdf
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

if TYPE_CHECKING:
    from src.typesafe_decisions import TypesafeDecisionService


logger = logging.getLogger(__name__)


BOOK_ID: Final = "ioannis-protopsaltis-1905"
BOOK_TITLE: Final = "Ἀναστασιματάριον Ἰωάννου Πρωτοψάλτου"
BOOK_DETAILS: Final = "Ἀναστασιματάριον νέον ἀργὸν καὶ σύντομον · Κωνσταντινούπολη 1905"
SOURCE_PAGE: Final = "https://repository.mmb.org.gr/en/digma/handle/123456789/5477/"
DOWNLOAD_URL: Final = (
    "https://www.pdf-archive.com/2015/03/23/"
    "anastasimatarion-ioannou-protopsaltou-1905/"
    "anastasimatarion-ioannou-protopsaltou-1905.pdf"
)
PANDEKTI_BOOK_ID: Final = "pandekti-orthrou-1851"
IRMOLOGION_BOOK_ID: Final = "ioannis-protopsaltis-eirmologion-1903"
PANDEKTI_LITOURGIA_BOOK_ID: Final = "pandekti-litourgia-1851"
KYPSELI_BOOK_ID: Final = "kypseli-stefanou-lampadariou-minaia"
KOINONIKA_ALL_TONES_BOOK_ID: Final = "eis-mnimosynon-all-tones"
PLIROTHITO_BOOK_ID: Final = "melodos-plirothito-2023"
YPEREULOGIMENI_BOOK_ID: Final = "ypereulogimeni-tone2-pemptousia"
# The Menaia are date-indexed source material. A page from a neighbouring
# feast must never be used as a fallback for the selected date.
DATE_SCOPED_BOOK_IDS: Final[frozenset[str]] = frozenset({KYPSELI_BOOK_ID})


@dataclass(frozen=True)
class MusicBook:
    book_id: str
    title: str
    details: str
    source_page: str
    local_filename: str
    minimum_pdf_pages: int
    attribution: str
    download_url: str | None = None


BOOKS: Final[dict[str, MusicBook]] = {
    BOOK_ID: MusicBook(
        BOOK_ID,
        BOOK_TITLE,
        BOOK_DETAILS,
        SOURCE_PAGE,
        "anastasimatarion-ioannou-protopsaltou-1905.pdf",
        600,
        "Μουσική Βιβλιοθήκη «Λίλιαν Βουδούρη» · CC BY-NC",
        DOWNLOAD_URL,
    ),
    PANDEKTI_BOOK_ID: MusicBook(
        PANDEKTI_BOOK_ID,
        "Μουσικὴ Πανδέκτη · Τόμος Β΄",
        "Πανδέκτη τῆς Ἱερᾶς Ἐκκλησιαστικῆς Ὑμνῳδίας · Μαθήματα τοῦ Ὄρθρου · 1851",
        "https://anemi.lib.uoc.gr/metadata/b/8/4/metadata-06-0000088.tkl",
        "pandekti-tomos-b-1851-pages-490-494.pdf",
        5,
        "Ψηφιακή Βιβλιοθήκη «Ανέμη» · Πανεπιστήμιο Κρήτης",
    ),
    IRMOLOGION_BOOK_ID: MusicBook(
        IRMOLOGION_BOOK_ID,
        "Εἱρμολόγιον Καταβασιῶν Ἰωάννου Πρωτοψάλτου",
        "Εἱρμολόγιον Καταβασιῶν τοῦ ὅλου ἐνιαυτοῦ, ἀργὸν τε καὶ σύντομον · Κωνσταντινούπολη 1903",
        "https://repository.mmb.org.gr/digma/handle/123456789/5481/",
        "eirmologion-katavasion-ioannou-protopsaltou-1903.pdf",
        500,
        "Μουσική Βιβλιοθήκη «Λίλιαν Βουδούρη» · CC BY-NC",
        "https://backend.mmb.org.gr/files/original/1103/5481/Eirmologion_Katavasion_No1_Byzantine.pdf",
    ),
    PANDEKTI_LITOURGIA_BOOK_ID: MusicBook(
        PANDEKTI_LITOURGIA_BOOK_ID,
        "Μουσικὴ Πανδέκτη · Δ΄ Τόμος Θείας Λειτουργίας",
        "Ἔκδοσις «Ζωή» · Θεία Λειτουργία · ἐπιλεγμένα μέλη σε ἦχο δ΄ ἅγια",
        "https://melodos.com/bibliothiki/?cat=157",
        "pandekti-tomos-d-liturgy.pdf",
        552,
        "Μελωδός · ψηφιοποιημένος Μουσικὸς Πανδέκτης Δ΄",
        "https://melodos.com/bibliothiki/wp-content/uploads/2019/09/04-%CE%9C%CE%9F%CE%A5%CE%A3%CE%99%CE%9A%CE%9F%CE%A3-%CE%A0%CE%91%CE%9D%CE%94%CE%95%CE%9A%CE%A4%CE%97%CE%A3-%CE%94%CE%84-%CE%A4%CE%9F%CE%9C%CE%9F%CE%A3-%CE%BC%CE%B5-%CE%A3%CE%B5%CE%BB-.pdf",
    ),
    KYPSELI_BOOK_ID: MusicBook(
        KYPSELI_BOOK_ID,
        "Μουσικὴ Κυψέλη Στεφάνου Λαμπαδαρίου · Μηναία",
        "Μηναία · ἰδιόμελα, δοξαστικά, ἀπολυτίκια καὶ κοντάκια τοῦ ὅλου ἐνιαυτοῦ",
        "https://melodos.com/bibliothiki/?cat=157",
        "kypseli-stefanou-lampadariou-minaia.pdf",
        1075,
        "Μελωδός · ψηφιοποιημένη Μουσικὴ Κυψέλη",
        "https://melodos.com/bibliothiki/wp-content/uploads/1622/02/Κυψέλη-Στεφάνου-Λαμπαδαρίου.-Μηναία.pdf",
    ),
    KOINONIKA_ALL_TONES_BOOK_ID: MusicBook(
        KOINONIKA_ALL_TONES_BOOK_ID,
        "Εἰς μνημόσυνον αἰώνιον · ἀνθολογία ὀκτὼ ἤχων",
        "Κοινωνικὸν «Εἰς μνημόσυνον αἰώνιον» · μουσικὰ κείμενα κατὰ ἦχον",
        "https://psaltiri.gr/index2.php?fid=2661&no_html=1&option=com_sobi2&sobi2Task=dd_download",
        "eis-mnimosynon-all-tones.pdf",
        104,
        "Ψαλτήρι · ψηφιοποίηση 10uk15",
        "https://psaltiri.gr/index2.php?fid=2661&no_html=1&option=com_sobi2&sobi2Task=dd_download",
    ),
    PLIROTHITO_BOOK_ID: MusicBook(
        PLIROTHITO_BOOK_ID,
        "Πληρωθήτω τὸ στόμα ἡμῶν · ἦχος δ΄",
        "Θεοφάνεια 2023 · μουσικὸ παράρτημα Θείας Λειτουργίας",
        "https://melodos.com/bibliothiki/?cat=157",
        "melodos-theophany-2023-plirothito.pdf",
        121,
        "Μελωδός · ψηφιοποιημένο μουσικό τεκμήριο",
        "https://melodos.com/bibliothiki/wp-content/uploads/2018/01/06-01-2023-%CE%8C%CF%81%CE%B8%CF%81%CE%BF%CF%82-%CE%9C%CE%AD%CE%B3%CE%B1%CF%82-%CE%91%CE%B3%CE%B9%CE%B1%CF%83%CE%BC%CF%8C%CF%82.pdf",
    ),
    YPEREULOGIMENI_BOOK_ID: MusicBook(
        YPEREULOGIMENI_BOOK_ID,
        "Ὑπερευλογημένη · ἦχος β΄ · Πέτρου Λαμπαδαρίου",
        "Κυριακὴ β΄ Ματθαίου · μουσικὸ τεκμήριο τοῦ Ὑπερευλογημένη",
        "https://www.pemptousia.gr/",
        "ypereulogimeni-tone2-pemptousia.pdf",
        524,
        "Πεμπτουσία · μουσικὸ τεκμήριο ἤχου β΄",
        "https://www.pemptousia.gr/wp-content/uploads/2022/06/26062022-%CE%9A%CF%85%CF%81%CE%B9%CE%B1%CE%BA%CE%AE-%CE%B2-%CE%9C%CE%B1%CF%84%CE%B8%CE%B1%CE%AF%CE%BF%CF%85-%CE%AE%CF%87.%CE%B1-%CE%B5%CF%89%CE%B8.%CE%B2.pdf",
    ),
}


@dataclass(frozen=True)
class ScanRegion:
    """A verified region in the scan; PDF page numbers are one-based."""

    pdf_page: int
    printed_page: int
    clip: tuple[float, float, float, float] = (0.02, 0.02, 0.98, 0.98)


@dataclass(frozen=True)
class MusicPiece:
    piece_id: str
    title: str
    incipit: str
    regions: tuple[ScanRegion, ...]
    book_id: str = BOOK_ID


@dataclass(frozen=True)
class AttachmentRule:
    service: str
    after_text: str
    piece_id: str
    occurrences: Literal["first", "all"] = "first"
    required_text: tuple[str, ...] = ()
    required_text_any: tuple[str, ...] = ()
    # Every group must match; at least one variant inside a group is enough.
    # This is used by the katavasies rules, where a decorated initial letter
    # can split the first word (e.g. «Ἀ νοίξω»), so both the plain and the
    # first-letter-dropped forms are accepted.
    required_text_groups: tuple[tuple[str, ...], ...] = ()
    # Check required_text/required_text_groups only after the first occurrence
    # of one of these markers (e.g. the first «Καταβασίες» heading).  When the
    # marker is absent, the whole document is searched.
    required_after_any: tuple[str, ...] = ()
    excluded_text_any: tuple[str, ...] = ()
    weekdays: tuple[int, ...] = ()
    # The weekly tone is read from the returned Melodos document. It is never
    # derived from the calendar date.
    weekly_tone: int | None = None
    month_days: tuple[tuple[int, int], ...] = ()
    match_number: int = 1
    preceding_text: str | None = None
    nearest_preceding_text: str | None = None
    exact_after_text: str | None = None
    following_text: str | None = None
    # A local liturgical instruction can determine a score independently of
    # the weekly tone.  This is intentionally a semantic, bounded context
    # (not a document-wide phrase search): it must be resolved immediately
    # before the member that will receive the score.
    semantic_context: Literal["timiotera", "ainoi"] | None = None
    expected_context_tone: int | None = None
    # TypeSafe validates only a closed, already verified alternative.  It may
    # never choose a scan region which is not in this catalogue.
    expected_reviewer_choice: str | None = None
    insert_before: bool = False
    # A verified digital (Neanes) score from the catalogue instead of a scanned
    # piece: ``piece_id`` is then the catalogue id.  It is attached only when
    # the caller reports that score as verified, and ``digital_title`` is the
    # bookmark label.
    digital_title: str | None = None
    # A digital score normally replaces a scan attached to the same hymn text
    # (owner, 2026-10-30).  The Timiotera is the exception: the scan stays and
    # the digital score is shown in addition to it.
    replace_scan: bool = True


@dataclass(frozen=True)
class EnrichmentResult:
    html: str
    attachment_count: int
    unmatched_piece_ids: tuple[str, ...]
    bookmarks: tuple["MusicBookmark", ...]


@dataclass(frozen=True)
class MusicBookmark:
    """A navigable entry for one inserted musical excerpt."""

    anchor_id: str
    title: str


def _region(pdf_page: int, y0: float = 0.02, y1: float = 0.98) -> ScanRegion:
    return ScanRegion(pdf_page, pdf_page - 2, (0.02, y0, 0.98, y1))


# These are not generic guesses based only on the weekly tone. Each range was
# checked against the scan's printed headings and the incipit returned by
# Melodos for Sunday 13 September 2026.
PIECES: Final[dict[str, MusicPiece]] = {
    "tone6-apolytikion": MusicPiece(
        "tone6-apolytikion",
        "Ἀναστάσιμον Ἀπολυτίκιον, πλ. β΄",
        "Ἀγγελικαὶ Δυνάμεις",
        (_region(279, 0.35), _region(280, 0.02, 0.43)),
    ),
    "tone6-kathismata-a": MusicPiece(
        "tone6-kathismata-a",
        "Καθίσματα μετὰ τὴν α΄ Στιχολογίαν",
        "Τοῦ τάφου ἀνεωγμένου",
        (_region(280, 0.42), _region(281, 0.02, 0.58)),
    ),
    "tone6-kathismata-b": MusicPiece(
        "tone6-kathismata-b",
        "Καθίσματα μετὰ τὴν β΄ Στιχολογίαν",
        "Ἡ Ζωή, ἐν τῷ τάφῳ ἀνέκειτο",
        (_region(281, 0.78), _region(282, 0.02, 0.74)),
    ),
    "resurrectional-evlogitaria": MusicPiece(
        "resurrectional-evlogitaria",
        "Ἀναστάσιμα Εὐλογητάρια, πλ. α΄ · Πέτρου Λαμπαδαρίου",
        "Εὐλογητὸς εἶ, Κύριε, δίδαξόν με τὰ δικαιώματά σου",
        (
            _region(19, 0.22),
            _region(20),
            _region(21),
            _region(22, 0.02, 0.86),
        ),
    ),
    "tone6-anavathmoi": MusicPiece(
        "tone6-anavathmoi",
        "Οἱ Ἀναβαθμοί, πλ. β΄",
        "Ἐν τῷ οὐρανῷ τοὺς ὀφθαλμούς μου αἴρω",
        (_region(283, 0.15), _region(284), _region(285, 0.02, 0.24)),
    ),
    "tone4-anavathmoi-first-antiphon": MusicPiece(
        "tone4-anavathmoi-first-antiphon",
        "Ἀναβαθμοί · α΄ Ἀντίφωνον δ΄ ἤχου",
        "Ἐκ νεότητός μου πολλὰ πολεμεῖ με πάθη",
        (
            # The first antiphon begins in the lower half of p. 176 and
            # finishes just before the heading for the second antiphon on p. 177.
            _region(178, 0.46),
            _region(179, 0.02, 0.22),
        ),
    ),
    "tone6-canon-ode-1": MusicPiece(
        "tone6-canon-ode-1",
        "Ἀναστάσιμος Κανών · ᾨδὴ α΄",
        "Ὡς ἐν ἠπείρῳ πεζεύσας ὁ Ἰσραήλ",
        (_region(285, 0.42), _region(286, 0.02, 0.92)),
    ),
    "tone6-canon-ode-3": MusicPiece(
        "tone6-canon-ode-3",
        "Ἀναστάσιμος Κανών · ᾨδὴ γ΄",
        "Οὐκ ἔστιν ἅγιος ὡς σύ",
        (_region(286, 0.89), _region(287, 0.02, 0.92)),
    ),
    "plagal4-timiotera": MusicPiece(
        "plagal4-timiotera",
        "Ἡ Τιμιωτέρα, πλ. δ΄",
        "Τὴν Τιμιωτέραν τῶν Χερουβείμ",
        (_region(420, 0.50), _region(421, 0.02, 0.42)),
    ),
    "tone4-timiotera": MusicPiece(
        "tone4-timiotera",
        "Ἡ Τιμιωτέρα, δ΄ ἦχος",
        "Τὴν Τιμιωτέραν τῶν Χερουβείμ",
        # The title and opening are at the foot of printed p. 191; the
        # refrains end immediately before the ninth-ode Heirmos on p. 192.
        # The PDF has two unnumbered preliminary pages.
        (_region(193, 0.72), _region(194, 0.02, 0.47)),
    ),
    "tone2-ainoi": MusicPiece(
        "tone2-ainoi",
        "Αἶνοι · τὰ ὀκτὼ ἀναστάσιμα στιχηρά · ἦχος β΄ · μέλος ἀργόν",
        "Πᾶσα πνοὴ αἰνεσάτω τὸν Κύριον",
        (
            # Printed pp. 86–91: the Eothinon B΄ begins at the foot of p. 91.
            _region(88, 0.37),
            _region(89),
            _region(90),
            _region(91),
            _region(92),
            _region(93, 0.02, 0.77),
        ),
    ),
    "tone2-great-doxology": MusicPiece(
        "tone2-great-doxology",
        "Μεγάλη Δοξολογία, ἦχος β΄ · Μανουὴλ Πρωτοψάλτου",
        "Δόξα σοι τῷ δείξαντι τὸ φῶς",
        (
            # Printed pp. 93–97. «Ὁ Μακαρισμός» begins in the lower third
            # of printed p. 97 and is deliberately excluded.
            _region(95, 0.34),
            _region(96),
            _region(97),
            _region(98),
            _region(99, 0.02, 0.33),
        ),
    ),
    "tone3-ainoi": MusicPiece(
        "tone3-ainoi",
        "Αἶνοι · τὰ ὀκτὼ ἀναστάσιμα στιχηρά · ἦχος γ΄ · μέλος σύντομον",
        "Πᾶσα πνοὴ αἰνεσάτω τὸν Κύριον",
        (
            # Printed pp. 138–145: the Eothinon Γ΄ follows at the foot of p. 145.
            _region(140, 0.48),
            _region(141),
            _region(142),
            _region(143),
            _region(144),
            _region(145),
            _region(146),
            _region(147, 0.02, 0.55),
        ),
    ),
    "tone4-ainoi": MusicPiece(
        "tone4-ainoi",
        "Αἶνοι · τὰ ὀκτὼ ἀναστάσιμα στιχηρά · ἦχος δ΄ · μέλος σύντομον",
        "Πᾶσα πνοὴ αἰνεσάτω τὸν Κύριον",
        (
            # Printed pp. 193–198: the Eothinon Δ΄ begins at the foot of p. 198.
            _region(195),
            _region(196),
            _region(197),
            _region(198),
            _region(199),
            _region(200, 0.02, 0.78),
        ),
    ),
    "tone5-ainoi": MusicPiece(
        "tone5-ainoi",
        "Αἶνοι · τὰ ὀκτὼ ἀναστάσιμα στιχηρά · ἦχος πλ. α΄ · μέλος ἀργόν",
        "Πᾶσα πνοὴ αἰνεσάτω τὸν Κύριον",
        (
            # Printed pp. 244–251: the Eothinon E΄ follows at the foot of p. 251.
            _region(246),
            _region(247),
            _region(248),
            _region(249),
            _region(250),
            _region(251),
            _region(252),
            _region(253, 0.02, 0.78),
        ),
    ),
    "tone6-ainoi": MusicPiece(
        "tone6-ainoi",
        "Αἶνοι · τὰ ὀκτὼ ἀναστάσιμα στιχηρά · ἦχος πλ. β΄ · μέλος ἀργόν",
        "Πᾶσα πνοὴ αἰνεσάτω τὸν Κύριον",
        (
            # Printed pp. 298–304: the Eothinon ΣΤ΄ begins part-way through p. 304.
            _region(300, 0.45),
            _region(301),
            _region(302),
            _region(303),
            _region(304),
            _region(305),
            _region(306, 0.02, 0.31),
        ),
    ),
    "tone7-ainoi": MusicPiece(
        "tone7-ainoi",
        "Αἶνοι · τὰ ὀκτὼ ἀναστάσιμα στιχηρά · ἦχος βαρύς · μέλος σύντομον",
        "Πᾶσα πνοὴ αἰνεσάτω τὸν Κύριον",
        (
            # Printed pp. 360–365: the Eothinon Ζ΄ follows at the foot of p. 365.
            _region(362, 0.28),
            _region(363),
            _region(364),
            _region(365),
            _region(366),
            _region(367, 0.02, 0.76),
        ),
    ),
    "tone8-ainoi": MusicPiece(
        "tone8-ainoi",
        "Αἶνοι · τὰ ὀκτὼ ἀναστάσιμα στιχηρά · ἦχος πλ. δ΄ · μέλος σύντομον",
        "Πᾶσα πνοὴ αἰνεσάτω τὸν Κύριον",
        # The plagal-fourth Pasapnoaria and all eight resurrectional Ainoi
        # run from printed p. 420 to the end immediately before Eothinon II
        # on p. 425 in the 1905 Anastasimatario.
        (_region(422), _region(423), _region(424), _region(425), _region(426), _region(427, 0.02, 0.52)),
    ),
    "tone1-ainoi": MusicPiece(
        "tone1-ainoi",
        "Αἶνοι · τὰ ὀκτὼ ἀναστάσιμα στιχηρά · ἦχος α΄ · μέλος ἀργόν",
        "Πᾶσα πνοὴ αἰνεσάτω τὸν Κύριον",
        # The first-tone Pasapnoaria and all eight resurrectional Ainoi begin
        # on printed p. 39 and finish before Eothinon A begins on p. 43.
        (_region(41), _region(42), _region(43), _region(44), _region(45, 0.02, 0.72)),
    ),
    "eothinon-4": MusicPiece(
        "eothinon-4",
        "Δοξαστικὸν Ἑωθινὸν Δ΄",
        "Ὄρθρος ἦν βαθύς",
        (_region(200, 0.82), _region(201), _region(202, 0.02, 0.45)),
    ),
    "eothinon-6": MusicPiece(
        "eothinon-6",
        "Δοξαστικὸν Ἑωθινὸν ΣΤ΄ · ἦχος πλ. β΄",
        "Ἡ ὄντως εἰρήνη σὺ Χριστέ",
        # The local scan prints the heading «Ἑωθινὸν ΣΤ΄ · Ἦχος πλ. β΄»
        # in the middle of printed p. 304.  The piece finishes immediately
        # before the Great Doxology starts on printed p. 305.
        (_region(306, 0.35), _region(307, 0.02, 0.70)),
    ),
    "eothinon-7": MusicPiece(
        "eothinon-7",
        "Δοξαστικὸν Ἑωθινὸν Ζ΄ · ἦχος βαρύς",
        "Ἰδοὺ σκοτία καὶ πρωΐ",
        # The seventh Eothinon begins at the foot of printed p. 365 and ends
        # before the following first-tone Great Doxology on p. 366.
        (_region(367, 0.75), _region(368, 0.02, 0.67)),
    ),
    "tone6-great-doxology": MusicPiece(
        "tone6-great-doxology",
        "Μεγάλη Δοξολογία, πλ. β΄ · Μανουὴλ Πρωτοψάλτου",
        "Δόξα σοι τῷ δείξαντι τὸ φῶς",
        (
            _region(307, 0.78),
            _region(308),
            _region(309),
            _region(310),
            _region(311),
            _region(312, 0.02, 0.17),
        ),
    ),
    "plagal4-great-doxology": MusicPiece(
        "plagal4-great-doxology",
        "Μεγάλη Δοξολογία, πλ. δ΄ · Μανουὴλ Πρωτοψάλτου",
        "Δόξα σοι τῷ δείξαντι τὸ φῶς",
        # The local 1905 scan explicitly heads the setting «Δοξολογία
        # Μανουὴλ Πρωτοψάλτου · Ἦχος πλ. δ΄» at the foot of printed p. 426.
        # It finishes before the following plagal-first material on p. 431.
        (_region(428, 0.69), _region(429), _region(430), _region(431), _region(432, 0.02, 0.68)),
    ),
    "tone1-great-doxology": MusicPiece(
        "tone1-great-doxology",
        "Μεγάλη Δοξολογία, ἦχος α΄ · Μανουὴλ Πρωτοψάλτου",
        "Δόξα σοι τῷ δείξαντι τὸ φῶς",
        # The first-tone setting is explicitly headed «Δοξολογία Μανουὴλ
        # Πρωτοψάλτου · Ἦχος Α΄» on printed p. 45.  The final cropped page
        # stops before «Σήμερον σωτηρία», which is a separate hymn.
        (_region(47), _region(48), _region(49), _region(50, 0.02, 0.55)),
    ),
    "psalm-50-tone2": MusicPiece(
        "psalm-50-tone2",
        "Ν΄ Ψαλμός, ἦχος β΄ · Πέτρου Λαμπαδαρίου",
        "Ἐλέησόν με, ὁ Θεός, κατὰ τὸ μέγα ἔλεός σου",
        (
            ScanRegion(1, 490, (0.02, 0.405, 0.98, 0.98)),
            ScanRegion(2, 491),
            ScanRegion(3, 492),
            ScanRegion(4, 493),
            ScanRegion(5, 494, (0.02, 0.02, 0.98, 0.55)),
        ),
        book_id=PANDEKTI_BOOK_ID,
    ),
    "ypereulogimeni-tone2": MusicPiece(
        "ypereulogimeni-tone2",
        "Ὑπερευλογημένη · ἦχος β΄ · Πέτρου Λαμπαδαρίου",
        "Ὑπερευλογημένη ὑπάρχεις, Θεοτόκε Παρθένε",
        (ScanRegion(288, 288, (0.02, 0.02, 0.98, 0.72)),),
        book_id=YPEREULOGIMENI_BOOK_ID,
    ),
    "cross-katavasies": MusicPiece(
        "cross-katavasies",
        "Σύντομες Καταβασίαι Ὑψώσεως Τιμίου Σταυροῦ",
        "Σταυρὸν χαράξας Μωσῆς",
        (
            # Short heirmoi from the second half of the book. The intervening
            # troparia of the complete canon are deliberately excluded.
            ScanRegion(233, 225, (0.02, 0.19, 0.98, 0.615)),
            ScanRegion(234, 226, (0.02, 0.85, 0.98, 0.98)),
            ScanRegion(235, 227, (0.02, 0.02, 0.98, 0.32)),
            ScanRegion(235, 227, (0.02, 0.755, 0.98, 0.98)),
            ScanRegion(236, 228, (0.02, 0.02, 0.98, 0.19)),
            ScanRegion(236, 228, (0.02, 0.72, 0.98, 0.98)),
            ScanRegion(237, 229, (0.02, 0.02, 0.98, 0.25)),
            ScanRegion(238, 230, (0.02, 0.315, 0.98, 0.80)),
            ScanRegion(239, 231, (0.02, 0.75, 0.98, 0.98)),
            ScanRegion(240, 232, (0.02, 0.02, 0.98, 0.43)),
            ScanRegion(241, 233, (0.02, 0.835, 0.98, 0.98)),
            ScanRegion(242, 234, (0.02, 0.02, 0.98, 0.37)),
            ScanRegion(243, 235, (0.02, 0.55, 0.98, 0.86)),
        ),
        book_id=IRMOLOGION_BOOK_ID,
    ),
    "theotokos-katavasies-tone4": MusicPiece(
        "theotokos-katavasies-tone4",
        "Καταβασίες Θεοτόκου · ἦχος δ΄ · Ἀνοίξω τὸ στόμα μου",
        "Ἀνοίξω τὸ στόμα μου, καὶ πληρωθήσεται Πνεύματος",
        # The complete short Theotokos Katavasies, printed pages 51–56.
        # They are the setting explicitly selected by Melodos on 26/9.
        (
            ScanRegion(59, 51),
            ScanRegion(60, 52),
            ScanRegion(61, 53),
            ScanRegion(62, 54),
            ScanRegion(63, 55),
            ScanRegion(64, 56),
        ),
        book_id=IRMOLOGION_BOOK_ID,
    ),
    "kypseli-08-apolytikion": MusicPiece(
        "kypseli-08-apolytikion",
        "Ἀπολυτίκιον Γενεθλίου Θεοτόκου · ἦχος δ΄ · Μηναία",
        "Ἡ γέννησίς σου Θεοτόκε, χαρὰν ἐμήνυσε",
        (ScanRegion(640, 51, (0.02, 0.56, 0.98, 0.99)),),
        book_id=KYPSELI_BOOK_ID,
    ),
    "kypseli-08-kontakion": MusicPiece(
        "kypseli-08-kontakion",
        "Κοντάκιον Γενεθλίου Θεοτόκου · ἦχος δ΄ · Μηναία",
        "Ἰωακεὶμ καὶ Ἄννα ὀνειδισμοῦ ἀτεκνίας",
        (ScanRegion(641, 52, (0.02, 0.12, 0.98, 0.72)),),
        book_id=KYPSELI_BOOK_ID,
    ),
    "kypseli-08-doxastikon": MusicPiece(
        "kypseli-08-doxastikon",
        "Δοξαστικὸν Γενεθλίου Θεοτόκου · ἦχος πλ. α΄ · Μηναία",
        "Αὕτη ἡ ἡμέρα Κυρίου, ἀγαλλιάσθε λαοί",
        (ScanRegion(623, 34, (0.02, 0.02, 0.98, 0.88)),),
        book_id=KYPSELI_BOOK_ID,
    ),
    "kypseli-09-doxastikon": MusicPiece(
        "kypseli-09-doxastikon",
        "Δοξαστικὸν Θεοπατόρων · ἦχος δ΄ · Μηναία",
        "Σήμερον ἡ πανάμωμος Ἁγνὴ προῆλθεν ἐκ τῆς στείρας",
        (
            ScanRegion(647, 57, (0.02, 0.10, 0.98, 0.98)),
            ScanRegion(648, 58, (0.02, 0.02, 0.98, 0.30)),
        ),
        book_id=KYPSELI_BOOK_ID,
    ),
    "litourgia-eisodikon-pandekti": MusicPiece(
        "litourgia-eisodikon-pandekti",
        "Εἰσοδικόν · Μουσικὴ Πανδέκτη",
        "Δεῦτε προσκυνήσωμεν καὶ προσπέσωμεν Χριστῷ",
        # The Eisodikon is printed on p. 41.  Keep the first setting and its
        # heading, stopping before the alternate setting on the same page.
        (ScanRegion(41, 41, (0.02, 0.02, 0.98, 0.48)),),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-trisagion-argon-pandekti": MusicPiece(
        "litourgia-trisagion-argon-pandekti",
        "Τρισάγιος ὕμνος · ἀργός · τριπλή ἐκτέλεση · Μουσικὴ Πανδέκτη",
        "Ἅγιος ὁ Θεός, ἅγιος ἰσχυρός, ἅγιος ἀθάνατος",
        # The complete slow setting begins on p. 43, includes the third
        # execution, and continues through the Dynamis at the top of p. 45.
        # Do not include the separate short alternatives lower on p. 45.
        (
            ScanRegion(43, 43),
            ScanRegion(44, 44),
            ScanRegion(45, 45, (0.02, 0.02, 0.98, 0.29)),
        ),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-cherouvikon-pandekti": MusicPiece(
        "litourgia-cherouvikon-pandekti",
        "Χερουβικὸν · ἦχος δ΄ ἅγια · Πέτρου Λαμπαδαρίου",
        "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες",
        (ScanRegion(95, 95), ScanRegion(96, 96), ScanRegion(97, 97)),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-epinikios-pandekti": MusicPiece(
        "litourgia-epinikios-pandekti",
        "Λειτουργικά · Ἔλεον εἰρήνης… Ἅγιος… Ὡσαννὰ · Μουσικὴ Πανδέκτη",
        "Ἔλεον εἰρήνης, θυσίαν αἰνέσεως",
        (
            # Page 255 continues from the Patera response through the
            # beginning of the Sanctus; page 256 completes the Sanctus and
            # the two Hosanna responses.
            ScanRegion(255, 255, (0.02, 0.42, 0.98, 0.98)),
            ScanRegion(256, 256, (0.02, 0.02, 0.98, 0.57)),
        ),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-amin-se-ymnoumen-pandekti": MusicPiece(
        "litourgia-amin-se-ymnoumen-pandekti",
        "Ἀμήν · Σὲ ὑμνοῦμεν… · Λειτουργικά · Μουσικὴ Πανδέκτη",
        "Ἀμήν · Σὲ ὑμνοῦμεν, σὲ εὐλογοῦμεν",
        (
            # The lower half of p. 256 contains the two Amens and the first
            # part of the response; p. 257 completes «ὁ Θεὸς ἡμῶν».
            ScanRegion(256, 256, (0.02, 0.54, 0.98, 0.98)),
            ScanRegion(257, 257, (0.02, 0.02, 0.98, 0.15)),
        ),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-koinonikon-pandekti": MusicPiece(
        "litourgia-koinonikon-pandekti",
        "Κοινωνικὸν · ἦχος δ΄ ἅγια · Ποτήριον σωτηρίου",
        "Ποτήριον σωτηρίου λήψομαι",
        (ScanRegion(341, 341), ScanRegion(342, 342), ScanRegion(343, 343)),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-kyrie-eleison-pandekti": MusicPiece(
        "litourgia-kyrie-eleison-pandekti",
        "Κύριε ἐλέησον · σύντομα · Μουσικὴ Πανδέκτη",
        "Κύριε ἐλέησον",
        (ScanRegion(5, 5), ScanRegion(6, 6)),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-tais-presveiais-pandekti": MusicPiece(
        "litourgia-tais-presveiais-pandekti",
        "Ταῖς πρεσβείαις τῆς Θεοτόκου · Μουσικὴ Πανδέκτη",
        "Ταῖς πρεσβείαις τῆς Θεοτόκου, Σῶτερ, σῶσον ἡμᾶς",
        (ScanRegion(11, 11),),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-soson-yie-pandekti": MusicPiece(
        "litourgia-soson-yie-pandekti",
        "Σῶσον ἡμᾶς Υἱὲ Θεοῦ · Μουσικὴ Πανδέκτη",
        "Σῶσον ἡμᾶς Υἱὲ Θεοῦ",
        (ScanRegion(11, 11),),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-monogenis-pandekti": MusicPiece(
        "litourgia-monogenis-pandekti",
        "Ὁ Μονογενὴς Υἱὸς καὶ Λόγος · Μουσικὴ Πανδέκτη",
        "Ὁ Μονογενὴς Υἱὸς καὶ Λόγος τοῦ Θεοῦ",
        (ScanRegion(12, 12),),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-paraschou-pandekti": MusicPiece(
        "litourgia-paraschou-pandekti",
        "Παράσχου Κύριε · σύντομα · Μουσικὴ Πανδέκτη",
        "Παράσχου Κύριε",
        (ScanRegion(8, 8), ScanRegion(9, 9), ScanRegion(10, 10)),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-patera-pandekti": MusicPiece(
        "litourgia-patera-pandekti",
        "Πατέρα, Υἱὸν καὶ Ἅγιον Πνεῦμα · Λειτουργικά",
        "Πατέρα, Υἱὸν καὶ Ἅγιον Πνεῦμα",
        # The previous excerpt file accidentally reused the Agapiso pages for
        # this response.  In the full Pandekti D΄ volume the distinct Patera
        # setting begins on printed page 255.
        (ScanRegion(255, 255, (0.02, 0.18, 0.98, 0.55)),),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-agapiso-pandekti": MusicPiece(
        "litourgia-agapiso-pandekti",
        "Ἀγαπήσω σε, Κύριε · ἦχος δ΄ ἅγια",
        "Ἀγαπήσω σε, Κύριε, ἡ ἰσχύς μου",
        (ScanRegion(251, 251), ScanRegion(252, 252)),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-eie-to-onoma-pandekti": MusicPiece(
        "litourgia-eie-to-onoma-pandekti",
        "Εἴη τὸ ὄνομα Κυρίου · ὕμνος ἀπολύσεως",
        "Εἴη τὸ ὄνομα Κυρίου εὐλογημένον",
        (ScanRegion(501, 501, (0.02, 0.12, 0.98, 0.58)),),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-plirothito-melodos": MusicPiece(
        "litourgia-plirothito-melodos",
        "Εἰς ἄφεσιν ἁμαρτιῶν · Πληρωθήτω τὸ στόμα ἡμῶν",
        "Πληρωθήτω τὸ στόμα ἡμῶν αἰνέσεως Κύριε",
        (ScanRegion(93, 93),),
        book_id=PLIROTHITO_BOOK_ID,
    ),
}


# The D΄ volume above contains the original fourth-tone agia material used
# for the September feasts.  For ordinary days Melodos explicitly names the
# tone of the Cheroubikon, the Litourgika and the Koinonikon.  Melodos also
# publishes compact, tone-specific scans for those three members.  Register
# those scans as first-class local books so the same three positions are
# filled for every one of the eight weekly tones, without reusing a page from
# a different tone.
_TONE_SOURCE_SPECS: Final[dict[int, tuple[str, str, str, str, str, int, tuple[int, ...], tuple[int, ...], tuple[int, ...]]]] = {
    1: (
        "melodos-liturgy-tone-1",
        "Μουσικὰ μέλη Θείας Λειτουργίας · ἦχος α΄",
        "melodos-liturgy-tone-1.pdf",
        "https://melodos.com/bibliothiki/?p=2063",
        "https://melodos.com/bibliothiki/wp-content/uploads/01-Χερουβικό-Λειτουργικά-και-Κοινωνικό-σε-Α΄-ήχο.pdf",
        17,
        (1, 2, 3, 4),
        (10, 11),
        # The Sunday Koinonikon starts on p. 15 and its final «Ἀλληλούϊα»
        # concludes on p. 17.  Do not truncate the musical phrase at p. 16.
        (15, 16, 17),
    ),
    2: (
        "melodos-liturgy-tone-2",
        "Μουσικὰ μέλη Θείας Λειτουργίας · ἦχος β΄",
        "melodos-liturgy-tone-2.pdf",
        "https://melodos.com/bibliothiki/?p=2087",
        "https://melodos.com/bibliothiki/wp-content/uploads/02-Χερουβικό-Λειτουργικά-και-Κοινωνικό-σε-B΄-ήχο.mel.pdf",
        16,
        (1, 2, 3, 4),
        (8, 9),
        (14, 15),
    ),
    3: (
        "melodos-liturgy-tone-3",
        "Μουσικὰ μέλη Θείας Λειτουργίας · ἦχος γ΄",
        "melodos-liturgy-tone-3.pdf",
        "https://melodos.com/bibliothiki/?p=2167",
        "https://melodos.com/bibliothiki/wp-content/uploads/03-Χερουβικό-Λειτουργικά-και-Κοινωνικό-σε-Γ΄-ήχο.pdf",
        12,
        (1, 2, 3, 4),
        (7, 8),
        (11, 12),
    ),
    4: (
        "melodos-liturgy-tone-4",
        "Μουσικὰ μέλη Θείας Λειτουργίας · ἦχος δ΄",
        "melodos-liturgy-tone-4.pdf",
        "https://melodos.com/bibliothiki/?cat=157",
        "https://melodos.com/bibliothiki/wp-content/uploads/04-Χερουβικό-Λειτουργικά-και-Κοινωνικό-σε-Δ΄-ήχο.pdf",
        13,
        (1, 2, 3, 4),
        (5, 6, 7, 8, 9, 10),
        (11, 12),
    ),
    5: (
        "melodos-liturgy-tone-5",
        "Μουσικὰ μέλη Θείας Λειτουργίας · ἦχος πλ. α΄",
        "melodos-liturgy-tone-5.pdf",
        "https://melodos.com/bibliothiki/?p=2238",
        "https://melodos.com/bibliothiki/wp-content/uploads/05-Χερουβικό-Λειτουργικά-και-Κοινωνικό-σε-Πλ.-Α΄-ήχο.pdf",
        23,
        (1, 2, 3, 4),
        (9, 10),
        (22, 23),
    ),
    6: (
        "melodos-liturgy-tone-6",
        "Μουσικὰ μέλη Θείας Λειτουργίας · ἦχος πλ. β΄",
        "melodos-liturgy-tone-6.pdf",
        "https://melodos.com/bibliothiki/?p=1932",
        "https://melodos.com/bibliothiki/wp-content/uploads/06-Χερουβικό-Λειτουργικά-και-Κοινωνικό-σε-πλ.-β΄.pdf",
        14,
        (1, 2, 3, 4),
        (8, 9),
        (12, 13),
    ),
    7: (
        "melodos-liturgy-tone-7",
        "Μουσικὰ μέλη Θείας Λειτουργίας · ἦχος βαρύς",
        "melodos-liturgy-tone-7.pdf",
        "https://melodos.com/bibliothiki/?p=1967",
        "https://melodos.com/bibliothiki/wp-content/uploads/07-Χερουβικό-Λειτουργικά-και-Κοινωνικό-σε-βαρύ.pdf",
        14,
        (1, 2, 3, 4),
        (5, 6, 7, 8),
        (12, 13),
    ),
    8: (
        "melodos-liturgy-tone-8",
        "Μουσικὰ μέλη Θείας Λειτουργίας · ἦχος πλ. δ΄",
        "melodos-liturgy-tone-8.pdf",
        "https://melodos.com/bibliothiki/?p=2037",
        "https://melodos.com/bibliothiki/wp-content/uploads/08-Χερουβικό-Λειτουργικά-και-Κοινωνικό-σε-Πλ.-δ΄.pdf",
        15,
        (1, 2, 3, 4),
        (10, 11),
        (13, 14),
    ),
}

_TONE_LABEL_TEXT: Final[dict[int, str]] = {
    1: "α΄",
    2: "β΄",
    3: "γ΄",
    4: "δ΄",
    5: "πλ. α΄",
    6: "πλ. β΄",
    7: "βαρύς",
    8: "πλ. δ΄",
}

# In the compact Melodos books the two Amens / «Σὲ ὑμνοῦμεν» and
# «Ἄξιον ἐστίν» commonly share a page.  Keep each as one complete excerpt:
# do not start the first response on a continuation syllable, and do not make
# its final page also begin the Axion Estin setting.
_TONE_AMIN_REGIONS: Final[dict[int, tuple[ScanRegion, ...]]] = {
    1: (ScanRegion(11, 11, (0.02, 0.52, 0.98, 0.98)), ScanRegion(12, 12, (0.02, 0.02, 0.98, 0.38))),
    2: (ScanRegion(9, 9, (0.02, 0.67, 0.98, 0.98)), ScanRegion(10, 10, (0.02, 0.02, 0.98, 0.51))),
    3: (ScanRegion(8, 8, (0.02, 0.62, 0.98, 0.98)), ScanRegion(9, 9, (0.02, 0.02, 0.98, 0.25))),
    4: (ScanRegion(8, 8, (0.02, 0.60, 0.98, 0.98)), ScanRegion(9, 9, (0.02, 0.02, 0.98, 0.14))),
    5: (ScanRegion(10, 10, (0.02, 0.33, 0.98, 0.98)),),
    6: (ScanRegion(9, 9, (0.02, 0.45, 0.98, 0.98)), ScanRegion(10, 10, (0.02, 0.02, 0.98, 0.15))),
    7: (ScanRegion(9, 9, (0.02, 0.10, 0.98, 0.65)),),
    8: (ScanRegion(11, 11, (0.02, 0.23, 0.98, 0.67)),),
}

_TONE_AXION_ESTIN_REGIONS: Final[dict[int, tuple[ScanRegion, ...]]] = {
    1: (
        ScanRegion(12, 12, (0.02, 0.39, 0.98, 0.98)),
        ScanRegion(13, 13),
        ScanRegion(14, 14, (0.02, 0.02, 0.98, 0.23)),
    ),
    2: (ScanRegion(10, 10, (0.02, 0.52, 0.98, 0.98)), ScanRegion(11, 11, (0.02, 0.02, 0.98, 0.64))),
    3: (ScanRegion(9, 9, (0.02, 0.27, 0.98, 0.98)), ScanRegion(10, 10, (0.02, 0.02, 0.98, 0.57))),
    4: (ScanRegion(9, 9, (0.02, 0.18, 0.98, 0.98)), ScanRegion(10, 10, (0.02, 0.02, 0.98, 0.40))),
    5: (ScanRegion(11, 11), ScanRegion(12, 12, (0.02, 0.02, 0.98, 0.39))),
    6: (ScanRegion(10, 10, (0.02, 0.18, 0.98, 0.98)), ScanRegion(11, 11, (0.02, 0.02, 0.98, 0.83))),
    7: (
        ScanRegion(9, 9, (0.02, 0.66, 0.98, 0.98)),
        ScanRegion(10, 10),
        ScanRegion(11, 11, (0.02, 0.02, 0.98, 0.28)),
    ),
    8: (ScanRegion(11, 11, (0.02, 0.68, 0.98, 0.98)), ScanRegion(12, 12, (0.02, 0.02, 0.98, 0.86))),
}

_TONE_KYRIE_PARASCHOU_REGIONS: Final[dict[int, tuple[ScanRegion, ...]]] = {
    tone: (
        ScanRegion(5, 5, (0.02, 0.68, 0.98, 0.98)),
        ScanRegion(6, 6),
    )
    for tone in range(1, 8)
}
_TONE_KYRIE_PARASCHOU_REGIONS[8] = (
    ScanRegion(5, 5, (0.02, 0.68, 0.98, 0.98)),
    ScanRegion(6, 6),
    ScanRegion(7, 7, (0.02, 0.02, 0.98, 0.34)),
)


def _tone_scan_regions(pages: tuple[int, ...]) -> tuple[ScanRegion, ...]:
    return tuple(ScanRegion(page, page) for page in pages)


for _tone, (
    _book_id,
    _book_title,
    _filename,
    _source_page,
    _download_url,
    _minimum_pages,
    _cherouvikon_pages,
    _leitourgika_pages,
    _koinonikon_pages,
) in _TONE_SOURCE_SPECS.items():
    BOOKS[_book_id] = MusicBook(
        _book_id,
        _book_title,
        "Χερουβικόν, Λειτουργικά καὶ Κοινωνικόν · σύντομη τονική έκδοση",
        _source_page,
        _filename,
        _minimum_pages,
        "Μελωδός · ψηφιοποιημένο μουσικό τεκμήριο",
        _download_url,
    )
    PIECES[f"litourgia-tone-{_tone}-cherouvikon"] = MusicPiece(
        f"litourgia-tone-{_tone}-cherouvikon",
        f"Χερουβικὸν · σύντομον · ἦχος {_TONE_LABEL_TEXT[_tone]} · Μελωδός",
        "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες",
        _tone_scan_regions(_cherouvikon_pages),
        book_id=_book_id,
    )
    PIECES[f"litourgia-tone-{_tone}-kyrie-paraschou"] = MusicPiece(
        f"litourgia-tone-{_tone}-kyrie-paraschou",
        f"Κύριε ἐλέησον καὶ Παράσχου Κύριε · ἦχος {_TONE_LABEL_TEXT[_tone]} · Μελωδός",
        "Κύριε ἐλέησον · Παράσχου Κύριε",
        _TONE_KYRIE_PARASCHOU_REGIONS[_tone],
        book_id=_book_id,
    )
    PIECES[f"litourgia-tone-{_tone}-leitourgika"] = MusicPiece(
        f"litourgia-tone-{_tone}-leitourgika",
        f"Λειτουργικά · ἦχος {_TONE_LABEL_TEXT[_tone]} · Μελωδός",
        "Ἔλεον εἰρήνης, θυσίαν αἰνέσεως",
        _tone_scan_regions(_leitourgika_pages),
        book_id=_book_id,
    )
    PIECES[f"litourgia-tone-{_tone}-amin-se-ymnoumen"] = MusicPiece(
        f"litourgia-tone-{_tone}-amin-se-ymnoumen",
        f"Ἀμήν · Σὲ ὑμνοῦμεν… · ἦχος {_TONE_LABEL_TEXT[_tone]} · Μελωδός",
        "Σὲ ὑμνοῦμεν, σὲ εὐλογοῦμεν, σοὶ εὐχαριστοῦμεν",
        _TONE_AMIN_REGIONS[_tone],
        book_id=_book_id,
    )
    PIECES[f"litourgia-tone-{_tone}-axion-estin"] = MusicPiece(
        f"litourgia-tone-{_tone}-axion-estin",
        f"Ἄξιόν ἐστιν · ἦχος {_TONE_LABEL_TEXT[_tone]} · Μελωδός",
        "Ἄξιόν ἐστιν ὡς ἀληθῶς μακαρίζειν σε τὴν Θεοτόκον",
        _TONE_AXION_ESTIN_REGIONS[_tone],
        book_id=_book_id,
    )
    PIECES[f"litourgia-tone-{_tone}-axion-kai-dikaion"] = MusicPiece(
        f"litourgia-tone-{_tone}-axion-kai-dikaion",
        f"Ἄξιον καὶ δίκαιον · ἦχος {_TONE_LABEL_TEXT[_tone]} · Μελωδός",
        "Ἄξιον καὶ δίκαιον",
        _tone_scan_regions(_leitourgika_pages),
        book_id=_book_id,
    )
    PIECES[f"litourgia-tone-{_tone}-koinonikon"] = MusicPiece(
        f"litourgia-tone-{_tone}-koinonikon",
        f"Κοινωνικόν · Αἰνεῖτε τὸν Κύριον · ἦχος {_TONE_LABEL_TEXT[_tone]} · Μελωδός",
        "Αἰνεῖτε τὸν Κύριον ἐκ τῶν οὐρανῶν",
        _tone_scan_regions(_koinonikon_pages),
        book_id=_book_id,
    )


# Melodos words the plagal-second Great-Doxology instruction in two ways.  The
# second is the «ἦχος τῆς ἡμέρας» wording used on the Archangels' Sunday
# (8 November 2026); both name the πλ. β΄ setting explicitly, and the tone
# marker is still required separately, so the score is never guessed from the
# weekday.  Matching is accent- and punctuation-insensitive (see _normalized).
_TONE6_DOXOLOGY_INSTRUCTIONS: Final[tuple[str, ...]] = (
    "η δοξολογία σήμερα ψάλλεται στον ήχο του δοξαστικού",
    "η δοξολογία σήμερα ψάλλεται στην ήχο της ημέρας δηλαδή ήχο πλ β",
)

# Matching is accent- and punctuation-insensitive; the stored polytonic text
# and the HTML delivered to the browser are never altered.
def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFD", value.casefold())
    # Melodos alternates commas, Greek ano teleia, apostrophes and full stops
    # between otherwise identical liturgical lines.  Strip punctuation for
    # matching only; the source HTML and all displayed polytonic text remain
    # untouched.
    cleaned = "".join(
        ch
        for ch in value
        if unicodedata.category(ch) not in {"Mn", "Pc", "Pd", "Pe", "Pf", "Pi", "Po", "Ps"}
    )
    return " ".join(cleaned.split())


# The short katavasies of the whole year come from the catalogue registry. They
# are all inserted before the invitation to the Timiotera, in the order the data
# file lists them (sets in registry order, odes in liturgical order). The old
# eis/eisp/kyrpx rules are generated here too, so the data file is the single
# source of truth.
KATAVASIES_DATA_PATH: Final = Path(__file__).resolve().parent / "data" / "katavasies.json"
_KATAVASIES_ANCHOR: Final = (
    "Τὴν Θεοτόκον καὶ Μητέρα τοῦ Φωτός, ἐν ὕμνοις τιμῶντες μεγαλύνωμεν."
)
# The main heading is «Καταβασίες»; the ninth-ode block says «Καταβασία».
# These complete word forms deliberately do not match «συγκατάβασιν», which
# occurs in ordinary hymn text (e.g. the 2026-11-09 Orthros).
_KATAVASIA_HEADING_MARKERS: Final[tuple[str, ...]] = (
    "καταβασιεσ",
    "καταβασια",
    "καταβασιων",
)
# The tone-4 «Ἀνοίξω τὸ στόμα μου» family shares its eirmoi across several
# feasts.  Require the feast-specific heading wording so an Eisodia page does
# not also attach the Triodion Theotokos or Annunciation odes that quote the
# same lines.  Other sets are already distinguished by their first eirmos.
_KATAVASIA_SET_HEADING_GROUPS: Final[dict[str, tuple[tuple[str, ...], ...]]] = {
    "eisp": (("καταβασιεσ εισοδιων", "καταβασιεσ τησ θεοτοκου"),),
    "theot": (("εορτασ τησ θεοτοκου", "τριωδι"),),
    "evang": (("ευαγγελισμ",),),
}
# The scanned Cross and Theotokos katavasies remain authoritative on their own
# services; the short digital odes must not replace them.
_CROSS_THEOTOKOS_SCAN_HEADERS: Final[tuple[str, ...]] = (
    "Καταβασίες τῆς Ὑψώσεως τοῦ Τιμίου Σταυροῦ",
    "Καταβασίες Τῆς Θεοτόκου",
)
# The Eisodia and pre-feast Theotokos text shares the first eirmos with the
# Christmas katavasies, so the Theotokos set is excluded from Christmas days.
_CHRISTMAS_KATAVASIES_INCIPITS: Final[tuple[str, ...]] = (
    "Χριστὸς γεννᾶται, δοξάσατε",
    "Χριστὸς γεννᾶται δοξάσατε",
)


def _katavasia_variants(value: str) -> tuple[str, ...]:
    """Return the plain incipit and its decorated-initial-letter form."""
    normalized = _normalized(value)
    variants = [normalized]
    tokens = normalized.split()
    if tokens:
        dropped = tokens[:]
        dropped[0] = dropped[0][1:]
        candidate = " ".join(token for token in dropped if token)
        if candidate and candidate not in variants:
            variants.append(candidate)
    return tuple(variants)


def _generated_katavasies_rules() -> tuple[AttachmentRule, ...]:
    entries = json.loads(KATAVASIES_DATA_PATH.read_text(encoding="utf-8"))
    rules: list[AttachmentRule] = []
    for entry in entries:
        # Melodos often quotes the set's first eirmos and the ode's own
        # incipit.  Both must be present; a short incipit alone would match
        # ordinary psalm text.  The generator already drops shorter incipits,
        # but keep the guard here for a stale data file.
        if len(_normalized(entry["incipit"]).split()) < 3:
            continue
        if len(_normalized(entry["first_incipit"]).split()) < 3:
            continue
        required_groups = (
            _KATAVASIA_HEADING_MARKERS,
            _katavasia_variants(entry["incipit"]),
            _katavasia_variants(entry["first_incipit"]),
            *_KATAVASIA_SET_HEADING_GROUPS.get(entry["set"], ()),
        )
        if entry["set"] == "eisp":
            # The short Theotokos setting sits beside the verified full
            # Theotokos scan, so the scan stays and the digital odes are added.
            excluded = _CHRISTMAS_KATAVASIES_INCIPITS
            replace_scan = False
        else:
            excluded = _CROSS_THEOTOKOS_SCAN_HEADERS
            replace_scan = True
        rules.append(
            AttachmentRule(
                "orthros",
                _KATAVASIES_ANCHOR,
                entry["id"],
                required_text_groups=required_groups,
                required_after_any=_KATAVASIA_HEADING_MARKERS,
                excluded_text_any=excluded,
                insert_before=True,
                digital_title=entry["title"],
                replace_scan=replace_scan,
            )
        )
    return tuple(rules)


PILOT_RULES: Final[tuple[AttachmentRule, ...]] = (
    AttachmentRule(
        "orthros",
        "ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.",
        "tone6-apolytikion",
        weekly_tone=6,
    ),
    AttachmentRule(
        "orthros",
        "ὁ ἐν νεκροῖς καὶ τοὺς νεκροὺς ἀναστήσας δόξα σοί.",
        "tone6-kathismata-a",
        weekly_tone=6,
    ),
    AttachmentRule(
        "orthros",
        "Χριστὲ ὁ Θεὸς ἡμῶν, φωτίσας τοὺς ἐν σκότει.",
        "tone6-kathismata-b",
        weekly_tone=6,
    ),
    AttachmentRule(
        "orthros",
        "λληλούϊα, Ἀλληλούϊα, Ἀλληλούϊα. Δόξα σοὶ ὁ Θεός.",
        "resurrectional-evlogitaria",
        required_text=("Ἐν συνεχεία ψάλλονται τά Ἀναστάσιμα εὐλογητάρια.",),
        match_number=3,
    ),
    AttachmentRule(
        "orthros",
        "σὺν πάση πνοὴ τῶν κάτω.",
        "tone6-anavathmoi",
        weekly_tone=6,
    ),
    AttachmentRule(
        "orthros",
        "πρὸς ζωογονίαν.",
        "tone4-anavathmoi-first-antiphon",
        required_text=("Ἀναβαθμοί τὸ α΄ Ἀντίφωνον τοῦ δ΄ Ἤχου",),
    ),
    AttachmentRule(
        "orthros",
        "τῶν κτισμάτων ἀληθῶς, ἐδείχθης Δέσποινα.",
        "tone6-canon-ode-1",
        weekly_tone=6,
    ),
    AttachmentRule(
        "orthros",
        "καὶ τεκοῦσα, μένεις ἀειπάρθενος.",
        "tone6-canon-ode-3",
        weekly_tone=6,
    ),
    AttachmentRule(
        "orthros",
        "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",
        "tone8-ainoi",
        weekly_tone=8,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        semantic_context="ainoi",
        expected_reviewer_choice="short_ainoi",
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",
        "tone1-ainoi",
        weekly_tone=1,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        semantic_context="ainoi",
        expected_reviewer_choice="slow_ainoi",
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",
        "tone2-ainoi",
        weekly_tone=2,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        semantic_context="ainoi",
        expected_reviewer_choice="slow_ainoi",
        insert_before=True,
    ),
    # A feast Sunday can replace the Eothinon Doxastikon with the Doxastikon
    # of the feast. The Resurrectional Ainoi still belong immediately before
    # those feast Prosomoia (Holy Fathers, 11 October 2026).
    AttachmentRule(
        "orthros",
        "Στιχηρὰ Προσόμοια τῶν Πατέρων.",
        "tone2-ainoi",
        weekly_tone=2,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        semantic_context="ainoi",
        expected_reviewer_choice="slow_ainoi",
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",
        "tone3-ainoi",
        weekly_tone=3,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        semantic_context="ainoi",
        expected_reviewer_choice="short_ainoi",
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",
        "papline-ainoi-lambadarios-tone4-private-draft",
        weekly_tone=4,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        weekdays=(6,),
        insert_before=True,
        digital_title="Αἶνοι · Πασαπνοάρια και στιχηρὰ ἦχος δ΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
    AttachmentRule(
        "orthros",
        "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",
        "papline-ainoi-byzantios-pl1-private-draft",
        weekly_tone=5,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        weekdays=(6,),
        insert_before=True,
        digital_title="Αἶνοι · Πασαπνοάρια και στιχηρὰ ἦχος πλ. α΄ · Πέτρου Βυζαντίου (ψηφιακή)",
    ),
    AttachmentRule(
        "orthros",
        "ἐντρυφῆσαι φιλάνθρωπε Κύριε.",
        "papline-doxastikon-eothinon10-lambadarios-private-draft",
        required_text=("τὴν εἰς ᾍδου κάθοδον",),
        weekdays=(6,),
        digital_title="Ἑωθινὸν Δοξαστικὸν ι΄ · Μετὰ τὴν εἰς ᾍδου κάθοδον · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
    AttachmentRule(
        "orthros",
        "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",
        "tone4-ainoi",
        weekly_tone=4,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        semantic_context="ainoi",
        expected_reviewer_choice="short_ainoi",
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",
        "tone5-ainoi",
        weekly_tone=5,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        semantic_context="ainoi",
        expected_reviewer_choice="slow_ainoi",
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",
        "tone6-ainoi",
        weekly_tone=6,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        semantic_context="ainoi",
        expected_reviewer_choice="slow_ainoi",
        insert_before=True,
    ),
    # A feast Sunday can replace the Eothinon Doxastikon with the feast
    # Doxastikon (Synaxis of the Archangels, 8 November 2026), so the
    # «ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ» anchor above never appears.  The resurrectional
    # Ainoi still belong immediately before the feast Prosomoia, exactly as on
    # the Sunday of the Holy Fathers.  The exclusion keeps a normal Sunday from
    # receiving the same score twice.
    AttachmentRule(
        "orthros",
        "Στιχηρὰ Προσόμοια τῶν Ἀρχιστρατήγων.",
        "tone6-ainoi",
        weekly_tone=6,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        semantic_context="ainoi",
        expected_reviewer_choice="slow_ainoi",
        insert_before=True,
        excluded_text_any=("ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",),
    ),
    AttachmentRule(
        "orthros",
        "ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ",
        "tone7-ainoi",
        weekly_tone=7,
        required_text=("Στιχηρὰ Ἀναστάσιμα",),
        semantic_context="ainoi",
        expected_reviewer_choice="short_ainoi",
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "plagal4-timiotera",
        semantic_context="timiotera",
        expected_context_tone=8,
        match_number=6,
    ),
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "tone4-timiotera",
        semantic_context="timiotera",
        expected_context_tone=4,
        match_number=6,
    ),
    # Papagiannis' digital Ode 9 «Μεγαλύνει» with the Timiotera refrain.  These
    # follow the same local Melodos instruction and sixth refrain as the scans
    # above, but are attached in addition to them (replace_scan=False): the
    # tone-4 and plagal-fourth scans stay.  Tones without a scan get only the
    # digital score.
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "papline-tim-1-private-draft",
        semantic_context="timiotera",
        expected_context_tone=1,
        match_number=6,
        replace_scan=False,
        digital_title="Ὠδὴ θ΄ · Μεγαλύνει ἡ ψυχή μου · Ἡ Τιμιωτέρα · ἦχος α΄ · Κωνσταντίνου Παπαγιάννη (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
    ),
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "papline-tim-3-private-draft",
        semantic_context="timiotera",
        expected_context_tone=3,
        match_number=6,
        replace_scan=False,
        digital_title="Ὠδὴ θ΄ · Μεγαλύνει ἡ ψυχή μου · Ἡ Τιμιωτέρα · ἦχος γ΄ · Κωνσταντίνου Παπαγιάννη (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
    ),
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "papline-tim-4-private-draft",
        semantic_context="timiotera",
        expected_context_tone=4,
        match_number=6,
        replace_scan=False,
        digital_title="Ὠδὴ θ΄ · Μεγαλύνει ἡ ψυχή μου · Ἡ Τιμιωτέρα · ἦχος δ΄ · Κωνσταντίνου Παπαγιάννη (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
    ),
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "papline-tim-pl1-private-draft",
        semantic_context="timiotera",
        expected_context_tone=5,
        match_number=6,
        replace_scan=False,
        digital_title="Ὠδὴ θ΄ · Μεγαλύνει ἡ ψυχή μου · Ἡ Τιμιωτέρα · ἦχος πλ. α΄ · Κωνσταντίνου Παπαγιάννη (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
    ),
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "papline-tim-pl2-private-draft",
        semantic_context="timiotera",
        expected_context_tone=6,
        match_number=6,
        replace_scan=False,
        digital_title="Ὠδὴ θ΄ · Μεγαλύνει ἡ ψυχή μου · Ἡ Τιμιωτέρα · ἦχος πλ. β΄ · Κωνσταντίνου Παπαγιάννη (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
    ),
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "papline-tim-varys-private-draft",
        semantic_context="timiotera",
        expected_context_tone=7,
        match_number=6,
        replace_scan=False,
        digital_title="Ὠδὴ θ΄ · Μεγαλύνει ἡ ψυχή μου · Ἡ Τιμιωτέρα · ἦχος βαρύς · Κωνσταντίνου Παπαγιάννη (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
    ),
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "papline-tim-pl4ga-private-draft",
        semantic_context="timiotera",
        expected_context_tone=8,
        match_number=6,
        replace_scan=False,
        digital_title="Ὠδὴ θ΄ · Μεγαλύνει ἡ ψυχή μου · Ἡ Τιμιωτέρα · ἦχος πλ. δ΄ (ἐκ τοῦ Γα) · Κωνσταντίνου Παπαγιάννη (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
    ),
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "papline-tim-pl4ni-private-draft",
        semantic_context="timiotera",
        expected_context_tone=8,
        match_number=6,
        replace_scan=False,
        digital_title="Ὠδὴ θ΄ · Μεγαλύνει ἡ ψυχή μου · Ἡ Τιμιωτέρα · ἦχος πλ. δ΄ (ἐκ τοῦ Νη) · Κωνσταντίνου Παπαγιάννη (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
    ),
    # Owner-approved public drafts (25 Oct 2026): unreviewed digital scores that
    # the service page labels as automatic transcriptions.  They come before the
    # scanned setting of the same piece.
    AttachmentRule(
        "orthros",
        "Τὴν Θεοτόκον καὶ Μητέρα τοῦ Φωτός, ἐν ὕμνοις τιμῶντες μεγαλύνωμεν.",
        "papline-katavasies-theotokos-lambadarios-private-draft",
        required_text=("Καταβασίες Τῆς Θεοτόκου", "νοίξω τὸ στόμα μου"),
        weekdays=(6,),
        insert_before=True,
        digital_title="Καταβασίες Θεοτόκου · Ἀνοίξω τὸ στόμα μου · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
    # The short katavasies of the whole year, generated from the catalogue
    # registry. They keep the ode order of the data file and come before the
    # scanned Cross/Theotokos settings, which stay authoritative.
    *_generated_katavasies_rules(),
    AttachmentRule(
        "orthros",
        "ἐκ λύκων λυμαινομένων αὐτήν.",
        "papline-doxastikon-eothinon11-lambadarios-private-draft",
        required_text=("Σίμωνι δέδωκας τὴν τῶν προβάτων νομήν",),
        weekdays=(6,),
        digital_title="Ἑωθινὸν Δοξαστικὸν ια΄ · Φανερῶν σεαυτὸν · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
    AttachmentRule(
        "orthros",
        "αράτεινον τὸ ἔλεός σου τοὶς γινώσκουσί σε.",
        "papline-doxologia-manuel1-pl1-private-draft",
        weekly_tone=5,
        weekdays=(6,),
        digital_title="Μεγάλη Δοξολογία, ἦχος πλ. α΄ · Μανουὴλ Πρωτοψάλτου (ψηφιακή)",
    ),
    AttachmentRule(
        "orthros",
        "Τὴν Θεοτόκον καὶ Μητέρα τοῦ Φωτός, ἐν ὕμνοις τιμῶντες μεγαλύνωμεν.",
        "theotokos-katavasies-tone4",
        required_text=(
            "Καταβασίες Τῆς Θεοτόκου",
            # Melodos separates the decorated initial alpha into its own span.
            "νοίξω τὸ στόμα μου",
        ),
        # The complete score must precede the invitation to the Timiotera,
        # after the eighth ode and before the ninth ode.
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "Τὴν Θεοτόκον καὶ Μητέρα τοῦ Φωτός, ἐν ὕμνοις τιμῶντες μεγαλύνωμεν.",
        "cross-katavasies",
        required_text=(
            "Καταβασίες τῆς Ὑψώσεως τοῦ Τιμίου Σταυροῦ",
            # The decorated initial sigma is a separate span in Melodos.
            "ταυρὸν χαράξας Μωσῆς",
        ),
        # The scan contains the complete set of katavasies.  Keep it before
        # the hymn which introduces the Timiotera.  This is the liturgical
        # boundary used by Melodos, not merely the first later occurrence of
        # the word «Τιμιωτέρα».
        insert_before=True,
    ),
    # A few feast-day documents explicitly say that the Timiotera is omitted.
    # Keep the Katavasies before that replacement boundary without weakening
    # the normal, more precise anchor above.
    AttachmentRule(
        "orthros",
        "ἡ Τιμιωτέρα",
        "cross-katavasies",
        required_text=(
            "Καταβασίες τῆς Ὑψώσεως τοῦ Τιμίου Σταυροῦ",
            "ταυρὸν χαράξας Μωσῆς",
        ),
        excluded_text_any=("Τὴν Θεοτόκον καὶ Μητέρα τοῦ Φωτός",),
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "Κύριε δόξα σοι.",
        "eothinon-6",
        # The conclusion itself also occurs in the Kathismata.  Require the
        # actual Melodos heading and make it precede the matched conclusion.
        required_text=("ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ ΣΤ",),
        preceding_text="ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ ΣΤ",
    ),
    AttachmentRule(
        "orthros",
        "ἀνυμνοῦμέν σε τὸν ζωοδότην Χριστόν.",
        "eothinon-7",
        required_text=("ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ Ζ",),
        preceding_text="ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ Ζ",
    ),
    AttachmentRule(
        "orthros",
        "πρὸς ἑαυτὸν τὰ θαυμάσια.",
        "eothinon-4",
    ),
    AttachmentRule(
        "orthros",
        "ὁ οὕτως εὐδοκήσας, δόξα σοι.",
        "ypereulogimeni-tone2",
        # Melodos splits the decorated initial «Ὑ» into its own span, but its
        # preceding rubrical note remains a stable, unbroken identifier.
        required_text_any=("Υπερευλογημένη ψάλλεται πάντοτε", "Ὑπερευλογημένη ψάλλεται πάντοτε"),
    ),
    AttachmentRule(
        "orthros",
        "ότε ἀνοίσουσιν ἐπὶ τὸ θυσιαστήριόν σου μόσχους.",
        "psalm-50-tone2",
        required_text=("Οι Χοροί, ψάλλουν σε ήχο β΄ τον Ν΄ Ψαλμόν, κατ’ αντιφωνίαν",),
    ),
    AttachmentRule(
        "orthros",
        "Σήμερον σωτηρία τῷ κόσμῳ γέγονεν.",
        "tone6-great-doxology",
        # The Great Doxology can take the local Doxastikon's tone even when
        # the weekly tone is different (for example 28 September 2026).
        # Trust Melodos' explicit Doxology instruction, not the week's tone.
        required_text=("Ἦχος πλ β΄",),
        required_text_any=_TONE6_DOXOLOGY_INSTRUCTIONS,
        # The Great Doxology belongs immediately before the resurrectional
        # dismissal hymn, never at the opening Trisagion.
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "αράτεινον τὸ ἔλεός σου τοὶς γινώσκουσί σε.",
        "plagal4-great-doxology",
        # This marker is added only when Melodos explicitly says that the
        # Doxology takes the preceding Doxastikon's local plagal-fourth tone.
        # It avoids using the weekly tone or an unrelated feast tone.
        required_text=("Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος πλ. δ΄",),
        preceding_text="Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος πλ. δ΄",
    ),
    AttachmentRule(
        "orthros",
        "αράτεινον τὸ ἔλεός σου τοὶς γινώσκουσί σε.",
        "tone1-great-doxology",
        # The selector immediately before the heading is parsed from
        # Melodos' own Doxology directory (``70 doxologies/1``).  Require its
        # reconstructed local label rather than guessing from the weekday.
        required_text=("Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος α΄",),
        preceding_text="Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος α΄",
    ),
    AttachmentRule(
        "orthros",
        "αράτεινον τὸ ἔλεός σου τοὶς γινώσκουσί σε.",
        "tone2-great-doxology",
        # This local selector takes precedence over the distinct plagal-sixth
        # tone of the Holy-Fathers Doxastikon earlier in the Ainoi.
        required_text=("Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος β΄",),
        preceding_text="Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος β΄",
    ),
    AttachmentRule(
        "orthros",
        "αράτεινον τὸ ἔλεός σου τοὶς γινώσκουσί σε.",
        "papline-doxologia-manuel1-tone4-private-draft",
        # Sunday only; the tone comes from Melodos' own Doxology selector,
        # exactly as for the scanned first- and second-tone settings.
        required_text=("Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος δ΄",),
        preceding_text="Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος δ΄",
        weekdays=(6,),
        digital_title="Μεγάλη Δοξολογία, ἦχος δ΄ · Μανουὴλ Πρωτοψάλτου (ψηφιακή)",
    ),
    # Compatibility for a shortened source extract which contains the
    # Doxology but not its following resurrectional dismissal hymn.
    AttachmentRule(
        "orthros",
        "γιος ὁ Θεός, Ἅγιος Ἰσχυρός, Ἅγιος Ἀθάνατος, ἐλέησον ἡμᾶς.",
        "tone6-great-doxology",
        required_text=("Ἦχος πλ β΄",),
        required_text_any=_TONE6_DOXOLOGY_INSTRUCTIONS,
        excluded_text_any=("Σήμερον σωτηρία τῷ κόσμῳ γέγονεν.",),
        preceding_text="ἐν τῷ φωτί σου ὀψόμεθα φῶς.",
    ),
    AttachmentRule(
        "orthros",
        "καὶ καταργήσας τὸν θάνατον, ἐδωρήσατο ἡμῖν ζωὴν τὴν αἰώνιον.",
        "kypseli-08-apolytikion",
        month_days=((9, 8), (9, 9)),
    ),
    AttachmentRule(
        "orthros",
        "πρὸς σωτηρίαν τῶν ψυχῶν ἡμῶν.",
        "kypseli-08-doxastikon",
        month_days=((9, 8),),
    ),
    AttachmentRule(
        "orthros",
        "Ἡμεῖς δὲ δοξολογοῦντες βοῶμεν· Δόξα ἐν ὑψίστοις Θεῷ, καὶ ἐπὶ γῆς εἰρήνη, ἐν ἀνθρώποις εὐδοκία.",
        "kypseli-09-doxastikon",
        month_days=((9, 9),),
    ),
    AttachmentRule(
        "litourgia",
        "ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.",
        "tone6-apolytikion",
        occurrences="all",
    ),
    AttachmentRule(
        "litourgia",
        "καὶ καταργήσας τὸν θάνατον, ἐδωρήσατο ἡμῖν ζωὴν τὴν αἰώνιον.",
        "kypseli-08-apolytikion",
        month_days=((9, 8), (9, 9)),
    ),
    AttachmentRule(
        "litourgia",
        "Ἡ στεῖρα τίκτει τὴν Θεοτόκον, καὶ τροφὸν τῆς ζωῆς ἡμῶν.",
        "kypseli-08-kontakion",
        month_days=((9, 8), (9, 9)),
    ),
    AttachmentRule(
        "litourgia",
        "Κύριε, ἐλέησον.",
        "litourgia-kyrie-eleison-pandekti",
        # The first Kyrie is the opening response and is independent of the
        # weekly tone.  The post-Cheroubikon responses have their own rule.
    ),
    AttachmentRule(
        "litourgia",
        "Δεῦτε προσκυνήσωμεν καὶ προσπέσωμεν Χριστῷ.",
        "litourgia-eisodikon-pandekti",
    ),
    AttachmentRule(
        "litourgia",
        "Ἅγιος ὁ Θεός, ἅγιος ἰσχυρός, ἅγιος ἀθάνατος, ἐλέησον ἡμᾶς.",
        "litourgia-trisagion-argon-pandekti",
        match_number=3,
        following_text="Δύναμις",
    ),
    AttachmentRule(
        "litourgia",
        "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες",
        "litourgia-cherouvikon-pandekti",
        required_text_any=(
            "ψάλλονται σε ήχο δ΄ άγια",
        ),
    ),
    AttachmentRule(
        "litourgia",
        "Σὲ ὑμνοῦμεν, σὲ εὐλογοῦμεν, σοὶ εὐχαριστοῦμεν, Κύριε, καὶ δεόμεθά σου, ὁ Θεὸς ἡμῶν.",
        "litourgia-amin-se-ymnoumen-pandekti",
        required_text_any=(
            "ψάλλονται σε ήχο δ΄ άγια",
        ),
    ),
    AttachmentRule(
        "litourgia",
        "Ποτήριον σωτηρίου λήψομαι, καὶ τὸ ὄνομα Κυρίου ἐπικαλέσομαι.",
        "litourgia-koinonikon-pandekti",
        required_text_any=(
            "ψάλλονται σε ήχο δ΄ άγια",
        ),
    ),
    AttachmentRule(
        "litourgia",
        "Ταῖς πρεσβείαις τῆς Θεοτόκου, Σῶτερ, σῶσον ἡμᾶς.",
        "litourgia-tais-presveiais-pandekti",
        # The first Antiphon has four refrains.  The musical page belongs
        # after the final refrain, following «Δόξα... Καὶ νῦν...», not after
        # the first refrain following the alpha verse.
        nearest_preceding_text="Δόξα... Καὶ νῦν...",
    ),
    # Keep a single-refrain excerpt usable in partial source documents (for
    # example, an intentionally shortened test or imported bulletin).  A
    # complete Antiphon always has its «Δόξα... Καὶ νῦν...» marker and uses
    # the rule above instead.
    AttachmentRule(
        "litourgia",
        "Ταῖς πρεσβείαις τῆς Θεοτόκου, Σῶτερ, σῶσον ἡμᾶς.",
        "litourgia-tais-presveiais-pandekti",
        excluded_text_any=("Δόξα... Καὶ νῦν...",),
    ),
    AttachmentRule(
        "litourgia",
        "Ταῖς πρεσβείαις τῆς Θεοτόκου...",
        "litourgia-tais-presveiais-pandekti",
        # Weekday documents abbreviate the repeated final refrain. Its score
        # still follows the completed A Antiphon, just as it does on Sunday.
        nearest_preceding_text="Δόξα... Καὶ νῦν...",
        exact_after_text="Ταῖς πρεσβείαις τῆς Θεοτόκου...",
    ),
    AttachmentRule(
        "litourgia",
        "Δόξα... Καὶ νῦν...",
        "litourgia-soson-yie-pandekti",
        # The second occurrence closes Antiphon B, after its beta and gamma
        # verses and their «Σῶσον ἡμᾶς» refrains.
        required_text=("Σῶσον ἡμᾶς Υἱὲ Θεοῦ",),
        match_number=2,
    ),
    AttachmentRule(
        "litourgia",
        "Σῶσον ἡμᾶς Υἱὲ Θεοῦ, ὁ ἐν Ἁγίοις θαυμαστός ψάλλοντάς σοι, Ἀλληλούϊα.",
        "litourgia-soson-yie-pandekti",
        excluded_text_any=("Δόξα... Καὶ νῦν...",),
    ),
    AttachmentRule(
        "litourgia",
        "Σῶσον ἡμᾶς Υἱὲ Θεοῦ, ὁ ἀναστὰς ἐκ νεκρῶν ψάλλοντάς σοι, Ἀλληλούϊα.",
        "litourgia-soson-yie-pandekti",
        excluded_text_any=("Δόξα... Καὶ νῦν...",),
    ),
    AttachmentRule(
        "litourgia",
        "Καὶ νῦν...",
        "litourgia-soson-yie-pandekti",
        # On weekdays Melodos supplies the saints' refrain for Antiphon B
        # and abbreviates the closing as «Καὶ νῦν...».  Retain the same
        # requested score placement before the Monogenes.
        required_text=("Πρεσβείαις τῶν ἁγίων σου",),
        match_number=2,
        following_text="Ὁ Μονογενὴς Υἱὸς καὶ Λόγος",
    ),
    AttachmentRule(
        "litourgia",
        "Μονογενὴς Υἱὸς καὶ Λόγος",
        "litourgia-monogenis-pandekti",
    ),
    AttachmentRule(
        "litourgia",
        "Πατέρα, Υἱὸν καὶ Ἅγιον Πνεῦμα, Τριάδα ὁμοούσιον καὶ ἀχώριστον.",
        "litourgia-patera-pandekti",
    ),
    AttachmentRule(
        "litourgia",
        "Ἀγαπήσω σε, Κύριε, ἡ ἰσχύς μου",
        "litourgia-agapiso-pandekti",
        # The existing D΄-volume scan is the fourth-tone agia setting.  Do
        # not display it on a day whose Melodos note selects another tone;
        # those days use the matching setting from the tone-specific scan.
        required_text_any=("ψάλλονται σε ήχο δ΄ άγια",),
    ),
    AttachmentRule(
        "litourgia",
        "Παράσχου Κύριε.",
        "litourgia-tone-4-kyrie-paraschou",
        required_text_any=("ψάλλονται σε ήχο δ΄ άγια",),
        preceding_text="Χριστιανὰ τὰ τέλη τῆς ζωῆς ἡμῶν",
    ),
    AttachmentRule(
        "litourgia",
        "Πληρωθήτω τὸ στόμα ἡμῶν αἰνέσεως Κύριε",
        "litourgia-plirothito-melodos",
    ),
    AttachmentRule(
        "litourgia",
        "Εἴη τὸ ὄνομα Κυρίου εὐλογημένον ἀπὸ τοῦ νῦν καὶ ἕως τοῦ αἰῶνος",
        "litourgia-eie-to-onoma-pandekti",
    ),
)


_TONE_REQUIREMENTS: Final[dict[int, tuple[str, ...]]] = {
    1: ("ψάλλονται σε ήχο α΄", "ψάλλονται στον κύριο ήχο της ημέρας, ήχο α΄"),
    2: ("ψάλλονται σε ήχο β΄", "ψάλλονται στον κύριο ήχο της ημέρας, ήχο β΄"),
    3: ("ψάλλονται σε ήχο γ΄", "ψάλλονται στον κύριο ήχο της ημέρας, ήχο γ΄"),
    # A simple fourth-tone day uses the compact fourth-tone scan below.  The
    # feast-day «δ΄ ἅγια» note is intentionally excluded: it has its own
    # verified settings in the D΄ volume and must not receive both variants.
    4: ("ψάλλονται σε ήχο δ΄", "ψάλλονται στον κύριο ήχο της ημέρας, ήχο δ΄"),
    5: (
        "ψάλλονται σε ήχο πλ α΄",
        "ψάλλονται στον πλ α΄",
        "ήχο της εβδομάδος  πλ α΄",
        "ψάλλονται στον κύριο ήχο της ημέρας, ήχο πλ α΄",
    ),
    6: ("ψάλλονται σε ήχο πλ β΄", "ήχο πλ β΄", "ψάλλονται στον κύριο ήχο της ημέρας, ήχο πλ β΄"),
    7: (
        "ψάλλονται σε ήχο βαρύ",
        "κύριο ήχο της ημέρας, ήχο βαρύ",
    ),
    8: (
        "ψάλλονται σε ήχο πλ δ΄",
        # Sunday 27 September 2026: Melodos spells the same instruction as
        # «στον κύριο ήχο της ημέρας, ήχο πλ δ΄».
        "ψάλλονται στον κύριο ήχο της ημέρας, ήχο πλ δ΄",
    ),
}

# Sunday Orthros is not an appendix: the resurrectional Kathismata,
# Anavathmoi and the first and third odes belong at their actual places in
# the order of service.  The following clips were checked in the 1905 scan.
# They deliberately stop before the next heading, so a neighbouring hymn is
# never presented as part of the selected one.
_ORTHROS_TONE_LABELS: Final[dict[int, str]] = {
    1: "α΄", 2: "β΄", 3: "γ΄", 4: "δ΄", 5: "πλ. α΄", 6: "πλ. β΄", 7: "βαρύς", 8: "πλ. δ΄",
}
_ORTHROS_TONE_CONTEXT: Final[dict[int, tuple[str, ...]]] = {
    1: ("Ήχος εβδομάδος α΄",),
    2: ("Ήχος εβδομάδος β΄",),
    3: ("Ήχος εβδομάδος γ΄",),
    4: ("Ήχος εβδομάδος δ΄",),
    5: ("Ήχος εβδομάδος πλ α΄",),
    6: ("Ήχος εβδομάδος πλ β΄",),
    7: ("Ήχος εβδομάδος βαρύς",),
    8: ("Ήχος εβδομάδος πλ δ΄",),
}
_ORTHROS_ANAVATHMOI_CONTEXT: Final[dict[int, tuple[str, ...]]] = {
    1: ("Οἱ Ἀναβαθμοὶ Ἦχος α΄",),
    2: ("Οἱ Ἀναβαθμοὶ Ἦχος β΄",),
    3: ("Οἱ Ἀναβαθμοὶ Ἦχος γ΄",),
    4: ("Οἱ Ἀναβαθμοὶ Ἦχος δ΄",),
    5: ("Οἱ Ἀναβαθμοὶ Ἦχος πλ α΄",),
    6: ("Οἱ Ἀναβαθμοὶ Ἦχος πλ β΄",),
    7: ("Οἱ Ἀναβαθμοὶ Ἦχος βαρύς",),
    8: ("Οἱ Ἀναβαθμοὶ Ἦχος πλ δ΄",),
}

# (Kathismata, Anavathmoi, Ode 1, Ode 3).  The sixth tone retains the tighter
# hand-checked clips above, which also give the two Kathismata separate titles.
_ORTHROS_TONE_REGIONS: Final[dict[int, tuple[tuple[ScanRegion, ...], ...]]] = {
    1: (
        (_region(16, .48), _region(17), _region(18, .02, .58)),
        (_region(22, .78), _region(23), _region(24, .02, .42)),
        (_region(25, .18), _region(26, .02, .76)),
        # Ode 3 begins on printed p. 24 and completes before Ode 4 on p. 25.
        # The former p. 25–26 crop was the following Ode 4, not Ode 3.
        (_region(26, .37), _region(27, .02, .54)),
    ),
    2: (
        (_region(68, .42), _region(69), _region(70, .02, .72)),
        # The Anavathmoi begin halfway down printed p. 69. Keep all three
        # antiphons and stop before the Prokeimenon.
        (_region(71, .56), _region(72), _region(73, .02, .70)),
        # Ode 1 starts on printed p. 72 and ends just before Ode 3 on p. 73.
        (_region(74, .24), _region(75, .02, .64)),
        # Ode 3 begins at the foot of printed p. 73 and ends before Ode 5.
        (_region(75, .64), _region(76, .02, .86)),
    ),
    3: (
        (_region(115, .36), _region(116), _region(117, .02, .72)),
        (_region(120, .18), _region(121), _region(122, .02, .42)),
        (_region(124, .14), _region(125, .02, .34)),
        (_region(125, .72), _region(126, .02, .76)),
    ),
    4: (
        (_region(175, .34), _region(176), _region(177, .02, .70)),
        (_region(178, .46), _region(179), _region(180, .02, .34)),
        (_region(180, .74), _region(181, .02, .76)),
        (_region(182, .34), _region(183, .02, .76)),
    ),
    5: (
        (_region(227, .30), _region(228), _region(229, .02, .70)),
        (_region(230, .22), _region(231), _region(232, .02, .30)),
        (_region(232, .28), _region(233, .02, .76)),
        (_region(235, .16), _region(236, .02, .76)),
    ),
    7: (
        (_region(335, .30), _region(336), _region(337, .02, .66)),
        (_region(337, .60), _region(338), _region(339, .02, .40)),
        (_region(340, .30), _region(341, .02, .76)),
        (_region(345, .64), _region(346, .02, .76)),
    ),
    8: (
        # Include both Sunday Kathismata.  The old crop began with the
        # second one and lost the opening music of «Τὴν Σοφίαν καὶ Λόγον».
        (_region(398, .10), _region(399), _region(400), _region(401, .02, .57)),
        # The first antiphon begins at the foot of printed p. 399.  Starting
        # from p. 400 cut its first three melodic phrases; retain all four
        # antiphons and stop before the Canon on printed p. 403.
        (_region(401, .57), _region(402), _region(403), _region(404)),
        # Keep the heading and the opening Heirmos «Ἁρματηλάτην Φαραώ».
        (_region(405, .08), _region(406, .02, .76)),
        # The third Ode begins under its own heading on printed p. 405 and
        # its Theotokion ends at the top of p. 407, before Ode 5 begins.
        # Do not crop its opening phrases as the old .62 crop did.
        (_region(407, .24), _region(408), _region(409, .02, .20)),
    ),
}

for _tone, _groups in _ORTHROS_TONE_REGIONS.items():
    for _kind, _title, _incipit, _regions in zip(
        ("kathismata", "anavathmoi", "canon-ode-1", "canon-ode-3"),
        (
            f"Καθίσματα Κυριακῆς · ἦχος {_ORTHROS_TONE_LABELS[_tone]}",
            f"Οἱ Ἀναβαθμοί · ἦχος {_ORTHROS_TONE_LABELS[_tone]}",
            f"Ἀναστάσιμος Κανών · ᾨδὴ α΄ · ἦχος {_ORTHROS_TONE_LABELS[_tone]}",
            f"Ἀναστάσιμος Κανών · ᾨδὴ γ΄ · ἦχος {_ORTHROS_TONE_LABELS[_tone]}",
        ),
        ("Καθίσματα", "Οἱ Ἀναβαθμοί", "Ὠδὴ α΄", "Ὠδὴ γ΄"),
        _groups,
    ):
        PIECES[f"tone{_tone}-{_kind}"] = MusicPiece(
            f"tone{_tone}-{_kind}", _title, _incipit, _regions
        )

_LITOURGIA_SANCTUS: Final[str] = (
    "Ἅγιος, ἅγιος, ἅγιος Κύριος Σαβαώθ· πλήρης ὁ οὐρανὸς καὶ ἡ γῆ "
    "τῆς δόξης σου, ὡσαννὰ ἐν τοῖς ὑψίστοις. Εὐλογημένος ὁ ἐρχόμενος "
    "ἐν ὀνόματι Κυρίου. Ὡσαννὰ ὁ ἐν τοῖς ὑψίστοις."
)

_LITOURGIA_AXION_ESTIN: Final[str] = (
    "Ἄξιόν ἐστιν ὡς ἀληθῶς μακαρίζειν σε τὴν Θεοτόκον, τὴν "
    "ἀειμακάριστον καὶ παναμώμητον καὶ μητέρα τοῦ Θεοῦ ἡμῶν. Τὴν "
    "τιμιωτέραν τῶν Χερουβεὶμ καὶ ἐνδοξοτέραν ἀσυγκρίτως τῶν Σεραφείμ· "
    "τὴν ἀδιαφθόρως Θεὸν Λόγον τεκοῦσαν, τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν."
)

_TONE_ATTACHMENT_RULES: list[AttachmentRule] = []
for _tone, _requirements in _TONE_REQUIREMENTS.items():
    _TONE_ATTACHMENT_RULES.extend(
        (
            AttachmentRule(
                "litourgia",
                "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες",
                f"litourgia-tone-{_tone}-cherouvikon",
                required_text_any=_requirements,
                excluded_text_any=("ψάλλονται σε ήχο δ΄ άγια",) if _tone == 4 else (),
            ),
            AttachmentRule(
                "litourgia",
                "Παράσχου Κύριε.",
                f"litourgia-tone-{_tone}-kyrie-paraschou",
                required_text_any=_requirements,
                excluded_text_any=("ψάλλονται σε ήχο δ΄ άγια",) if _tone == 4 else (),
                preceding_text="Χριστιανὰ τὰ τέλη τῆς ζωῆς ἡμῶν",
            ),
            AttachmentRule(
                "litourgia",
                "Σὲ ὑμνοῦμεν, σὲ εὐλογοῦμεν, σοὶ εὐχαριστοῦμεν, Κύριε, καὶ δεόμεθά σου, ὁ Θεὸς ἡμῶν",
                f"litourgia-tone-{_tone}-amin-se-ymnoumen",
                required_text_any=_requirements,
                excluded_text_any=("ψάλλονται σε ήχο δ΄ άγια",) if _tone == 4 else (),
            ),
            AttachmentRule(
                "litourgia",
                _LITOURGIA_AXION_ESTIN,
                f"litourgia-tone-{_tone}-axion-estin",
                required_text_any=_requirements,
                excluded_text_any=("ψάλλονται σε ήχο δ΄ άγια",) if _tone == 4 else (),
            ),
            AttachmentRule(
                "litourgia",
                _LITOURGIA_SANCTUS,
                f"litourgia-tone-{_tone}-axion-kai-dikaion",
                required_text_any=_requirements,
                excluded_text_any=("ψάλλονται σε ήχο δ΄ άγια",) if _tone == 4 else (),
            ),
            AttachmentRule(
                "litourgia",
                "Αἰνεῖτε τὸν Κύριον ἐκ τῶν οὐρανῶν",
                f"litourgia-tone-{_tone}-koinonikon",
                required_text_any=_requirements,
                excluded_text_any=("ψάλλονται σε ήχο δ΄ άγια",) if _tone == 4 else (),
                # This is the Sunday Koinonikon.  The same phrase also occurs
                # in Melodos' weekday Gospel/Alleluia instructions, so the
                # weekday gate prevents a Sunday setting from leaking into a
                # Monday–Saturday service.
                weekdays=(6,),
                preceding_text="Τῇ Κυριακῇ ψάλλεται το Κοινωνικόν",
            ),
        )
    )

# The daily-cycle socials are kept in the same D΄ volume, with their printed
# headings checked against the day named by Melodos.  They complement the
# Sunday «Αἰνεῖτε» setting in each tone-specific scan above.
PIECES.update(
    {
        "litourgia-koinonikon-thursday-pandekti": MusicPiece(
            "litourgia-koinonikon-thursday-pandekti",
            "Κοινωνικὸν Πέμπτης · ἦχος πλ. δ΄ · Εἰς πᾶσαν τὴν γῆν",
            "Εἰς πᾶσαν τὴν γῆν ἐξῆλθεν ὁ φθόγγος αὐτῶν",
            (ScanRegion(348, 348), ScanRegion(349, 349), ScanRegion(350, 350)),
            book_id=PANDEKTI_LITOURGIA_BOOK_ID,
        ),
        "litourgia-koinonikon-friday-pandekti": MusicPiece(
            "litourgia-koinonikon-friday-pandekti",
            "Κοινωνικὸν Παρασκευῆς · ἦχος πλ. α΄ · Σωτηρίαν εἰργάσω",
            "Σωτηρίαν εἰργάσω ἐν μέσῳ τῆς γῆς",
            (ScanRegion(354, 354), ScanRegion(355, 355)),
            book_id=PANDEKTI_LITOURGIA_BOOK_ID,
        ),
        "litourgia-tone4-meta-pneumatos": MusicPiece(
            "litourgia-tone4-meta-pneumatos",
            "Καὶ μετὰ τοῦ πνεύματός σου · ἦχος δ΄ · Μελωδός",
            "Καὶ μετὰ τοῦ πνεύματός σου",
            (ScanRegion(7, 7, (0.02, 0.02, 0.98, 0.62)),),
            book_id="melodos-liturgy-tone-4",
        ),
        "litourgia-axion-tone4-pandekti": MusicPiece(
            "litourgia-axion-tone4-pandekti",
            "Ἄξιον καὶ δίκαιον · ἦχος δ΄ · Μελωδός",
            "Ἄξιον καὶ δίκαιον",
            # The response appears at the foot of the fourth-tone setting;
            # retain the complete musical line rather than cutting its neumes.
            (ScanRegion(7, 7, (0.02, 0.66, 0.98, 0.98)),),
            book_id="melodos-liturgy-tone-4",
        ),
    }
)

# This verified anthology supplies the Tuesday/saints Koinonikon in every
# tone.  Select the setting from Melodos' own recommendation for that day.
_MNIMOSYNON_PAGES: Final[dict[int, tuple[int, ...]]] = {
    1: (4, 5, 6, 7),
    2: (13, 14, 15, 16),
    3: (28, 29, 30, 31, 32),
    4: (47, 48, 49, 50),
    5: (62, 63, 64, 65),
    6: (72, 73, 74, 75),
    7: (84, 85, 86),
    8: (97, 98, 99),
}
for _tone, _pages in _MNIMOSYNON_PAGES.items():
    PIECES[f"litourgia-tone-{_tone}-eis-mnimosynon"] = MusicPiece(
        f"litourgia-tone-{_tone}-eis-mnimosynon",
        f"Κοινωνικὸν · Εἰς μνημόσυνον αἰώνιον · ἦχος {_TONE_LABEL_TEXT[_tone]}",
        "Εἰς μνημόσυνον αἰώνιον ἔσται δίκαιος",
        _tone_scan_regions(_pages),
        book_id=KOINONIKA_ALL_TONES_BOOK_ID,
    )
    _TONE_ATTACHMENT_RULES.append(
        AttachmentRule(
            "litourgia",
            "Εἰς μνημόσυνον αἰώνιον ἔσται Δίκαιος",
            f"litourgia-tone-{_tone}-eis-mnimosynon",
            required_text_any=_TONE_REQUIREMENTS[_tone],
            excluded_text_any=("ψάλλονται σε ήχο δ΄ άγια",) if _tone == 4 else (),
            preceding_text="Το κοινωνικὸν συνήθως ψάλλεται",
        )
    )
_TONE_ATTACHMENT_RULES.extend(
    (
        AttachmentRule(
            "litourgia",
            "Εἰς πᾶσαν τὴν γῆν ἐξῆλθεν ὁ φθόγγος αὐτῶν",
            "litourgia-koinonikon-thursday-pandekti",
            required_text_any=("ψάλλονται σε ήχο πλ δ΄",),
            preceding_text="Το κοινωνικὸν συνήθως ψάλλεται",
        ),
        AttachmentRule(
            "litourgia",
            "Σωτηρίαν εἰργάσω ἐν μέσῳ τῆς γῆς",
            "litourgia-koinonikon-friday-pandekti",
            required_text_any=("ψάλλονται σε ήχο πλ α΄",),
            preceding_text="Το κοινωνικὸν συνήθως ψάλλεται",
        ),
        AttachmentRule(
            "litourgia",
            "Καὶ μετὰ τοῦ πνεύματός σου",
            "litourgia-tone4-meta-pneumatos",
            required_text_any=("ψάλλονται σε ήχο δ΄ άγια",),
        ),
        AttachmentRule(
            "litourgia",
            _LITOURGIA_SANCTUS,
            "litourgia-axion-tone4-pandekti",
            required_text_any=("ψάλλονται σε ήχο δ΄ άγια",),
        ),
    )
)

# These rules are intentionally tied to headings supplied by Melodos.  Thus a
# weekday set of Anavathmoi uses its own declared tone, while the Sunday-only
# material additionally requires the resurrectional markers in that day's
# Orthros.
_ORTHROS_TONE_ATTACHMENT_RULES: list[AttachmentRule] = []
for _tone, _context in _ORTHROS_TONE_CONTEXT.items():
    if _tone == 6:
        # The pilot clips above use their precise closing incipits and retain
        # the two sixth-tone Kathismata as separate excerpts.
        continue
    _ode_one_anchor = "ΩΔΗ Α΄ ΚΑΝΟΝΩΝ"
    _ode_one_before = True
    _ode_three_anchor = "ΩΔΗ Γ΄ ΚΑΝΟΝΩΝ"
    _ode_three_before = True
    _ode_one_match_number = 1
    _ode_three_match_number = 1
    _kathismata_anchor = "Καθίσματα Ἀναστάσιμα"
    _kathismata_before = False
    if _tone == 2:
        # On the Holy-Fathers Sunday Melodos prints the two resurrectional
        # Kathismata and then the Theotokion before the Evlogitaria. The score
        # belongs after their final text, not below the initial heading.
        _kathismata_anchor = "τῶ λαῶ σου παράσχου τὸ μέγα ἔλεος."
        # Each resurrectional Ode is followed by the Fathers' Canon. Put the
        # score at that boundary, after the Ode's complete text.
        _ode_one_anchor = "Ὁ Κανὼν τῶν Ἁγίων Πατέρων."
        _ode_three_anchor = "Ὁ Κανὼν τῶν Ἁγίων Πατέρων."
        _ode_three_match_number = 2
    if _tone == 8:
        # In the plagal-fourth Sunday source, Melodos puts the full
        # resurrectional first ode before the feast-day Canon.  Attach the
        # score after that final resurrectional troparion, not before its
        # heading, so «Ἁρματηλάτην Φαραώ» remains visible first.
        _ode_one_anchor = "τὴν μετὰ Θεὸν προστασίαν ἡμῶν."
        _ode_one_before = False
        # The next explicit heading is the feast Canon.  Put the complete
        # resurrectional third-Ode score immediately before it, rather than
        # before the opening heading of Ode 3.
        _ode_three_anchor = "Κανόνας τοῦ Ἁγίου Καλλιστράτου."
        _ode_three_before = True
    _ORTHROS_TONE_ATTACHMENT_RULES.extend(
        (
            AttachmentRule(
                "orthros",
                _kathismata_anchor,
                f"tone{_tone}-kathismata",
                weekly_tone=_tone,
                # Use the completed matching text. Tone 2 has a dedicated
                # final-text boundary above; other tones retain their heading.
                required_text=("Ἐν συνεχεία ψάλλονται τά Ἀναστάσιμα εὐλογητάρια.",),
                insert_before=_kathismata_before,
            ),
            AttachmentRule(
                "orthros",
                "Προκείμενον",
                f"tone{_tone}-anavathmoi",
                weekly_tone=_tone,
                # A weekday may have the same weekly tone and a Prokeimenon,
                # but no resurrectional Anavathmoi.  The Sunday marker from
                # Melodos is therefore required before adding this scan.
                required_text=("Ἐν συνεχεία ψάλλονται τά Ἀναστάσιμα εὐλογητάρια.",),
                insert_before=True,
            ),
            AttachmentRule(
                "orthros",
                _ode_one_anchor,
                f"tone{_tone}-canon-ode-1",
                weekly_tone=_tone,
                required_text=("Κανὼν Ἀναστάσιμος",),
                match_number=_ode_one_match_number,
                insert_before=_ode_one_before,
            ),
            AttachmentRule(
                "orthros",
                _ode_three_anchor,
                f"tone{_tone}-canon-ode-3",
                weekly_tone=_tone,
                required_text=("Κανὼν Ἀναστάσιμος",),
                match_number=_ode_three_match_number,
                insert_before=_ode_three_before,
            ),
        )
    )

PILOT_RULES += tuple(_TONE_ATTACHMENT_RULES + _ORTHROS_TONE_ATTACHMENT_RULES)

# Sunday Liturgy digital drafts (25 Oct 2026).  They are applied after the scanned
# tone rules, so each digital score sits above the scanned setting of its piece.
PILOT_RULES += (
    AttachmentRule(
        "litourgia",
        "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες",
        "papline-cherubikon-lambadarios-pl1-private-draft",
        weekly_tone=5,
        weekdays=(6,),
        digital_title="Χερουβικόν, ἦχος πλ. α΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
    AttachmentRule(
        "litourgia",
        "Αἰνεῖτε τὸν Κύριον ἐκ τῶν οὐρανῶν",
        "papline-koinonikon-aineite-lambadarios1-pl1-private-draft",
        weekly_tone=5,
        weekdays=(6,),
        preceding_text="Τῇ Κυριακῇ ψάλλεται το Κοινωνικόν",
        digital_title="Κοινωνικόν «Αἰνεῖτε», ἦχος πλ. α΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
)

# The Trisagion after the Eisodikon is always sung in tone 2, whatever the
# weekly tone (owner, 2026-11-01).  Both settings are digital, so the scanned
# Pandekti Trisagion (tone 4) is replaced.  The later rule is placed first.
PILOT_RULES += tuple(
    AttachmentRule(
        "litourgia",
        "Ἅγιος ὁ Θεός, ἅγιος ἰσχυρός, ἅγιος ἀθάνατος, ἐλέησον ἡμᾶς.",
        _score_id,
        match_number=3,
        following_text="Δύναμις",
        digital_title=_title,
    )
    for _score_id, _title in (
        ("papline-trisagion-progakis-tone2-private-draft", "Τρισάγιος ὕμνος · σύντομος, ἦχος β΄ · Γεωργίου Πρωγάκη (ψηφιακή)"),
        ("papline-trisagion-klasika-tone2-private-draft", "Τρισάγιος ὕμνος · ἀργός (κλασικά), ἦχος β΄ (ψηφιακή)"),
    )
)

# Weekday Liturgy digital drafts (27-31 Oct 2026).  On plain weekdays the Great
# Church practice puts the Cherubikon and the Koinonikon in the tone that
# Melodos names in the day's own instruction, so each rule is keyed on that
# sentence and on the weekday, not on the weekly tone.
_CHERUBIKON_ANCHOR = "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες"
_WEEKDAY_LITURGY_DRAFTS = (
    # (python weekday, Melodos sentence naming the tone, Cherubikon id, Cherubikon title)
    (1, "απλή Τρίτη, ψάλλονται σε ήχο βαρύ", "papline-cherubikon-lambadarios-varys-private-draft",
     "Χερουβικόν, ἦχος βαρύς · Πέτρου Λαμπαδαρίου (ψηφιακή)"),
    (2, "απλή Τετάρτη, ψάλλονται σε ήχο δ΄ άγια", "papline-cherubikon-lambadarios-tone4-private-draft",
     "Χερουβικόν, ἦχος δ΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)"),
    (3, "απλή Πέμπτη, ψάλλονται σε ήχο πλ δ΄", "papline-cherubikon-lambadarios-pl4-private-draft",
     "Χερουβικόν, ἦχος πλ. δ΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)"),
    (4, "απλή Παρασκευή, ψάλλονται σε ήχο πλ α΄", "papline-cherubikon-lambadarios-pl1-private-draft",
     "Χερουβικόν, ἦχος πλ. α΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)"),
    (5, "απλό Σάββατο, ψάλλονται στον πλ α΄", "papline-cherubikon-lambadarios-pl1-private-draft",
     "Χερουβικόν, ἦχος πλ. α΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)"),
)
PILOT_RULES += tuple(
    AttachmentRule(
        "litourgia",
        _CHERUBIKON_ANCHOR,
        _piece,
        weekdays=(_weekday,),
        required_text=(_sentence,),
        digital_title=_title,
    )
    for _weekday, _sentence, _piece, _title in _WEEKDAY_LITURGY_DRAFTS
)
PILOT_RULES += tuple(
    AttachmentRule(
        "litourgia",
        "Ὁ ὑψωθεὶς ἐν τῷ Σταυρῷ ἑκουσίως",
        "papline-kontakion-stavrou-prigos-tone4-private-draft",
        weekdays=(_weekday,),
        required_text=(_sentence,),
        digital_title="Κοντάκιον Σταυροῦ «Ὁ ὑψωθείς», ἦχος δ΄ · Κωνσταντίνου Πρίγγου (ψηφιακή)",
    )
    for _weekday, _sentence in (
        (2, "απλή Τετάρτη, ψάλλονται σε ήχο δ΄ άγια"),
        (4, "απλή Παρασκευή, ψάλλονται σε ήχο πλ α΄"),
    )
)
PILOT_RULES += (
    AttachmentRule(
        "litourgia",
        "Ἀγαλλιᾶσθε",
        "papline-koinonikon-agalliasthe-tsiknopoulos-tone1-private-draft",
        weekdays=(0,),
        required_text=("απλή Δευτέρα, ψάλλονται σε ήχο α΄",),
        preceding_text="Κοινωνικόν της εορτής της ημέρας",
        digital_title="Κοινωνικόν «Ἀγαλλιᾶσθε δίκαιοι», ἦχος α΄ · Ἀνδρέου Τσικνοπούλου (ψηφιακή)",
    ),
)
# Liturgy digital scores by tone.  On a day whose local Melodos instruction
# selects that tone they replace the scanned setting of the same hymn at the
# very same anchor, so every other tone keeps its existing behaviour.
_LITURGY_DIGITAL_DRAFTS: Final[dict[int, tuple[tuple[str, str, str, str | None], ...]]] = {
    1: (
        (
            "Παράσχου Κύριε.",
            "papline-lit1-kyrie-parashou-private-draft",
            "Κύριε ἐλέησον καὶ Παράσχου Κύριε · ἦχος α΄ · Βασιλείου Νικολαΐδου (ψηφιακή)",
            "Χριστιανὰ τὰ τέλη τῆς ζωῆς ἡμῶν",
        ),
        (
            "Πατέρα, Υἱὸν καὶ Ἅγιον Πνεῦμα, Τριάδα ὁμοούσιον καὶ ἀχώριστον.",
            "papline-lit1-patera-private-draft",
            "Πατέρα, Υἱὸν καὶ Ἅγιον Πνεῦμα · ἦχος α΄ · Βασιλείου Νικολαΐδου (ψηφιακή)",
            None,
        ),
        (
            _LITOURGIA_SANCTUS,
            "papline-lit1-axion-dikaion-private-draft",
            "Ἄξιον καὶ δίκαιον · ἦχος α΄ · Βασιλείου Νικολαΐδου (ψηφιακή)",
            None,
        ),
        (
            "Σὲ ὑμνοῦμεν, σὲ εὐλογοῦμεν, σοὶ εὐχαριστοῦμεν, Κύριε, καὶ δεόμεθά σου, ὁ Θεὸς ἡμῶν",
            "papline-lit1-se-ymnoumen-private-draft",
            "Ἀμήν… Σὲ ὑμνοῦμεν · ἦχος α΄ · Βασιλείου Νικολαΐδου (ψηφιακή)",
            None,
        ),
        (
            _LITOURGIA_AXION_ESTIN,
            "papline-lit1-axion-estin-private-draft",
            "Ἄξιόν ἐστιν · ἦχος α΄ · Γρηγορίου Πρωτοψάλτου (ψηφιακή)",
            None,
        ),
    ),
    2: (
        (
            "Παράσχου Κύριε.",
            "papline-lit2-kyrie-parashou-private-draft",
            "Κύριε ἐλέησον καὶ Παράσχου Κύριε · ἦχος β΄ · Βασιλείου Νικολαΐδου (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
            "Χριστιανὰ τὰ τέλη τῆς ζωῆς ἡμῶν",
        ),
        (
            "Πατέρα, Υἱὸν καὶ Ἅγιον Πνεῦμα, Τριάδα ὁμοούσιον καὶ ἀχώριστον.",
            "papline-lit2-patera-private-draft",
            "Πατέρα, Υἱὸν καὶ Ἅγιον Πνεῦμα · ἦχος β΄ · Βασιλείου Νικολαΐδου (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
            None,
        ),
        (
            _LITOURGIA_SANCTUS,
            "papline-lit2-axion-dikaion-private-draft",
            "Ἄξιον καὶ δίκαιον · ἦχος β΄ · Βασιλείου Νικολαΐδου (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
            None,
        ),
        (
            "Σὲ ὑμνοῦμεν, σὲ εὐλογοῦμεν, σοὶ εὐχαριστοῦμεν, Κύριε, καὶ δεόμεθά σου, ὁ Θεὸς ἡμῶν",
            "papline-lit2-se-ymnoumen-private-draft",
            "Ἀμήν… Σὲ ὑμνοῦμεν · ἦχος β΄ · Βασιλείου Νικολαΐδου (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
            None,
        ),
        (
            _LITOURGIA_AXION_ESTIN,
            "papline-lit2-axion-estin-private-draft",
            "Ἄξιόν ἐστιν · ἦχος β΄ · Γρηγορίου Πρωτοψάλτου (ψηφιακή) · πρόχειρη αυτόματη μεταγραφή",
            None,
        ),
    ),
}
PILOT_RULES += tuple(
    AttachmentRule(
        "litourgia",
        _anchor,
        _score_id,
        required_text_any=_TONE_REQUIREMENTS[_tone],
        preceding_text=_preceding,
        digital_title=_title,
    )
    for _tone, _drafts in _LITURGY_DIGITAL_DRAFTS.items()
    for _anchor, _score_id, _title, _preceding in _drafts
)
# Fixed Monogenes (Lambadarios, Pandekti 1851) and the Axion Estin in the tone of
# the day's Leitourgika.  Both sit beside the scanned settings of the same piece.
PILOT_RULES += (
    AttachmentRule(
        "litourgia",
        "Μονογενὴς Υἱὸς καὶ Λόγος",
        "papline-monogenis-lambadarios-tone2-private-draft",
        digital_title="Ὁ Μονογενής, ἦχος β΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
    AttachmentRule(
        "litourgia",
        _LITOURGIA_AXION_ESTIN,
        "papline-axion-estin-nikolaidis-varys-private-draft",
        weekdays=(1,),
        required_text=("απλή Τρίτη, ψάλλονται σε ήχο βαρύ",),
        digital_title="Ἄξιόν ἐστιν, ἦχος βαρύς · Βασιλείου Νικολαΐδου (ψηφιακή)",
    ),
    AttachmentRule(
        "litourgia",
        _LITOURGIA_AXION_ESTIN,
        "papline-axion-estin-patriarchal-pl1-private-draft",
        weekly_tone=5,
        weekdays=(6,),
        digital_title="Ἄξιόν ἐστιν, ἦχος πλ. α΄ · Τὸ Πατριαρχικόν (ψηφιακή)",
    ),
)
PILOT_RULES += tuple(
    AttachmentRule(
        "litourgia",
        _LITOURGIA_AXION_ESTIN,
        "papline-axion-estin-patriarchal-pl1-private-draft",
        weekdays=(_weekday,),
        required_text=(_sentence,),
        digital_title="Ἄξιόν ἐστιν, ἦχος πλ. α΄ · Τὸ Πατριαρχικόν (ψηφιακή)",
    )
    for _weekday, _sentence in (
        (4, "απλή Παρασκευή, ψάλλονται σε ήχο πλ α΄"),
        (5, "απλό Σάββατο, ψάλλονται στον πλ α΄"),
    )
)
PILOT_RULES += (
    AttachmentRule(
        "litourgia",
        "Τοὺς ἀσφαλεῖς καὶ θεοφθόγγους κήρυκας",
        "papline-kontakion-apostolon-papachristou-tone2-private-draft",
        weekdays=(3,),
        required_text=("απλή Πέμπτη, ψάλλονται σε ήχο πλ δ΄",),
        digital_title="Κοντάκιον Ἀποστόλων «Τοὺς ἀσφαλεῖς», ἦχος β΄ (ψηφιακή)",
    ),
)
PILOT_RULES += (
    AttachmentRule(
        "litourgia",
        "Ἀγαλλιᾶσθε",
        "papline-koinonikon-agalliasthe-protopsaltes-varys-private-draft",
        weekdays=(1,),
        required_text=("απλή Τρίτη, ψάλλονται σε ήχο βαρύ",),
        preceding_text="Κοινωνικόν της εορτής της ημέρας",
        digital_title="Κοινωνικόν «Ἀγαλλιᾶσθε δίκαιοι», ἦχος βαρύς · Κωνσταντίνου Πρωτοψάλτου (ψηφιακή)",
    ),
    AttachmentRule(
        "litourgia",
        "Ποτήριον σωτηρίου λήψομαι",
        "papline-koinonikon-potirion-lambadarios-tone4-private-draft",
        weekdays=(2,),
        required_text=("απλή Τετάρτη, ψάλλονται σε ήχο δ΄ άγια",),
        preceding_text="Τῇ Τετάρτῃ, εις το πάθος του Κυρίου",
        digital_title="Κοινωνικόν «Ποτήριον σωτηρίου», ἦχος δ΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
    AttachmentRule(
        "litourgia",
        "Εἰς πᾶσαν τὴν γῆν ἐξῆλθεν",
        "papline-koinonikon-eis-pasan-lambadarios-pl4-private-draft",
        weekdays=(3,),
        required_text=("απλή Πέμπτη, ψάλλονται σε ήχο πλ δ΄",),
        preceding_text="Τῇ Πέμπτῃ, τῶν ἀποστόλων",
        digital_title="Κοινωνικόν «Εἰς πᾶσαν τὴν γῆν», ἦχος πλ. δ΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
    AttachmentRule(
        "litourgia",
        "Σωτηρίαν εἰργάσω ἐν μέσῳ τῆς γῆς",
        "papline-koinonikon-soterian-lambadarios-pl1-private-draft",
        weekdays=(4,),
        required_text=("απλή Παρασκευή, ψάλλονται σε ήχο πλ α΄",),
        preceding_text="Τῇ Παρασκευῇ,",
        digital_title="Κοινωνικόν «Σωτηρίαν εἰργάσω», ἦχος πλ. α΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
    AttachmentRule(
        "litourgia",
        "Μακάριοι",
        "papline-koinonikon-makarioi-lambadarios-pl1-private-draft",
        weekdays=(5,),
        required_text=("απλό Σάββατο, ψάλλονται στον πλ α΄",),
        preceding_text="Τῷ Σαββάτῳ με Αλληλούια",
        digital_title="Κοινωνικόν «Μακάριοι οὓς ἐξελέξω», ἦχος πλ. α΄ · Πέτρου Λαμπαδαρίου (ψηφιακή)",
    ),
)


def catalog_pieces() -> tuple[MusicPiece, ...]:
    piece_ids = dict.fromkeys(rule.piece_id for rule in PILOT_RULES if rule.digital_title is None)
    return tuple(PIECES[piece_id] for piece_id in piece_ids)


def catalog_books() -> tuple[MusicBook, ...]:
    book_ids = dict.fromkeys(piece.book_id for piece in catalog_pieces())
    return tuple(BOOKS[book_id] for book_id in book_ids)


def get_piece(book_id: str, piece_id: str) -> MusicPiece:
    if piece_id not in PIECES or PIECES[piece_id].book_id != book_id:
        raise KeyError(f"Άγνωστο μουσικό τεκμήριο: {book_id}/{piece_id}")
    return PIECES[piece_id]


def _weekly_tone_from_document(normalized_document: str) -> int | None:
    """Read the current weekly tone from Melodos' own heading."""
    # `casefold()` normalizes final sigmas to σ.
    marker = "ηχοσ εβδομαδοσ"
    start = normalized_document.find(marker)
    if start < 0:
        return None
    value = normalized_document[start + len(marker) : start + len(marker) + 48]
    if "πλ α" in value:
        return 5
    if "πλ β" in value:
        return 6
    if "βαρυ" in value:
        return 7
    if "πλ δ" in value:
        return 8
    for letter, tone in (("α", 1), ("β", 2), ("γ", 3), ("δ", 4)):
        if value.lstrip().startswith(letter):
            return tone
    return None


def _explicit_tone_from_local_text(normalized_text: str) -> int | None:
    """Parse one explicitly printed tone label, never a weekly-tone heading."""
    value = normalized_text.strip()
    if "πλ α" in value:
        return 5
    if "πλ β" in value:
        return 6
    if "βαρυ" in value:
        return 7
    if "πλ δ" in value:
        return 8
    for letter, tone in (("α", 1), ("β", 2), ("γ", 3), ("δ", 4)):
        if value.startswith(letter):
            return tone
    return None


def _semantic_context_tone(context: str, preceding_text: str) -> int | None:
    """Interpret a Melodos instruction in the local liturgical block.

    A member's score is chosen only from the instruction which introduces
    that member.  This deliberately differs from a document-wide phrase
    match: a preceding hymn may have a different tone on the same day.
    """
    if context != "timiotera":
        return None

    instruction = "και ψαλλεται η τιμιωτερα στον ιδιο ηχο"
    start = preceding_text.rfind(instruction)
    if start < 0:
        return None

    # Melodos prints either «...των καταβασιών. Ἦχος ...» or
    # «...του Ειρμού. Ἦχος ...».  Restrict interpretation to this small
    # instruction block, ending before the first Timiotera refrain.
    block = preceding_text[start : start + 180]
    label_start = block.find("ηχοσ")
    # The label belongs to the instruction itself; do not borrow a tone from
    # a later hymn if an incomplete instruction happens to precede it.
    if label_start < 0 or label_start > 96:
        return None
    return _explicit_tone_from_local_text(block[label_start + len("ηχοσ") :])


def _semantic_context_block(context: str, preceding_text: str) -> str | None:
    """Return just the local instruction which determines a member's score."""
    if context != "timiotera":
        return None
    marker = "και ψαλλεται η τιμιωτερα στον ιδιο ηχο"
    start = preceding_text.rfind(marker)
    return preceding_text[start : start + 180] if start >= 0 else None


def _bookmark_id(piece: MusicPiece, instance: int) -> str:
    return f"music-{piece.piece_id}-{instance}"


def _music_markup(piece: MusicPiece, instance: int) -> str:
    book = BOOKS[piece.book_id]
    bookmark_id = _bookmark_id(piece, instance)
    bookmark_label = f"Σελιδοδείκτης · {piece.title}"
    pages = ", ".join(str(region.printed_page) for region in piece.regions)
    figures = []
    for index, region in enumerate(piece.regions, start=1):
        # Relative URLs work both at / locally and behind the public /kihem/ prefix.
        # Include the source region in the URL so a corrected scan cannot be
        # hidden by a browser's old 24-hour image cache.
        version = "-".join(str(round(value * 1000)) for value in region.clip)
        url = f"music/{piece.book_id}/{piece.piece_id}/{index}.png?v=p{region.pdf_page}-{version}"
        figures.append(
            '<figure class="music-page">'
            f'<a href="{url}" target="_blank" title="Άνοιγμα σε πλήρες μέγεθος">'
            f'<img src="{url}" loading="lazy" '
            f'alt="{html.escape(piece.title)} — έντυπη σελίδα {region.printed_page}">'
            "</a>"
            f"<figcaption>έντυπη σελ. {region.printed_page}</figcaption>"
            "</figure>"
        )
    return (
        f'<aside id="{bookmark_id}" class="music-attachment" '
        f'data-music-piece="{html.escape(piece.piece_id)}" '
        f'data-music-instance="{instance}">'
        '<div class="music-attachment-heading">'
        f'<a class="music-bookmark" href="#{bookmark_id}" '
        f'title="Μόνιμος σύνδεσμος προς αυτό το μουσικό απόσπασμα">'
        f'🔖 {html.escape(bookmark_label)}</a>'
        '<span class="music-match-label">Μουσικό κείμενο που αντιστοιχίστηκε</span>'
        f"<h3>{html.escape(piece.title)}</h3>"
        f"<p>{html.escape(book.title)} · σελ. {pages}</p>"
        "</div>"
        f'<div class="music-pages">{"".join(figures)}</div>'
        '<p class="music-source">'
        f'<a href="{book.source_page}" target="_blank" rel="noreferrer">{html.escape(book.details)}</a>'
        f" · {html.escape(book.attribution)}"
        "</p>"
        "</aside>"
    )


def _digital_music_markup(rule: AttachmentRule, instance: int, *, unreviewed: bool = False) -> str:
    score_id = rule.piece_id
    title = rule.digital_title or score_id
    bookmark_id = f"music-{score_id}-{instance}"
    # Relative, like the scanned excerpts, so it works below the /kihem/ prefix.
    url = f"digital-scores/{score_id}/"
    return (
        f'<aside id="{bookmark_id}" class="music-attachment" '
        f'data-music-piece="{html.escape(score_id)}" '
        f'data-music-instance="{instance}">'
        '<div class="music-attachment-heading">'
        f'<a class="music-bookmark" href="#{bookmark_id}" '
        'title="Μόνιμος σύνδεσμος προς αυτό το μουσικό απόσπασμα">'
        f'🔖 Σελιδοδείκτης · {html.escape(title)}</a>'
        f"<h3>{html.escape(title)}</h3>"
        "</div>"
        f'<iframe class="digital-score-frame" src="{url}" loading="lazy" '
        f'title="{html.escape(title)}" '
        'style="width:100%;height:640px;border:1px solid #ccc;border-radius:6px"></iframe>'
        '<p class="music-source">'
        f'<a href="{url}" target="_blank" rel="noreferrer">Άνοιγμα σε νέα καρτέλα</a>'
        " · Πηγή: papline.gr"
        + (" · αυτόματη μεταγραφή, δεν έχει ελεγχθεί από ψάλτη" if unreviewed else "")
        + "</p>"
        "</aside>"
    )


def _insertion_point(text_node: NavigableString) -> NavigableString | Tag:
    point: NavigableString | Tag = text_node
    # Melodos places the complete service in one #div1.  Lifting a text node
    # to that container would append every score to the end of the service;
    # lift only a small inline wrapper that contains this one text fragment.
    if (
        isinstance(text_node.parent, Tag)
        and text_node.parent.name not in {"[document]", "body"}
        and len(list(text_node.parent.stripped_strings)) == 1
    ):
        point = text_node.parent
    sibling = point.next_sibling
    while isinstance(sibling, NavigableString) and not str(sibling).strip():
        sibling = sibling.next_sibling
    if isinstance(sibling, Tag) and sibling.name == "br":
        point = sibling
    return point


def _insertion_point_before(text_node: NavigableString) -> NavigableString | Tag:
    point: NavigableString | Tag = text_node
    if (
        isinstance(text_node.parent, Tag)
        and text_node.parent.name not in {"[document]", "body"}
        and len(list(text_node.parent.stripped_strings)) == 1
    ):
        point = text_node.parent
    return point


def enrich_service_html(
    selected_date: date,
    service: str,
    service_html: str,
    *,
    instance_offset: int = 0,
    semantic_reviewer: "TypesafeDecisionService | None" = None,
    verified_digital_scores: Collection[str] = (),
    unreviewed_digital_scores: Collection[str] = (),
) -> EnrichmentResult:
    """Attach verified book matches based on the actual text returned by Melodos.

    ``verified_digital_scores`` lists every digital score that may be shown (verified
    ones and owner-approved public drafts); ``unreviewed_digital_scores`` is the subset
    that has no psaltis review and gets a label.
    """
    rules = tuple(rule for rule in PILOT_RULES if rule.service == service)
    soup = BeautifulSoup(service_html, "html.parser")
    attachment_count = 0
    unmatched: list[str] = []
    bookmarks: list[MusicBookmark] = []
    # (anchor text node, inserted aside, is_digital, replaces_scan): a digital
    # score normally replaces the scanned setting attached to the same hymn
    # (owner, 2026-10-30), unless the rule says the scan must stay.
    placed: list[tuple[object, Tag, bool, bool]] = []
    normalized_document = _normalized(soup.get_text(" ", strip=True))
    weekly_tone = _weekly_tone_from_document(normalized_document)
    # The many generated katavasies rules all scan the same text nodes. Cache
    # each node's normalized form so a matching rule does not re-normalize the
    # whole document; the value depends only on the immutable node text.
    normalized_nodes: dict[int, str] = {}

    def _normalized_node(node: NavigableString) -> str:
        key = id(node)
        value = normalized_nodes.get(key)
        if value is None:
            value = _normalized(str(node))
            normalized_nodes[key] = value
        return value

    for rule in rules:
        if rule.digital_title is not None:
            if rule.piece_id not in verified_digital_scores:
                continue
            piece = None
        else:
            piece = PIECES[rule.piece_id]
        # Date-scoped books (currently the Menaia) are intentionally strict:
        # every attachment must carry an exact month/day entry. This keeps a
        # feast's musical pages from leaking into an ordinary weekday or from
        # being guessed from the preceding/following day.
        if piece is not None and piece.book_id in DATE_SCOPED_BOOK_IDS and not rule.month_days:
            continue
        if rule.month_days and (selected_date.month, selected_date.day) not in rule.month_days:
            continue
        if rule.weekdays and selected_date.weekday() not in rule.weekdays:
            continue
        if rule.weekly_tone is not None and weekly_tone != rule.weekly_tone:
            continue
        needle = _normalized(rule.after_text)
        required_scope = normalized_document
        if rule.required_after_any:
            marker_positions = [
                normalized_document.find(_normalized(marker))
                for marker in rule.required_after_any
            ]
            marker_positions = [position for position in marker_positions if position >= 0]
            if marker_positions:
                required_scope = normalized_document[min(marker_positions) :]
        if any(_normalized(required) not in required_scope for required in rule.required_text):
            continue
        if rule.required_text_groups and not all(
            any(_normalized(variant) in required_scope for variant in group)
            for group in rule.required_text_groups
        ):
            continue
        if rule.excluded_text_any and any(
            _normalized(excluded) in normalized_document for excluded in rule.excluded_text_any
        ):
            continue
        if rule.required_text_any and not any(
            _normalized(required) in normalized_document for required in rule.required_text_any
        ):
            continue
        text_nodes = list(soup.find_all(string=True))
        matches = []
        for node_index, node in enumerate(text_nodes):
            if needle not in _normalized_node(node):
                continue
            if rule.exact_after_text and str(node).strip() != rule.exact_after_text.strip():
                continue
            if isinstance(node.parent, Tag) and node.parent.find_parent("aside"):
                continue
            preceding = ""
            if rule.preceding_text or rule.semantic_context:
                preceding = _normalized(" ".join(str(item) for item in text_nodes[:node_index]))
            if rule.preceding_text:
                if _normalized(rule.preceding_text) not in preceding:
                    continue
            if rule.semantic_context:
                # The same refrain occurs six times.  Only its selected
                # occurrence is a candidate for attachment, so review that
                # one instead of needlessly reading the same cached decision
                # for every refrain.
                is_selected_occurrence = (
                    rule.occurrences != "first" or len(matches) == rule.match_number - 1
                )
                if rule.semantic_context == "timiotera":
                    local_tone = _semantic_context_tone(rule.semantic_context, preceding)
                    if local_tone != rule.expected_context_tone:
                        continue
                    if not semantic_reviewer or not is_selected_occurrence:
                        pass
                    else:
                        instruction = _semantic_context_block(rule.semantic_context, preceding)
                        expected_choice = {
                            "plagal4-timiotera": "plagal4_timiotera",
                            "tone4-timiotera": "tone4_timiotera",
                        }.get(rule.piece_id)
                        # The TypeSafe reviewer only knows the two scanned
                        # alternatives. Digital rules (and any future member)
                        # are intentionally not vetoed by this lookup.
                        decision = (
                            semantic_reviewer.review_timiotera(instruction or "")
                            if instruction and expected_choice is not None
                            else None
                        )
                        # Jev can only confirm the explicit local instruction;
                        # it cannot invent a third score. An unavailable API
                        # leaves the deterministic Melodos instruction in
                        # force, while a high-confidence disagreement blocks
                        # an unsafe insertion.
                        if (
                            expected_choice is not None
                            and decision is not None
                            and decision.confidence >= 0.95
                            and decision.choice != expected_choice
                        ):
                            logger.warning(
                                "TypeSafe rejected %s for %s (choice=%s, confidence=%.3f)",
                                rule.piece_id,
                                rule.semantic_context,
                                decision.choice,
                                decision.confidence,
                            )
                            continue
                elif (
                    semantic_reviewer
                    and rule.semantic_context == "ainoi"
                    and is_selected_occurrence
                ):
                    # The Sunday Ainoi form is a stable rule from the
                    # verified Anastasimatario: a/b/plagal-a/plagal-b are
                    # slow; c/d/grave/plagal-d are short. Jev sees exactly
                    # this closed choice and can only veto a doubtful match.
                    decision = semantic_reviewer.review_ainoi_style(
                        weekly_tone=weekly_tone,
                        local_heading=_normalized(str(node)),
                    )
                    if (
                        decision is not None
                        and decision.confidence >= 0.95
                        and decision.choice != rule.expected_reviewer_choice
                    ):
                        logger.warning(
                            "TypeSafe rejected %s for Sunday Ainoi (choice=%s, confidence=%.3f)",
                            rule.piece_id,
                            decision.choice,
                            decision.confidence,
                        )
                        continue
            if rule.nearest_preceding_text:
                preceding_nodes = (
                    _normalized(str(item)) for item in reversed(text_nodes[:node_index])
                )
                nearest_preceding = next((item for item in preceding_nodes if item), "")
                if _normalized(rule.nearest_preceding_text) not in nearest_preceding:
                    continue
            if rule.following_text:
                following = _normalized(" ".join(str(item) for item in text_nodes[node_index + 1 :]))
                if _normalized(rule.following_text) not in following:
                    continue
            matches.append(node)
        if rule.occurrences == "first":
            match_index = rule.match_number - 1
            matches = matches[match_index : match_index + 1]
        if not matches:
            unmatched.append(rule.piece_id)
            continue

        for text_node in matches:
            attachment_count += 1
            instance = instance_offset + attachment_count
            markup = (
                _digital_music_markup(rule, instance, unreviewed=rule.piece_id in unreviewed_digital_scores)
                if piece is None
                else _music_markup(piece, instance)
            )
            fragment = BeautifulSoup(markup, "html.parser").aside
            if fragment is None:
                continue
            if rule.insert_before:
                _insertion_point_before(text_node).insert_before(fragment)
            else:
                _insertion_point(text_node).insert_after(fragment)
            placed.append((text_node, fragment, piece is None, rule.replace_scan))
            if piece is None:
                bookmarks.append(MusicBookmark(f"music-{rule.piece_id}-{instance}", rule.digital_title or rule.piece_id))
            else:
                bookmarks.append(MusicBookmark(_bookmark_id(piece, instance), piece.title))

    digital_nodes = {
        id(node) for node, _, digital, replaces_scan in placed if digital and replaces_scan
    }
    for node, aside, digital, _ in placed:
        if not digital and id(node) in digital_nodes:
            aside.decompose()

    # Rules are maintained by source/matching concerns, not by the order in
    # which a particular service prints its hymns.  Re-read the inserted
    # anchors from the finished document so the bookmark menu follows the same
    # top-to-bottom order as the attached excerpts.
    bookmarks_by_id = {bookmark.anchor_id: bookmark for bookmark in bookmarks}
    ordered_bookmarks = tuple(
        bookmarks_by_id[aside["id"]]
        for aside in soup.find_all("aside", class_="music-attachment")
        if aside.get("id") in bookmarks_by_id
    )
    return EnrichmentResult(str(soup), attachment_count, tuple(unmatched), ordered_bookmarks)


class AnastasimatarionRenderer:
    """Render verified regions from the server's persistent local book library."""

    _download_lock = threading.Lock()

    def __init__(
        self,
        cache_dir: str | Path = "/tmp/kihem-cache",
        books_dir: str | Path | None = None,
        session=None,
    ):
        self.cache_dir = Path(cache_dir) / "music"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.books_dir = Path(books_dir or os.environ.get("KIHEM_BOOKS_DIR", "/var/lib/kihem/books"))
        self.pdf_paths = {
            BOOK_ID: Path(
                os.environ.get(
                    "KIHEM_ANASTASIMATARION_PDF",
                    self.books_dir / BOOKS[BOOK_ID].local_filename,
                )
            ),
            PANDEKTI_BOOK_ID: Path(
                os.environ.get(
                    "KIHEM_PANDEKTI_PDF",
                    self.books_dir / BOOKS[PANDEKTI_BOOK_ID].local_filename,
                )
            ),
            IRMOLOGION_BOOK_ID: Path(
                os.environ.get(
                    "KIHEM_IRMOLOGION_PDF",
                    self.books_dir / BOOKS[IRMOLOGION_BOOK_ID].local_filename,
                )
            ),
            PANDEKTI_LITOURGIA_BOOK_ID: self.books_dir / BOOKS[PANDEKTI_LITOURGIA_BOOK_ID].local_filename,
            KYPSELI_BOOK_ID: self.books_dir / BOOKS[KYPSELI_BOOK_ID].local_filename,
        }
        # Tone-specific Melodos scans are registered in the catalogue above;
        # keep their persistent paths in the same renderer map so they are
        # downloaded lazily on the first requested excerpt.
        for book_id, book in BOOKS.items():
            self.pdf_paths.setdefault(book_id, self.books_dir / book.local_filename)
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "Kihem/0.3 (+personal liturgical reading tool)"})

    def render(self, book_id: str, piece_id: str, part: int) -> Path:
        piece = get_piece(book_id, piece_id)
        if part < 1 or part > len(piece.regions):
            raise KeyError(f"Άγνωστο μέρος μουσικού τεκμηρίου: {piece_id}/{part}")
        region = piece.regions[part - 1]
        clip_key = "-".join(str(round(value * 1000)) for value in region.clip)
        output = self.cache_dir / (
            f"{book_id}-{piece.piece_id}-{part}-p{region.pdf_page}-{clip_key}.png"
        )
        if output.exists():
            return output

        book = BOOKS[book_id]
        pdf_path = self.pdf_paths[book_id]
        self._ensure_pdf(book, pdf_path)
        document = pymupdf.open(pdf_path)
        try:
            if document.page_count < region.pdf_page:
                raise RuntimeError(f"Το PDF «{book.title}» δεν περιέχει την αναμενόμενη σελίδα.")
            page = document.load_page(region.pdf_page - 1)
            x0, y0, x1, y1 = region.clip
            clip = pymupdf.Rect(
                page.rect.width * x0,
                page.rect.height * y0,
                page.rect.width * x1,
                page.rect.height * y1,
            )
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0), clip=clip, alpha=False)
            pixmap.save(output)
        finally:
            document.close()
        return output

    def _ensure_pdf(self, book: MusicBook, pdf_path: Path) -> None:
        if self._valid_pdf(pdf_path, book.minimum_pdf_pages):
            return
        if not book.download_url:
            raise RuntimeError(f"Λείπει το τοπικό μουσικό βιβλίο: {pdf_path}")
        with self._download_lock:
            if self._valid_pdf(pdf_path, book.minimum_pdf_pages):
                return
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = pdf_path.with_suffix(".download")
            try:
                with self.session.get(book.download_url, stream=True, timeout=(10, 180)) as response:
                    response.raise_for_status()
                    with temporary.open("wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                handle.write(chunk)
                if not self._valid_pdf(temporary, book.minimum_pdf_pages):
                    raise RuntimeError(f"Η λήψη του βιβλίου «{book.title}» δεν είναι έγκυρο PDF.")
                temporary.replace(pdf_path)
            finally:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _valid_pdf(path: Path, minimum_pages: int) -> bool:
        if not path.exists() or path.stat().st_size < 10_000:
            return False
        try:
            document = pymupdf.open(path)
            valid = document.page_count >= minimum_pages
            document.close()
            return valid
        except Exception:
            return False
