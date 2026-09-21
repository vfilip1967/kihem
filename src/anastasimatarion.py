from __future__ import annotations

import html
import os
import threading
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final, Literal

import pymupdf
import requests
from bs4 import BeautifulSoup, NavigableString, Tag


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
    excluded_text_any: tuple[str, ...] = ()
    weekdays: tuple[int, ...] = ()
    month_days: tuple[tuple[int, int], ...] = ()
    match_number: int = 1
    preceding_text: str | None = None
    following_text: str | None = None
    insert_before: bool = False


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
    "tone6-ainoi-first-four": MusicPiece(
        "tone6-ainoi-first-four",
        "Αἶνοι · τὰ τέσσερα ἀναστάσιμα στιχηρά",
        "Ὁ Σταυρός σου Κύριε",
        (
            _region(300, 0.43),
            _region(301),
            _region(302),
            _region(303, 0.02, 0.53),
        ),
    ),
    "eothinon-4": MusicPiece(
        "eothinon-4",
        "Δοξαστικὸν Ἑωθινὸν Δ΄",
        "Ὄρθρος ἦν βαθύς",
        (_region(200, 0.82), _region(201), _region(202, 0.02, 0.45)),
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
    "litourgia-trisagion-pandekti": MusicPiece(
        "litourgia-trisagion-pandekti",
        "Τρισάγιος ὕμνος · σύντομον · Μουσικὴ Πανδέκτη",
        "Ἅγιος ὁ Θεός, ἅγιος ἰσχυρός, ἅγιος ἀθάνατος",
        # The former page 29 was an unrelated troparion.  Page 45 contains
        # the complete first short Trisagion, immediately before the Dynamis.
        (ScanRegion(45, 45, (0.02, 0.30, 0.98, 0.67)),),
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
        (15, 16),
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

_TONE_AMIN_PAGES: Final[dict[int, tuple[int, ...]]] = {
    1: (12,),
    2: (10,),
    3: (8, 9),
    4: (8, 9),
    5: (11, 12),
    6: (9,),
    7: (9,),
    8: (11, 12),
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
        _tone_scan_regions(_TONE_AMIN_PAGES[_tone]),
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


PILOT_RULES: Final[tuple[AttachmentRule, ...]] = (
    AttachmentRule(
        "orthros",
        "ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.",
        "tone6-apolytikion",
    ),
    AttachmentRule(
        "orthros",
        "ὁ ἐν νεκροῖς καὶ τοὺς νεκροὺς ἀναστήσας δόξα σοί.",
        "tone6-kathismata-a",
    ),
    AttachmentRule(
        "orthros",
        "Χριστὲ ὁ Θεὸς ἡμῶν, φωτίσας τοὺς ἐν σκότει.",
        "tone6-kathismata-b",
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
    ),
    AttachmentRule(
        "orthros",
        "καὶ τεκοῦσα, μένεις ἀειπάρθενος.",
        "tone6-canon-ode-3",
    ),
    AttachmentRule(
        "orthros",
        "τὴν ὄντως Θεοτόκον, σὲ μεγαλύνομεν.",
        "plagal4-timiotera",
        required_text=(
            "Καὶ ψάλλεται ἡ Τιμιωτέρα στον ίδιο ήχο των καταβασιών. "
            "Ἦχος πλ δ΄ Ωδή της θεοτόκου",
        ),
        match_number=6,
    ),
    AttachmentRule(
        "orthros",
        "ἡ Τιμιωτέρα",
        "cross-katavasies",
        required_text=(
            "Καταβασίες τῆς Ὑψώσεως τοῦ Τιμίου Σταυροῦ",
            # The decorated initial sigma is a separate span in Melodos.
            "ταυρὸν χαράξας Μωσῆς",
        ),
        # The scan contains the complete set of katavasies.  Keep it before
        # the Timiotera boundary, which also places it before the ninth ode of
        # the canons when the Timiotera is not chanted on a feast day.
        insert_before=True,
    ),
    AttachmentRule(
        "orthros",
        "καὶ ἀνυμνεῖ σου τὴν Ἀνάστασιν.",
        "tone6-ainoi-first-four",
    ),
    AttachmentRule(
        "orthros",
        "πρὸς ἑαυτὸν τὰ θαυμάσια.",
        "eothinon-4",
    ),
    AttachmentRule(
        "orthros",
        "ότε ἀνοίσουσιν ἐπὶ τὸ θυσιαστήριόν σου μόσχους.",
        "psalm-50-tone2",
        required_text=("Οι Χοροί, ψάλλουν σε ήχο β΄ τον Ν΄ Ψαλμόν, κατ’ αντιφωνίαν",),
    ),
    AttachmentRule(
        "orthros",
        "γιος ὁ Θεός, Ἅγιος Ἰσχυρός, Ἅγιος Ἀθάνατος, ἐλέησον ἡμᾶς.",
        "tone6-great-doxology",
        required_text=("Ἦχος πλ β΄",),
        # The same Trisagion appears near the beginning of Orthros. The
        # preceding verse belongs to the Great Doxology close to its end.
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
        "litourgia-trisagion-pandekti",
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
    ),
    AttachmentRule(
        "litourgia",
        "Σῶσον ἡμᾶς Υἱὲ Θεοῦ, ὁ ἐν Ἁγίοις θαυμαστός ψάλλοντάς σοι, Ἀλληλούϊα.",
        "litourgia-soson-yie-pandekti",
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
    1: ("ψάλλονται σε ήχο α΄",),
    2: ("ψάλλονται σε ήχο β΄",),
    3: ("ψάλλονται σε ήχο γ΄",),
    # A simple fourth-tone day uses the compact fourth-tone scan below.  The
    # feast-day «δ΄ ἅγια» note is intentionally excluded: it has its own
    # verified settings in the D΄ volume and must not receive both variants.
    4: ("ψάλλονται σε ήχο δ΄",),
    5: (
        "ψάλλονται σε ήχο πλ α΄",
        "ψάλλονται στον πλ α΄",
        "ήχο της εβδομάδος  πλ α΄",
    ),
    6: ("ψάλλονται σε ήχο πλ β΄", "ήχο πλ β΄"),
    7: (
        "ψάλλονται σε ήχο βαρύ",
        "κύριο ήχο της ημέρας, ήχο βαρύ",
    ),
    8: ("ψάλλονται σε ήχο πλ δ΄",),
}

_LITOURGIA_SANCTUS: Final[str] = (
    "Ἅγιος, ἅγιος, ἅγιος Κύριος Σαβαώθ· πλήρης ὁ οὐρανὸς καὶ ἡ γῆ "
    "τῆς δόξης σου, ὡσαννὰ ἐν τοῖς ὑψίστοις. Εὐλογημένος ὁ ἐρχόμενος "
    "ἐν ὀνόματι Κυρίου. Ὡσαννὰ ὁ ἐν τοῖς ὑψίστοις."
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
PILOT_RULES += tuple(_TONE_ATTACHMENT_RULES)


def catalog_pieces() -> tuple[MusicPiece, ...]:
    piece_ids = dict.fromkeys(rule.piece_id for rule in PILOT_RULES)
    return tuple(PIECES[piece_id] for piece_id in piece_ids)


def catalog_books() -> tuple[MusicBook, ...]:
    book_ids = dict.fromkeys(piece.book_id for piece in catalog_pieces())
    return tuple(BOOKS[book_id] for book_id in book_ids)


def get_piece(book_id: str, piece_id: str) -> MusicPiece:
    if piece_id not in PIECES or PIECES[piece_id].book_id != book_id:
        raise KeyError(f"Άγνωστο μουσικό τεκμήριο: {book_id}/{piece_id}")
    return PIECES[piece_id]


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


def _insertion_point(text_node: NavigableString) -> NavigableString | Tag:
    point: NavigableString | Tag = text_node
    if isinstance(text_node.parent, Tag) and text_node.parent.name not in {"[document]", "body"}:
        point = text_node.parent
    sibling = point.next_sibling
    while isinstance(sibling, NavigableString) and not str(sibling).strip():
        sibling = sibling.next_sibling
    if isinstance(sibling, Tag) and sibling.name == "br":
        point = sibling
    return point


def _insertion_point_before(text_node: NavigableString) -> NavigableString | Tag:
    point: NavigableString | Tag = text_node
    if isinstance(text_node.parent, Tag) and text_node.parent.name not in {"[document]", "body"}:
        point = text_node.parent
    return point


def enrich_service_html(
    selected_date: date,
    service: str,
    service_html: str,
    *,
    instance_offset: int = 0,
) -> EnrichmentResult:
    """Attach verified book matches based on the actual text returned by Melodos."""
    rules = tuple(rule for rule in PILOT_RULES if rule.service == service)
    soup = BeautifulSoup(service_html, "html.parser")
    attachment_count = 0
    unmatched: list[str] = []
    bookmarks: list[MusicBookmark] = []

    for rule in rules:
        piece = PIECES[rule.piece_id]
        # Date-scoped books (currently the Menaia) are intentionally strict:
        # every attachment must carry an exact month/day entry. This keeps a
        # feast's musical pages from leaking into an ordinary weekday or from
        # being guessed from the preceding/following day.
        if piece.book_id in DATE_SCOPED_BOOK_IDS and not rule.month_days:
            continue
        if rule.month_days and (selected_date.month, selected_date.day) not in rule.month_days:
            continue
        if rule.weekdays and selected_date.weekday() not in rule.weekdays:
            continue
        needle = _normalized(rule.after_text)
        normalized_document = _normalized(soup.get_text(" ", strip=True))
        if any(_normalized(required) not in normalized_document for required in rule.required_text):
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
            if needle not in _normalized(str(node)):
                continue
            if isinstance(node.parent, Tag) and node.parent.find_parent("aside"):
                continue
            if rule.preceding_text:
                preceding = _normalized(" ".join(str(item) for item in text_nodes[:node_index]))
                if _normalized(rule.preceding_text) not in preceding:
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
            fragment = BeautifulSoup(_music_markup(piece, instance), "html.parser").aside
            if fragment is None:
                continue
            if rule.insert_before:
                _insertion_point_before(text_node).insert_before(fragment)
            else:
                _insertion_point(text_node).insert_after(fragment)
            bookmarks.append(MusicBookmark(_bookmark_id(piece, instance), piece.title))

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
