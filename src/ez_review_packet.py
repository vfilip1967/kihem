"""Create a private, line-sized visual review packet for an EZ score."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pymupdf as fitz


class EzReviewPacketError(ValueError):
    """Raised for an invalid review sheet, line id or source PDF."""


_REVIEWER_READING_NOTES = {
    ("EZPsaltica", "U+F07A"): "βαρεία: άχρονο τροπικό σημάδι πριν από το νεύμα· δίνει ζωηρότητα στον επόμενο φθόγγο.",
    ("EZPsaltica", "U+F027"): "ίσον: παραλλαγή του ποσοτικού ισον· δεν είναι ισοκράτημα.",
    ("EZPsaltica", "U+F053"): "γοργόν: αναγνωρίζεται ως γοργόν, αλλά χρειάζεται ακόμη να επιβεβαιωθούν η πάνω/κάτω θέση και η βάση του.",
    ("EZPsaltica", "U+F03A"): "απλή χρονική: προσθέτει μία χρονική μονάδα στη βάση όπου ανήκει.",
    ("EZSpecial-II", "U+F04E"): "ισοκράτημα Γα (Γ).",
    ("EZSpecial-II", "U+F063"): "ισοκράτημα Νη (Ν).",
    ("EZSpecial-II", "U+F04D"): "ισοκράτημα Δι (Δ).",
    ("EZSpecial-II", "U+F03F"): "Μ: ο ισοκράτης παύει το ίσον και ψάλλει με τον κύριο ψάλτη.",
}

def _find_line(review_sheet: Mapping[str, Any], line_id: str) -> tuple[int, Mapping[str, Any]]:
    for page in review_sheet.get("pages", []):
        if not isinstance(page, Mapping):
            continue
        page_number = page.get("number")
        for line in page.get("lines", []):
            if isinstance(line, Mapping) and line.get("id") == line_id:
                if not isinstance(page_number, int) or page_number < 1:
                    raise EzReviewPacketError("Η γραμμή δεν έχει έγκυρο αριθμό σελίδας.")
                return page_number, line
    raise EzReviewPacketError(f"Δεν βρέθηκε γραμμή ελέγχου: {line_id}")


def _reviewer_readings_markdown(line: Mapping[str, Any]) -> str:
    """Render the small, stable record of meanings already confirmed by the reviewer."""

    readings: list[str] = []
    for position, glyph in enumerate(line.get("source_glyphs", []), start=1):
        if not isinstance(glyph, Mapping):
            continue
        anchor = glyph.get("source_anchor", {})
        if not isinstance(anchor, Mapping):
            continue
        font = str(anchor.get("pdf_font", ""))
        # Phrase-plan anchors intentionally store the stable font-instance
        # identity, not a redundant font-name field.  The current extractor's
        # instance label ends in ``+EZPsaltica`` / ``+EZSpecial-II``.
        if not font:
            font = str(anchor.get("pdf_font_instance", "")).rsplit("+", 1)[-1]
        key = (font, str(anchor.get("pua_codepoint", "")))
        note = _REVIEWER_READING_NOTES.get(key)
        if note:
            readings.append(f"- θέση {position}: {note}")
    return "\n".join(readings) or "(Δεν έχει καταγραφεί ακόμη επιβεβαίωση ψάλτη για αυτή τη γραμμή.)"


def _line_markdown(line_id: str, page_number: int, line: Mapping[str, Any]) -> str:
    candidate_text = [item.get("text", "") for item in line.get("nearby_text_candidates", []) if isinstance(item, Mapping)]
    glyph_lines = []
    for index, glyph in enumerate(line.get("source_glyphs", []), start=1):
        anchor = glyph.get("source_anchor", {}) if isinstance(glyph, Mapping) else {}
        definition = glyph.get("source_definition") if isinstance(glyph, Mapping) else None
        name = definition.get("source_name", "χωρίς τεκμηριωμένο ορισμό") if isinstance(definition, Mapping) else "χωρίς τεκμηριωμένο ορισμό"
        glyph_lines.append(
            f"{index}. `{anchor.get('pdf_font_instance')} / {anchor.get('pdf_glyph_id')} / {anchor.get('pua_codepoint')}` — {name}"
        )
    text = "\n\n".join(candidate_text) if candidate_text else "(Δεν βρέθηκε γειτονικό λεκτικό.)"
    return f"""# Ιδιωτικός έλεγχος EZ · {line_id}

Σελίδα PDF: {page_number}. Η εικόνα `source-crop.png` είναι η αυθεντική
οπτική πηγή για αυτή τη γραμμή. Δεν ανεβαίνει στο Git ή στον δημόσιο κατάλογο.

## Οπτικός έλεγχος

- [ ] Επιβεβαιώνω τα όρια της φράσης.
- [ ] Επιβεβαιώνω το βασικό νεύμα κάθε μουσικού γεγονότος.
- [ ] Επιβεβαιώνω γοργά, χρόνους, φθορές και την πάνω/κάτω θέση τους.
- [ ] Επιβεβαιώνω τη συλλαβοποίηση με την έντυπη πηγή.

## Γειτονικά λεκτικά — μόνο οπτικά υποψήφια

{text}

## Όσα έχουν ήδη επιβεβαιωθεί από τον ψάλτη

{_reviewer_readings_markdown(line)}

## Glyph anchors

{chr(10).join(glyph_lines)}

## Προσαρτήματα προς επιλογή

{_attachment_markdown(line)}

## Μετά τον οπτικό έλεγχο

Συμπλήρωσε το `phrase-plan.json`: ομαδοποίησε τα anchors σε `events`, γράψε
τη λύση Neanes και θέσε `confirmed: true` μόνο στα γεγονότα που είναι βέβαια.
Μετά το Kihem παράγει ιδιωτικό `.byzx` για ακουστικό έλεγχο στο Neanes.
"""


def _attachment_markdown(line: Mapping[str, Any]) -> str:
    values = line.get("attachment_candidates", [])
    if not values:
        return "(Δεν βρέθηκαν τεκμηριωμένα γοργά, χρόνοι ή ισοκρατήματα σε αυτή τη γραμμή.)"
    result = []
    for item in values:
        if not isinstance(item, Mapping):
            continue
        result.append(
            f"- θέση {item.get('attachment_position')}: `{item.get('attachment_type')}` "
            f"({item.get('documented_value') or 'τιμή προς επιβεβαίωση'}), "
            f"υποψήφια βάση πριν: θέση {item.get('nearest_previous_base_position')}, "
            f"μετά: θέση {item.get('nearest_following_base_position')}."
        )
    return "\n".join(result) or "(Δεν βρέθηκαν προσαρτήματα.)"


def create_ez_line_review_packet(
    review_sheet: Mapping[str, Any],
    *,
    line_id: str,
    source_pdf: str | Path,
    output_directory: str | Path,
    padding: float = 24.0,
    scale: float = 2.5,
) -> dict[str, Path]:
    """Write a crop, checklist and empty phrase-plan skeleton privately."""

    if review_sheet.get("purpose") != "private-ez-phrase-review-sheet; no-musical-meaning-inferred":
        raise EzReviewPacketError("Δεν δόθηκε έγκυρη ιδιωτική EZ καρτέλα ελέγχου.")
    if padding < 0 or scale <= 0:
        raise EzReviewPacketError("Το padding πρέπει να είναι μη αρνητικό και το scale θετικό.")
    page_number, line = _find_line(review_sheet, line_id)
    bbox = line.get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4:
        raise EzReviewPacketError("Η γραμμή δεν έχει έγκυρο πλαίσιο PDF.")
    try:
        rectangle = fitz.Rect(*(float(number) for number in bbox))
    except (TypeError, ValueError) as error:
        raise EzReviewPacketError("Η γραμμή δεν έχει αριθμητικό πλαίσιο PDF.") from error
    pdf_path = Path(source_pdf)
    if not pdf_path.is_file():
        raise EzReviewPacketError(f"Δεν βρέθηκε το PDF πηγής: {pdf_path}")
    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf_path) as document:
        if page_number > document.page_count:
            raise EzReviewPacketError("Η καρτέλα δείχνει σελίδα που δεν υπάρχει στο PDF.")
        page = document[page_number - 1]
        clip = (rectangle + (-padding, -padding, padding, padding)) & page.rect
        pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
        crop_path = destination / "source-crop.png"
        pixmap.save(crop_path)
    anchors = [glyph.get("source_anchor") for glyph in line.get("source_glyphs", []) if isinstance(glyph, Mapping)]
    plan = {
        "schema": 1,
        "purpose": "private-ez-confirmed-phrase-plan; awaiting-human-confirmation",
        "source_label": review_sheet.get("source_label"),
        "review_line": line_id,
        "source_page": page_number,
        "confirmed": False,
        "events": [],
        "unassigned_source_anchors": anchors,
        "warning": "Πρότυπο ελέγχου· δεν περνά στον compiler πριν συμπληρωθούν επιβεβαιωμένα events.",
    }
    plan_path = destination / "phrase-plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checklist_path = destination / "review.md"
    checklist_path.write_text(_line_markdown(line_id, page_number, line), encoding="utf-8")
    return {"crop": crop_path, "phrase_plan": plan_path, "checklist": checklist_path}
