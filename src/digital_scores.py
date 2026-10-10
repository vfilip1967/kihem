"""Local registry for reviewed, executable Byzantine music transcriptions.

The scanned books remain the authoritative visual sources in Kihem. A digital
score is a separate editorial object: it records a Neanes source (``.byzx``),
an optional MusicXML export and the provenance/review required before it is
presented as a teaching or playback aid.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, Mapping


REVIEW_STATES: Final[frozenset[str]] = frozenset({"draft", "needs_review", "verified"})
ReviewState = Literal["draft", "needs_review", "verified"]


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

    @property
    def is_verified(self) -> bool:
        return self.review_state == "verified"


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
