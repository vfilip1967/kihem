"""Make a private, geometry-led review sheet for an EZ-font PDF.

The vector extractor knows exactly where each glyph was painted, while the
EZ mapping template knows which of those glyph identities are backed by the
complete official font.  This module joins those two facts into staff-line
review rows.  It deliberately does *not* decide syllable attachment, event
boundaries, pitch, rhythm or a Neanes value.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any, Mapping


class EzPhraseReviewError(ValueError):
    """Raised when the inputs are not a compatible private EZ review pair."""


def _anchor_key(source: Mapping[str, Any]) -> tuple[str, int, str]:
    return (str(source.get("pdf_font_instance", "")), int(source.get("pdf_glyph_id", -1)), str(source.get("pua_codepoint", "")))


def _glyph_key(glyph: Mapping[str, Any]) -> tuple[str, int, str]:
    return (str(glyph.get("font_instance", "")), int(glyph.get("glyph_id", -1)), str(glyph.get("codepoint", "")))


def _bbox(value: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(value, list) or len(value) != 4:
        return None
    try:
        return tuple(float(number) for number in value)  # type: ignore[return-value]
    except (TypeError, ValueError):
        return None


def _origin_y(glyph: Mapping[str, Any]) -> float:
    origin = glyph.get("origin")
    if isinstance(origin, list) and len(origin) >= 2:
        try:
            return float(origin[1])
        except (TypeError, ValueError):
            pass
    box = _bbox(glyph.get("bbox"))
    return (box[1] + box[3]) / 2 if box else 0.0


def _origin_x(glyph: Mapping[str, Any]) -> float:
    origin = glyph.get("origin")
    if isinstance(origin, list) and origin:
        try:
            return float(origin[0])
        except (TypeError, ValueError):
            pass
    box = _bbox(glyph.get("bbox"))
    return box[0] if box else 0.0


def _line_groups(glyphs: list[dict[str, Any]], tolerance: float) -> list[list[dict[str, Any]]]:
    """Group nearby vertical origins; accents may sit a few points above a note."""

    groups: list[list[dict[str, Any]]] = []
    for glyph in sorted(glyphs, key=lambda item: (_origin_y(item["glyph"]), _origin_x(item["glyph"]))):
        if not groups:
            groups.append([glyph])
            continue
        baseline = median(_origin_y(item["glyph"]) for item in groups[-1])
        if abs(_origin_y(glyph["glyph"]) - baseline) <= tolerance:
            groups[-1].append(glyph)
        else:
            groups.append([glyph])
    return groups


def _nearby_text(spans: list[Mapping[str, Any]], notation_fonts: set[str], x0: float, y0: float, x1: float, y1: float) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for span in spans:
        if span.get("font") in notation_fonts:
            continue
        box = _bbox(span.get("bbox"))
        text = span.get("text")
        if box is None or not isinstance(text, str) or not text.strip():
            continue
        # A generous band makes nearby lyric candidates visible but is never
        # represented as an attachment to any individual note.
        if box[2] < x0 - 36 or box[0] > x1 + 36 or box[3] < y0 - 40 or box[1] > y1 + 48:
            continue
        candidates.append({"text": text, "font": span.get("font"), "bbox": list(box), "location": span.get("location")})
    return candidates


def _attachment_candidates(source_glyphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """List reviewable neighbours for attachments without choosing one."""

    bases = [
        glyph
        for glyph in source_glyphs
        if isinstance(glyph.get("source_definition"), Mapping)
        and glyph["source_definition"].get("neanes_candidate", {}).get("element_type") == "quantitativeNeume"
    ]
    candidates: list[dict[str, Any]] = []
    for glyph in source_glyphs:
        definition = glyph.get("source_definition")
        candidate = definition.get("neanes_candidate") if isinstance(definition, Mapping) else None
        if not isinstance(candidate, Mapping) or candidate.get("element_type") not in {"gorgonNeume", "timeNeume", "vocalExpressionNeume", "ison", "isonControl", "vareia"}:
            continue
        x = float(glyph.get("origin", [0])[0])
        previous = [base for base in bases if float(base.get("origin", [0])[0]) <= x]
        following = [base for base in bases if float(base.get("origin", [0])[0]) > x]
        candidates.append(
            {
                "attachment_position": glyph["line_position"],
                "attachment_type": candidate.get("element_type"),
                "documented_value": candidate.get("value"),
                "nearest_previous_base_position": previous[-1]["line_position"] if previous else None,
                "nearest_following_base_position": following[0]["line_position"] if following else None,
                "status": "reviewer-must-select-or-reject",
            }
        )
    return candidates


def build_ez_phrase_review_sheet(
    vector_report: Mapping[str, Any], mapping_template: Mapping[str, Any], *, line_tolerance: float = 7.0
) -> dict[str, Any]:
    """Build private staff-line review data without inferring music semantics."""

    if mapping_template.get("purpose") != "private-ez-to-neanes-mapping-template; no-byzx-generated":
        raise EzPhraseReviewError("Δεν δόθηκε έγκυρο EZ mapping template.")
    if line_tolerance <= 0:
        raise EzPhraseReviewError("Το line_tolerance πρέπει να είναι θετικό.")
    rows = mapping_template.get("rows")
    if not isinstance(rows, list):
        raise EzPhraseReviewError("Το EZ mapping template δεν έχει rows.")
    index = {_anchor_key(row.get("source", {})): row for row in rows if isinstance(row, Mapping)}
    if not index:
        raise EzPhraseReviewError("Το EZ mapping template δεν έχει αναγνωρίσιμα glyph anchors.")
    notation_fonts = {row["source"].get("pdf_font") for row in index.values() if isinstance(row.get("source"), Mapping)}
    pages: list[dict[str, Any]] = []
    glyph_count = 0
    for page in vector_report.get("pages", []):
        if not isinstance(page, Mapping):
            continue
        matched: list[dict[str, Any]] = []
        for occurrence, glyph in enumerate(page.get("glyphs", [])):
            if not isinstance(glyph, Mapping):
                continue
            row = index.get(_glyph_key(glyph))
            if row is not None:
                matched.append({"glyph": glyph, "row": row, "occurrence": occurrence})
        glyph_count += len(matched)
        lines: list[dict[str, Any]] = []
        for line_number, group in enumerate(_line_groups(matched, line_tolerance), start=1):
            ordered = sorted(group, key=lambda item: (_origin_x(item["glyph"]), _origin_y(item["glyph"])))
            boxes = [_bbox(item["glyph"].get("bbox")) for item in ordered]
            actual_boxes = [box for box in boxes if box is not None]
            x0 = min(box[0] for box in actual_boxes) if actual_boxes else 0.0
            y0 = min(box[1] for box in actual_boxes) if actual_boxes else 0.0
            x1 = max(box[2] for box in actual_boxes) if actual_boxes else 0.0
            y1 = max(box[3] for box in actual_boxes) if actual_boxes else 0.0
            source_glyphs = []
            for line_position, item in enumerate(ordered, start=1):
                glyph = item["glyph"]
                row = item["row"]
                source = row["source"]
                source_glyphs.append(
                    {
                        "line_position": line_position,
                        "occurrence": item["occurrence"],
                        "source_anchor": {
                            "pdf_font_instance": source.get("pdf_font_instance"),
                            "pdf_glyph_id": source.get("pdf_glyph_id"),
                            "pua_codepoint": source.get("pua_codepoint"),
                        },
                        "font": source.get("pdf_font"),
                        "keyboard_keys": source.get("keyboard_keys", []),
                        "character_table_group": source.get("character_table_group", []),
                        "source_definition": row.get("source_definition"),
                        "bbox": glyph.get("bbox"),
                        "origin": glyph.get("origin"),
                        "sequence": glyph.get("sequence"),
                    }
                )
            lines.append(
                {
                    "id": f"page-{page.get('number', len(pages) + 1)}-line-{line_number}",
                    "bbox": [x0, y0, x1, y1],
                    "source_glyphs": source_glyphs,
                    "attachment_candidates": _attachment_candidates(source_glyphs),
                    "nearby_text_candidates": _nearby_text(list(page.get("spans", [])), notation_fonts, x0, y0, x1, y1),
                    "review": {
                        "status": "unreviewed",
                        "phrase_boundaries": [],
                        "note_events": [],
                        "warning": "Τα γειτονικά λεκτικά δεν έχουν αυτόματη αντιστοίχιση με νεύματα.",
                    },
                }
            )
        pages.append({"number": page.get("number"), "notation_line_count": len(lines), "lines": lines})
    return {
        "schema": 1,
        "purpose": "private-ez-phrase-review-sheet; no-musical-meaning-inferred",
        "source_label": mapping_template.get("source_label"),
        "notation_glyph_count": glyph_count,
        "pages": pages,
        "warning": (
            "Το φύλλο οργανώνει μόνο γεωμετρικά τα glyphs που ταυτίζονται με το πλήρες EZ font. "
            "Δεν δημιουργεί phrase plan, .byzx ή μουσική ερμηνεία."
        ),
    }
