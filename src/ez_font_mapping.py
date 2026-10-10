"""Private evidence templates for EZ Byzantine Music Font PDFs.

The EZ package uses Private Use Area character codes.  A PDF made with the
complete package preserves useful evidence (font family, PUA code point and
glyph id), but those values are *not* Neanes music objects.  This module
creates a reviewable bridge with deliberately empty Neanes fields.  A psaltis
or a documented source must confirm each musical meaning before any score is
created.

It never embeds the EZ font, republishes a source PDF, or writes a ``.byzx``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from fontTools.ttLib import TTFont


EZ_FONT_FILES: dict[str, str] = {
    "EZPsaltica": "EZ Psaltica.TTF",
    "EZFthora": "EZ Fthora.TTF",
    "EZSpecial-I": "EZ Special-I.TTF",
    "EZSpecial-II": "EZ Special-II.TTF",
    "EZOxeia": "EZ Oxeia.ttf",
    "EZOmega": "EZ Omega.ttf",
}

EZ_FONT_ROLES: dict[str, str] = {
    "EZPsaltica": "base_or_precomposed_neume",
    "EZFthora": "fthora_or_accidental",
    "EZSpecial-I": "time_or_supporting_mark",
    "EZSpecial-II": "martyria_measure_or_supporting_mark",
    "EZOxeia": "karas_oxeia_mark",
    "EZOmega": "text_or_omega_mark",
}

# These entries are transcribed only from the prose instructions distributed
# inside the official package.  They record what the *source character* means;
# they do not authorize a score writer to choose a vertical attachment or a
# timed Neanes event without its page context.
EZ_SOURCE_DEFINITIONS: dict[tuple[str, str], dict[str, Any]] = {
    ("EZPsaltica", "U+F030"): {
        "source_name": "ison (no interval)",
        "evidence": "Official EZ character table, Ascending key 0 (the zero interval / ison).",
        "neanes_candidate": {"element_type": "quantitativeNeume", "value": "Ison"},
    },
    ("EZPsaltica", "U+F031"): {
        "source_name": "oligon (up one)",
        "evidence": "EZ INSTRUCTIONS §3a: digit 1 is the jump up one.",
        "neanes_candidate": {"element_type": "quantitativeNeume", "value": "Oligon"},
    },
    ("EZPsaltica", "U+F033"): {
        "source_name": "oligon with kentima above (up three)",
        "evidence": "Official EZ character table, Ascending key 3.",
        "neanes_candidate": {"element_type": "quantitativeNeume", "value": "OligonPlusKentimaAbove"},
    },
    ("EZPsaltica", "U+F021"): {
        "source_name": "apostrophos (down one)",
        "evidence": "EZ INSTRUCTIONS §3a: ! is apostrophos, down one.",
        "neanes_candidate": {"element_type": "quantitativeNeume", "value": "Apostrophos"},
    },
    ("EZPsaltica", "U+F027"): {
        "source_name": "ison (variant)",
        "evidence": "Project reviewer visually confirmed the EZ apostrophe-key variant as ison in the private review packet.",
        "neanes_candidate": {"element_type": "quantitativeNeume", "value": "Ison"},
    },
    ("EZPsaltica", "U+F040"): {
        "source_name": "elaphron (down two)",
        "evidence": "EZ INSTRUCTIONS §3a: @ is elaphron, down two.",
        "neanes_candidate": {"element_type": "quantitativeNeume", "value": "Elaphron"},
    },
    ("EZPsaltica", "U+F029"): {
        "source_name": "yporroe / hyporoe",
        "evidence": "EZ INSTRUCTIONS §3c: ) is an yporroe.",
        "neanes_candidate": {"element_type": "quantitativeNeume", "value": "Hyporoe"},
    },
    ("EZPsaltica", "U+F053"): {
        "source_name": "gorgon",
        "evidence": "EZ INSTRUCTIONS §3c: S is a gorgon.",
        "neanes_candidate": {
            "element_type": "gorgonNeume",
            "value": None,
            "context_required": "top-or-bottom attachment",
        },
    },
    ("EZPsaltica", "U+F02D"): {
        "source_name": "precomposed hyporoe with gorgon",
        "evidence": "EZ INSTRUCTIONS §3c: - is yporroe with gorgon.",
        "neanes_candidate": {
            "element_type": "decomposition",
            "value": ["Hyporoe", "Gorgon (attachment unresolved)"],
        },
    },
    ("EZPsaltica", "U+F06C"): {
        "source_name": "precomposed oligon-kentemata-gorgon",
        "evidence": "EZ INSTRUCTIONS §3c: l is oligon-kentemata-gorgon.",
        "neanes_candidate": {
            "element_type": "decomposition",
            "value": ["OligonPlusKentemata", "Gorgon (attachment unresolved)"],
        },
    },
    ("EZPsaltica", "U+F041"): {
        "source_name": "klasma variant above apostrophos",
        "evidence": "EZ INSTRUCTIONS §3c: A aligns above apostrophos.",
        "neanes_candidate": {"element_type": "timeNeume", "value": "Klasma_Top"},
    },
    ("EZPsaltica", "U+F061"): {
        "source_name": "klasma general variant",
        "evidence": "EZ INSTRUCTIONS §3c: a aligns with most other neumes.",
        "neanes_candidate": {"element_type": "timeNeume", "value": "Klasma_Top"},
    },
    ("EZPsaltica", "U+F07A"): {
        "source_name": "vareia (τροπικό, άχρονο)",
        "evidence": "Project reviewer: βαρεία, placed before a note and giving liveliness to the following sound.",
        "neanes_candidate": {"element_type": "vareia", "value": True, "context_required": "following note"},
    },
    ("EZPsaltica", "U+F03A"): {
        "source_name": "hapli / απλή χρονική (μία χρονική μονάδα)",
        "evidence": "Project reviewer visually identified the simple time sign and confirmed its value as one time unit.",
        "neanes_candidate": {"element_type": "timeNeume", "value": "Hapli"},
    },
    # EZ Special-II uses the c/v/b/n/m row for note markers and isokratemata.
    # The values below are tied both to the official key-row documentation and
    # to the first visual packet checked by the project reviewer.  The final
    # special marker is intentionally only classified as an isokratema: its
    # pitch is not safe to infer from the glyph code alone.
    ("EZSpecial-II", "U+F04E"): {
        "source_name": "isokratema Ga (Γ)",
        "evidence": "EZ INSTRUCTIONS §3a: n/N belongs to the Ga note-marker/isokratema key; visually confirmed in the private review packet.",
        "neanes_candidate": {"element_type": "ison", "value": "Ison.Ga"},
    },
    ("EZSpecial-II", "U+F063"): {
        "source_name": "isokratema Ni (Ν)",
        "evidence": "EZ INSTRUCTIONS §3a: c/C belongs to the Ni note-marker/isokratema key; visually confirmed in the private review packet.",
        "neanes_candidate": {"element_type": "ison", "value": "Ison.Ni"},
    },
    ("EZSpecial-II", "U+F04D"): {
        "source_name": "isokratema Di (Δ)",
        "evidence": "EZ INSTRUCTIONS §3a: m/M belongs to the Di note-marker/isokratema key; visually confirmed in the private review packet.",
        "neanes_candidate": {"element_type": "ison", "value": "Ison.Thi"},
    },
    ("EZSpecial-II", "U+F03F"): {
        "source_name": "isokratema pause (Μ)",
        "evidence": "Project reviewer: Μ means the human isokratis stops ison and chants with the main singer.",
        "neanes_candidate": {"element_type": "isonControl", "value": "Pause"},
    },
}

EZ_PSALTICA_GROUPS: dict[str, str] = {
    **{key: "ascending" for key in "0p123456789`~=qwertyui"},
    **{key: "descending" for key in "!@_)-#$%^&*(QWE"},
    **{key: "support_combinations" for key in "OolLPIU YTR" if key != " "},
    **{key: "time" for key in "sSxX-hHdDfFgG;:kKaAzZ"},
    **{key: "qualitative" for key in "\\'\"}=[{]"},
    **{key: "martyria_measure_or_breath" for key in "Jjcvbnm,./+|CVBNM>?<"},
}


def _pua_cmap(font: TTFont) -> dict[int, str]:
    """Return the Windows-symbol PUA map used by the legacy EZ fonts."""

    preferred = [
        table
        for table in font["cmap"].tables
        if table.platformID == 3 and table.platEncID == 0
    ]
    tables = preferred or [table for table in font["cmap"].tables if table.isUnicode()]
    mapping: dict[int, str] = {}
    for table in tables:
        mapping.update(table.cmap)
    return {codepoint: glyph for codepoint, glyph in mapping.items() if 0xF000 <= codepoint <= 0xF8FF}


def _legacy_keyboard_codes(font: TTFont) -> dict[str, list[str]]:
    """Return legacy keyboard characters for each PUA glyph name."""

    legacy_tables = [
        table
        for table in font["cmap"].tables
        if table.platformID == 1 and table.platEncID == 0
    ]
    by_glyph: dict[str, list[str]] = {}
    for table in legacy_tables:
        for codepoint, glyph_name in table.cmap.items():
            if 32 <= codepoint <= 126:
                by_glyph.setdefault(glyph_name, []).append(chr(codepoint))
    return {glyph_name: sorted(set(keys)) for glyph_name, keys in by_glyph.items()}


def build_ez_font_inventory(font_directory: str | Path) -> dict[str, dict[str, Any]]:
    """Read only locally supplied EZ font metadata into a JSON-safe inventory."""

    root = Path(font_directory)
    result: dict[str, dict[str, Any]] = {}
    for pdf_font_name, filename in EZ_FONT_FILES.items():
        path = root / filename
        if not path.is_file():
            continue
        font = TTFont(path)
        glyph_order = font.getGlyphOrder()
        cmap = _pua_cmap(font)
        keyboard_codes = _legacy_keyboard_codes(font)
        result[pdf_font_name] = {
            "font_file": filename,
            "role": EZ_FONT_ROLES[pdf_font_name],
            "entries": {
                f"U+{codepoint:04X}": {
                    "glyph_name": glyph_name,
                    "glyph_id": glyph_order.index(glyph_name),
                    "keyboard_keys": keyboard_codes.get(glyph_name, []),
                }
                for codepoint, glyph_name in sorted(cmap.items())
                if glyph_name in glyph_order
            },
        }
    if not result:
        raise FileNotFoundError(f"Δεν βρέθηκαν EZ γραμματοσειρές στον φάκελο: {root}")
    return result


def build_ez_mapping_template(
    vector_report: Mapping[str, Any],
    inventory: Mapping[str, Mapping[str, Any]],
    *,
    source_label: str,
    visual_candidates: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Create a private, non-semantic EZ→Neanes review template.

    Rows are keyed by the *PDF font instance and glyph id*.  A PUA codepoint
    is secondary evidence because PDF generators can subset or remap fonts.
    A mismatch between the supplied full font and the PDF glyph id is reported
    instead of silently assigning a music meaning.
    """

    candidate_index = {
        (str(item.get("source_font")), int(item.get("source_glyph_id", -1))): item
        for item in visual_candidates
    }
    rows: dict[tuple[str, int, str], dict[str, Any]] = {}
    skipped_non_notation_codes = 0
    for page in vector_report.get("pages", []):
        for glyph in page.get("glyphs", []):
            pdf_font = str(glyph.get("font", ""))
            codepoint = glyph.get("codepoint")
            glyph_id = int(glyph.get("glyph_id", -1))
            font_definition = inventory.get(pdf_font)
            if not font_definition or not isinstance(codepoint, str):
                continue
            expected = font_definition.get("entries", {}).get(codepoint)
            # EZOmega contains ordinary Greek text and punctuation. It is not
            # a notation source and must not enter a Neanes mapping template.
            if expected is None:
                skipped_non_notation_codes += 1
                continue
            if expected.get("keyboard_keys") == [" "]:
                skipped_non_notation_codes += 1
                continue
            key = (str(glyph.get("font_instance", "unknown")), glyph_id, codepoint)
            if key in rows:
                continue
            visual = candidate_index.get((pdf_font, glyph_id))
            source_definition = EZ_SOURCE_DEFINITIONS.get((pdf_font, codepoint))
            keyboard_keys = expected.get("keyboard_keys", [])
            rows[key] = {
                "source": {
                    "pdf_font": pdf_font,
                    "pdf_font_instance": glyph.get("font_instance"),
                    "pdf_glyph_id": glyph_id,
                    "pua_codepoint": codepoint,
                    "full_ez_font": font_definition.get("font_file"),
                    "full_ez_glyph_name": expected.get("glyph_name") if expected else None,
                    "keyboard_keys": keyboard_keys,
                    "character_table_group": (
                        [EZ_PSALTICA_GROUPS.get(item, "unclassified") for item in keyboard_keys]
                        if pdf_font == "EZPsaltica"
                        else []
                    ),
                    "glyph_id_matches_full_font": bool(expected and expected.get("glyph_id") == glyph_id),
                    "role": font_definition.get("role"),
                },
                "neanes": {
                    "status": "unconfirmed",
                    "element_type": None,
                    "value": None,
                    "notes": "Απαιτείται τεκμηριωμένη μουσική επιβεβαίωση· δεν είναι οπτική εικασία.",
                },
                "source_definition": source_definition,
                "visual_evidence": {
                    "status": visual.get("evidence") if visual else "not-collected",
                    "top_candidates": visual.get("candidates", []) if visual else [],
                },
            }

    return {
        "schema": 1,
        "purpose": "private-ez-to-neanes-mapping-template; no-byzx-generated",
        "source_label": source_label,
        "row_count": len(rows),
        "skipped_non_notation_code_count": skipped_non_notation_codes,
        "rows": list(rows.values()),
        "warning": (
            "Το template καταγράφει κωδικούς EZ και αποδείξεις προέλευσης. "
            "Καμία γραμμή δεν αποτελεί ακόμη αντικείμενο Neanes ή μεταγραφή .byzx."
        ),
    }
