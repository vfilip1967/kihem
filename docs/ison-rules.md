# Ison (isokratima) rules used by Kihem

Status: working defaults, **not psaltis-verified**. Recorded 2026-11-07.

## Where the ison comes from
1. **Marks in the PDF** (24 catalogue scores): the small blue ison letters of the papline PDFs are converted to `ison: "Ison.X"` events of the `.byzx`. They always win. Neanes plays them with its own synth; the public page also offers «Ίσον mp3» (numbered mp3 loops, `src/isokratis.py ISON_MARK_NUMBERS`).
2. **Automatic default** for scores without marks (315): `DigitalScoreCatalog.auto_ison_marks` in `src/digital_scores.py`, using `default_ison_for` in `src/isokratis.py` and the genus table `src/data/ison_genus.json`.

## Neanes itself
Neanes has no mode→ison table and no melody-following rule: an ison applies from the note that carries it until the next mark; before the first mark there is none; `Ison.Unison` makes the drone double the melody (the mp3 mode keeps silent there).

## Automatic defaults (current)
| Mode | Default | Notes |
|---|---|---|
| α΄ | Πα | real marks: Πα 55 %, Νη 37 % |
| β΄ hard chromatic | Πα | |
| β΄ soft chromatic | per Martyria segment: median melody ≤ Γα → Βου, above → Δι | leave-one-piece-out 0.87 vs 0.56 constant (4 pieces) |
| γ΄ | Γα | no real data |
| δ΄ | follows the opening note: Δι→Δι, Πα→Πα, else Βου | real marks (Δι-start pieces): Δι 57 %, Πα 22 %, Βου 17 % ; Πα for Βου-start pieces was NOT testable (no data) |
| πλ. α΄ | Πα | real: Πα 69 % |
| πλ. β΄ hard | Πα | real: Πα 75 % |
| πλ. β΄ soft | Δι | no real data (theory: Δι or Βου) |
| βαρύς enharmonic | Γα | |
| βαρύς diatonic | Ζω | real data (2 pieces): Πα 55 %, Ζω 40 % — open question |
| πλ. δ΄ | Νη; «ἐκ τοῦ Γα» (label or start Γα) → Γα | real isons move a lot (Δι 29, Δι κάτω 22, Νη 19, Πα 16 %); no constant fits |
Extra rule (modes δ΄ and πλ. δ΄ only): a Martyria segment whose median melody lies above Δι gets Δι (agreement with real marks rose 0.15→0.44 and 0.20→0.41; it lowered agreement in πλ. α΄/πλ. β΄, so it is not used there).

## Genus detection
In the papline PDFs the genus is printed as the small note letters/fthora signs beside the martyria (e.g. the small Πα of plagal-2 = hard chromatic, the small Γα = enharmonic). `src/data/ison_genus.json` (303 scores) was made by reading them (opencode, `lib/genus_scan.py` in the private workspace /root/anast-work).

## Sources
byzantinechant.org (Takis/Melling, «Reading Psalmodia»), analogion.com (Isokratema, Ison for second mode, Barys), kelfar.net Byzantine music guide, Wikipedia «Ison (music)», Unicode TN20; Neanes issues #1588 and #2138. No source gives a complete machine-readable table; practice differs by school.

## Caveat
The evaluation sample is small (22 scores, mostly Lambadarios/Nikolaidis). Re-measure with `scripts` above when more scores with real marks exist.
