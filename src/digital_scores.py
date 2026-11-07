"""Local registry for reviewed, executable Byzantine music transcriptions.

The scanned books remain the authoritative visual sources in Kihem. A digital
score is a separate editorial object: it records a Neanes source (``.byzx``),
an optional MusicXML export and the provenance/review required before it is
presented as a teaching or playback aid.
"""

from __future__ import annotations

import json
import os
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal, Mapping

from src.isokratis import DI_RULE_MODES, default_ison_for, mode_key_from_tone_label


REVIEW_STATES: Final[frozenset[str]] = frozenset({"draft", "needs_review", "verified"})
ReviewState = Literal["draft", "needs_review", "verified"]

# Parallage (note names) shown while a score plays.  The raw values are
# Neanes ``ScaleNote`` names recorded by ``write_note_names``.
_PARALLAGE_NAMES: Final[Mapping[str, str]] = {
    "Zo": "Ζω",
    "Ni": "Νη",
    "Pa": "Πα",
    "Vou": "Βου",
    "Ga": "Γα",
    "Thi": "Δι",
    "Ke": "Κε",
}

# Written ScaleNote names to the seven-step scale used by the automatic ison:
# Pa = 0, Δι (Thi) = 3.  The names come from Neanes' private note-name sidecar.
_ISON_NOTE_VALUES: Final[Mapping[str, int]] = {
    "ZoLow": -9,
    "NiLow": -8,
    "PaLow": -7,
    "VouLow": -6,
    "GaLow": -5,
    "ThiLow": -4,
    "KeLow": -3,
    "Zo": -2,
    "Ni": -1,
    "Pa": 0,
    "Vou": 1,
    "Ga": 2,
    "Thi": 3,
    "Ke": 4,
    "ZoHigh": 5,
    "NiHigh": 6,
    "PaHigh": 7,
}
_DI_VALUE: Final[int] = 3
_GA_VALUE: Final[int] = 2

# Optional editorial data: the genus and opening note read from the small
# signs beside each score's martyria.  It is private project data, not part of
# the public catalogue schema.
ISON_GENUS_PATH: Final = Path(__file__).resolve().parent / "data" / "ison_genus.json"


def load_ison_genus(path: str | Path | None = None) -> dict[str, dict[str, str]]:
    """Read ``{score_id: {"genus": ..., "start": ...}}`` without ever raising.

    A missing, unreadable or malformed file yields an empty mapping, and
    malformed rows are ignored.  The caller treats absent data as unknown.
    """

    try:
        payload = json.loads(Path(path or ISON_GENUS_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for score_id, entry in payload.items():
        if not isinstance(score_id, str) or not isinstance(entry, dict):
            continue
        row = {
            key: value.strip()
            for key, value in entry.items()
            if key in {"genus", "start"} and isinstance(value, str) and value.strip()
        }
        if row:
            result[score_id] = row
    return result


@lru_cache(maxsize=1)
def ison_genus_table() -> dict[str, dict[str, str]]:
    """Load the genus table once, lazily; an absent file yields ``{}``."""

    return load_ison_genus(ISON_GENUS_PATH)


def parallage_label(scale_note: str) -> str | None:
    """Return the Greek note name for a Neanes ScaleNote, with its octave."""

    for suffix, octave in (("Low", " κάτω"), ("High", " άνω"), ("", "")):
        base = scale_note[: -len(suffix)] if suffix else scale_note
        if (not suffix or scale_note.endswith(suffix)) and base in _PARALLAGE_NAMES:
            return _PARALLAGE_NAMES[base] + octave
    return None


def _physical_note_value(physical: object, index: int) -> int | None:
    """Return the first written ScaleNote value for one element index."""

    if not isinstance(physical, dict):
        return None
    notes = physical.get(str(index))
    if not isinstance(notes, list) or not notes or not isinstance(notes[0], str):
        return None
    return _ISON_NOTE_VALUES.get(notes[0])


@dataclass(frozen=True)
class DigitalScore:
    """One locally stored transcription and its editorial provenance."""

    score_id: str
    title: str
    incipit: str
    tone_label: str
    source_description: str
    source_reference: str | None
    source_url: str | None
    transcription_by: str
    review_state: ReviewState
    reviewed_by: str | None
    notes: str | None
    byzx_filename: str | None
    ocr_filename: str | None
    musicxml_filename: str | None
    preview_filename: str | None
    source_scan_filenames: tuple[str, ...]
    # Neanes speed multiplier (0.1–3); slow genres such as koinonika use < 1.
    playback_speed: float = 1.0
    # The owner may let an unreviewed ``needs_review`` draft appear in the
    # service pages and the public player; the pages then label it as an
    # automatic draft.  It never counts as verified and is not listed in the
    # public catalogue.
    public_draft: bool = False

    @property
    def is_verified(self) -> bool:
        return self.review_state == "verified"

    @property
    def is_public(self) -> bool:
        """True for a verified score or an owner-approved public draft."""

        return self.is_verified or self.public_draft


class DigitalScoreCatalog:
    """Read a small JSON catalogue and expose only safely local assets."""

    def __init__(self, catalog_path: str | Path, storage_dir: str | Path):
        self.catalog_path = Path(catalog_path)
        self.storage_dir = Path(storage_dir)

    def scores(self) -> tuple[DigitalScore, ...]:
        if not self.catalog_path.is_file():
            return ()
        try:
            payload = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Μη έγκυρος κατάλογος ψηφιακών παρτιτούρων: {self.catalog_path}") from exc
        if payload.get("schema") != 1 or not isinstance(payload.get("scores"), list):
            raise ValueError("Ο κατάλογος ψηφιακών παρτιτούρων δεν έχει τη μορφή schema 1.")

        result: list[DigitalScore] = []
        seen_ids: set[str] = set()
        for item in payload["scores"]:
            score = self._parse_score(item)
            if score.score_id in seen_ids:
                raise ValueError(f"Διπλό αναγνωριστικό ψηφιακής παρτιτούρας: {score.score_id}")
            seen_ids.add(score.score_id)
            result.append(score)
        return tuple(result)

    def get(self, score_id: str) -> DigitalScore | None:
        return next((score for score in self.scores() if score.score_id == score_id), None)

    def verified_scores(self) -> tuple[DigitalScore, ...]:
        return tuple(score for score in self.scores() if score.is_verified)

    def public_scores(self) -> tuple[DigitalScore, ...]:
        """Scores that may be shown in a service page: verified or public drafts."""

        return tuple(score for score in self.scores() if score.is_public)

    def asset_path(self, score: DigitalScore, kind: Literal["byzx", "ocr", "musicxml", "preview"]) -> Path | None:
        filename = {
            "byzx": score.byzx_filename,
            "ocr": score.ocr_filename,
            "musicxml": score.musicxml_filename,
            "preview": score.preview_filename,
        }[kind]
        if not filename:
            return None
        candidate = (self.storage_dir / filename).resolve()
        try:
            candidate.relative_to(self.storage_dir.resolve())
        except ValueError:
            return None
        return candidate if candidate.is_file() else None

    def note_labels(self, score: DigitalScore) -> dict[str, list[str]] | None:
        """Return ``{element index: [Greek note names]}`` from the private sidecar.

        The sidecar ``<score>.notes.json`` is optional; without it the player
        simply shows no parallage.  Unknown or malformed data is ignored.
        """

        byzx = self.asset_path(score, "byzx")
        if byzx is None:
            return None
        sidecar = byzx.with_suffix(".notes.json")
        try:
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        elements = payload.get("elements") if isinstance(payload, dict) and payload.get("schema") == 1 else None
        if not isinstance(elements, dict):
            return None
        labels: dict[str, list[str]] = {}
        for index, notes in elements.items():
            if not (isinstance(index, str) and index.isdigit() and isinstance(notes, list)):
                continue
            names = [name for note in notes if isinstance(note, str) and (name := parallage_label(note))]
            if names:
                labels[index] = names
        return labels or None

    def hidden_elements(self, score: DigitalScore) -> list[int]:
        """Return the element indices the readers must not draw.

        They are listed in the optional ``hidden`` entry of the same sidecar,
        for elements that sound without being part of the source notation,
        such as a pause added for the chanter.  Malformed data is ignored.
        """

        byzx = self.asset_path(score, "byzx")
        if byzx is None:
            return []
        try:
            payload = json.loads(byzx.with_suffix(".notes.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        hidden = payload.get("hidden") if isinstance(payload, dict) and payload.get("schema") == 1 else None
        if not isinstance(hidden, list):
            return []
        return sorted({index for index in hidden if isinstance(index, int) and not isinstance(index, bool) and index >= 0})

    def ison_marks(self, score: DigitalScore) -> list[list[int | str]]:
        """Return ``[[element index, ison name], ...]`` from the private ``.byzx``.

        A score carries its ison marks (``ison: "Ison.Pa"``) on staff elements.
        The element index is the zero-based position in ``staff.elements``,
        the same number used by the Neanes ``element-N`` boxes and the
        ``.notes.json`` sidecar keys.  Only the tiny mark list is exposed; the
        score file itself is never served here.  Missing or malformed files
        yield an empty list and never raise.
        """

        byzx = self.asset_path(score, "byzx")
        if byzx is None:
            return []
        try:
            payload = json.loads(byzx.read_text(encoding="utf-8"))
            elements = payload["staff"]["elements"]
        except (OSError, ValueError, KeyError, TypeError):
            return []
        if not isinstance(elements, list):
            return []
        marks: list[list[int | str]] = []
        for index, element in enumerate(elements):
            if not isinstance(element, dict):
                continue
            name = element.get("ison")
            if isinstance(name, str) and name.strip():
                marks.append([index, name.strip()])
        return marks

    def auto_ison_marks(self, score: DigitalScore) -> list[list[int | str]]:
        """Return automatic ison marks for a score with no marks of its own.

        This is a deliberately simple editorial default, not a claim about
        what the PDF says.  The mode comes from ``tone_label`` and the
        refined default from ``src/data/ison_genus.json`` (loaded once,
        lazily) through :func:`src.isokratis.default_ison_for`; the first
        sounding note gets that ison.  The score is then split at its
        Martyria elements.  In modes 4 and 8 (:data:`src.isokratis.DI_RULE_MODES`)
        a segment whose median written melody note lies above Δι uses Δι for
        that segment, unless the mode default is already at or above Δι.  In
        mode 2 with the soft-chromatic genus the real ison alternates Βου and
        Δι with the melody: a segment whose median is up to Γα uses Βου and a
        higher segment uses Δι, so the first mark is the first segment's.
        This rule comes from 22 real-marked papline scores (5109 notes; small
        sample, mainly Lambadarios/Nikolaidis); leave-one-piece-out accuracy
        was 0.87 versus 0.56 for the best constant, with real marks split
        Βου 44 % / Δι 56 %.  Hard-chromatic mode 2 keeps constant Πα.  Other
        modes keep the plain mode/genus default for the whole piece.  Equal
        consecutive marks are merged.  Missing files, sidecars or genus data
        never raise; without the private ``.notes.json`` sidecar only the
        single default mark is returned.
        """

        if self.ison_marks(score):
            return []
        mode = mode_key_from_tone_label(score.tone_label)
        if mode is None:
            return []
        genus_entry = ison_genus_table().get(score.score_id, {})
        genus = genus_entry.get("genus")
        default = default_ison_for(
            mode,
            genus,
            score.tone_label,
            genus_entry.get("start"),
        )
        if default is None:
            return []
        byzx = self.asset_path(score, "byzx")
        if byzx is None:
            return []
        try:
            payload = json.loads(byzx.read_text(encoding="utf-8"))
            elements = payload["staff"]["elements"]
        except (OSError, ValueError, KeyError, TypeError):
            return []
        if not isinstance(elements, list):
            return []
        first_note = next(
            (
                index
                for index, element in enumerate(elements)
                if isinstance(element, dict) and element.get("elementType") == "Note"
            ),
            None,
        )
        if first_note is None:
            return []
        marks: list[list[int | str]] = [[first_note, default]]

        genus_key = genus.strip().lower() if isinstance(genus, str) else None
        soft_chromatic_mode_two = mode == "2" and genus_key == "soft-chromatic"
        if mode not in DI_RULE_MODES and not soft_chromatic_mode_two:
            return marks

        try:
            sidecar = json.loads(byzx.with_suffix(".notes.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return marks
        physical = sidecar.get("physical") if isinstance(sidecar, dict) and sidecar.get("schema") == 1 else None
        if not isinstance(physical, dict):
            return marks

        segments: list[list[tuple[int, int]]] = []
        current: list[tuple[int, int]] = []
        for index, element in enumerate(elements):
            if not isinstance(element, dict):
                continue
            element_type = element.get("elementType")
            if element_type == "Martyria":
                if current:
                    segments.append(current)
                    current = []
            elif element_type == "Note":
                value = _physical_note_value(physical, index)
                if value is not None:
                    current.append((index, value))
        if current:
            segments.append(current)

        if soft_chromatic_mode_two:
            segment_marks: list[list[int | str]] = []
            current_ison: str | None = None
            for segment in segments:
                if not segment:
                    continue
                median = statistics.median(value for _, value in segment)
                wanted = "Ison.Vou" if median <= _GA_VALUE else "Ison.Thi"
                if wanted != current_ison:
                    segment_marks.append([segment[0][0], wanted])
                    current_ison = wanted
            return segment_marks or marks

        default_value = _ISON_NOTE_VALUES.get(default[5:])
        if default_value is None or default_value >= _DI_VALUE:
            return marks
        current_ison = default
        # The first segment already starts with the default mark above.
        for segment in segments[1:]:
            if not segment:
                continue
            median = statistics.median(value for _, value in segment)
            wanted = "Ison.Thi" if median > _DI_VALUE else default
            if wanted != current_ison:
                marks.append([segment[0][0], wanted])
                current_ison = wanted
        return marks

    def source_scan_path(self, score: DigitalScore, position: int) -> Path | None:
        """Return one reviewed-source image without permitting path traversal."""
        if position < 0 or position >= len(score.source_scan_filenames):
            return None
        candidate = (self.storage_dir / score.source_scan_filenames[position]).resolve()
        try:
            candidate.relative_to(self.storage_dir.resolve())
        except ValueError:
            return None
        return candidate if candidate.is_file() else None

    @staticmethod
    def _parse_score(item: object) -> DigitalScore:
        if not isinstance(item, dict):
            raise ValueError("Κάθε ψηφιακή παρτιτούρα πρέπει να είναι αντικείμενο JSON.")
        required = ("id", "title", "incipit", "tone_label", "source_description", "transcription_by", "review_state")
        values: dict[str, str] = {}
        for name in required:
            value = item.get(name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Λείπει το υποχρεωτικό πεδίο ψηφιακής παρτιτούρας: {name}")
            values[name] = value.strip()

        score_id = values["id"]
        if not score_id.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Μη ασφαλές αναγνωριστικό ψηφιακής παρτιτούρας: {score_id}")
        review_state = values["review_state"]
        if review_state not in REVIEW_STATES:
            raise ValueError(f"Άγνωστη κατάσταση ελέγχου ψηφιακής παρτιτούρας: {review_state}")

        def optional_text(name: str) -> str | None:
            value = item.get(name)
            if value is None:
                return None
            if not isinstance(value, str):
                raise ValueError(f"Το πεδίο {name} πρέπει να είναι κείμενο.")
            return value.strip() or None

        def optional_filename(name: str, suffixes: tuple[str, ...]) -> str | None:
            filename = optional_text(name)
            if filename is None:
                return None
            path = Path(filename)
            if path.name != filename or path.suffix.lower() not in suffixes:
                raise ValueError(f"Μη ασφαλές ή ακατάλληλο όνομα αρχείου στο {name}: {filename}")
            return filename

        def optional_filenames(name: str, suffixes: tuple[str, ...]) -> tuple[str, ...]:
            value = item.get(name)
            if value is None:
                return ()
            if not isinstance(value, list):
                raise ValueError(f"Το πεδίο {name} πρέπει να είναι λίστα ονομάτων αρχείων.")
            filenames: list[str] = []
            for index, filename in enumerate(value):
                if not isinstance(filename, str):
                    raise ValueError(f"Το στοιχείο {index} του {name} πρέπει να είναι κείμενο.")
                path = Path(filename)
                if path.name != filename or path.suffix.lower() not in suffixes:
                    raise ValueError(f"Μη ασφαλές ή ακατάλληλο όνομα αρχείου στο {name}: {filename}")
                filenames.append(filename)
            return tuple(filenames)

        playback_speed = item.get("playback_speed", 1.0)
        if isinstance(playback_speed, bool) or not isinstance(playback_speed, (int, float)) or not 0.1 <= playback_speed <= 3:
            raise ValueError("Το πεδίο playback_speed πρέπει να είναι αριθμός από 0.1 έως 3.")

        public_draft = item.get("public_draft", False)
        if not isinstance(public_draft, bool):
            raise ValueError("Το πεδίο public_draft πρέπει να είναι true ή false.")
        if public_draft and review_state != "needs_review":
            raise ValueError("Δημόσιο draft πρέπει να έχει κατάσταση needs_review.")

        reviewed_by = optional_text("reviewed_by")
        if review_state == "verified" and not reviewed_by:
            raise ValueError("Επαληθευμένη ψηφιακή παρτιτούρα απαιτεί όνομα ελεγκτή ψάλτη.")
        return DigitalScore(
            score_id=score_id,
            title=values["title"],
            incipit=values["incipit"],
            tone_label=values["tone_label"],
            source_description=values["source_description"],
            source_reference=optional_text("source_reference"),
            source_url=optional_text("source_url"),
            transcription_by=values["transcription_by"],
            review_state=review_state,  # type: ignore[arg-type]
            reviewed_by=reviewed_by,
            notes=optional_text("notes"),
            byzx_filename=optional_filename("byzx_filename", (".byzx",)),
            ocr_filename=optional_filename("ocr_filename", (".byzocr",)),
            musicxml_filename=optional_filename("musicxml_filename", (".musicxml", ".xml")),
            preview_filename=optional_filename("preview_filename", (".png", ".jpg", ".jpeg", ".webp")),
            source_scan_filenames=optional_filenames("source_scan_filenames", (".png", ".jpg", ".jpeg", ".webp")),
            playback_speed=float(playback_speed),
            public_draft=public_draft,
        )


class DigitalScoreReviewStore:
    """Private, local notes from a human review; never a publication switch."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def read(self, score_id: str) -> dict[str, object] | None:
        path = self._path(score_id)
        if not path.is_file():
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def save(self, score_id: str, reviewer: str, checks: Mapping[str, bool], notes: str) -> dict[str, object]:
        self.directory.mkdir(parents=True, exist_ok=True)
        record: dict[str, object] = {
            "score_id": score_id,
            "reviewer": reviewer.strip(),
            "checks": {key: bool(value) for key, value in checks.items()},
            "notes": notes.strip(),
            "saved_at": datetime.now(UTC).isoformat(),
        }
        target = self._path(score_id)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, target)
        return record

    @staticmethod
    def _safe_score_id(score_id: str) -> str:
        if not score_id or not score_id.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Μη ασφαλές αναγνωριστικό ελέγχου παρτιτούρας.")
        return score_id

    def _path(self, score_id: str) -> Path:
        return self.directory / f"{self._safe_score_id(score_id)}.json"
