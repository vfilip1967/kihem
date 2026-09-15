"""Safe cataloguing for the local Isokratis MP3 collection.

The old Android app addressed drone files by number and loaded recordings by
filename.  This module keeps that convention, but only serves files that are
present in the two explicitly configured media directories.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ISON_NOTES: tuple[dict[str, int | str], ...] = (
    {"label": "Δη", "base": 60},
    {"label": "Κε", "base": 72},
    {"label": "Ζω β", "base": 77},
    {"label": "Ζω", "base": 82},
    {"label": "Νη", "base": 90},
    {"label": "Πα", "base": 102},
    {"label": "Βου", "base": 112},
    {"label": "Γα", "base": 120},
    {"label": "Γα♯", "base": 126},
    {"label": "Δι", "base": 132},
    {"label": "Και", "base": 144},
)

MODE_LABELS = {
    "1": "Α΄ ήχος",
    "2": "Β΄ ήχος",
    "3": "Γ΄ ήχος",
    "4": "Δ΄ ήχος",
    "5": "Πλ. α΄",
    "6": "Πλ. β΄",
    "7": "Βαρύς",
    "8": "Πλ. δ΄",
    "other": "Λοιπά μέλη",
}
MODE_ORDER = tuple(MODE_LABELS)
_NUMBERED_FILE = re.compile(r"^(\d+)\.mp3$", re.IGNORECASE)
_MODE_PREFIX = re.compile(r"^([1-8])-")
# These are setup/test recordings, not entries for the public Α΄-ήχου menu.
_HIDDEN_PROSOMIA_FILENAMES = frozenset(
    {
        # Α΄ ήχος: setup/test recordings.
        "1-1.mp3",
        "1-1-1.mp3",
        "1-2.mp3",
        "1-2-1.mp3",
        "1-3.mp3",
        "1-3-1.mp3",
        "1-4.mp3",
        "1-4-1.mp3",
        # Β΄ ήχος: the user-selected exclusions below are kept on disk but
        # intentionally omitted from the public recording menu.
        "2-0.mp3",
        "2-0-1.mp3",
        "2-1.mp3",
        "2-1-1.mp3",
        "2-2.mp3",
        "2-2-1.mp3",
        "2-3-1.mp3",
        "2-mathites.mp3",
        "2-mathitwn.mp3",
        "2-oikos.mp3",
        "2-ote-katil8es (1).mp3",
        "2-ote-katil8es-1.mp3",
        "2-poiois (1).mp3",
        "2-sarki.mp3",
        "2-stauros (1).mp3",
        "2-stauros.mp3",
        "2-gynaikes-1.mp3",
        "2-mathites-1.mp3",
        "2-mathitwn-1.mp3",
        "2-oikos-1.mp3",
        "2-poiois.mp3",
        "2-ta-anw.mp3",
        "2-ta-anw (1).mp3",
        "2-ta-anw-1.mp3",
    }
)


@dataclass(frozen=True)
class ProsomiaTrack:
    """One known recording, represented by its direct filename only."""

    filename: str
    label: str
    mode: str


class IsokratisLibrary:
    """Read-only index of the two MP3 folders used by the web player."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self._ison_numbers = self._read_ison_numbers()
        self._prosomia_tracks = self._read_prosomia_tracks()
        self._prosomia_names = {track.filename for track in self._prosomia_tracks}

    def _files(self, directory: str) -> tuple[Path, ...]:
        folder = self.root / directory
        if not folder.is_dir():
            return ()
        return tuple(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".mp3")

    def _read_ison_numbers(self) -> frozenset[int]:
        values = set()
        for path in self._files("isokratis"):
            match = _NUMBERED_FILE.fullmatch(path.name)
            if match:
                values.add(int(match.group(1)))
        return frozenset(values)

    def _read_prosomia_tracks(self) -> tuple[ProsomiaTrack, ...]:
        tracks = []
        for path in self._files("prosomia"):
            if path.name in _HIDDEN_PROSOMIA_FILENAMES:
                continue
            prefix = _MODE_PREFIX.match(path.stem)
            mode = prefix.group(1) if prefix else "other"
            tracks.append(ProsomiaTrack(path.name, path.stem, mode))
        return tuple(sorted(tracks, key=lambda track: (MODE_ORDER.index(track.mode), track.label.casefold())))

    @property
    def ison_numbers(self) -> frozenset[int]:
        return self._ison_numbers

    @property
    def prosomia_tracks(self) -> tuple[ProsomiaTrack, ...]:
        return self._prosomia_tracks

    def prosomia_by_mode(self) -> tuple[tuple[str, tuple[ProsomiaTrack, ...]], ...]:
        return tuple(
            (mode, tuple(track for track in self._prosomia_tracks if track.mode == mode))
            for mode in MODE_ORDER
            if any(track.mode == mode for track in self._prosomia_tracks)
        )

    def ison_path(self, number: int) -> Path | None:
        if number not in self._ison_numbers:
            return None
        return self.root / "isokratis" / f"{number}.mp3"

    def prosomia_path(self, filename: str) -> Path | None:
        # Membership in the catalog also rejects traversal, nested paths and
        # non-MP3 media such as the PDFs deliberately excluded from this UI.
        if filename not in self._prosomia_names:
            return None
        return self.root / "prosomia" / filename
