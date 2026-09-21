from __future__ import annotations

import hashlib
import os
import threading
from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class InvalidMelodosAudioUrl(ValueError):
    pass


class MelodosAudioCache:
    """Persistent, origin-locked cache for the MP3 links published by Melodos."""

    _download_lock = threading.Lock()
    _maximum_bytes = 100 * 1024 * 1024

    def __init__(self, cache_dir: str | Path, session=None):
        self.cache_dir = Path(cache_dir) / "audio"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = session or self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.headers.update({"User-Agent": "Kihem/0.4 (+cached Melodos audio)"})
        return session

    @staticmethod
    def validate_url(source_url: str) -> str:
        parsed = urlsplit(source_url)
        decoded_path = unquote(parsed.path)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "melodos.com"
            or parsed.port not in (None, 443)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or not decoded_path.startswith("/akolouthies/mousika/")
            or not decoded_path.casefold().endswith(".mp3")
            or "\x00" in decoded_path
        ):
            raise InvalidMelodosAudioUrl("Μη έγκυρη διεύθυνση ηχητικού Μελωδού.")
        return source_url

    def _cache_path(self, source_url: str) -> Path:
        digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.mp3"

    def get(self, source_url: str) -> Path:
        source_url = self.validate_url(source_url)
        output = self._cache_path(source_url)
        if output.exists() and output.stat().st_size:
            return output

        with self._download_lock:
            if output.exists() and output.stat().st_size:
                return output
            temporary = output.with_suffix(".download")
            downloaded = 0
            try:
                response = self.session.get(source_url, stream=True, timeout=(7, 90))
                response.raise_for_status()
                with temporary.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        if not chunk:
                            continue
                        downloaded += len(chunk)
                        if downloaded > self._maximum_bytes:
                            raise ValueError("Το ηχητικό υπερβαίνει το επιτρεπτό μέγεθος.")
                        handle.write(chunk)
                if not downloaded:
                    raise ValueError("Ο Μελωδός επέστρεψε κενό ηχητικό αρχείο.")
                os.replace(temporary, output)
            finally:
                temporary.unlink(missing_ok=True)
        return output
