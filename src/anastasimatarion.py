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
        "pandekti-tomos-d-liturgy-excerpts.pdf",
        12,
        "Μελωδός · ψηφιοποιημένος Μουσικὸς Πανδέκτης Δ΄",
        "https://melodos.com/bibliothiki/wp-content/uploads/2019/09/04-%CE%9C%CE%9F%CE%A5%CE%A3%CE%99%CE%9A%CE%9F%CE%A3-%CE%A0%CE%91%CE%9D%CE%94%CE%95%CE%9A%CE%A4%CE%97%CE%A3-%CE%94%CE%84-%CE%A4%CE%9F%CE%9C%CE%9F%CE%A3-%CE%BC%CE%B5-%CE%A3%CE%B5%CE%BB-.pdf",
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
    match_number: int = 1


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
    "litourgia-eisodikon-pandekti": MusicPiece(
        "litourgia-eisodikon-pandekti",
        "Εἰσοδικόν · Μουσικὴ Πανδέκτη",
        "Δεῦτε προσκυνήσωμεν καὶ προσπέσωμεν Χριστῷ",
        (ScanRegion(1, 27),),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-trisagion-pandekti": MusicPiece(
        "litourgia-trisagion-pandekti",
        "Τρισάγιος ὕμνος · σύντομον · Μουσικὴ Πανδέκτη",
        "Ἅγιος ὁ Θεός, ἅγιος ἰσχυρός, ἅγιος ἀθάνατος",
        (ScanRegion(2, 29),),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-cherouvikon-pandekti": MusicPiece(
        "litourgia-cherouvikon-pandekti",
        "Χερουβικὸν · ἦχος δ΄ ἅγια · Πέτρου Λαμπαδαρίου",
        "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες",
        (ScanRegion(3, 95), ScanRegion(4, 96)),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-leitourgika-pandekti": MusicPiece(
        "litourgia-leitourgika-pandekti",
        "Λειτουργικά · ἦχος δ΄ ἅγια · Μουσικὴ Πανδέκτη",
        "Ἅγιος, ἅγιος, ἅγιος Κύριος Σαβαώθ",
        (
            ScanRegion(5, 270),
            ScanRegion(6, 271),
            ScanRegion(7, 272),
            ScanRegion(8, 273),
            ScanRegion(9, 274),
        ),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
    "litourgia-koinonikon-pandekti": MusicPiece(
        "litourgia-koinonikon-pandekti",
        "Κοινωνικὸν · ἦχος δ΄ ἅγια · Ποτήριον σωτηρίου",
        "Ποτήριον σωτηρίου λήψομαι",
        (ScanRegion(10, 341), ScanRegion(11, 342), ScanRegion(12, 343)),
        book_id=PANDEKTI_LITOURGIA_BOOK_ID,
    ),
}


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
        "ἣν πᾶσαι αἱ Δυνάμεις, τῶν οὐρανῶν μεγαλύνουσι.",
        "cross-katavasies",
        required_text=(
            "Καταβασίες τῆς Ὑψώσεως τοῦ Τιμίου Σταυροῦ",
            # The decorated initial sigma is a separate span in Melodos.
            "ταυρὸν χαράξας Μωσῆς",
        ),
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
    ),
    AttachmentRule(
        "litourgia",
        "ὁ ἀναστὰς ἐκ των νεκρῶν, Κύριε δόξα σοί.",
        "tone6-apolytikion",
        occurrences="all",
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
    ),
    AttachmentRule(
        "litourgia",
        "Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες",
        "litourgia-cherouvikon-pandekti",
        required_text=(
            "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, "
            "Θεομητορική εορτή, ψάλλονται σε ήχο δ΄ άγια",
        ),
    ),
    AttachmentRule(
        "litourgia",
        "Ἄξιον καὶ δίκαιον.",
        "litourgia-leitourgika-pandekti",
        required_text=(
            "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, "
            "Θεομητορική εορτή, ψάλλονται σε ήχο δ΄ άγια",
        ),
    ),
    AttachmentRule(
        "litourgia",
        "Ποτήριον σωτηρίου λήψομαι, καὶ τὸ ὄνομα Κυρίου ἐπικαλέσομαι.",
        "litourgia-koinonikon-pandekti",
        required_text=(
            "το Χερουβικό, τα Λειτουργικά και το Κοινωνικό σήμερα, "
            "Θεομητορική εορτή, ψάλλονται σε ήχο δ΄ άγια",
        ),
    ),
)


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
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")


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
        url = f"music/{piece.book_id}/{piece.piece_id}/{index}.png"
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


def enrich_service_html(
    selected_date: date,
    service: str,
    service_html: str,
    *,
    instance_offset: int = 0,
) -> EnrichmentResult:
    """Attach verified book matches based on the actual text returned by Melodos."""
    # The date remains part of the API because later books may contain rules
    # tied to a movable or fixed feast. Current Anastasimatarion rules are
    # selected from the content itself, regardless of weekday.
    _ = selected_date

    rules = tuple(rule for rule in PILOT_RULES if rule.service == service)
    soup = BeautifulSoup(service_html, "html.parser")
    attachment_count = 0
    unmatched: list[str] = []
    bookmarks: list[MusicBookmark] = []

    for rule in rules:
        needle = _normalized(rule.after_text)
        normalized_document = _normalized(soup.get_text(" ", strip=True))
        if any(_normalized(required) not in normalized_document for required in rule.required_text):
            continue
        matches = [
            node
            for node in list(soup.find_all(string=True))
            if needle in _normalized(str(node))
            and not (isinstance(node.parent, Tag) and node.parent.find_parent("aside"))
        ]
        if rule.occurrences == "first":
            match_index = rule.match_number - 1
            matches = matches[match_index : match_index + 1]
        if not matches:
            unmatched.append(rule.piece_id)
            continue

        piece = PIECES[rule.piece_id]
        for text_node in matches:
            attachment_count += 1
            instance = instance_offset + attachment_count
            fragment = BeautifulSoup(_music_markup(piece, instance), "html.parser").aside
            if fragment is None:
                continue
            _insertion_point(text_node).insert_after(fragment)
            bookmarks.append(MusicBookmark(_bookmark_id(piece, instance), piece.title))

    return EnrichmentResult(str(soup), attachment_count, tuple(unmatched), tuple(bookmarks))


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
        }
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
