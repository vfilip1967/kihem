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
    if any(not isinstance(event, Mapping) or event.get("elementType") != "Note" for event in events):
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
      const {{ elementType: _elementType, ...fields }} = saved;
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
