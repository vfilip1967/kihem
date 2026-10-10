"""Build a private Neanes event draft from exact-font EZ Word evidence.

Legacy Word files do not contain PDF glyph ids, but Apache POI preserves the
actual font run and ordered PUA occurrence.  This bridge therefore uses the
stable pair ``word_occurrence + pua_codepoint`` as its auditable source anchor.
It intentionally accepts only reviewer-confirmed events whose EZ definitions
already identify one quantitative neume.
"""

from __future__ import annotations

from typing import Any, Mapping

from .ez_neanes_draft import (
    _ATTACHMENT_TYPES,
    _MARTYRIA_FIELDS,
    _NEANES_NOTE_FIELDS,
    EzPhrasePlanError,
)


class EzWordPhrasePlanError(EzPhrasePlanError):
    """Raised when a direct-Word phrase plan lacks verifiable evidence."""


_MARTYRIA_NOTES = {
    "ZoLow", "NiLow", "PaLow", "VouLow", "GaLow", "ThiLow", "KeLow",
    "Zo", "Ni", "Pa", "Vou", "Ga", "Thi", "Ke",
    "ZoHigh", "NiHigh", "PaHigh", "VouHigh", "GaHigh", "ThiHigh", "KeHigh",
}
_MARTYRIA_ROOT_SIGNS = {
    "Delta", "Alpha", "Legetos", "Nana", "Tilt", "TiltLow", "Varys", "VarysLow",
    "Squiggle", "SquiggleLow", "Zygos", "ZygosLow", "SoftChromaticSquiggle",
    "SoftChromaticSquiggleLow", "DeltaDotted", "DeltaDottedLow", "AlphaDotted",
    "AlphaDottedLow", "SoftChromaticPaRootSign", "SoftChromaticPaRootSignLow",
    "NanaLow", "DeltaLow", "AlphaLow", "LegetosLow",
}
_MARTYRIA_SCALES = {
    "Diatonic", "SoftChromatic", "HardChromatic", "EnharmonicGa", "EnharmonicZo",
    "EnharmonicZoHigh", "EnharmonicVou", "EnharmonicVouHigh", "Zygos", "Spathi",
    "SpathiGa", "Kliton",
}


def _anchor_key(anchor: Mapping[str, Any]) -> tuple[int, str]:
    try:
        return int(anchor["word_occurrence"]), str(anchor["pua_codepoint"])
    except (KeyError, TypeError, ValueError) as error:
        raise EzWordPhrasePlanError("Κάθε Word anchor χρειάζεται word_occurrence και pua_codepoint.") from error


def _index_word_occurrences(report: Mapping[str, Any]) -> dict[tuple[int, str], Mapping[str, Any]]:
    expected = "private-ez-word-font-run-report; source-font-confirmed; no-byzx-generated"
    if report.get("purpose") != expected:
        raise EzWordPhrasePlanError("Δεν δόθηκε έγκυρο private EZ Word font-run report.")
    index: dict[tuple[int, str], Mapping[str, Any]] = {}
    for run in report.get("runs", []):
        for occurrence in run.get("pua_occurrences", []):
            if occurrence.get("status") != "source-font-confirmed; no-neanes-event":
                continue
            index[_anchor_key(occurrence)] = occurrence
    if not index:
        raise EzWordPhrasePlanError("Το Word report δεν έχει επιβεβαιωμένα EZ font-runs.")
    return index


def _candidate(occurrence: Mapping[str, Any]) -> Mapping[str, Any]:
    definition = occurrence.get("source_definition")
    candidate = definition.get("neanes_candidate") if isinstance(definition, Mapping) else None
    if not isinstance(candidate, Mapping):
        raise EzWordPhrasePlanError("Το Word σύμβολο δεν έχει τεκμηριωμένο ορισμό EZ.")
    return candidate


def _compile_opening_martyria(phrase_plan: Mapping[str, Any]) -> dict[str, str] | None:
    """Keep a starting martyria only after separate human/source confirmation.

    Formula Word files often omit an initial martyria. A collection heading
    such as “First Mode” must therefore never establish a formula's base.
    """

    martyria = phrase_plan.get("opening_martyria")
    if martyria is None:
        return None
    if not isinstance(martyria, Mapping) or martyria.get("confirmed") is not True:
        raise EzWordPhrasePlanError("Η αρχική μαρτυρία χρειάζεται δική της επιβεβαίωση (confirmed: true).")
    evidence = martyria.get("source_evidence")
    if not isinstance(evidence, Mapping):
        raise EzWordPhrasePlanError("Η αρχική μαρτυρία χρειάζεται source_evidence από την ορατή πηγή.")
    reference = evidence.get("reference")
    if not isinstance(reference, str) or not reference.strip():
        raise EzWordPhrasePlanError("Η αρχική μαρτυρία χρειάζεται μη κενή παραπομπή πηγής.")
    missing = _MARTYRIA_FIELDS - set(martyria)
    if missing:
        raise EzWordPhrasePlanError(f"Η αρχική μαρτυρία δεν έχει πεδία: {sorted(missing)}.")
    result = {field: str(martyria[field]) for field in _MARTYRIA_FIELDS}
    if result["note"] not in _MARTYRIA_NOTES:
        raise EzWordPhrasePlanError("Η αρχική μαρτυρία έχει άγνωστο Neanes note.")
    if result["rootSign"] not in _MARTYRIA_ROOT_SIGNS:
        raise EzWordPhrasePlanError("Η αρχική μαρτυρία έχει άγνωστο Neanes rootSign.")
    if result["scale"] not in _MARTYRIA_SCALES:
        raise EzWordPhrasePlanError("Η αρχική μαρτυρία έχει άγνωστη Neanes scale.")
    return result


def compile_confirmed_ez_word_phrase_plan(
    report: Mapping[str, Any], phrase_plan: Mapping[str, Any]
) -> dict[str, Any]:
    """Compile a verified Word formula phrase to private Neanes Note events."""

    if phrase_plan.get("schema") != 1:
        raise EzWordPhrasePlanError("Το Word phrase plan χρειάζεται schema: 1.")
    if not isinstance(phrase_plan.get("reviewer"), str) or not phrase_plan["reviewer"].strip():
        raise EzWordPhrasePlanError("Το Word phrase plan χρειάζεται ονομασμένο ψάλτη ελεγκτή.")
    events = phrase_plan.get("events")
    if not isinstance(events, list) or not events:
        raise EzWordPhrasePlanError("Το Word phrase plan δεν έχει μουσικά γεγονότα.")
    index = _index_word_occurrences(report)
    compiled: list[dict[str, Any]] = []
    for number, event in enumerate(events, start=1):
        if not isinstance(event, Mapping) or event.get("confirmed") is not True:
            raise EzWordPhrasePlanError(f"Το Word γεγονός {number} χρειάζεται confirmed: true.")
        resolution = event.get("resolution")
        if not isinstance(resolution, Mapping):
            raise EzWordPhrasePlanError(f"Το Word γεγονός {number} δεν έχει resolution Neanes.")
        unexpected = set(resolution) - _NEANES_NOTE_FIELDS
        if unexpected:
            raise EzWordPhrasePlanError(f"Το Word γεγονός {number} έχει άγνωστα πεδία: {sorted(unexpected)}.")
        quantitative = resolution.get("quantitativeNeume")
        if not isinstance(quantitative, str) or not quantitative:
            raise EzWordPhrasePlanError(f"Το Word γεγονός {number} χρειάζεται quantitativeNeume.")
        anchors = event.get("source_anchors")
        if not isinstance(anchors, list) or not anchors:
            raise EzWordPhrasePlanError(f"Το Word γεγονός {number} δεν έχει source_anchors.")
        occurrences = []
        for anchor in anchors:
            if not isinstance(anchor, Mapping):
                raise EzWordPhrasePlanError(f"Το Word γεγονός {number} έχει μη έγκυρο source_anchor.")
            occurrence = index.get(_anchor_key(anchor))
            if occurrence is None:
                raise EzWordPhrasePlanError(f"Το Word γεγονός {number} δείχνει σύμβολο που δεν υπάρχει στο report.")
            occurrences.append(occurrence)
        candidates = [_candidate(occurrence) for occurrence in occurrences]
        bases = [item for item in candidates if item.get("element_type") == "quantitativeNeume"]
        if len(bases) != 1 or bases[0].get("value") != quantitative:
            raise EzWordPhrasePlanError(f"Το Word γεγονός {number} δεν τεκμηριώνει το βασικό νεύμα {quantitative}.")
        if any(item.get("element_type") == "decomposition" for item in candidates):
            raise EzWordPhrasePlanError(f"Το Word γεγονός {number} περιέχει σύνθετο EZ glyph και δεν αυτοματοποιείται.")
        for field, source_type in _ATTACHMENT_TYPES.items():
            if field not in resolution:
                continue
            matches = [item for item in candidates if item.get("element_type") == source_type]
            if not matches:
                raise EzWordPhrasePlanError(f"Το Word γεγονός {number} έχει {field} χωρίς δικό του EZ anchor.")
            values = {item.get("value") for item in matches if item.get("value") is not None}
            if values and resolution[field] not in values:
                raise EzWordPhrasePlanError(f"Το Word γεγονός {number} διαφωνεί με τον τεκμηριωμένο κωδικό EZ.")
        compiled.append({"elementType": "Note", **dict(resolution)})
    result = {
        "schema": 1,
        "purpose": "private-confirmed-ez-neanes-event-draft; not-a-complete-byzx-score",
        "source_label": report.get("source_label"),
        "source_filename": report.get("source_filename"),
        "reviewer": phrase_plan["reviewer"],
        "review_state": "needs_score_and_auditory_review",
        "events": compiled,
        "warning": "Ιδιωτικό Word→Neanes pilot· απαιτεί οπτικό και ακουστικό ψαλτικό έλεγχο.",
    }
    martyria = _compile_opening_martyria(phrase_plan)
    if martyria is not None:
        result["opening_martyria"] = martyria
    return result
