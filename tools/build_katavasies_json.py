"""Build src/data/katavasies.json from the short-katavasies registry.

The registry (kat_registry_src.json) describes 40 feast sets of short
katavasies.  Only odes marked as passing review and present in the public
digital-score catalogue become attachment candidates.  Both the set's first
eirmos and the ode's own incipit must have at least three words; shorter
incipits are too likely to occur in ordinary psalm or hymn text, so they are
left to the printed scan.  Several sets share the same eirmos, so entries are
de-duplicated by normalized incipit.  The output is consumed by
src/anastasimatarion.py to generate the Orthros attachment rules.

Run from the repository root:

    python tools/build_katavasies_json.py
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "kat_registry_src.json"
CATALOGUE_PATH = ROOT / "src" / "data" / "digital_scores.json"
OUTPUT_PATH = ROOT / "src" / "data" / "katavasies.json"

PREFERRED_SETS = frozenset({"eis", "eisp", "kyrpx"})
GREEK_ODE_TO_DIGIT = {
    "α": "1",
    "β": "2",
    "γ": "3",
    "δ": "4",
    "ε": "5",
    "ς": "6",
    "ζ": "7",
    "η": "8",
    "θ": "9",
}


def _normalized(value: str) -> str:
    """Match the accent/punctuation-insensitive normalization used by rules."""
    value = unicodedata.normalize("NFD", value.casefold())
    cleaned = "".join(
        ch
        for ch in value
        if unicodedata.category(ch) not in {"Mn", "Pc", "Pd", "Pe", "Pf", "Pi", "Po", "Ps"}
    )
    return " ".join(cleaned.split())


def _word_count(value: str) -> int:
    return len(_normalized(value).split())


def _catalogue_id(set_name: str, ode: str, registry_id: str, catalogue_ids: set[str]) -> str | None:
    if registry_id in catalogue_ids:
        return registry_id
    # The three old sets use Greek ode letters in the registry but digit ode
    # suffixes in the catalogue (eis-s-α vs eis-s-1).
    digit = GREEK_ODE_TO_DIGIT.get(ode)
    if digit is None:
        return None
    candidate = registry_id.replace(f"-s-{ode}-", f"-s-{digit}-")
    return candidate if candidate in catalogue_ids else None


def build_entries() -> tuple[list[dict[str, str]], int]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    catalogue = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))["scores"]
    catalogue_by_id = {score["id"]: score for score in catalogue}

    candidates: list[dict[str, object]] = []
    for set_index, (set_name, set_data) in enumerate(registry.items()):
        first_incipit = set_data["first_incipit"]
        if _word_count(first_incipit) < 3:
            # A short first eirmos cannot safely identify its feast set.
            continue
        for ode_index, (ode, ode_data) in enumerate(set_data["odes"].items()):
            status = ode_data.get("status", "")
            if not status.startswith("pass"):
                continue
            if _word_count(ode_data["incipit"]) < 3:
                continue
            score_id = _catalogue_id(set_name, ode, ode_data["id"], set(catalogue_by_id))
            if score_id is None:
                continue
            score = catalogue_by_id[score_id]
            candidates.append(
                {
                    "set": set_name,
                    "ode": ode,
                    "id": score_id,
                    "incipit": ode_data["incipit"],
                    "first_incipit": first_incipit,
                    "feast": set_data["title"],
                    "composer": set_data["composer"],
                    "tone": set_data["tone"],
                    "title": score["title"],
                    "status": status,
                    "set_index": set_index,
                    "ode_index": ode_index,
                }
            )

    chosen: dict[str, tuple[tuple[int, int, int, int], dict[str, object]]] = {}
    for candidate in candidates:
        key = _normalized(str(candidate["incipit"]))
        preference = (
            0 if candidate["set"] in PREFERRED_SETS else 1,
            0 if candidate["status"] == "pass" else 1,
            int(candidate["set_index"]),
            int(candidate["ode_index"]),
        )
        if key not in chosen or preference < chosen[key][0]:
            chosen[key] = (preference, candidate)

    entries = sorted(
        (item for _, item in chosen.values()),
        key=lambda item: (int(item["set_index"]), int(item["ode_index"])),
    )
    public_fields = (
        "set",
        "ode",
        "id",
        "incipit",
        "first_incipit",
        "feast",
        "composer",
        "tone",
        "title",
    )
    output = [{field: str(entry[field]) for field in public_fields} for entry in entries]
    duplicated = len(candidates) - len(output)
    return output, duplicated


def main() -> None:
    entries, duplicated = build_entries()
    OUTPUT_PATH.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Entries: {len(entries)}")
    print(f"Incipits deduplicated: {duplicated}")


if __name__ == "__main__":
    main()
