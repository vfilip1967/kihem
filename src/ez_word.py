"""Private first-stage reader for legacy Word documents written with EZ fonts.

The Word files published by St Anthony's Monastery are better evidence than a
PDF: they retain the ordered Private Use Area (PUA) characters typed by the
author. ``wvWare`` can recover that order from Word 6–2003 ``.doc`` files.
It cannot, however, preserve the font run for each character. Since EZ font
families share their PUA range, this module reports possible owning fonts
instead of guessing one or emitting Neanes events.

The report is private research material. It is not a score converter and it
never writes ``.byzx``.
"""

from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
import re

from olefile import OleFileIO

from .ez_font_mapping import EZ_SOURCE_DEFINITIONS


class EzWordExtractionError(ValueError):
    """Raised for unreadable legacy Word input or a failed Word extractor."""


def declared_ez_fonts_from_table(table_bytes: bytes, known_fonts: Iterable[str]) -> list[str]:
    """Find named EZ families in the Word table stream.

    This establishes that a document declares the supplied font family. It
    does *not* say which font was used by a particular PUA character; that
    requires the character-property runs from a fuller Word importer.
    """

    decoded = table_bytes.decode("utf-16le", errors="ignore")
    normalized_table = re.sub(r"[^a-z0-9]", "", decoded.casefold())
    result: list[str] = []
    seen: set[str] = set()
    for font in known_fonts:
        normalized_font = re.sub(r"[^a-z0-9]", "", font.casefold())
        if normalized_font in normalized_table and normalized_font not in seen:
            result.append(font)
            seen.add(normalized_font)
    return result


def _word_table_bytes(source: Path) -> bytes:
    try:
        with OleFileIO(source) as document:
            for stream in ("1Table", "0Table"):
                if document.exists(stream):
                    return document.openstream(stream).read()
    except OSError as error:
        raise EzWordExtractionError(f"Δεν ανοίγει ως παλαιό αρχείο Word: {source}") from error
    raise EzWordExtractionError("Το Word δεν έχει πίνακα μορφοποίησης 0Table/1Table.")


def _wv_xml(source: Path, executable: str) -> str:
    try:
        result = subprocess.run(
            [executable, "-X", str(source)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as error:
        raise EzWordExtractionError(
            f"Δεν βρέθηκε ο αναγνώστης Word {executable!r}. Απαιτείται το wvWare."
        ) from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip() or str(error)
        raise EzWordExtractionError(f"Αποτυχία ανάγνωσης Word από wvWare: {detail}") from error
    return result.stdout


def _pua_rows(xml_text: str, declared_fonts: list[str]) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as error:
        raise EzWordExtractionError(f"Το wvWare δεν επέστρεψε έγκυρο XML: {error}") from error

    rows: list[dict[str, Any]] = []
    occurrence = 0
    for paragraph_number, paragraph in enumerate(root.findall(".//p"), start=1):
        text = "".join(paragraph.itertext())
        pua = [character for character in text if 0xF000 <= ord(character) <= 0xF8FF]
        if not pua:
            continue
        occurrences = []
        for character in pua:
            occurrence += 1
            codepoint = f"U+{ord(character):04X}"
            candidates = [
                {
                    "font": font,
                    "source_definition": EZ_SOURCE_DEFINITIONS.get((font, codepoint)),
                }
                for font in declared_fonts
            ]
            occurrences.append(
                {
                    "word_occurrence": occurrence,
                    "pua_codepoint": codepoint,
                    "font_candidates": candidates,
                    "status": "font-run-unresolved; no-neanes-event",
                }
            )
        rows.append(
            {
                "word_paragraph": paragraph_number,
                "pua_occurrences": occurrences,
                # Nearby non-PUA text helps a reviewer orient themselves but
                # is never automatically assigned to a musical event.
                "nearby_text": "".join(character for character in text if not 0xF000 <= ord(character) <= 0xF8FF).strip(),
            }
        )
    return rows


def build_ez_word_report(
    xml_text: str,
    *,
    source_label: str,
    source_filename: str,
    declared_fonts: list[str],
) -> dict[str, Any]:
    """Build a JSON-safe direct-Word report from an extracted XML stream."""

    rows = _pua_rows(xml_text, declared_fonts)
    occurrences = [item for row in rows for item in row["pua_occurrences"]]
    counts = Counter(item["pua_codepoint"] for item in occurrences)
    return {
        "schema": 1,
        "purpose": "private-ez-word-character-report; no-font-run-inferred; no-byzx-generated",
        "source_label": source_label,
        "source_filename": source_filename,
        "extractor": "wvWare -X; ordered PUA character stream only",
        "declared_ez_fonts": declared_fonts,
        "font_run_status": "unresolved; use a font-preserving Word importer before semantic conversion",
        "paragraph_count_with_pua": len(rows),
        "pua_occurrence_count": len(occurrences),
        "pua_counts": dict(sorted(counts.items())),
        "paragraphs": rows,
    }


def extract_ez_word_document(
    source: str | Path,
    *,
    source_label: str,
    known_fonts: Iterable[str],
    executable: str = "wvWare",
) -> dict[str, Any]:
    """Read a legacy EZ Word file directly into a conservative private report."""

    path = Path(source)
    if path.suffix.lower() != ".doc" or not path.is_file():
        raise EzWordExtractionError(f"Απαιτείται υπάρχον αρχείο .doc: {path}")
    fonts = declared_ez_fonts_from_table(_word_table_bytes(path), known_fonts)
    if not fonts:
        raise EzWordExtractionError("Το Word δεν δηλώνει καμία από τις αναμενόμενες EZ γραμματοσειρές.")
    return build_ez_word_report(
        _wv_xml(path, executable),
        source_label=source_label,
        source_filename=path.name,
        declared_fonts=fonts,
    )
