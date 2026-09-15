# Kihem working memory

Read [`README.md`](README.md) first; it is the full project documentation.
This file records only durable implementation decisions.

## Current application

- Kihem is a Flask app served at `/kihem/`. A request without `date` opens the
  current day's Orthros; `KIHEM_DEFAULT_DATE` is only an explicit override.
- Orthros and Divine Liturgy are separate page loads. Their sticky toolbar
  keeps the date in both links, has fixed auto-scroll speed 1 with an
  icon-only pause/resume control, and keeps the compact Isokratis controls.
- The heading copies Melodos' date, weekly tone and feast/saints text. The
  monthly calendar response is cached; it is never guessed.
- The Great Doxology scan is anchored after “ἐν τῷ φωτί σου ὀψόμεθα φῶς”.

## Melodos music

- Treat Melodos as untrusted HTML: never retain its scripts or event handlers.
- `src/melodos.py` rebuilds only its own `mousika/` selectors/buttons as safe
  local controls with the same labels and direct MP3 URLs. This includes the
  `___Επίλεξε ή PAUSE` selectors and one-click MP3 buttons.

## Isokratis

- The legacy project is `oldapp/isokratis_new.aia`; the web version is inside
  the main page, not a separate route. PDFs are intentionally out of scope.
- `src/isokratis.py` catalogs only direct MP3 files in
  `KIHEM_BYZ_DIR` (default `/var/lib/kihem/byz`) under `isokratis/` and
  `prosomia/`. Asset routes are explicit; arbitrary paths and PDFs are never
  served.
- Ison filename formula: `note base + register + semitone × 6`. Note buttons
  start looping playback; only «Διακοπή» stops it. The visible adjustment
  steps are −1/+1 and −6/+6.
- Selecting a prosomia MP3 starts it immediately; only «Διακοπή» remains.
  The source-maintained hidden-recording set in `isokratis.py` controls which
  uploaded tracks appear—do not delete source MP3s to change a menu.
- Workspace media is in `byz/isokratis` and `byz/prosomia`; never stage those
  binaries or `oldapp/` in Git.
