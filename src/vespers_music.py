"""Attach verified scanned music to the DCS-rendered Vespers.

The Melodos rule engine keys on Melodos' own wording, which the DCS document
does not have.  Instead of duplicating those anchors, Vespers uses a narrow,
content-based rule: a catalogue piece is attached only when its own incipit
appears in the text of a hymn it belongs to (currently the Apolytikion).  That
keeps the attachment verifiable — a piece can never be chosen from the date or
the weekday alone — and it starts working automatically as soon as a new
Apolytikion is added to the catalogue.
"""

from __future__ import annotations

import unicodedata

from bs4 import BeautifulSoup, Tag

from src.anastasimatarion import PIECES, MusicPiece, _music_markup

# A section accepts only the piece families that belong to it.  This is the
# guard that keeps, for example, a Liturgy setting of «Πατέρα, Υἱὸν…» out of
# the Vespers prayer of the entrance: a piece may not float to any text that
# happens to contain its incipit.
SECTION_FAMILIES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("Ἀπολυτίκιον", ("apolytikion",)),
    ("Δοξαστικόν", ("doxastikon",)),
    ("Ἀπόστιχα", ("aposticha", "doxastikon")),
    ("Στιχηρά", ("sticheron", "stichera", "doxastikon")),
)
# Very short incipits are liturgical formulae and would match noise.
MIN_INCIPIT_LENGTH: Final = 12


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFD", value.casefold())
    cleaned = "".join(
        ch
        for ch in value
        if unicodedata.category(ch) not in {"Mn", "Pc", "Pd", "Pe", "Pf", "Pi", "Po", "Ps"}
    )
    return " ".join(cleaned.split())


# The hymn itself, not the dialogue responses around it: "Κύριε ἐλέησον"
# appears in almost every section as a choir response and must never be able
# to match a piece on its own.
CONTENT_CLASSES: Final = {"dcs-hymn", "dcs-verse", "dcs-reading"}
GENERIC_INCIPITS: Final = {"κυριε ελεησον", "αμην", "σοι κυριε"}


def _section_text(heading: Tag) -> list[Tag]:
    """Return the hymn paragraphs that belong to one heading."""
    nodes: list[Tag] = []
    for sibling in heading.next_siblings:
        if not isinstance(sibling, Tag):
            continue
        if sibling.name == "h3":
            break
        classes = set(sibling.get("class") or [])
        if classes & CONTENT_CLASSES:
            nodes.append(sibling)
    return nodes


def _families_for(title: str) -> tuple[str, ...]:
    normalized = _normalized(title)
    families: list[str] = []
    for prefix, allowed in SECTION_FAMILIES:
        if normalized.startswith(_normalized(prefix)):
            for family in allowed:
                if family not in families:
                    families.append(family)
    return tuple(families)


def _candidates(section_text: str, families: tuple[str, ...]) -> list[MusicPiece]:
    haystack = _normalized(section_text)
    matches = []
    for piece in PIECES.values():
        if not any(family in piece.piece_id for family in families):
            continue
        needle = _normalized(piece.incipit)
        if not needle or needle in GENERIC_INCIPITS or len(needle) < MIN_INCIPIT_LENGTH:
            continue
        if needle in haystack:
            matches.append(piece)
    # Prefer the most specific incipit when several would match.
    matches.sort(key=lambda piece: len(_normalized(piece.incipit)), reverse=True)
    return matches


def attach_music(
    service_html: str, *, instance_start: int = 0
) -> tuple[str, list[dict[str, str]], list[str]]:
    """Insert verified excerpts after matching hymn paragraphs.

    Returns the new HTML, the music bookmarks and the ids of the attached
    pieces (so the caller can keep counting instances across documents).
    """
    if not service_html:
        return service_html, [], []

    soup = BeautifulSoup(f"<div id='vespers-root'>{service_html}</div>", "html.parser")
    root = soup.find("div", id="vespers-root")
    if root is None:  # pragma: no cover - defensive
        return service_html, [], []

    bookmarks: list[dict[str, str]] = []
    attached: list[str] = []
    instance = instance_start

    for heading in root.find_all("h3", class_="dcs-heading"):
        raw_title = heading.get_text(" ", strip=True)
        # Compare accent-insensitively: DCS prints «Ἀπολυτίκιον» with a different
        # iota codepoint than a plain Greek keyboard produces.
        families = _families_for(raw_title)
        if not families:
            continue
        paragraphs = _section_text(heading)
        text = " ".join(node.get_text(" ", strip=True) for node in paragraphs)
        if not text.strip():
            continue
        for piece in _candidates(text, families):
            if piece.piece_id in attached:
                continue
            instance += 1
            fragment = BeautifulSoup(_music_markup(piece, instance), "html.parser")
            target = paragraphs[-1] if paragraphs else heading
            target.insert_after(fragment)
            attached.append(piece.piece_id)
            bookmarks.append(
                {
                    "anchor_id": f"music-{piece.piece_id}-{instance}",
                    "label": f"Σελιδοδείκτης · {piece.title}",
                    "title": piece.title,
                }
            )

    return root.decode_contents(), bookmarks, attached
