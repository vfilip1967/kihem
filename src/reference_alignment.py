"""Private, supervised reference ledgers for Byzantine-score comparison.

This module deliberately does *not* convert a scan into a Neanes document.
It records what an already reviewed Neanes source says, in a stable sequence,
so that a psaltis can associate it with the corresponding visual groups in a
scan.  Only those later, explicit human associations may become evidence for
a font- or edition-specific mapping.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from src.digital_scores import DigitalScore


REFERENCE_LEDGER_SCHEMA = 1
_NOTATION_FIELDS = (
    "quantitativeNeume",
    "gorgonNeume",
    "timeNeume",
    "vareia",
    "vocalExpressionNeume",
)


def build_reference_ledger(
    score: DigitalScore,
    byzx_path: str | Path,
    *,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    """Build an editable, private alignment scaffold for a reviewed score.

    A ``verified`` catalogue state proves that the score may be used as a
    reference document.  It does not prove the positional correspondence of
    every printed neume, so all ``source_anchor`` fields start as ``null`` and
    ``confirmed`` starts as false.
    """

    if not score.is_verified or not score.reviewed_by:
        raise ValueError("Μόνο επαληθευμένη παρτιτούρα με ονομασμένο ελεγκτή μπορεί να γίνει ζεύγος αναφοράς.")

    path = Path(byzx_path)
    try:
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Δεν διαβάζεται έγκυρο αρχείο Neanes .byzx: {path}") from exc
    if not isinstance(document, dict):
        raise ValueError("Το αρχείο Neanes .byzx δεν είναι αντικείμενο JSON.")

    staff = document.get("staff")
    elements = staff.get("elements") if isinstance(staff, dict) else None
    if not isinstance(elements, list):
        raise ValueError("Το αρχείο Neanes .byzx δεν περιέχει staff.elements.")

    notes: list[dict[str, object]] = []
    for element in elements:
        if not isinstance(element, dict) or element.get("elementType") != "Note":
            continue
        identifier = element.get("id")
        if not isinstance(identifier, int):
            raise ValueError("Βρέθηκε σημείο Neanes χωρίς ασφαλές αριθμητικό id.")
        notation = {name: element[name] for name in _NOTATION_FIELDS if isinstance(element.get(name), str) and element[name]}
        if not notation.get("quantitativeNeume"):
            raise ValueError(f"Το σημείο Neanes {identifier} δεν έχει ποσοτικό νεύμα.")
        lyric = element.get("lyrics")
        notes.append(
            {
                "sequence": len(notes) + 1,
                "neanes_element_id": identifier,
                "lyrics": lyric if isinstance(lyric, str) else "",
                "notation": notation,
                "source_anchor": None,
                "confirmed": False,
            }
        )
    if not notes:
        raise ValueError("Το αρχείο Neanes .byzx δεν περιέχει μουσικά σημεία.")

    timestamp = generated_at or datetime.now(UTC)
    return {
        "schema": REFERENCE_LEDGER_SCHEMA,
        "kind": "supervised-reference-pair",
        "status": "awaiting_phrase_alignment",
        "generated_at": timestamp.astimezone(UTC).isoformat(),
        "score": {
            "id": score.score_id,
            "title": score.title,
            "incipit": score.incipit,
            "tone_label": score.tone_label,
            "reviewed_by": score.reviewed_by,
            "byzx_sha256": hashlib.sha256(raw).hexdigest(),
            "note_count": len(notes),
        },
        "source": {
            "reference": score.source_reference,
            "scan_filenames": list(score.source_scan_filenames),
        },
        "notes": notes,
        "rules": {
            "mapping_scope": "edition-specific-and-human-confirmed-only",
            "do_not_generate_byzx": True,
            "do_not_promote_visual_similarity_to_music": True,
            "required_confirmation": "Κάθε source_anchor δηλώνει οπτικό τμήμα της σάρωσης και επιβεβαιώνεται από ψάλτη.",
        },
    }


def write_reference_ledger(path: str | Path, ledger: Mapping[str, Any]) -> Path:
    """Persist a private ledger atomically, without copying source images."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target


def record_phrase_anchors(
    ledger: Mapping[str, Any],
    groups: list[Mapping[str, Any]],
) -> dict[str, object]:
    """Record provisional scan-to-Neanes phrase ranges without a glyph map.

    The caller must supply each group in reading order.  The syllables are
    checked against the reviewed Neanes document, which prevents a phrase
    anchor from silently drifting to another part of the chant.  A phrase
    range is deliberately not a confirmation of individual printed glyphs.
    """

    notes = ledger.get("notes")
    if not isinstance(notes, list) or not notes:
        raise ValueError("Το ledger δεν περιέχει ακολουθία σημείων Neanes.")
    normalized = json.loads(json.dumps(ledger, ensure_ascii=False))
    expected_start = 1
    anchors: list[dict[str, object]] = []

    for index, group in enumerate(groups, start=1):
        group_id = group.get("id")
        start = group.get("sequence_start")
        end = group.get("sequence_end")
        syllables = group.get("syllables")
        source_part = group.get("source_scan_part")
        text = group.get("text")
        if not isinstance(group_id, str) or not group_id.strip():
            raise ValueError(f"Η φράση {index} δεν έχει ασφαλές αναγνωριστικό.")
        if not isinstance(start, int) or not isinstance(end, int) or start != expected_start or end < start:
            raise ValueError("Οι φράσεις πρέπει να καλύπτουν διαδοχικά τη σειρά Neanes χωρίς κενά ή επικάλυψη.")
        if not isinstance(syllables, list) or not all(isinstance(value, str) for value in syllables):
            raise ValueError(f"Η φράση {group_id} δεν έχει έγκυρες συλλαβές.")
        if not isinstance(source_part, int) or source_part < 1:
            raise ValueError(f"Η φράση {group_id} δεν έχει έγκυρο τμήμα σάρωσης.")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Η φράση {group_id} δεν έχει αναγνώσιμο κείμενο.")
        selected = notes[start - 1 : end]
        if len(selected) != end - start + 1:
            raise ValueError(f"Η φράση {group_id} υπερβαίνει τη σειρά Neanes.")
        actual_syllables = [note.get("lyrics", "") for note in selected if isinstance(note, dict)]
        if actual_syllables != syllables:
            raise ValueError(f"Οι συλλαβές της φράσης {group_id} δεν συμφωνούν με τη σειρά Neanes.")
        anchors.append(
            {
                "id": group_id.strip(),
                "sequence_start": start,
                "sequence_end": end,
                "text": text.strip(),
                "source_scan_part": source_part,
                "source_line": None,
                "visual_status": "pending_line_check",
                "individual_glyphs_confirmed": False,
            }
        )
        expected_start = end + 1

    if expected_start != len(notes) + 1:
        raise ValueError("Οι φράσεις δεν καλύπτουν όλα τα σημεία Neanes.")
    normalized["phrase_anchors"] = anchors
    normalized["status"] = "phrase_anchors_recorded_pending_visual_check"
    return normalized
