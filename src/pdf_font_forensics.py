"""Private inspection of embedded PDF fonts used by music-score sources.

This is a provenance/feasibility check, not a font decompiler or score
converter. It reports whether a PDF preserves semantic font data such as a
cmap, named glyphs and OpenType layout tables before any transcription work is
attempted.
"""

from __future__ import annotations

from io import BytesIO
import re
from pathlib import Path
from typing import Any, Iterable

import pymupdf as fitz
from fontTools.ttLib import TTFont

from src.vector_pdf import parse_page_spec


_TO_UNICODE_REFERENCE = re.compile(r"/ToUnicode\s+(\d+)\s+0\s+R")
_BFCHAR_PAIR = re.compile(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>")


def _decode_unicode(hex_value: str) -> str | None:
    try:
        return bytes.fromhex(hex_value).decode("utf-16-be")
    except (UnicodeDecodeError, ValueError):
        return None


def parse_to_unicode_mappings(cmap_source: str) -> list[dict[str, str | None]]:
    """Read only ``beginbfchar`` entries from a PDF ToUnicode CMap stream."""

    mappings: list[dict[str, str | None]] = []
    for section in cmap_source.split("beginbfchar")[1:]:
        body = section.split("endbfchar", 1)[0]
        for source, target in _BFCHAR_PAIR.findall(body):
            mappings.append({"cid": f"0x{source.upper()}", "unicode": _decode_unicode(target)})
    return mappings


def _font_program_summary(program: bytes) -> dict[str, Any]:
    try:
        font = TTFont(BytesIO(program), recalcBBoxes=False, recalcTimestamp=False)
    except Exception as exc:  # A PDF can embed a non-SFNT font program.
        return {"readable_by_fonttools": False, "error": str(exc)}

    glyph_order = font.getGlyphOrder()
    named_glyphs = [glyph for glyph in glyph_order if glyph != ".notdef" and not re.fullmatch(r"glyph\d+", glyph)]
    cmap_entries = sum(len(table.cmap) for table in font["cmap"].tables) if "cmap" in font else 0
    gsub_features: list[str] = []
    if "GSUB" in font and font["GSUB"].table.FeatureList:
        gsub_features = [record.FeatureTag for record in font["GSUB"].table.FeatureList.FeatureRecord]
    gpos_features: list[str] = []
    if "GPOS" in font and font["GPOS"].table.FeatureList:
        gpos_features = [record.FeatureTag for record in font["GPOS"].table.FeatureList.FeatureRecord]
    reasons: list[str] = []
    if not cmap_entries:
        reasons.append("missing-cmap")
    if not named_glyphs:
        reasons.append("anonymous-glyph-names")
    if not gsub_features:
        reasons.append("missing-gsub")
    if not gpos_features:
        reasons.append("missing-gpos")
    return {
        "readable_by_fonttools": True,
        "tables": sorted(font.keys()),
        "glyph_count": len(glyph_order),
        "glyph_names_are_anonymous": not named_glyphs,
        "named_glyphs": named_glyphs[:30],
        "cmap_entries": cmap_entries,
        "gsub_features": gsub_features,
        "gpos_features": gpos_features,
        "direct_semantic_mapping_feasible": not reasons,
        "mapping_blockers": reasons,
    }


def inspect_embedded_fonts(
    pdf_path: str | Path,
    pages: Iterable[int] | None = None,
    font_name_filters: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Inspect selected PDF font resources without copying their binaries."""

    source = Path(pdf_path)
    if not source.is_file():
        raise FileNotFoundError(f"Δεν βρέθηκε PDF: {source}")
    filters = tuple(item.casefold() for item in (font_name_filters or ()) if item)
    with fitz.open(source) as document:
        selected_pages = tuple(pages) if pages is not None else tuple(range(1, document.page_count + 1))
        selected_pages = parse_page_spec(",".join(str(page) for page in selected_pages), document.page_count)
        references: list[dict[str, Any]] = []
        xrefs: dict[int, dict[str, Any]] = {}
        for page_number in selected_pages:
            for resource in document[page_number - 1].get_fonts(full=True):
                xref, extension, font_type, embedded_name, resource_name, encoding = resource[:6]
                if filters and not any(item in embedded_name.casefold() for item in filters):
                    continue
                references.append(
                    {
                        "page": page_number,
                        "xref": xref,
                        "embedded_name": embedded_name,
                        "resource_name": resource_name,
                        "encoding": encoding,
                    }
                )
                xrefs.setdefault(
                    xref,
                    {
                        "xref": xref,
                        "embedded_name": embedded_name,
                        "extension": extension,
                        "pdf_font_type": font_type,
                        "encoding": encoding,
                    },
                )
        inspected: list[dict[str, Any]] = []
        for xref, descriptor in sorted(xrefs.items()):
            object_source = document.xref_object(xref, compressed=False)
            match = _TO_UNICODE_REFERENCE.search(object_source)
            to_unicode = []
            if match:
                to_unicode = parse_to_unicode_mappings(document.xref_stream(int(match.group(1))).decode("latin1"))
            extracted = document.extract_font(xref)
            program_summary = _font_program_summary(extracted[3]) if extracted else {"readable_by_fonttools": False}
            inspected.append(
                {
                    **descriptor,
                    "to_unicode_entry_count": len(to_unicode),
                    "to_unicode_sample": to_unicode[:20],
                    "font_program": program_summary,
                }
            )
    return {
        "schema": 1,
        "purpose": "private-pdf-font-forensics; no-score-conversion",
        "source_filename": source.name,
        "selected_pages": list(selected_pages),
        "font_name_filters": list(filters),
        "references": references,
        "fonts": inspected,
    }
