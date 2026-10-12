# BZ (papline) PDF → Neanes event draft — prototype

Private research prototype, **not** a supported importer. It reads one music
line of a papline.gr PDF (BZ fonts), groups glyphs into Neanes notes and writes
an event draft plus a private `.byzx` through `src/neanes_byzx_bridge.py`.

- `bz_extract.py`: glyph origins/ink boxes (fontTools, package BZ fonts) and
  line detection from the lyric baselines.
- `bz_convert.py`: (font, code) → Neanes tables, attachment assignment by x
  overlap, syllable assignment, isokrata from `BZIson`.
- `run_line.py`: `python run_line.py <pdf> <page-index> <line-index> <tag>`;
  writes the draft/`.byzx` and a review sheet.

Known limits: paths to the CTAN BZ fonts, the Neanes checkout and the debug
folder are hard-coded; only glyphs confirmed by the psaltis are mapped
(`debug/bz-answers.json`, private); martyria, fthores and the opening mode are
not converted yet. Never publish the output without the source owner's
permission. Run `bz_extract.py` with PyMuPDF and fontTools (the project venv).
