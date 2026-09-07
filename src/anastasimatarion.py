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
    "tone6-anavathmoi": MusicPiece(
        "tone6-anavathmoi",
        "Οἱ Ἀναβαθμοί, πλ. β΄",
        "Ἐν τῷ οὐρανῷ τοὺς ὀφθαλμούς μου αἴρω",
        (_region(283, 0.15), _region(284), _region(285, 0.02, 0.24)),
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
        "σὺν πάση πνοὴ τῶν κάτω.",
        "tone6-anavathmoi",
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
)


def catalog_pieces() -> tuple[MusicPiece, ...]:
    piece_ids = dict.fromkeys(rule.piece_id for rule in PILOT_RULES)
    return tuple(PIECES[piece_id] for piece_id in piece_ids)


def get_piece(book_id: str, piece_id: str) -> MusicPiece:
    if book_id != BOOK_ID or piece_id not in PIECES:
        raise KeyError(f"Άγνωστο μουσικό τεκμήριο: {book_id}/{piece_id}")
    return PIECES[piece_id]


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFD", value.casefold())
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")


def _music_markup(piece: MusicPiece, instance: int) -> str:
    pages = ", ".join(str(region.printed_page) for region in piece.regions)
    figures = []
    for index, region in enumerate(piece.regions, start=1):
        # Relative URLs work both at / locally and behind the public /kihem/ prefix.
        url = f"music/{BOOK_ID}/{piece.piece_id}/{index}.png"
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
        f'<aside class="music-attachment" data-music-piece="{html.escape(piece.piece_id)}" '
        f'data-music-instance="{instance}">'
        '<div class="music-attachment-heading">'
        '<span class="music-match-label">Μουσικό κείμενο που αντιστοιχίστηκε</span>'
        f"<h3>{html.escape(piece.title)}</h3>"
        f"<p>{html.escape(BOOK_TITLE)} · σελ. {pages}</p>"
        "</div>"
        f'<div class="music-pages">{"".join(figures)}</div>'
        '<p class="music-source">'
        f'<a href="{SOURCE_PAGE}" target="_blank" rel="noreferrer">{html.escape(BOOK_DETAILS)}</a>'
        " · Μουσική Βιβλιοθήκη «Λίλιαν Βουδούρη» · CC BY-NC"
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


def enrich_service_html(selected_date: date, service: str, service_html: str) -> EnrichmentResult:
    """Attach verified book matches based on the actual text returned by Melodos."""
    # The date remains part of the API because later books may contain rules
    # tied to a movable or fixed feast. Current Anastasimatarion rules are
    # selected from the content itself, regardless of weekday.
    _ = selected_date

    rules = tuple(rule for rule in PILOT_RULES if rule.service == service)
    soup = BeautifulSoup(service_html, "html.parser")
    attachment_count = 0
    unmatched: list[str] = []

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
            fragment = BeautifulSoup(_music_markup(piece, attachment_count), "html.parser").aside
            if fragment is None:
                continue
            _insertion_point(text_node).insert_after(fragment)

    return EnrichmentResult(str(soup), attachment_count, tuple(unmatched))


class AnastasimatarionRenderer:
    """Download once and render verified regions from the scanned book."""

    _download_lock = threading.Lock()

    def __init__(self, cache_dir: str | Path = "/tmp/kihem-cache", session=None):
        self.cache_dir = Path(cache_dir) / "anastasimatarion"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_path = Path(os.environ.get("KIHEM_ANASTASIMATARION_PDF", self.cache_dir / "source.pdf"))
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "Kihem/0.3 (+personal liturgical reading tool)"})

    def render(self, book_id: str, piece_id: str, part: int) -> Path:
        piece = get_piece(book_id, piece_id)
        if part < 1 or part > len(piece.regions):
            raise KeyError(f"Άγνωστο μέρος μουσικού τεκμηρίου: {piece_id}/{part}")
        region = piece.regions[part - 1]
        output = self.cache_dir / f"{piece.piece_id}-{part}-p{region.pdf_page}.png"
        if output.exists():
            return output

        self._ensure_pdf()
        document = pymupdf.open(self.pdf_path)
        try:
            if document.page_count < region.pdf_page:
                raise RuntimeError("Το PDF του Αναστασιματαρίου δεν περιέχει την αναμενόμενη σελίδα.")
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

    def _ensure_pdf(self) -> None:
        if self._valid_pdf(self.pdf_path):
            return
        with self._download_lock:
            if self._valid_pdf(self.pdf_path):
                return
            temporary = self.pdf_path.with_suffix(".download")
            try:
                with self.session.get(DOWNLOAD_URL, stream=True, timeout=(10, 180)) as response:
                    response.raise_for_status()
                    with temporary.open("wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                handle.write(chunk)
                if not self._valid_pdf(temporary):
                    raise RuntimeError("Η λήψη του Αναστασιματαρίου δεν είναι έγκυρο PDF.")
                temporary.replace(self.pdf_path)
            finally:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _valid_pdf(path: Path) -> bool:
        if not path.exists() or path.stat().st_size < 1_000_000:
            return False
        try:
            document = pymupdf.open(path)
            valid = document.page_count >= 600
            document.close()
            return valid
        except Exception:
            return False
