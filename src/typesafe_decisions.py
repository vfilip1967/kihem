from __future__ import annotations

"""Confidence-gated TypeSafe/Jev decisions for ambiguous music placement."""

import hashlib
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import requests


TYPESAFE_SYSTEMONE_URL: Final = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL: Final = "jev-latest"
CACHE_VERSION: Final = 1
MINIMUM_CONFIDENCE: Final = 0.95
AINOI_STYLE_BY_TONE: Final[dict[int, str]] = {
    1: "slow_ainoi",
    2: "slow_ainoi",
    3: "short_ainoi",
    4: "short_ainoi",
    5: "slow_ainoi",
    6: "slow_ainoi",
    7: "short_ainoi",
    8: "short_ainoi",
}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MusicDecision:
    """A cached closed-set decision, with no free-form generated text."""

    choice: str
    confidence: float
    probabilities: dict[str, float]
    model: str


class TypesafeDecisionService:
    """Ask Jev only to choose among verified pieces or ``no_score``.

    A network/API failure intentionally returns ``None``.  The caller then
    follows the conservative local rule instead of treating an unavailable AI
    service as evidence for a musical choice.
    """

    def __init__(
        self,
        cache_dir: str | Path,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        session: requests.Session | None = None,
    ):
        self.cache_dir = Path(cache_dir) / "typesafe-decisions"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key if api_key is not None else os.environ.get("TYPESAFE_API_KEY")
        self.model = model
        self.session = session or requests.Session()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def review_timiotera(self, local_instruction: str) -> MusicDecision | None:
        """Choose only between the two verified Timiotera scores and no score."""
        if not self.enabled:
            return None

        payload = {
            "model": self.model,
            "state": {
                "member": "Τιμιωτέρα",
                "local_melodos_instruction": local_instruction,
            },
            "questions": {
                "score": {
                    "type": "choice",
                    "instructions": (
                        "Choose the sole verified score justified by the explicit "
                        "local Melodos instruction for the Timiotera."
                    ),
                    "criteria": {
                        "plagal4_timiotera": "Use only when the local instruction explicitly says Ἦχος πλ δ΄.",
                        "tone4_timiotera": "Use only when the local instruction explicitly says Ἦχος δ΄.",
                        "no_score": "Use when the instruction has no explicit local tone or is ambiguous.",
                    },
                }
            },
        }
        cached = self._read_cache(payload)
        if cached is not None:
            return cached

        try:
            response = self.session.post(
                TYPESAFE_SYSTEMONE_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=(4, 20),
            )
            response.raise_for_status()
            body = response.json()
            answer = body["answers"]["score"]
            if answer.get("type") != "choice":
                raise ValueError("TypeSafe returned a non-choice answer")
            decision = MusicDecision(
                choice=str(answer["choice"]),
                confidence=float(answer["confidence"]),
                probabilities={str(key): float(value) for key, value in answer["probabilities"].items()},
                model=str(body["model"]),
            )
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            logger.warning("TypeSafe Timiotera review unavailable: %s", exc)
            return None

        self._write_cache(payload, decision)
        return decision

    def review_ainoi_style(
        self, *, weekly_tone: int | None, local_heading: str
    ) -> MusicDecision | None:
        """Validate the fixed slow/short Sunday-Ainoi rule for one tone.

        This is not a request to choose scan pages. The app has the only
        verified score per tone; Jev can choose only a style or ``no_score``.
        """
        if not self.enabled or weekly_tone not in AINOI_STYLE_BY_TONE:
            return None

        payload = {
            "model": self.model,
            "state": {
                "member": "Κυριακάτικοι αναστάσιμοι Αίνοι",
                "weekly_tone": weekly_tone,
                "local_melodos_heading": local_heading,
            },
            "questions": {
                "style": {
                    "type": "choice",
                    "instructions": (
                        "Validate the fixed Anastasimatario form for the Sunday "
                        "resurrectional Ainoi from the explicit weekly tone."
                    ),
                    "criteria": {
                        "slow_ainoi": "Use only for tones 1, 2, 5, or 6.",
                        "short_ainoi": "Use only for tones 3, 4, 7, or 8.",
                        "no_score": "Use when this is not clearly the Sunday resurrectional Ainoi block.",
                    },
                }
            },
        }
        cached = self._read_cache(payload)
        if cached is not None:
            return cached

        try:
            response = self.session.post(
                TYPESAFE_SYSTEMONE_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=(4, 20),
            )
            response.raise_for_status()
            body = response.json()
            answer = body["answers"]["style"]
            if answer.get("type") != "choice":
                raise ValueError("TypeSafe returned a non-choice answer")
            decision = MusicDecision(
                choice=str(answer["choice"]),
                confidence=float(answer["confidence"]),
                probabilities={str(key): float(value) for key, value in answer["probabilities"].items()},
                model=str(body["model"]),
            )
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            logger.warning("TypeSafe Sunday Ainoi review unavailable: %s", exc)
            return None

        self._write_cache(payload, decision)
        return decision

    def _cache_path(self, payload: dict[str, object]) -> Path:
        material = json.dumps(
            {"version": CACHE_VERSION, "payload": payload},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return self.cache_dir / f"{hashlib.sha256(material.encode('utf-8')).hexdigest()}.json"

    def _read_cache(self, payload: dict[str, object]) -> MusicDecision | None:
        path = self._cache_path(payload)
        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
            return MusicDecision(
                choice=str(stored["choice"]),
                confidence=float(stored["confidence"]),
                probabilities={str(key): float(value) for key, value in stored["probabilities"].items()},
                model=str(stored["model"]),
            )
        except (FileNotFoundError, OSError, ValueError, KeyError, TypeError):
            return None

    def _write_cache(self, payload: dict[str, object], decision: MusicDecision) -> None:
        path = self._cache_path(payload)
        data = json.dumps(
            {
                "choice": decision.choice,
                "confidence": decision.confidence,
                "probabilities": decision.probabilities,
                "model": decision.model,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=self.cache_dir, delete=False
        ) as temporary:
            temporary.write(data)
            temporary_path = Path(temporary.name)
        temporary_path.replace(path)
