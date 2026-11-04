"""Compact labels for the music bookmark menu."""

from __future__ import annotations

import re
import unicodedata

__all__ = ["short_music_label"]

_MAX_LABEL_LENGTH = 24
_FALLBACK_LENGTH = 22

_GENRE_MARKERS = (
    ("χερουβικ", "Χερ."),
    ("κοινωνικ", "Κοιν."),
    ("τρισαγ", "Τρισ."),
    ("μονογεν", "Μονογ."),
    ("απολυτικ", "Απολ."),
    ("κοντακ", "Κοντ."),
    ("δυναμ", "Δύν."),
    ("αλληλου", "Ἀλλ."),
    ("αξι", "Ἄξ."),
    ("εισοδικ", "Εἰσ."),
    ("προκειμ", "Προκ."),
    ("αντιφων", "Ἀντ."),
)

_STOPWORDS = frozenset(
    {
        "ο",
        "η",
        "το",
        "οι",
        "τα",
        "του",
        "της",
        "των",
        "τον",
        "την",
        "τους",
        "τις",
        "εις",
        "εν",
        "εκ",
        "εξ",
        "προς",
        "μετα",
        "κατα",
        "δια",
        "επι",
        "απο",
        "υπερ",
        "υπο",
        "συν",
        "και",
        "ηχος",
        "ηχου",
        "μελος",
        "μελους",
        "ψηφιακη",
        "πλ",
        "βαρυς",
    }
)

_TONE_NUMERALS = {
    "α": "α΄",
    "β": "β΄",
    "γ": "γ΄",
    "δ": "δ΄",
}

_VARIANT_MARKERS = {
    "αργοσ": "αργ.",
    "αργα": "αργ.",
    "αργον": "αργ.",
    "συντομοσ": "σύντ.",
    "συντομον": "σύντ.",
    "συντομα": "σύντ.",
    "συντομη": "σύντ.",
}

_PRIMES = "΄'′’᾽"
_TOKEN_RE = re.compile(r"[^\s·,;:(){}\[\]«»\"“”]+")


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


def _clean_token(token: str) -> str:
    return token.strip(".,;:(){}[]«»\"“”")


def _tokens(title: str) -> list[str]:
    return [token for raw in _TOKEN_RE.findall(title) if (token := _clean_token(raw))]


def _prepare(token: str) -> str:
    prepared = _fold(_clean_token(token))
    for prime in _PRIMES:
        prepared = prepared.replace(prime, "΄")
    return prepared


def _numeral_from_folded(value: str, require_prime: bool) -> str | None:
    has_prime = value.endswith("΄")
    base = value[:-1] if has_prime else value
    if base not in _TONE_NUMERALS:
        return None
    if require_prime and not has_prime:
        return None
    return _TONE_NUMERALS[base]


def _numeral(token: str, require_prime: bool) -> str | None:
    return _numeral_from_folded(_prepare(token), require_prime)


def _is_plagal_marker(token: str) -> bool:
    return _prepare(token) == "πλ"


def _plagal_tone(token: str, require_prime: bool) -> str | None:
    prepared = _prepare(token)
    if not prepared.startswith("πλ"):
        return None
    rest = prepared[2:].lstrip(".")
    if not rest:
        return None
    numeral = _numeral_from_folded(rest, require_prime)
    return f"πλ.{numeral}" if numeral else None


def _tone_token(token: str, require_prime: bool) -> str | None:
    plagal = _plagal_tone(token, require_prime)
    if plagal:
        return plagal
    if _prepare(token) == "βαρυς":
        return "βαρ."
    return _numeral(token, require_prime)


def _explicit_tone(tokens: list[str]) -> str | None:
    folded = [_prepare(token) for token in tokens]
    for index, value in enumerate(folded):
        if value == "ηχος":
            next_index = index + 1
            if next_index >= len(tokens):
                continue
            if _is_plagal_marker(tokens[next_index]):
                if next_index + 1 < len(tokens):
                    numeral = _numeral(tokens[next_index + 1], require_prime=False)
                    if numeral:
                        return f"πλ.{numeral}"
                continue
            tone = _tone_token(tokens[next_index], require_prime=False)
            if tone:
                return tone
        elif value == "ηχου":
            previous_index = index - 1
            if previous_index < 0:
                continue
            tone = _tone_token(tokens[previous_index], require_prime=False)
            if tone:
                if previous_index - 1 >= 0 and _is_plagal_marker(tokens[previous_index - 1]):
                    return f"πλ.{tone}"
                return tone
    return None


def _fallback_tone(tokens: list[str]) -> str | None:
    folded = [_prepare(token) for token in tokens]
    for index, token in enumerate(tokens):
        if _is_plagal_marker(token):
            if index + 1 < len(tokens):
                numeral = _numeral(tokens[index + 1], require_prime=True)
                if numeral:
                    return f"πλ.{numeral}"
            continue
        plagal = _plagal_tone(token, require_prime=True)
        if plagal:
            return plagal
    for token in tokens:
        if _prepare(token) == "βαρυς":
            return "βαρ."
    for index, token in enumerate(tokens):
        if index > 0 and folded[index - 1] in {"ωδη", "ωδης"}:
            continue
        numeral = _numeral(token, require_prime=True)
        if numeral:
            return numeral
    return None


def _genre_label(tokens: list[str]) -> str | None:
    for token in tokens:
        prepared = _prepare(token)
        for stem, abbreviation in _GENRE_MARKERS:
            if prepared.startswith(stem):
                return abbreviation
    return None


def _variant_label(tokens: list[str]) -> str | None:
    for token in tokens:
        prepared = _prepare(token).replace("ς", "σ")
        variant = _VARIANT_MARKERS.get(prepared)
        if variant:
            return variant
    return None


def _significant_tokens(tokens: list[str]) -> list[str]:
    significant = []
    for token in tokens:
        if _prepare(token) in _STOPWORDS:
            continue
        if len([char for char in token if char.isalpha()]) < 3:
            continue
        significant.append(token)
    return significant


def short_music_label(title: str) -> str:
    stripped = title.strip()
    if not stripped:
        return "Μουσικό"

    tokens = _tokens(stripped)
    tone = _explicit_tone(tokens) or _fallback_tone(tokens)
    digital = "ψηφιακη" in _fold(stripped)
    suffix = ([tone] if tone else []) + (["ψηφ."] if digital else [])

    genre = _genre_label(tokens)
    if genre:
        parts = [genre]
        variant = _variant_label(tokens)
        if variant:
            parts.append(variant)
        parts.extend(suffix)
        label = " ".join(parts)
        if len(label) > _MAX_LABEL_LENGTH and "ψηφ." in parts:
            parts.remove("ψηφ.")
            label = " ".join(parts)
    else:
        words = _significant_tokens(tokens)
        without_digital = [tone] if tone else []
        extras_options = [suffix]
        if digital:
            extras_options.append(without_digital)
        label = ""
        for count in (2, 1):
            if len(words) < count:
                continue
            prefix = " ".join(word[:4] + "." for word in words[:count])
            for extras in extras_options:
                candidate = " ".join([prefix] + extras)
                if len(candidate) <= _MAX_LABEL_LENGTH:
                    label = candidate
                    break
            if label:
                break
        if not label:
            label = stripped[:_FALLBACK_LENGTH] + "…"

    if len(label) > _MAX_LABEL_LENGTH:
        label = stripped[:_FALLBACK_LENGTH] + "…"
    return label
