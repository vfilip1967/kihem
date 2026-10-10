"""Compile a *confirmed* EZ phrase plan into Neanes note-event data.

This is deliberately a small, conservative bridge.  The EZ mapping template
records what a PDF glyph is; a phrase plan records a reviewer’s decision about
which glyphs form one musical event and where the attached signs belong.  Only
then can this module produce the event objects that Neanes stores in a
``.byzx`` score.

It does not write a complete score file, publish a source, or make decisions
from glyph appearance.  The resulting JSON is a private draft payload for the
Neanes import step.  A caller must still create the score, assign lyrics and
visually/audibly review the result.
"""

from __future__ import annotations

from typing import Any, Mapping


class EzPhrasePlanError(ValueError):
    """Raised when a phrase plan lacks auditable musical confirmation."""


_NEANES_NOTE_FIELDS = {
    "quantitativeNeume",
    "gorgonNeume",
    "timeNeume",
    "vocalExpressionNeume",
    "accidental",
    "fthora",
    "ison",
    "measureBar",
    "measureNumber",
    "vareia",
    "lyrics",
    "isMelisma",
    "isMelismaStart",
    "isHyphen",
    "lineBreak",
}

_ATTACHMENT_TYPES = {
    "gorgonNeume": "gorgonNeume",
    "timeNeume": "timeNeume",
    "vocalExpressionNeume": "vocalExpressionNeume",
    "ison": "ison",
    "vareia": "vareia",
}

_MARTYRIA_FIELDS = {"note", "rootSign", "scale"}


def _anchor_key(anchor: Mapping[str, Any]) -> tuple[str, int, str]:
    """Return the stable PDF glyph identity used by the EZ template."""

    try:
        return (
            str(anchor["pdf_font_instance"]),
            int(anchor["pdf_glyph_id"]),
            str(anchor["pua_codepoint"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EzPhrasePlanError(
            "Κάθε source_anchor χρειάζεται pdf_font_instance, pdf_glyph_id και pua_codepoint."
        ) from exc


def _row_index(mapping_template: Mapping[str, Any]) -> dict[tuple[str, int, str], Mapping[str, Any]]:
    rows: dict[tuple[str, int, str], Mapping[str, Any]] = {}
    for row in mapping_template.get("rows", []):
        source = row.get("source", {})
        try:
            rows[_anchor_key(source)] = row
        except EzPhrasePlanError:
            continue
    return rows


def _candidate(row: Mapping[str, Any]) -> Mapping[str, Any]:
    source_definition = row.get("source_definition")
    candidate = source_definition.get("neanes_candidate") if isinstance(source_definition, Mapping) else None
    if not isinstance(candidate, Mapping):
        raise EzPhrasePlanError(
            "Το glyph δεν έχει τεκμηριωμένο ορισμό EZ· δεν μπορεί να μπει σε draft."
        )
    return candidate


def _require_confirmed_event(event: Mapping[str, Any], number: int) -> None:
    if event.get("confirmed") is not True:
        raise EzPhrasePlanError(
            f"Το γεγονός {number} δεν έχει ρητή επιβεβαίωση ψάλτη (confirmed: true)."
        )


def _resolve_note(
    event: Mapping[str, Any], index: Mapping[tuple[str, int, str], Mapping[str, Any]], number: int
) -> dict[str, Any]:
    _require_confirmed_event(event, number)
    resolution = event.get("resolution")
    if not isinstance(resolution, Mapping):
        raise EzPhrasePlanError(f"Το γεγονός {number} δεν έχει resolution Neanes.")
    unexpected = set(resolution) - _NEANES_NOTE_FIELDS
    if unexpected:
        raise EzPhrasePlanError(f"Το γεγονός {number} έχει άγνωστα πεδία Neanes: {sorted(unexpected)}.")
    quantitative = resolution.get("quantitativeNeume")
    if not isinstance(quantitative, str) or not quantitative:
        raise EzPhrasePlanError(f"Το γεγονός {number} χρειάζεται quantitativeNeume.")

    anchors = event.get("source_anchors")
    if not isinstance(anchors, list) or not anchors:
        raise EzPhrasePlanError(f"Το γεγονός {number} δεν έχει source_anchors.")
    rows: list[Mapping[str, Any]] = []
    for anchor in anchors:
        if not isinstance(anchor, Mapping):
            raise EzPhrasePlanError(f"Το γεγονός {number} έχει μη έγκυρο source_anchor.")
        row = index.get(_anchor_key(anchor))
        if row is None:
            raise EzPhrasePlanError(f"Το γεγονός {number} δείχνει glyph που δεν υπάρχει στο EZ template.")
        if row.get("source", {}).get("glyph_id_matches_full_font") is not True:
            raise EzPhrasePlanError(f"Το γεγονός {number} έχει glyph id που δεν συμφωνεί με την πλήρη EZ γραμματοσειρά.")
        rows.append(row)

    candidates = [_candidate(row) for row in rows]
    base_candidates = [item for item in candidates if item.get("element_type") == "quantitativeNeume"]
    if len(base_candidates) != 1 or base_candidates[0].get("value") != quantitative:
        raise EzPhrasePlanError(
            f"Το γεγονός {number} δεν τεκμηριώνει μονοσήμαντα το βασικό νεύμα {quantitative}."
        )

    # Each optional attachment must be anchored by a documented EZ symbol.
    # A bare gorgon has no fixed top/bottom position; the reviewer resolves
    # that position explicitly in ``resolution`` and signs off the event.
    for field, source_type in _ATTACHMENT_TYPES.items():
        if field not in resolution:
            continue
        matches = [item for item in candidates if item.get("element_type") == source_type]
        if not matches:
            raise EzPhrasePlanError(f"Το γεγονός {number} έχει {field} χωρίς αντίστοιχο EZ glyph anchor.")
        if any(item.get("element_type") == "decomposition" for item in matches):
            raise EzPhrasePlanError(f"Το γεγονός {number} απαιτεί διάσπαση προ-συντεθειμένου glyph και δεν αυτοματοποιείται.")
        known_values = {item.get("value") for item in matches if item.get("value") is not None}
        if known_values and resolution[field] not in known_values:
            raise EzPhrasePlanError(f"Το γεγονός {number} δίνει {field} που διαφωνεί με τον τεκμηριωμένο κωδικό EZ.")
        if resolution[field] in (None, ""):
            raise EzPhrasePlanError(f"Το γεγονός {number} δεν καθορίζει την τιμή του {field}.")

    # A precomposed glyph needs a separate documented rule before it can be
    # silently decomposed into base plus attachment(s).
    if any(item.get("element_type") == "decomposition" for item in candidates):
        raise EzPhrasePlanError(
            f"Το γεγονός {number} περιέχει προ-συντεθειμένο EZ glyph· απαιτεί ειδικό, ελεγμένο κανόνα διάσπασης."
        )

    return {"elementType": "Note", **dict(resolution)}


def _resolve_ison_controls(
    controls: Any, index: Mapping[tuple[str, int, str], Mapping[str, Any]], note_count: int
) -> list[dict[str, Any]]:
    """Keep confirmed software-ison controls outside the Neanes note stream."""

    if controls is None:
        return []
    if not isinstance(controls, list):
        raise EzPhrasePlanError("Το ison_controls πρέπει να είναι λίστα.")
    result: list[dict[str, Any]] = []
    for number, control in enumerate(controls, start=1):
        if not isinstance(control, Mapping) or control.get("confirmed") is not True:
            raise EzPhrasePlanError(f"Το ison control {number} χρειάζεται confirmed: true.")
        if control.get("after_note_event") not in range(1, note_count + 1):
            raise EzPhrasePlanError(f"Το ison control {number} χρειάζεται έγκυρο after_note_event.")
        anchors = control.get("source_anchors")
        if not isinstance(anchors, list) or not anchors:
            raise EzPhrasePlanError(f"Το ison control {number} δεν έχει source_anchors.")
        candidates = []
        for anchor in anchors:
            if not isinstance(anchor, Mapping):
                raise EzPhrasePlanError(f"Το ison control {number} έχει μη έγκυρο source_anchor.")
            row = index.get(_anchor_key(anchor))
            if row is None or row.get("source", {}).get("glyph_id_matches_full_font") is not True:
                raise EzPhrasePlanError(f"Το ison control {number} δείχνει μη επιβεβαιωμένο EZ glyph.")
            candidates.append(_candidate(row))
        if len(candidates) != 1 or candidates[0].get("element_type") != "isonControl" or candidates[0].get("value") != "Pause":
            raise EzPhrasePlanError(f"Το ison control {number} δεν τεκμηριώνεται ως παύση ισοκράτηματος.")
        result.append({"kind": "pause", "after_note_event": control["after_note_event"]})
    return result


def compile_confirmed_ez_phrase_plan(
    mapping_template: Mapping[str, Any], phrase_plan: Mapping[str, Any]
) -> dict[str, Any]:
    """Return private Neanes-compatible Note event data from a checked plan.

    ``phrase_plan`` has a list of events.  Every event must have a reviewer
    confirmation, one known base glyph anchor and anchors for all requested
    gorgon/time/quality attachments.  The function fails closed: an unknown
    glyph or a precomposed glyph without a dedicated rule rejects the whole
    phrase.
    """

    if mapping_template.get("purpose") != "private-ez-to-neanes-mapping-template; no-byzx-generated":
        raise EzPhrasePlanError("Δεν δόθηκε έγκυρο EZ mapping template.")
    if phrase_plan.get("schema") != 1:
        raise EzPhrasePlanError("Το phrase plan χρειάζεται schema: 1.")
    events = phrase_plan.get("events")
    if not isinstance(events, list) or not events:
        raise EzPhrasePlanError("Το phrase plan δεν έχει μουσικά γεγονότα.")

    index = _row_index(mapping_template)
    compiled = [_resolve_note(event, index, number + 1) for number, event in enumerate(events)]
    result = {
        "schema": 1,
        "purpose": "private-confirmed-ez-neanes-event-draft; not-a-complete-byzx-score",
        "source_label": mapping_template.get("source_label"),
        "review_state": "needs_score_and_auditory_review",
        "events": compiled,
        "warning": (
            "Πρόχειρα στοιχεία Note για εισαγωγή Neanes. Δεν είναι πλήρες .byzx, "
            "δεν περιέχουν αυτόματα λεκτικό και δεν δημοσιεύονται."
        ),
    }
    martyria = phrase_plan.get("opening_martyria")
    if martyria is not None:
        if not isinstance(martyria, Mapping) or martyria.get("confirmed") is not True:
            raise EzPhrasePlanError("Η αρχική μαρτυρία χρειάζεται δική της επιβεβαίωση (confirmed: true).")
        missing = _MARTYRIA_FIELDS - set(martyria)
        if missing:
            raise EzPhrasePlanError(f"Η αρχική μαρτυρία δεν έχει πεδία: {sorted(missing)}.")
        result["opening_martyria"] = {field: martyria[field] for field in _MARTYRIA_FIELDS}
    ison_controls = _resolve_ison_controls(phrase_plan.get("ison_controls"), index, len(compiled))
    if ison_controls:
        result["ison_controls"] = ison_controls
    return result
