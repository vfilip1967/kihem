"""Font-preserving Apache POI import for legacy EZ Word documents.

The bundled Java helper reads every HWPF ``CharacterRun`` and writes JSONL.
Unlike ``wvWare``, it preserves the actual font name for each PUA character,
so a shared EZ code point can be resolved to the correct source font.  This
is still a source extraction step, not automatic musical transcription.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from .ez_font_mapping import EZ_SOURCE_DEFINITIONS


class EzWordRunExtractionError(ValueError):
    """Raised for unavailable/import-failed Apache POI extraction."""


_FONT_ALIASES = {
    "ez psaltica": "EZPsaltica",
    "ez fthora": "EZFthora",
    "ez special-i": "EZSpecial-I",
    "ez special-ii": "EZSpecial-II",
    "ez oxeia": "EZOxeia",
    "ez omega": "EZOmega",
}


def canonical_ez_font(font_name: str) -> str | None:
    """Return the source-font key only for a known official EZ run font."""

    return _FONT_ALIASES.get(" ".join(font_name.replace("–", "-").casefold().split()))


def build_ez_word_run_report(
    json_lines: str,
    *,
    source_label: str,
    source_filename: str,
) -> dict[str, Any]:
    """Turn POI JSONL into an auditable private report with exact run fonts."""

    runs: list[dict[str, Any]] = []
    occurrence = 0
    for line_number, line in enumerate(json_lines.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            font_name = str(raw["font_name"])
            codepoints = raw["pua_codepoints"]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise EzWordRunExtractionError(f"Μη έγκυρη γραμμή Apache POI {line_number}.") from error
        if not isinstance(codepoints, list) or not all(isinstance(value, str) for value in codepoints):
            raise EzWordRunExtractionError(f"Η γραμμή Apache POI {line_number} δεν έχει έγκυρους PUA κωδικούς.")
        source_font = canonical_ez_font(font_name)
        occurrences = []
        for codepoint in codepoints:
            occurrence += 1
            definition = EZ_SOURCE_DEFINITIONS.get((source_font, codepoint)) if source_font else None
            occurrences.append(
                {
                    "word_occurrence": occurrence,
                    "pua_codepoint": codepoint,
                    "source_font": source_font,
                    "source_definition": definition,
                    "status": (
                        "source-font-confirmed; no-neanes-event"
                        if source_font
                        else "non-ez-font; excluded-from-ez-conversion"
                    ),
                }
            )
        runs.append(
            {
                "run_index": raw.get("run_index"),
                "start_offset": raw.get("start_offset"),
                "end_offset": raw.get("end_offset"),
                "word_font_name": font_name,
                "source_font": source_font,
                "font_size_half_points": raw.get("font_size_half_points"),
                "bold": bool(raw.get("bold")),
                "italic": bool(raw.get("italic")),
                "text": raw.get("text", ""),
                "pua_occurrences": occurrences,
            }
        )
    all_occurrences = [item for run in runs for item in run["pua_occurrences"]]
    if not runs:
        raise EzWordRunExtractionError("Το Word δεν είχε PUA χαρακτήρες σε αναγνώσιμα font-runs.")
    counts = Counter(item["pua_codepoint"] for item in all_occurrences)
    fonts = sorted({run["source_font"] for run in runs if run["source_font"]})
    non_ez = sorted({run["word_font_name"] for run in runs if run["source_font"] is None})
    return {
        "schema": 1,
        "purpose": "private-ez-word-font-run-report; source-font-confirmed; no-byzx-generated",
        "source_label": source_label,
        "source_filename": source_filename,
        "extractor": "Apache POI HWPF CharacterRun.getFontName; Apache POI 5.5.1",
        "source_ez_fonts": fonts,
        "non_ez_run_fonts": non_ez,
        "font_run_count_with_pua": len(runs),
        "pua_occurrence_count": len(all_occurrences),
        "pua_counts": dict(sorted(counts.items())),
        "runs": runs,
    }


def extract_ez_word_font_runs(
    source: str | Path,
    *,
    source_label: str,
    importer_jar: str | Path,
    java: str = "java",
) -> dict[str, Any]:
    """Run the private POI helper and return an exact-font report."""

    source_path = Path(source)
    jar_path = Path(importer_jar)
    if source_path.suffix.lower() != ".doc" or not source_path.is_file():
        raise EzWordRunExtractionError(f"Απαιτείται υπάρχον αρχείο .doc: {source_path}")
    if not jar_path.is_file():
        raise EzWordRunExtractionError(f"Δεν βρέθηκε το Apache POI importer JAR: {jar_path}")
    try:
        result = subprocess.run(
            [java, "-jar", str(jar_path), str(source_path)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
        )
    except FileNotFoundError as error:
        raise EzWordRunExtractionError(f"Δεν βρέθηκε Java εκτελέσιμο: {java}") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip() or str(error)
        raise EzWordRunExtractionError(f"Αποτυχία Apache POI κατά την ανάγνωση Word: {detail}") from error
    return build_ez_word_run_report(
        result.stdout,
        source_label=source_label,
        source_filename=source_path.name,
    )
