"""DCS (Digital Chant Stand, GOARCH) provider for the daily Vespers.

Melodos supplies Orthros and the Divine Liturgy today.  It publishes no
Vespers page, so Vespers is taken from ``dcs.goarch.org``, which publishes a
per-date Greek service as HTML (``h/s/YYYY/MM/DD/<code>/gr/``).

The upstream page is a full web application (menus, score dropdowns, scripts).
This module keeps only the liturgical paragraphs, maps their ``class`` to a
small document model, and renders escaped HTML that the Kihem templates can
style exactly like the Melodos documents.

Nothing from the upstream page is copied verbatim into storage: the rendered
blocks are stored in the local cache so a page can be re-served without
hitting the source again.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Final

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.melodos import TONE_LABELS, ServiceDocument

DCS_ENDPOINT: Final = (
    "https://dcs.goarch.org/goa/dcs/h/s/{year:04d}/{month:02d}/{day:02d}/{code}/gr/index.html"
)
DCS_HOME: Final = "https://dcs.goarch.org/goa/dcs/"
DCS_SOURCE_NAME: Final = "Digital Chant Stand (GOARCH)"

# The evening of a civil date belongs to the next liturgical day.  DCS keys the
# page by that evening, which is what the reader expects from ``services=esperinos``.
# ``ve2`` is the same service with Litia and Artoklasia, so it wins on feasts.
SERVICE_CODES: Final[tuple[str, ...]] = ("ve2", "ve")
CODE_LABELS: Final = {
    "ve": "Ἑσπερινός",
    "ve2": "Ἑσπερινὸς μετὰ Λιτῆς καὶ Ἀρτοκλασίας",
}
SERVICE_LABELS: Final = {"esperinos": "Ἑσπερινός"}

# Paragraph class -> document-model kind.  Semantics come from DCS itself.
KIND_BY_CLASS: Final = {
    "designation": "heading",
    "mode": "mode",
    "rubric": "rubric",
    "actor": "actor",
    "dialogwithactor": "dialog",
    "dialog": "dialog",
    "hymn": "hymn",
    "verse": "verse",
    "chapverse": "verse",
    "reading": "reading",
    "mixed": "text",
    "inaudible": "text",
    "chant": "text",
    "greekmelody": "text",
    "source": "source",
    "source0": "source",
}

TONE_PATTERNS: Final = (
    ("plagal4", r"πλ\.?\s*δ"),
    ("plagal2", r"πλ\.?\s*β"),
    ("plagal1", r"πλ\.?\s*α"),
    ("grave", r"βαρ"),
)
TONE_NUMBERS: Final = {
    "plagal4": 8,
    "plagal2": 6,
    "plagal1": 5,
    "grave": 7,
    "alpha": 1,
    "beta": 2,
    "gamma": 3,
    "delta": 4,
}

NOISE: Final = {"bookmark", "…", "...", "-", "—", "·"}
_SEPARATOR_RE: Final = re.compile(r"^[-_\u2013\u2014\s·]+$")
_DROPCAP_RE: Final = re.compile(r"^\W{0,2}[Α-ΩΆΈΉΊΌΎΏἈ-Ὧ]$")
# A decorated initial is its own inline element, so the extractor leaves a space
# between it and the rest of the word ("Π ᾶσα").  Rejoin it.
_INITIAL_SPLIT_RE: Final = re.compile(r"^([Α-ΩΆΈΉΊΌΎΏἈ-Ὧ]) ([\u03b1-\u03c9\u1f00-\u1fff])")


class DcsError(RuntimeError):
    """Raised when no usable Greek service page can be fetched."""


@dataclass(frozen=True)
class DcsBlock:
    kind: str
    text: str


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFD", value.casefold())
    cleaned = "".join(
        ch
        for ch in value
        if unicodedata.category(ch) not in {"Mn", "Pc", "Pd", "Pe", "Pf", "Pi", "Po", "Ps"}
    )
    return " ".join(cleaned.split())


def tone_from_text(value: str) -> int | None:
    """Read an explicit «Ἦχος …» label, never a date-derived guess."""
    # _normalized() casefolds the final sigma to "σ", and DCS prints the tone
    # numeral with U+02B9 (modifier letter prime); strip both before matching.
    text = _normalized(value).replace("\u02b9", "").replace("\u0384", "").replace("'", "")
    if "ηχοσ" not in text and not text.strip().startswith(("πλ", "βαρ", "α", "β", "γ", "δ")):
        return None
    for name, pattern in TONE_PATTERNS:
        if re.search(pattern, text):
            return TONE_NUMBERS[name]
    for name in ("alpha", "beta", "gamma", "delta"):
        letter = {"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ"}[name]
        if re.search(rf"(^|\s){letter}(\s|$)", text):
            return TONE_NUMBERS[name]
    return None


def _kind_of(tag) -> str:
    raw = tag.get("class") or []
    first = str(raw[0]) if raw else ""
    if first.startswith("sb_cover"):
        return "cover"
    if first.startswith("sb_credits") or first.startswith("sb_pdf"):
        return "skip"
    return KIND_BY_CLASS.get(first, "text")


def parse_document(markup: str) -> tuple[list[DcsBlock], list[str]]:
    """Return the liturgical blocks and the cover lines of a DCS page."""
    soup = BeautifulSoup(markup, "html.parser")
    for tag in soup.select("script, style, noscript, .agesMenu, .media-group, .jqm-dropdown"):
        tag.decompose()

    content = soup.select_one("div.content") or soup
    cover: list[str] = []
    blocks: list[DcsBlock] = []
    for tag in content.find_all("p"):
        kind = _kind_of(tag)
        text = " ".join(tag.get_text(" ", strip=True).split())
        if not text:
            continue
        if kind == "cover":
            cover.append(text)
            continue
        if kind == "skip":
            continue
        if text in NOISE or _SEPARATOR_RE.match(text):
            continue
        # Upstream UI strings ("Link to Vesperal Prayers") carry no Greek text.
        if len(text) < 80 and not re.search(r"[\u0370-\u03ff\u1f00-\u1fff]", text):
            continue
        text = re.sub(r"\s*- - -\s*$", "", text).strip()
        text = _INITIAL_SPLIT_RE.sub(r"\1\2", text)
        if not text:
            continue
        blocks.append(DcsBlock(kind, text))

    # DCS renders decorated initials in their own paragraph: "Π" then "ᾶσα".
    merged: list[DcsBlock] = []
    for block in blocks:
        if merged and _DROPCAP_RE.match(merged[-1].text) and block.text[:1].islower():
            previous = merged.pop()
            merged.append(DcsBlock(block.kind, previous.text + block.text))
        else:
            merged.append(block)
    return merged, cover


def render_blocks(blocks: list[DcsBlock]) -> str:
    """Render escaped HTML; the document model is the only thing that survives."""
    parts: list[str] = []
    for block in blocks:
        safe = html.escape(block.text, quote=False)
        if block.kind == "heading":
            parts.append(f'<h3 class="dcs-heading">{safe}</h3>')
        else:
            parts.append(f'<p class="dcs-{block.kind}">{safe}</p>')
    return "\n".join(parts)


def _label_lines(cover: list[str], code: str) -> tuple[str | None, str | None]:
    """Split the cover into «day label» and «commemoration» lines."""
    noise = {"…", "...", "-", "—", "·", "Μηναῖον", "Ὀκτώηχος", "Βιβλία - Πηγές", "Βιβλία - Πηγές"}
    lines = [
        line.strip(" ,-·")
        for line in cover
        if line and line.strip(" ,-·") not in noise and not line.startswith("Συμπλήρωμα")
    ]
    day_parts: list[str] = []
    title_parts: list[str] = []
    for line in lines:
        # Stop at the appendix/credits area of the cover page.
        if line.startswith("Ὡρολόγιον") or re.search(r"[A-Za-z]{3}", line):
            break
        if line.startswith(("Ἀκολουθία", "τῇ", "τῆς", "διὰ")) or re.match(r"^20\d{2}$", line):
            day_parts.append(line)
        else:
            title_parts.append(line)
    deduped: list[str] = []
    for part in day_parts:
        cooked = part.strip(", ")
        if not deduped or deduped[-1] != cooked:
            deduped.append(cooked)
    day_label = ", ".join(deduped) or None
    day_title = " · ".join(part.strip(" ·") for part in title_parts) or None
    if day_label and code == "ve2":
        day_label = f"{day_label} · μετὰ Λιτῆς καὶ Ἀρτοκλασίας"
    return day_label, day_title


class DcsClient:
    """Fetch and render the Greek daily service published by DCS."""

    def __init__(self, cache_dir: str | Path = "/tmp/kihem-cache", session: requests.Session | None = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = session or self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=2,
            backoff_factor=0.4,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.headers.update(
            {
                "User-Agent": "Kihem/1.0 (+liturgical composer; contact via site)",
                "Accept-Language": "el,en;q=0.5",
            }
        )
        return session

    def _cache_path(self, selected_date: date, service: str) -> Path:
        key = f"{selected_date.isoformat()}-{service}"
        digest = hashlib.sha256(key.encode()).hexdigest()[:12]
        return self.cache_dir / f"dcs-{key}-{digest}.json"

    def _url(self, selected_date: date, code: str) -> str:
        return DCS_ENDPOINT.format(
            year=selected_date.year, month=selected_date.month, day=selected_date.day, code=code
        )

    def fetch_service(
        self,
        selected_date: date,
        service: str = "esperinos",
        *,
        refresh: bool = False,
    ) -> ServiceDocument:
        if service not in SERVICE_LABELS:
            raise ValueError(f"Μη υποστηριζόμενη ακολουθία DCS: {service}")

        cache_path = self._cache_path(selected_date, service)
        if not refresh and cache_path.exists():
            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
                return self._document_from_cache(payload)
            except (OSError, ValueError, KeyError):
                pass  # corrupt cache: fall through and refetch

        errors: list[str] = []
        for code in SERVICE_CODES:
            url = self._url(selected_date, code)
            try:
                response = self.session.get(url, timeout=30)
            except requests.RequestException as exc:
                errors.append(f"{code}: {exc}")
                continue
            if response.status_code == 404:
                continue
            if response.status_code != 200:
                errors.append(f"{code}: HTTP {response.status_code}")
                continue
            # DCS serves UTF-8 without a charset in the Content-Type header, so
            # ``response.text`` would decode it as ISO-8859-1 and mangle the
            # polytonic Greek.  Decode the bytes explicitly.
            markup = response.content.decode("utf-8", errors="replace")
            blocks, cover = parse_document(markup)
            if not blocks:
                errors.append(f"{code}: κενή σελίδα")
                continue
            return self._build(selected_date, service, code, url, blocks, cover, cache_path)

        detail = "; ".join(errors) if errors else "κανένας κωδικός δεν επέστρεψε σελίδα"
        raise DcsError(
            f"Το DCS δεν επέστρεψε ελληνικό κείμενο για τις {selected_date.isoformat()} ({detail})."
        )

    def _build(
        self,
        selected_date: date,
        service: str,
        code: str,
        url: str,
        blocks: list[DcsBlock],
        cover: list[str],
        cache_path: Path,
    ) -> ServiceDocument:
        day_label, day_title = _label_lines(cover, code)
        # The weekly tone is printed on the cover («Ὀκτώηχος - Ἦχος πλ. βʹ»).
        tone = next(
            (tone_from_text(line) for line in cover if tone_from_text(line)),
            None,
        )
        # No weekly-tone line on the cover: leave the badge empty rather than
        # reporting the tone of some later hymn as the tone of the day.
        rendered = render_blocks(blocks)
        plain = "\n".join(block.text for block in blocks)
        fetched_at = datetime.now(timezone.utc)

        payload = {
            "service": service,
            "code": code,
            "label": SERVICE_LABELS[service],
            "day_label": day_label,
            "day_title": day_title,
            "tone": tone,
            "html": rendered,
            "plain": plain,
            "source_url": url,
            "fetched_at": fetched_at.isoformat(),
        }
        try:
            cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass  # a read-only cache must not break the page

        return self._document_from_cache(payload)

    @staticmethod
    def _document_from_cache(payload: dict) -> ServiceDocument:
        tone = payload.get("tone")
        return ServiceDocument(
            service=payload["service"],
            label=payload["label"],
            service_html=payload["html"],
            plain_text=payload["plain"],
            tone=tone,
            tone_label=TONE_LABELS.get(tone) if tone else None,
            fetched_at=datetime.fromisoformat(payload["fetched_at"]),
            source_url=payload["source_url"],
            source_day_label=payload.get("day_label"),
            source_tone_label=TONE_LABELS.get(tone) if tone else None,
            day_title=payload.get("day_title"),
        )
