"""Private analysis of born-digital Byzantine-music PDFs.

This module deliberately stops before musical transcription. A PDF typeset
with a Byzantine-music font has usable layout data (glyph, font, bounding box
and lyric text), but its character codes are not yet a documented Neanes
vocabulary. The extractor preserves evidence for a later explicit glyph map.

It does not copy a source PDF into the application, publish any text or create
a ``.byzx`` file. It is a private research/import aid only.
"""

from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path
from typing import Any, Iterable

try:
    import pymupdf as fitz
except ImportError as exc:  # pragma: no cover - exercised by the command user
    raise RuntimeError("Απαιτείται PyMuPDF. Εκτελέστε: pip install -r requirements.txt") from exc


SCHEMA_VERSION = 1
_SIGNATURE_SIZE = 32
DEFAULT_REFERENCE_GLYPH_LIMIT = 96


def parse_page_spec(specification: str | None, page_count: int) -> tuple[int, ...]:
    """Return unique one-based PDF pages selected by ``11-13,19``."""

    if page_count < 1:
        raise ValueError("Το PDF δεν περιέχει σελίδες.")
    if not specification:
        return tuple(range(1, page_count + 1))

    selected: list[int] = []
    for raw_part in specification.split(","):
        part = raw_part.strip()
        if not part:
            raise ValueError("Κενό τμήμα στον ορισμό σελίδων.")
        if "-" in part:
            bounds = [value.strip() for value in part.split("-", 1)]
            if len(bounds) != 2 or not all(value.isdecimal() for value in bounds):
                raise ValueError(f"Μη έγκυρο εύρος σελίδων: {part!r}")
            start, end = (int(value) for value in bounds)
            if end < start:
                raise ValueError(f"Ανάστροφο εύρος σελίδων: {part!r}")
            selected.extend(range(start, end + 1))
        elif part.isdecimal():
            selected.append(int(part))
        else:
            raise ValueError(f"Μη έγκυρη σελίδα: {part!r}")

    ordered = tuple(dict.fromkeys(selected))
    invalid = [page for page in ordered if page < 1 or page > page_count]
    if invalid:
        raise ValueError(
            f"Οι σελίδες {', '.join(str(page) for page in invalid)} είναι εκτός PDF (1–{page_count})."
        )
    return ordered


def _number(value: float) -> float:
    return round(float(value), 3)


def _box(values: Iterable[float]) -> list[float]:
    return [_number(value) for value in values]


def _character(character: dict[str, Any]) -> dict[str, Any]:
    value = character.get("c", "")
    return {
        "text": value,
        "codepoint": f"U+{ord(value):04X}" if len(value) == 1 else None,
        "bbox": _box(character.get("bbox", (0, 0, 0, 0))),
        "origin": _box(character.get("origin", (0, 0))),
    }


def _span(span: dict[str, Any], block_index: int, line_index: int, span_index: int) -> dict[str, Any]:
    characters = [_character(character) for character in span.get("chars", [])]
    text = "".join(character["text"] for character in characters)
    return {
        "location": {"block": block_index, "line": line_index, "span": span_index},
        "font": span.get("font", ""),
        "size": _number(span.get("size", 0)),
        "flags": span.get("flags", 0),
        "color": span.get("color", 0),
        "bbox": _box(span.get("bbox", (0, 0, 0, 0))),
        "text": text,
        "characters": characters,
    }


def _page_spans(page: fitz.Page) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for block_index, block in enumerate(page.get_text("rawdict").get("blocks", [])):
        if block.get("type") != 0:
            continue
        for line_index, line in enumerate(block.get("lines", [])):
            for span_index, span in enumerate(line.get("spans", [])):
                spans.append(_span(span, block_index, line_index, span_index))
    return spans


def _font_summary(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for span in spans:
        grouped.setdefault(str(span["font"]), []).append(span)

    summary: list[dict[str, Any]] = []
    for font, font_spans in sorted(grouped.items()):
        characters = [character for span in font_spans for character in span["characters"]]
        codes = Counter(character["codepoint"] for character in characters if character["codepoint"])
        examples = "".join(character["text"] for character in characters if not character["text"].isspace())[:80]
        summary.append(
            {
                "font": font,
                "span_count": len(font_spans),
                "character_count": len(characters),
                "distinct_codepoints": len(codes),
                "codepoints": [code for code, _count in codes.most_common()],
                "text_example": examples,
            }
        )
    return summary


def _font_instances(page: fitz.Page) -> dict[str, dict[str, Any]]:
    """Resolve a trace font name to its page-local embedded PDF font object."""

    instances: dict[str, dict[str, Any]] = {}
    for resource in page.get_fonts(full=True):
        xref, _extension, _type, embedded_name, resource_name = resource[:5]
        visible_name = embedded_name.split("+", 1)[-1]
        # A page normally has one resource for each trace font. Preserve a
        # deterministic first one if a malformed PDF repeats a name.
        instances.setdefault(
            visible_name,
            {
                "font_instance": f"{xref}:{embedded_name}",
                "font_subset_name": embedded_name,
                "font_resource_name": resource_name,
            },
        )
    return instances


def _glyph_trace(page: fitz.Page) -> list[dict[str, Any]]:
    """Return the PDF's rendered glyph identifiers, not merely Unicode text.

    A music font can use a misleading Unicode CMap or OpenType substitutions.
    The glyph id emitted by MuPDF's text trace is therefore the stable key for
    a font-specific mapping; Unicode remains useful only as supporting data.
    """

    font_instances = _font_instances(page)
    glyphs: list[dict[str, Any]] = []
    for trace in page.get_texttrace():
        font = str(trace.get("font", ""))
        instance = font_instances.get(font, {})
        for unicode_value, glyph_id, origin, bbox in trace.get("chars", ()):
            text = chr(unicode_value) if unicode_value else ""
            glyphs.append(
                {
                    "font": font,
                    "font_instance": instance.get("font_instance", f"unknown:{font}"),
                    "font_subset_name": instance.get("font_subset_name"),
                    "font_resource_name": instance.get("font_resource_name"),
                    "glyph_id": int(glyph_id),
                    "text": text,
                    "codepoint": f"U+{unicode_value:04X}" if unicode_value else None,
                    "origin": _box(origin),
                    "bbox": _box(bbox),
                    "size": _number(trace.get("size", 0)),
                    "color": trace.get("color"),
                    "sequence": trace.get("seqno"),
                }
            )
    return glyphs


def _add_glyph_summary(fonts: list[dict[str, Any]], glyphs: list[dict[str, Any]]) -> None:
    glyph_ids_by_font: dict[str, set[int]] = {}
    instances_by_font: dict[str, set[str]] = {}
    for glyph in glyphs:
        glyph_ids_by_font.setdefault(glyph["font"], set()).add(glyph["glyph_id"])
        instances_by_font.setdefault(glyph["font"], set()).add(glyph["font_instance"])
    for font in fonts:
        glyph_ids = sorted(glyph_ids_by_font.get(font["font"], set()))
        font["distinct_glyph_ids"] = len(glyph_ids)
        font["glyph_ids"] = glyph_ids
        font["font_instances"] = sorted(instances_by_font.get(font["font"], set()))


def extract_vector_pdf(pdf_path: str | Path, pages: Iterable[int] | None = None) -> dict[str, Any]:
    """Extract layout evidence from selected one-based pages of a vector PDF.

    The returned JSON-safe dictionary contains no inferred note semantics.
    Reports should remain outside Git and are only input to a separately
    reviewed font-code mapping.
    """

    source = Path(pdf_path)
    if not source.is_file():
        raise FileNotFoundError(f"Δεν βρέθηκε PDF: {source}")

    with fitz.open(source) as document:
        selected_pages = tuple(pages) if pages is not None else tuple(range(1, document.page_count + 1))
        selected_pages = parse_page_spec(",".join(str(page) for page in selected_pages), document.page_count)
        document_fonts: set[str] = set()
        extracted_pages: list[dict[str, Any]] = []
        for page_number in selected_pages:
            page = document[page_number - 1]
            spans = _page_spans(page)
            glyphs = _glyph_trace(page)
            fonts = _font_summary(spans)
            _add_glyph_summary(fonts, glyphs)
            document_fonts.update(item["font"] for item in fonts)
            extracted_pages.append(
                {
                    "number": page_number,
                    "size": {"width": _number(page.rect.width), "height": _number(page.rect.height)},
                    "image_count": len(page.get_images(full=True)),
                    "drawing_count": len(page.get_drawings()),
                    "fonts": fonts,
                    "spans": spans,
                    "glyphs": glyphs,
                }
            )

        metadata = document.metadata or {}
        return {
            "schema": SCHEMA_VERSION,
            "purpose": "private-vector-pdf-analysis; no-note-semantics-inferred",
            "document": {
                "filename": source.name,
                "page_count": document.page_count,
                "metadata": {
                    key: metadata.get(key)
                    for key in ("title", "author", "creator", "producer", "creationDate", "modDate")
                    if metadata.get(key)
                },
                "fonts_on_selected_pages": sorted(document_fonts),
            },
            "pages": extracted_pages,
        }


def _safe_filename_part(value: str) -> str:
    return "".join(character if character.isascii() and character.isalnum() else "-" for character in value).strip("-") or "font"


def write_glyph_atlas(
    pdf_path: str | Path,
    output_directory: str | Path,
    pages: Iterable[int] | None = None,
    fonts: Iterable[str] | None = None,
    scale: float = 4,
) -> dict[str, Any]:
    """Render one private sample for each extracted ``font + glyph id``.

    The samples are deliberately crops from the original vector PDF, rather
    than a claim about note meaning. They make it possible to build a reviewed
    mapping table for one particular music font. ``output_directory`` must be
    private because the crops are source material.
    """

    if scale <= 0:
        raise ValueError("Η κλίμακα του άτλαντα πρέπει να είναι θετική.")
    source = Path(pdf_path)
    target = Path(output_directory)
    target.mkdir(parents=True, exist_ok=True)
    wanted_fonts = set(fonts or ())
    samples: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    with fitz.open(source) as document:
        selected_pages = tuple(pages) if pages is not None else tuple(range(1, document.page_count + 1))
        selected_pages = parse_page_spec(",".join(str(page) for page in selected_pages), document.page_count)
        for page_number in selected_pages:
            page = document[page_number - 1]
            for glyph in _glyph_trace(page):
                font = glyph["font"]
                if wanted_fonts and font not in wanted_fonts:
                    continue
                glyph_id = glyph["glyph_id"]
                font_instance = glyph["font_instance"]
                text = glyph["text"]
                if not text or text.isspace() or (font_instance, glyph_id) in seen:
                    continue
                rectangle = fitz.Rect(glyph["bbox"])
                if rectangle.is_empty or rectangle.width <= 0 or rectangle.height <= 0:
                    continue
                seen.add((font_instance, glyph_id))
                padding = max(2.0, min(8.0, rectangle.height * 0.6))
                clip = fitz.Rect(
                    rectangle.x0 - padding,
                    rectangle.y0 - padding,
                    rectangle.x1 + padding,
                    rectangle.y1 + padding,
                )
                filename = (
                        f"p{page_number:03d}-{_safe_filename_part(font_instance)}-"
                    f"g{glyph_id:05d}-{str(glyph['codepoint']).lower().replace('+', '')}.png"
                )
                page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False).save(target / filename)
                samples.append(
                    {
                            "font": font,
                            "font_instance": font_instance,
                            "font_subset_name": glyph["font_subset_name"],
                        "glyph_id": glyph_id,
                        "text": text,
                        "codepoint": glyph["codepoint"],
                        "page": page_number,
                        "bbox": glyph["bbox"],
                        "file": filename,
                    }
                )

    manifest = {
        "schema": SCHEMA_VERSION,
        "purpose": "private-glyph-atlas; visual-identification-only",
        "source_filename": source.name,
        "font_filter": sorted(wanted_fonts),
        "samples": samples,
    }
    (target / "glyph-atlas.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _signature_from_pixmap(pixmap: fitz.Pixmap) -> tuple[tuple[int, ...], float] | None:
    """Reduce a rendered glyph to a small, font-independent binary outline."""

    channels = pixmap.n
    pixels = pixmap.samples
    width, height = pixmap.width, pixmap.height
    dark: list[tuple[int, int]] = []
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * channels
            # A non-white black or red notation mark is part of the glyph.
            if min(pixels[offset], pixels[offset + 1], pixels[offset + 2]) < 220:
                dark.append((x, y))
    if not dark:
        return None

    left = min(x for x, _y in dark)
    right = max(x for x, _y in dark)
    top = min(y for _x, y in dark)
    bottom = max(y for _x, y in dark)
    glyph_width, glyph_height = right - left + 1, bottom - top + 1
    occupied = {(x - left, y - top) for x, y in dark}
    signature: list[int] = []
    for output_y in range(_SIGNATURE_SIZE):
        start_y = math.floor(output_y * glyph_height / _SIGNATURE_SIZE)
        end_y = max(start_y + 1, math.ceil((output_y + 1) * glyph_height / _SIGNATURE_SIZE))
        for output_x in range(_SIGNATURE_SIZE):
            start_x = math.floor(output_x * glyph_width / _SIGNATURE_SIZE)
            end_x = max(start_x + 1, math.ceil((output_x + 1) * glyph_width / _SIGNATURE_SIZE))
            signature.append(
                int(
                    any(
                        (x, y) in occupied
                        for y in range(start_y, min(end_y, glyph_height))
                        for x in range(start_x, min(end_x, glyph_width))
                    )
                )
            )
    return tuple(signature), glyph_width / glyph_height


def rank_shape_candidates(
    source_signature: tuple[int, ...],
    source_aspect_ratio: float,
    candidates: Iterable[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Rank reference glyph outlines without assigning musical meaning.

    The returned similarity is an image-shape signal only. It cannot resolve
    a composite neume, contextual OpenType substitution or musical timing.
    """

    if not source_signature:
        return []
    results: list[dict[str, Any]] = []
    for candidate in candidates:
        reference_signature = tuple(candidate["signature"])
        if len(reference_signature) != len(source_signature):
            continue
        differing_pixels = sum(left != right for left, right in zip(source_signature, reference_signature))
        pixel_similarity = 1 - differing_pixels / len(source_signature)
        reference_aspect = float(candidate["aspect_ratio"])
        aspect_penalty = min(abs(math.log(max(source_aspect_ratio, 0.01) / max(reference_aspect, 0.01))) * 0.08, 0.2)
        result = {key: value for key, value in candidate.items() if key not in {"signature", "aspect_ratio"}}
        result["visual_similarity"] = round(max(0.0, pixel_similarity - aspect_penalty), 4)
        results.append(result)
    return sorted(results, key=lambda item: item["visual_similarity"], reverse=True)[:limit]


def assess_visual_evidence(candidates: list[dict[str, Any]]) -> str:
    """Classify image evidence conservatively; this never approves a mapping."""

    best = candidates[0]["visual_similarity"] if candidates else 0
    if best >= 0.82:
        return "reviewable-shape-only"
    return "insufficient-shape-evidence"


def _load_neanes_glyph_names(glyph_names_path: str | Path) -> list[dict[str, Any]]:
    raw = json.loads(Path(glyph_names_path).read_text(encoding="utf-8"))
    glyphs: list[dict[str, Any]] = []
    for name, definition in raw.items():
        codepoint = definition.get("codepoint")
        if not isinstance(codepoint, str) or not codepoint.startswith("U+"):
            continue
        glyphs.append({"glyph_name": name, "codepoint": codepoint, "unicode": int(codepoint[2:], 16)})
    if not glyphs:
        raise ValueError("Δεν βρέθηκαν SBMuFL glyph names στο αρχείο αναφοράς.")
    return glyphs


def _render_neanes_references(
    font_path: str | Path,
    glyph_names_path: str | Path,
    glyph_limit: int = DEFAULT_REFERENCE_GLYPH_LIMIT,
) -> list[dict[str, Any]]:
    """Render a safe, core subset of the Neanes vocabulary into outlines."""

    if glyph_limit < 1:
        raise ValueError("Το όριο glyph αναφοράς πρέπει να είναι θετικό.")
    glyphs = _load_neanes_glyph_names(glyph_names_path)[:glyph_limit]
    # Rendering every glyph in one very tall PDF page can make MuPDF allocate
    # a huge display list. Small batches keep this private utility predictable
    # on the production server as well as in tests.
    columns, rows, cell_width, cell_height = 5, 5, 104, 112
    batch_size = columns * rows
    references: list[dict[str, Any]] = []
    for batch_start in range(0, len(glyphs), batch_size):
        batch = glyphs[batch_start : batch_start + batch_size]
        with fitz.open() as document:
            page = document.new_page(width=columns * cell_width, height=rows * cell_height)
            page.insert_font(fontname="neanes-reference", fontfile=str(font_path))
            for index, glyph in enumerate(batch):
                column, row = index % columns, index // columns
                x, y = column * cell_width, row * cell_height
                page.insert_text((x + 16, y + 76), chr(glyph["unicode"]), fontname="neanes-reference", fontsize=72)

            for index, glyph in enumerate(batch):
                column, row = index % columns, index // columns
                rectangle = fitz.Rect(
                    column * cell_width,
                    row * cell_height,
                    (column + 1) * cell_width,
                    (row + 1) * cell_height,
                )
                rendered = _signature_from_pixmap(
                    # Reference cells are already large enough for the 32×32
                    # binary signature. Rendering at 1× avoids excessive
                    # memory use when the full 375-glyph vocabulary is read.
                    page.get_pixmap(matrix=fitz.Matrix(1, 1), clip=rectangle, alpha=False)
                )
                if rendered is None:
                    continue
                signature, aspect_ratio = rendered
                references.append({**glyph, "signature": signature, "aspect_ratio": aspect_ratio})
    return references


def write_neanes_glyph_suggestions(
    pdf_path: str | Path,
    output_path: str | Path,
    neanes_font_path: str | Path,
    neanes_glyph_names_path: str | Path,
    pages: Iterable[int] | None = None,
    fonts: Iterable[str] | None = None,
    candidate_limit: int = 5,
    reference_glyph_limit: int = DEFAULT_REFERENCE_GLYPH_LIMIT,
) -> dict[str, Any]:
    """Write private visual candidate matches from a source PDF to Neanes.

    This is deliberately not an importer. Composite notation, style variants,
    lyrics and red auxiliary signs make an automatic semantic conversion
    unsafe. Every row remains a visual candidate for a future mapping table.
    """

    if candidate_limit < 1:
        raise ValueError("Απαιτείται τουλάχιστον μία υποψήφια αντιστοίχιση.")
    source = Path(pdf_path)
    output = Path(output_path)
    wanted_fonts = set(fonts or ())
    references = _render_neanes_references(neanes_font_path, neanes_glyph_names_path, reference_glyph_limit)
    suggestions: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    with fitz.open(source) as document:
        selected_pages = tuple(pages) if pages is not None else tuple(range(1, document.page_count + 1))
        selected_pages = parse_page_spec(",".join(str(page) for page in selected_pages), document.page_count)
        for page_number in selected_pages:
            page = document[page_number - 1]
            for glyph in _glyph_trace(page):
                font, glyph_id = glyph["font"], glyph["glyph_id"]
                font_instance = glyph["font_instance"]
                if wanted_fonts and font not in wanted_fonts:
                    continue
                if not glyph["text"] or glyph["text"].isspace() or (font_instance, glyph_id) in seen:
                    continue
                rendered = _signature_from_pixmap(
                    page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(glyph["bbox"]), alpha=False)
                )
                if rendered is None:
                    continue
                seen.add((font_instance, glyph_id))
                signature, aspect_ratio = rendered
                candidates = rank_shape_candidates(signature, aspect_ratio, references, candidate_limit)
                suggestions.append(
                    {
                        "source_font": font,
                        "source_font_instance": font_instance,
                        "source_font_subset_name": glyph["font_subset_name"],
                        "source_glyph_id": glyph_id,
                        "source_codepoint": glyph["codepoint"],
                        "source_page": page_number,
                        "source_bbox": glyph["bbox"],
                        "candidates": candidates,
                        "evidence": assess_visual_evidence(candidates),
                        "status": "visual-candidate-only",
                    }
                )

    report = {
        "schema": SCHEMA_VERSION,
        "purpose": "private-neanes-visual-candidates; no-semantic-conversion",
        "source_filename": source.name,
        "reference_font": Path(neanes_font_path).name,
        "reference_glyph_names": Path(neanes_glyph_names_path).name,
        "font_filter": sorted(wanted_fonts),
        "candidate_limit": candidate_limit,
        "reference_glyph_limit": reference_glyph_limit,
        "suggestions": suggestions,
        "warning": (
            "Οι υποψήφιες αντιστοιχίσεις προέρχονται μόνο από οπτική ομοιότητα. "
            "Δεν αποτελούν μουσική ερμηνεία, δεν χειρίζονται σύνθετα νεύματα "
            "και δεν επιτρέπουν παραγωγή .byzx."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
