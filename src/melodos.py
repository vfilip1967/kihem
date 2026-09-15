from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Final
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


MELODOS_ENDPOINT: Final = "https://melodos.com/akolouthies/action_page.php"
MELODOS_CALENDAR_ENDPOINT: Final = "https://melodos.com/akolouthies/kane_imerologio_akolouthion.php"
MELODOS_HOME: Final = "https://melodos.com/akolouthies/"
MELODOS_AUDIO_ROOT: Final = "https://melodos.com/akolouthies/"
SUPPORTED_YEARS: Final = range(2015, 2030)
SERVICE_LABELS: Final = {
    "orthros": "Όρθρος",
    "litourgia": "Θεία Λειτουργία Ιωάννου Χρυσοστόμου",
}


class MelodosError(RuntimeError):
    pass


@dataclass(frozen=True)
class ServiceDocument:
    service: str
    label: str
    service_html: str
    plain_text: str
    tone: int | None
    tone_label: str | None
    fetched_at: datetime
    source_url: str = MELODOS_HOME
    source_day_label: str | None = None
    source_tone_label: str | None = None
    day_title: str | None = None


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")


def parse_tone(text: str) -> int | None:
    """Parse the weekly Byzantine tone from the heading returned by Melodos."""
    match = re.search(r"[ΉΗ]χος\s+εβδομάδος\s+([^.<\n]+)", text, flags=re.IGNORECASE)
    if not match:
        return None
    value = _normalized(match.group(1)).replace("΄", "").strip()
    if "πλ" in value and "α" in value:
        return 5
    if "πλ" in value and "β" in value:
        return 6
    if "βαρ" in value:
        return 7
    if "πλ" in value and "δ" in value:
        return 8
    for letter, number in (("α", 1), ("β", 2), ("γ", 3), ("δ", 4)):
        if value.startswith(letter):
            return number
    return None


TONE_LABELS: Final = {
    1: "Ἦχος α΄",
    2: "Ἦχος β΄",
    3: "Ἦχος γ΄",
    4: "Ἦχος δ΄",
    5: "Ἦχος πλ. α΄",
    6: "Ἦχος πλ. β΄",
    7: "Ἦχος βαρύς",
    8: "Ἦχος πλ. δ΄",
}


class MelodosClient:
    """Fetch and sanitize services for any supported Gregorian-calendar date."""

    def __init__(self, cache_dir: str | Path = "/tmp/kihem-cache", session=None):
        self.cache_dir = Path(cache_dir) / "melodos"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = session or self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"POST"}),
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.headers.update(
            {
                "User-Agent": "Kihem/0.2 (+personal liturgical reading tool)",
                "Accept-Language": "el,en;q=0.8",
            }
        )
        return session

    def fetch_service(self, selected_date: date, service: str, *, refresh: bool = False) -> ServiceDocument:
        self._validate(selected_date, service)
        cache_path = self._cache_path(selected_date, service)
        raw_html: str

        if cache_path.exists() and not refresh:
            raw_html = cache_path.read_text(encoding="utf-8")
            fetched_at = datetime.fromtimestamp(cache_path.stat().st_mtime, timezone.utc)
        else:
            payload = self._payload(selected_date, service)
            try:
                response = self.session.post(MELODOS_ENDPOINT, data=payload, timeout=(7, 60))
                response.raise_for_status()
            except requests.RequestException as exc:
                if cache_path.exists():
                    raw_html = cache_path.read_text(encoding="utf-8")
                    fetched_at = datetime.fromtimestamp(cache_path.stat().st_mtime, timezone.utc)
                else:
                    raise MelodosError(f"Αδυναμία σύνδεσης με τον Μελωδό: {exc}") from exc
            else:
                # The page declares UTF-8 in its markup, while some responses
                # omit the HTTP charset and requests would otherwise assume
                # ISO-8859-1.
                raw_html = response.content.decode("utf-8", errors="replace")
                self._assert_final_page(raw_html, service)
                cache_path.write_text(raw_html, encoding="utf-8")
                fetched_at = datetime.now(timezone.utc)

        document = self.parse_document(raw_html, service, fetched_at=fetched_at)
        return replace(document, day_title=self._fetch_day_title(selected_date, refresh=refresh))

    @staticmethod
    def _validate(selected_date: date, service: str) -> None:
        if selected_date.year not in SUPPORTED_YEARS:
            raise ValueError("Ο Μελωδός διαθέτει μέσω του επιλογέα ημερομηνίες από το 2015 έως το 2029.")
        if service not in SERVICE_LABELS:
            raise ValueError(f"Μη υποστηριζόμενη ακολουθία: {service}")

    @staticmethod
    def _payload(selected_date: date, service: str) -> dict[str, str]:
        common = {
            "selida": "3",
            "imera": str(selected_date.day),
            "minas": str(selected_date.month),
            "etos": str(selected_date.year),
            "palaio": "0",
            "tipos_akolouthias": service,
            "arxeio_extra_eortis_imeras": "",
            "mono_gia_emena": "",
        }
        if service == "orthros":
            common.update(
                {
                    "eothino_meta_kanones": "0",
                    "odes_oles": "0",
                    "katabasies_oxi_oles_mazi": "0",
                }
            )
        else:
            common.update({"tipika": "0", "hxos_litourgikon_epilogeas": "0"})
        return common

    def _cache_path(self, selected_date: date, service: str) -> Path:
        key = f"{selected_date.isoformat()}-{service}-gregorian-defaults"
        digest = hashlib.sha256(key.encode()).hexdigest()[:12]
        return self.cache_dir / f"{key}-{digest}.html"

    def _calendar_cache_path(self, selected_date: date) -> Path:
        return self.cache_dir / f"calendar-{selected_date.year:04d}-{selected_date.month:02d}-gregorian.json"

    def _fetch_day_title(self, selected_date: date, *, refresh: bool) -> str | None:
        """Return the exact feast/saints title shown by Melodos for one day.

        Melodos inserts this title into the service page from browser session
        storage. Fetching its public month-calendar data lets Kihem show the
        same visible information without executing remote JavaScript.
        """
        cache_path = self._calendar_cache_path(selected_date)
        calendar_data: object
        if cache_path.exists() and not refresh:
            try:
                calendar_data = json.loads(cache_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                calendar_data = None
        else:
            try:
                response = self.session.post(
                    MELODOS_CALENDAR_ENDPOINT,
                    params={
                        "etos": str(selected_date.year),
                        "minas": str(selected_date.month),
                        "palaio": "false",
                    },
                    timeout=(7, 30),
                )
                response.raise_for_status()
                calendar_data = response.json()
                cache_path.write_text(
                    json.dumps(calendar_data, ensure_ascii=False), encoding="utf-8"
                )
            except (requests.RequestException, ValueError, OSError):
                return None

        if not isinstance(calendar_data, list) or len(calendar_data) < selected_date.day:
            return None
        entry = calendar_data[selected_date.day - 1]
        if not isinstance(entry, list) or len(entry) < 5 or not isinstance(entry[4], str):
            return None

        # The source inserts this value with innerHTML. Kihem deliberately
        # keeps only its visible text, so remote markup cannot enter our page.
        return BeautifulSoup(entry[4], "html.parser").get_text(" ", strip=True) or None

    @staticmethod
    def _assert_final_page(raw_html: str, service: str) -> None:
        expected = "ΟΡΘΡΟΣ" if service == "orthros" else "Η ΘΕΙΑ ΛΕΙΤΟΥΡΓΙΑ"
        if "id='div1'" not in raw_html and 'id="div1"' not in raw_html:
            restriction = re.search(
                r"Επίλεξε λοιπόν ακολουθίες από\s+([^<]+)", raw_html, flags=re.IGNORECASE
            )
            if restriction:
                available = html.unescape(restriction.group(1)).strip().rstrip(".")
                raise MelodosError(
                    "Ο Μελωδός δεν επέστρεψε ακολουθία για αυτή την ημερομηνία. "
                    f"Αυτή τη στιγμή η πηγή επιτρέπει επιλογή {available}."
                )
            raise MelodosError("Ο Μελωδός δεν επέστρεψε τελικό κείμενο ακολουθίας.")
        if expected not in raw_html:
            raise MelodosError(f"Το αποτέλεσμα δεν περιέχει την αναμενόμενη ακολουθία: {expected}")

    @classmethod
    def parse_document(
        cls, raw_html: str, service: str, *, fetched_at: datetime | None = None
    ) -> ServiceDocument:
        if service not in SERVICE_LABELS:
            raise ValueError(f"Μη υποστηριζόμενη ακολουθία: {service}")
        soup = BeautifulSoup(raw_html, "html.parser")
        container = soup.find(id="div1")
        if not isinstance(container, Tag):
            raise MelodosError("Δεν βρέθηκε το κυρίως κείμενο της ακολουθίας.")

        source_text = container.get_text("\n", strip=True)
        tone = parse_tone(source_text)
        source_day_label = cls._extract_source_day_label(source_text)
        source_tone_label = cls._extract_source_tone_label(source_text)
        sanitized = cls._sanitize(container)
        plain_text = BeautifulSoup(sanitized, "html.parser").get_text("\n", strip=True)
        return ServiceDocument(
            service=service,
            label=SERVICE_LABELS[service],
            service_html=sanitized,
            plain_text=plain_text,
            tone=tone,
            tone_label=TONE_LABELS.get(tone),
            fetched_at=fetched_at or datetime.now(timezone.utc),
            source_day_label=source_day_label,
            source_tone_label=source_tone_label,
        )

    @staticmethod
    def _extract_source_day_label(source_text: str) -> str | None:
        match = re.search(
            r"(?:Κυριακή|Δευτέρα|Τρίτη|Τετάρτη|Πέμπτη|Παρασκευή|Σάββατο)\s+\d{1,2}\s+[^\n]+?\s+\d{4}",
            source_text,
        )
        return match.group(0).strip() if match else None

    @staticmethod
    def _extract_source_tone_label(source_text: str) -> str | None:
        match = re.search(r"[ΉΗ]χος\s+εβδομάδος\s+[^\n]+", source_text, flags=re.IGNORECASE)
        return match.group(0).strip() if match else None

    @staticmethod
    def _sanitize(container: Tag) -> str:
        # The remote page is data, never trusted markup. Audio controls are
        # rebuilt below from the exact, whitelisted ``mousika/`` paths that
        # Melodos supplies; its JavaScript never enters Kihem.
        generated_audio_controls = MelodosClient._replace_audio_controls(container)
        for node in container.find_all(("script", "style", "audio", "canvas", "iframe", "object")):
            node.decompose()
        for node in list(container.find_all(("select", "button"))):
            if id(node) not in generated_audio_controls:
                node.decompose()
        for link in container.find_all("a"):
            # Keep the visible source text in its exact position, but remove
            # the remote navigation target.
            link.unwrap()

        allowed_tags = {
            "br", "span", "strong", "em", "b", "i", "p", "h2", "h3", "h4", "ul", "ol", "li", "hr",
            "select", "option", "button",
        }
        allowed_classes = {
            "ie", "ia", "ar", "ep", "ep2", "ei",
            "xx", "xi", "ti", "si", "bl",
        }
        for node in list(container.find_all(True)):
            if node.name not in allowed_tags:
                node.unwrap()
                continue
            if node.name == "select" and id(node) in generated_audio_controls:
                node.attrs = {
                    "class": ["melodos-audio-picker"],
                    "aria-label": "Μουσικό απόσπασμα Μελωδού",
                }
                continue
            if node.name == "option" and isinstance(node.parent, Tag) and id(node.parent) in generated_audio_controls:
                node.attrs = {"value": str(node.get("value", ""))}
                continue
            if node.name == "button" and id(node) in generated_audio_controls:
                node.attrs = {
                    "type": "button",
                    "class": ["melodos-audio-button"],
                    "data-melodos-audio": str(node.get("data-melodos-audio", "")),
                }
                continue
            classes = [value for value in node.get("class", []) if value in allowed_classes]
            inline_style = str(node.get("style", "")).lower().replace(" ", "")
            if "color:green" in inline_style:
                classes.append("melodos-green")
            elif "color:red" in inline_style:
                classes.append("melodos-red")
            node.attrs = {"class": classes} if classes else {}

        rendered = "".join(str(child) for child in container.contents)
        # Do not normalize, retype or replace any visible source character.
        # Polytonic code points and even source separators must remain exactly
        # as Melodos returned them.
        return rendered.strip() or html.escape(container.get_text("\n", strip=True))

    @staticmethod
    def _replace_audio_controls(container: Tag) -> set[int]:
        """Rebuild Melodos' inline MP3 controls without accepting its JS.

        The source only points to its own ``mousika/`` directory. Selectors
        retain the same displayed recording labels; standalone source buttons
        become ordinary, safe buttons with a resolved MP3 URL.
        """
        generated: set[int] = set()
        fragment = BeautifulSoup("", "html.parser")

        for source_select in list(container.find_all("select")):
            prefix = MelodosClient._audio_prefix(str(source_select.get("onchange", "")))
            if prefix is None:
                continue
            picker = fragment.new_tag("select")
            picker["class"] = "melodos-audio-picker"
            picker["aria-label"] = "Μουσικό απόσπασμα Μελωδού"
            for source_option in source_select.find_all("option", recursive=False):
                filename = str(source_option.get("value", ""))
                option = fragment.new_tag("option")
                option["value"] = MelodosClient._audio_url(prefix + filename) if filename else ""
                option.string = str(source_option.get("label") or source_option.get_text(" ", strip=True))
                picker.append(option)
            source_select.replace_with(picker)
            generated.add(id(picker))

        for source_button in list(container.find_all("button")):
            audio_path = MelodosClient._audio_prefix(str(source_button.get("onclick", "")))
            if audio_path is None:
                continue
            button = fragment.new_tag("button")
            button["type"] = "button"
            button["class"] = "melodos-audio-button"
            button["data-melodos-audio"] = MelodosClient._audio_url(audio_path)
            button.string = source_button.get_text(" ", strip=True)
            source_button.replace_with(button)
            generated.add(id(button))

        return generated

    @staticmethod
    def _audio_prefix(handler: str) -> str | None:
        match = re.search(r"paixe_hxitiko\(\s*'([^']+)'", handler, flags=re.IGNORECASE)
        if not match:
            return None
        path = html.unescape(match.group(1)).strip()
        return path if path.startswith("mousika/") else None

    @staticmethod
    def _audio_url(path: str) -> str:
        # Quote Unicode and spaces while preserving this fixed source origin.
        return quote(urljoin(MELODOS_AUDIO_ROOT, path), safe=":/%")
