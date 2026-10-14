"""Private bridge from confirmed Kihem EZ events to a Neanes ``.byzx``.

The Neanes application owns the save format.  Instead of copying a large,
fragile JSON skeleton into Kihem, this bridge gives the already confirmed
``Note`` events to Neanes' own ``Score`` and ``SaveService`` classes in a
short-lived Vitest worker.  It is intentionally opt-in: callers name a local
Neanes source checkout, a private output path and a score title.

No source PDF, font or review draft is exposed by this module.  The produced
file is explicitly a private ``needs_review`` draft; it has no route into the
public catalogue.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping


class NeanesByzxBridgeError(RuntimeError):
    """Raised when the local Neanes serializer cannot create a valid file."""


def _require_private_event_draft(event_draft: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if event_draft.get("purpose") != "private-confirmed-ez-neanes-event-draft; not-a-complete-byzx-score":
        raise NeanesByzxBridgeError("Δεν δόθηκε έγκυρο ιδιωτικό EZ Neanes event draft.")
    if event_draft.get("review_state") != "needs_score_and_auditory_review":
        raise NeanesByzxBridgeError("Το event draft δεν έχει την υποχρεωτική κατάσταση needs_score_and_auditory_review.")
    events = event_draft.get("events")
    if not isinstance(events, list) or not events:
        raise NeanesByzxBridgeError("Το event draft δεν έχει γεγονότα Note.")
    if any(not isinstance(event, Mapping) or event.get("elementType") not in ("Note", "Martyria") for event in events):
        raise NeanesByzxBridgeError("Το event draft περιέχει μη έγκυρο στοιχείο Neanes Note.")
    controls = event_draft.get("ison_controls", [])
    if not isinstance(controls, list) or any(not isinstance(control, Mapping) or control.get("kind") != "pause" for control in controls):
        raise NeanesByzxBridgeError("Το event draft έχει μη έγκυρα ison controls.")
    return events


def _typescript_worker(event_draft: Mapping[str, Any], output_path: Path, title: str) -> str:
    """Return a one-test Neanes worker, with JSON values safely embedded."""

    payload = json.dumps(event_draft, ensure_ascii=False)
    output = json.dumps(str(output_path))
    score_title = json.dumps(title)
    return f"""import {{ readFileSync, writeFileSync }} from 'node:fs';

import {{ EmptyElement, MartyriaElement, NoteElement }} from '@/models/Element';
import {{ Score }} from '@/models/Score';
import {{ SaveService }} from '@/services/SaveService';

(globalThis as {{ APP_VERSION?: string }}).APP_VERSION = 'kihem-ez-private-draft';

const eventDraft = {payload};
const outputPath = {output};
const scoreTitle = {score_title};

describe('Kihem private EZ .byzx bridge', () => {{
  it('writes and reopens a Neanes score through its own serializer', () => {{
    const score = new Score();
    score.documentProperties.title = scoreTitle;
    score.documentProperties.author = 'Kihem · ιδιωτικό EZ draft · απαιτεί μουσικό έλεγχο';
    const elements = eventDraft.events.map((saved: Record<string, unknown>) => {{
      const {{ elementType: _elementType, source_note: _sourceNote, ...fields }} = saved;
      if (saved.elementType === 'Martyria') {{
        // Intermediate Martyria are automatic: Neanes derives them from the
        // notes before them, so a wrong note shows up as a wrong Martyria.
        const automatic = new MartyriaElement();
        if (typeof fields.fthora === 'string') {{
          Object.assign(automatic, {{ fthora: fields.fthora }});
        }}
        return automatic;
      }}
      const note = new NoteElement();
      Object.assign(note, fields);
      return note;
    }});
    const martyria = eventDraft.opening_martyria as Record<string, unknown> | undefined;
    if (martyria != null) {{
      const element = new MartyriaElement();
      // The Martyria is an explicit, human-confirmed visual starting sign.
      // It must not be automatic: on an empty staff Neanes would derive Pa.
      // A manual Martyria also resets Neanes' analysis state to its supplied
      // note and scale; rootSignOverride preserves the confirmed root sign.
      element.auto = false;
      Object.assign(element, martyria);
      element.rootSignOverride = element.rootSign;
      score.staff.elements = [element, ...elements, new EmptyElement()];
    }} else {{
      score.staff.elements = [...elements, new EmptyElement()];
    }}
    score.staff.lyrics.text = elements.map((element) => element.lyrics).filter(Boolean).join(' ');
    score.staff.lyrics.locked = true;
    writeFileSync(outputPath, JSON.stringify(SaveService.SaveScoreToJson(score), null, 2) + '\\n', 'utf8');
    const reopened = SaveService.LoadScoreFromJson(JSON.parse(readFileSync(outputPath, 'utf8')));
    expect(reopened.staff.elements).toHaveLength(score.staff.elements.length);
    if (martyria != null) {{
      const reopenedMartyria = reopened.staff.elements.find(
        (element) => element.elementType === 'Martyria',
      ) as MartyriaElement | undefined;
      expect(reopenedMartyria).toBeDefined();
      expect(reopenedMartyria!.auto).toBe(false);
      expect(reopenedMartyria!.note).toBe(martyria.note);
      expect(reopenedMartyria!.rootSign).toBe(martyria.rootSign);
      expect(reopenedMartyria!.scale).toBe(martyria.scale);
    }}
  }});
}});
"""


def write_private_byzx(
    event_draft: Mapping[str, Any],
    *,
    output_path: str | Path,
    title: str,
    neanes_source: str | Path,
) -> Path:
    """Write a private ``.byzx`` using the named local Neanes checkout.

    The checkout is never modified permanently.  A one-use test worker is
    created in its root solely because Vitest resolves Neanes' ``@`` imports
    from there, then removed even if serialization fails.
    """

    events = _require_private_event_draft(event_draft)
    del events  # Validation is intentional; the worker receives the full draft below.
    source_root = Path(neanes_source).resolve()
    if not (source_root / "package.json").is_file() or not (source_root / "vitest.config.mts").is_file():
        raise NeanesByzxBridgeError(f"Δεν βρέθηκε έγκυρο local checkout Neanes: {source_root}")
    destination = Path(output_path).resolve()
    if destination.suffix != ".byzx":
        raise NeanesByzxBridgeError("Το ιδιωτικό αρχείο εξόδου πρέπει να έχει κατάληξη .byzx.")
    if not title.strip():
        raise NeanesByzxBridgeError("Χρειάζεται τίτλος για το ιδιωτικό draft.")
    destination.parent.mkdir(parents=True, exist_ok=True)

    worker_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".test.ts",
            prefix=".kihem-ez-byzx-",
            dir=source_root,
            delete=False,
        ) as worker:
            worker.write(_typescript_worker(event_draft, destination, title))
            worker_path = Path(worker.name)
        result = subprocess.run(
            ["npm", "exec", "vitest", "--", "run", worker_path.name, "--config", "vitest.config.mts"],
            cwd=source_root,
            check=False,
            text=True,
            capture_output=True,
            timeout=90,
        )
        if result.returncode != 0:
            details = (result.stdout + "\n" + result.stderr).strip()
            raise NeanesByzxBridgeError(f"Ο serializer του Neanes απέτυχε:\n{details[-4000:]}")
    except FileNotFoundError as error:
        raise NeanesByzxBridgeError("Δεν βρέθηκε npm/Vitest για την τοπική εγκατάσταση Neanes.") from error
    except subprocess.TimeoutExpired as error:
        raise NeanesByzxBridgeError("Ο serializer του Neanes δεν ολοκληρώθηκε σε 90 δευτερόλεπτα.") from error
    finally:
        if worker_path is not None:
            worker_path.unlink(missing_ok=True)
    if not destination.is_file() or destination.stat().st_size == 0:
        raise NeanesByzxBridgeError("Το Neanes ολοκλήρωσε χωρίς να δημιουργήσει .byzx.")
    return destination


def _note_names_worker(byzx_path: Path, output_path: Path) -> str:
    """Return a one-test Neanes worker that records each played ScaleNote.

    Neanes' own ``PlaybackService`` decides which scale note every playback
    event sounds.  Recording it per element gives the parallage (the note names
    Πα, Βου, Γα ...) without re-implementing Neanes' analysis in Kihem.
    """

    source = json.dumps(str(byzx_path))
    output = json.dumps(str(output_path))
    return f"""import {{ readFileSync, writeFileSync }} from 'node:fs';

import {{ getScaleNoteFromValue, getScaleNoteValue, ScaleNote }} from '@/models/Scales';
import {{ PlaybackService }} from '@/services/audio/PlaybackService';
import {{ SaveService }} from '@/services/SaveService';

(globalThis as {{ APP_VERSION?: string }}).APP_VERSION = 'kihem-note-names';

class RecordingPlaybackService extends PlaybackService {{
  public played: string[] = [];
  // Distance from the written (physical) note to the name sung after the
  // last fthora; students follow the sung name.
  private sungShift = 0;

  handleModeKey(...args: Parameters<PlaybackService['handleModeKey']>) {{
    super.handleModeKey(...args);
    this.sungShift = 0;
  }}

  handleFthora(...args: Parameters<PlaybackService['handleFthora']>) {{
    super.handleFthora(...args);
    const node = args[0];
    const physical = getScaleNoteValue(node.physicalNote);
    const chromatic = /^(?:Hard|Soft)Chromatic(Pa|Thi)/.exec(String(node.fthora));
    if (!chromatic) {{
      this.sungShift = getScaleNoteValue(node.virtualNote) - physical;
      return;
    }}
    // Neanes keeps a chromatic shift only modulo one tetrachord: right for the
    // pitch, but the note under the fthora is sung by the fthora's own name
    // (e.g. hard-chromatic Pa on Ke is sung Pa).  Take that name's nearest octave.
    const named = getScaleNoteValue(
      node.chromaticFthoraNote ?? (chromatic[1] === 'Pa' ? ScaleNote.Pa : ScaleNote.Thi),
    );
    const target = [named - 7, named, named + 7].reduce((best, value) =>
      Math.abs(value - physical) < Math.abs(best - physical) ? value : best,
    );
    this.sungShift = target - physical;
  }}

  handleNoteAtom(...args: Parameters<PlaybackService['handleNoteAtom']>) {{
    super.handleNoteAtom(...args);
    const sung = getScaleNoteFromValue(getScaleNoteValue(args[0].physicalNote) + this.sungShift);
    this.played.push(sung ?? args[0].virtualNote);
  }}
}}

describe('Kihem note names', () => {{
  it('records the scale note of every played event', () => {{
    const score = SaveService.LoadScoreFromJson(JSON.parse(readFileSync({source}, 'utf8')));
    const elements = score.staff.elements;
    elements.forEach((element, index) => {{
      (element as {{ index?: number }}).index = index;
    }});
    const service = new RecordingPlaybackService();
    const events = service.computePlaybackSequence(
      elements,
      {{
        useLegetos: false, useDefaultAttractionZo: true, frequencyDi: 196, speed: 1,
        diatonicIntervals: [12, 10, 8], hardChromaticIntervals: [6, 20, 4],
        softChromaticIntervals: [8, 14, 8], legetosIntervals: [8, 10, 12],
        zygosIntervals: [18, 4, 16, 4], zygosLegetosIntervals: [18, 4, 20, 4],
        spathiIntervals: [20, 4, 4, 14], klitonIntervals: [14, 12, 4],
        defaultAttractionZoMoria: -4, defaultAttractionKeMoria: 5,
        volumeIson: -4, volumeMelody: 0, alterationMultipliers: [0.5, 0.25, 0.75],
        alterationMoriaMap: {{}},
      }},
      false,
    );
    const noteEvents = events.filter((event) => event.type === 'note');
    expect(noteEvents).toHaveLength(service.played.length);
    const byElement: Record<string, string[]> = {{}};
    noteEvents.forEach((event, position) => {{
      (byElement[String(event.elementIndex)] ??= []).push(service.played[position]);
    }});
    writeFileSync({output}, JSON.stringify({{ schema: 1, elements: byElement }}, null, 2) + '\\n', 'utf8');
  }});
}});
"""


def write_note_names(
    byzx_path: str | Path,
    *,
    output_path: str | Path,
    neanes_source: str | Path,
) -> Path:
    """Write ``{elementIndex: [ScaleNote, ...]}`` for a ``.byzx`` via Neanes."""

    source_root = Path(neanes_source).resolve()
    if not (source_root / "package.json").is_file() or not (source_root / "vitest.config.mts").is_file():
        raise NeanesByzxBridgeError(f"Δεν βρέθηκε έγκυρο local checkout Neanes: {source_root}")
    byzx = Path(byzx_path).resolve()
    if byzx.suffix != ".byzx" or not byzx.is_file():
        raise NeanesByzxBridgeError("Χρειάζεται υπαρκτό αρχείο .byzx.")
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    worker_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".test.ts", prefix=".kihem-note-names-", dir=source_root, delete=False
        ) as worker:
            worker.write(_note_names_worker(byzx, destination))
            worker_path = Path(worker.name)
        result = subprocess.run(
            ["npm", "exec", "vitest", "--", "run", worker_path.name, "--config", "vitest.config.mts"],
            cwd=source_root, check=False, text=True, capture_output=True, timeout=90,
        )
        if result.returncode != 0:
            details = (result.stdout + "\n" + result.stderr).strip()
            raise NeanesByzxBridgeError(f"Ο υπολογισμός νοτών του Neanes απέτυχε:\n{details[-4000:]}")
    except FileNotFoundError as error:
        raise NeanesByzxBridgeError("Δεν βρέθηκε npm/Vitest για την τοπική εγκατάσταση Neanes.") from error
    except subprocess.TimeoutExpired as error:
        raise NeanesByzxBridgeError("Ο υπολογισμός νοτών δεν ολοκληρώθηκε σε 90 δευτερόλεπτα.") from error
    finally:
        if worker_path is not None:
            worker_path.unlink(missing_ok=True)
    if not destination.is_file() or destination.stat().st_size == 0:
        raise NeanesByzxBridgeError("Το Neanes ολοκλήρωσε χωρίς να δημιουργήσει αρχείο νοτών.")
    return destination
