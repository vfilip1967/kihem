from __future__ import annotations

"""Cached, Greek Orthodox explanations for the Scripture readings in Orthros."""

import hashlib
import html
import json
import logging
import os
import re
import tempfile
import unicodedata
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.6-luna"
CACHE_VERSION = 1
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScripturePassage:
    kind: str
    title: str
    reference: str
    text: str
    end_node: Tag | NavigableString


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _node_text(node: object) -> str:
    if isinstance(node, (Tag, NavigableString)):
        return _compact(node.get_text(" ", strip=True) if isinstance(node, Tag) else str(node))
    return ""


def _normal(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", _compact(value).casefold())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _is_eothinon(value: str) -> bool:
    return "εωθιν" in _normal(value) and ("κεφ" in _normal(value) or "ευαγγελ" in _normal(value))


def _is_apostolos(value: str) -> bool:
    return _normal(value).replace("΄", "") == "αποστολοσ"


def _is_evangelion(value: str) -> bool:
    return _normal(value).replace("΄", "") == "ευαγγελιον"


def _is_boundary(value: str) -> bool:
    text = _normal(value)
    return (
        _is_apostolos(value)
        or _is_evangelion(value)
        or "εκτενησ δεηση" in text
        or "πληρωσωμεν την εωθινην δεησιν" in text
    )


def _reference_from(parts: Iterable[str], fallback: str) -> str:
    text = " ".join(part for part in parts if part)
    match = re.search(
        r"((?:[Α-ΩΆΈΉΊΌΎΏἈ-῿]+\s+){0,5}(?:\d+|[α-ωάέήίόύώ]+΄?)\s*(?::|΄|\s)\s*\d+(?:\s*[-–]\s*(?:(?:\d+|[α-ωάέήίόύώ]+΄?)\s*(?::|΄|\s*)\s*)?\d+)?)",
        text,
        flags=re.IGNORECASE,
    )
    return _compact(match.group(1)) if match else fallback


def extract_orthros_passages(service_html: str | BeautifulSoup) -> list[ScripturePassage]:
    """Find the Eothinon, first Apostle and Gospel in the Melodos fragment.

    Melodos returns a flat sequence of ``br`` and ``span`` nodes rather than
    semantic reading containers, so its headings are used as stable boundaries.
    """
    soup = service_html if isinstance(service_html, BeautifulSoup) else BeautifulSoup(service_html, "html.parser")
    # ``enrich_service_html`` can serialize Melodos' full document.  Its
    # service sequence lives inside ``#div1``; falling back keeps fixtures and
    # simpler fragments supported.
    root = soup.find(id="div1") or soup.body or soup
    nodes = [node for node in root.contents if isinstance(node, (Tag, NavigableString))]
    labels: list[tuple[str, int]] = []
    for index, node in enumerate(nodes):
        value = _node_text(node)
        if _is_eothinon(value):
            labels.append(("eothinon", index))
        elif _is_apostolos(value):
            labels.append(("apostolos", index))
        elif _is_evangelion(value):
            labels.append(("evangelion", index))

    passages: list[ScripturePassage] = []
    used: set[str] = set()
    for kind, start in labels:
        if kind in used:
            continue
        used.add(kind)
        end = len(nodes)
        for index in range(start + 1, len(nodes)):
            candidate = _node_text(nodes[index])
            is_eothinon_end = kind == "eothinon" and _normal(candidate).replace(":", "") == "χοροσ"
            if is_eothinon_end or (kind != "eothinon" and _is_boundary(candidate)):
                end = index
                break
        # The words introducing the Eothinon (book and liturgical formula)
        # immediately precede its heading and make its reference unambiguous.
        content_start = max(0, start - 7) if kind == "eothinon" else start
        parts = [_node_text(node) for node in nodes[content_start:end]]
        text = _compact("\n".join(part for part in parts if part and part != "~"))
        if len(text) < 80 or end <= start:
            continue
        title = _node_text(nodes[start])
        passages.append(
            ScripturePassage(
                kind=kind,
                title=title,
                reference=_reference_from(parts, title),
                text=text,
                end_node=nodes[end - 1],
            )
        )
    return passages


def _markdown_to_html(value: str) -> str:
    """Render the deliberately small Markdown subset returned by the model."""
    blocks: list[str] = []
    in_list = False
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            if in_list:
                blocks.append("</ul>")
                in_list = False
            continue
        safe = html.escape(line)
        safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
        if line.startswith("### ") or line.startswith("## "):
            if in_list:
                blocks.append("</ul>")
                in_list = False
            blocks.append(f"<h4>{safe.lstrip('#').strip()}</h4>")
        elif re.match(r"[-*]\s+", line):
            if not in_list:
                blocks.append("<ul>")
                in_list = True
            blocks.append(f"<li>{re.sub(r'^[-*]\s+', '', safe)}</li>")
        else:
            if in_list:
                blocks.append("</ul>")
                in_list = False
            blocks.append(f"<p>{safe}</p>")
    if in_list:
        blocks.append("</ul>")
    return "".join(blocks)


class ScriptureInterpretationService:
    """Generate once and then serve a local on-disk explanation per passage."""

    def __init__(
        self,
        cache_dir: str | Path,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        session: requests.Session | None = None,
        background: bool = True,
    ):
        self.cache_dir = Path(cache_dir) / "scripture-interpretations"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.session = session or requests.Session()
        self.background = background
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="kihem-scripture") if background else None
        self._scheduled: set[str] = set()
        self._scheduled_lock = Lock()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _cache_key(passage: ScripturePassage) -> str:
        material = "\n".join((str(CACHE_VERSION), passage.kind, passage.reference, passage.text))
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def _cache_path(self, passage: ScripturePassage) -> Path:
        return self.cache_dir / f"{self._cache_key(passage)}.json"

    @contextmanager
    def _locked_cache(self, path: Path):
        """Serialize cache misses across the Gunicorn worker processes."""
        import fcntl

        lock_path = path.with_suffix(".lock")
        with lock_path.open("w", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _prompt(passage: ScripturePassage) -> str:
        return f"""When given NT verse references, go sentence by sentence giving the νεοελληνική μετάφραση, then an ερμηνεία according to ελληνορθόδοξη πατερική θεολογία (in understandable modern Greek) for each verse (ancient text + translation + patristic interpretation), and end with a list of the passage's theological messages and which verses contain them.

Write only in modern, understandable Greek. Use the supplied ancient Greek text exactly as the source: do not invent verses or citations. Do not claim a precise patristic quotation unless you are certain of it; when appropriate, say simply «κατά την πατερική ερμηνευτική παράδοση». Keep the explanation reverent, educational, and concise enough to read on a phone. Use Markdown headings and bullet points.

Reading type: {passage.kind}
Liturgical heading: {passage.title}
Reference: {passage.reference}
Ancient Greek source text:
{passage.text}"""

    def _request(self, passage: ScripturePassage) -> str:
        response = self.session.post(
            OPENAI_RESPONSES_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "store": False,
                "reasoning": {"effort": "none"},
                "max_output_tokens": 5000,
                "input": self._prompt(passage),
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        output = payload.get("output_text", "")
        if not isinstance(output, str) or not output.strip():
            # ``output_text`` is an SDK convenience property. The raw
            # Responses REST API returns message content in ``output``.
            chunks: list[str] = []
            for item in payload.get("output", []):
                if not isinstance(item, dict) or item.get("type") != "message":
                    continue
                for content in item.get("content", []):
                    if isinstance(content, dict) and content.get("type") == "output_text":
                        text = content.get("text")
                        if isinstance(text, str):
                            chunks.append(text)
            output = "\n".join(chunks)
        if not isinstance(output, str) or not output.strip():
            raise RuntimeError("The interpretation response did not contain text.")
        return output.strip()

    def get(self, passage: ScripturePassage) -> str | None:
        path = self._cache_path(passage)
        def cached_value() -> str | None:
            if not path.exists():
                return None
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                result = data.get("interpretation")
                return result if isinstance(result, str) and result.strip() else None
            except (OSError, json.JSONDecodeError):
                return None

        cached = cached_value()
        if cached:
            return cached
        if not self.enabled:
            return None
        with self._locked_cache(path):
            cached = cached_value()
            if cached:
                return cached
            result = self._request(passage)
            record = {
                "version": CACHE_VERSION,
                "kind": passage.kind,
                "title": passage.title,
                "reference": passage.reference,
                "model": self.model,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "interpretation": result,
            }
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.cache_dir, delete=False) as handle:
                json.dump(record, handle, ensure_ascii=False, indent=2)
                temporary = Path(handle.name)
            temporary.replace(path)
            return result

    def enqueue(self, passage: ScripturePassage) -> None:
        """Start a cache miss without holding a Gunicorn request worker."""
        if not self.enabled or self._executor is None:
            return
        key = self._cache_key(passage)
        with self._scheduled_lock:
            if key in self._scheduled:
                return
            self._scheduled.add(key)

        def generate() -> None:
            try:
                self.get(passage)
            except Exception:
                logger.exception("Could not create cached %s interpretation", passage.kind)
            finally:
                with self._scheduled_lock:
                    self._scheduled.discard(key)

        self._executor.submit(generate)

    def enrich_orthros_html(self, service_html: str) -> str:
        if not service_html:
            return service_html
        soup = BeautifulSoup(service_html, "html.parser")
        # Extract from this parsed document, then append in reverse document
        # order so the insertion points remain valid.
        passages = extract_orthros_passages(soup)
        for passage in reversed(passages):
            path = self._cache_path(passage)
            result = None
            if path.exists():
                try:
                    cached = json.loads(path.read_text(encoding="utf-8")).get("interpretation")
                    result = cached if isinstance(cached, str) and cached.strip() else None
                except (OSError, json.JSONDecodeError):
                    pass
            if not result:
                self.enqueue(passage)
                continue
            box = soup.new_tag("section", attrs={"class": "scripture-interpretation"})
            heading = soup.new_tag("h3")
            heading.string = "Ερμηνεία αναγνώσματος"
            box.append(heading)
            body = BeautifulSoup(_markdown_to_html(result), "html.parser")
            for child in list(body.contents):
                box.append(child)
            if isinstance(passage.end_node, (Tag, NavigableString)):
                passage.end_node.insert_after(box)
            else:
                soup.append(box)
        return str(soup)
