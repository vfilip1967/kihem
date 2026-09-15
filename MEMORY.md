# Kihem working memory

## Required reading

Read [`README.md`](README.md) first. It is the authoritative documentation for
the existing Kihem Flask application: its setup, architecture, sources, and
current functionality. Then read this file for durable working context.

## Isokratis legacy app

The legacy App Inventor project is at
`oldapp/isokratis_new.aia`. It is a Byzantine chant companion named
`isokratis_2021`.

### Verified functionality

- It plays a continuous **ison** (drone) using selectable Byzantine-note
  buttons: Δη, Κε, Ζω, Ζω β, Νη, Πα, Βου, Γα, Γα#, Δι and Και.
- It supports changing the drone by semitone, selecting the natural setting,
  changing the interval/register, changing volume, looping, stopping,
  restarting, and resetting the selected note state.
- `Player1` is the looping ison player. Its source is built from the selected
  note and interval/semitone state, then played from an MP3 file.
- It offers chant recording lists for the eight modes, plagal modes, Varys,
  and Divine Liturgy. `Player2` plays the selected recording.
- It opens a local liturgical PDF library: Leitourgika, Typiko, Pandektis
  Zois, Minaia, Anastasimatarion, Eirmologion, Triodion, Pentikostarion,
  Apostolos, Paraklitiki, Orologion, Euchologion, and related items.

### Legacy storage assumptions

The Android app expects content on the device, primarily:

```text
/sdcard/isokratis/  # drone MP3 files
/sdcard/prosomia/   # chant-recording MP3 files
```

The `.aia` archive contains the logic and icon only; its MP3 and PDF content
will be uploaded separately.

### Web conversion decision

Implement the replacement **inside the main page** at `/kihem/`, not as a
separate user-facing page. Use a server-side media catalog and safe, explicit
MP3 asset routes. Do not expose arbitrary server filesystem paths. Browser
audio replaces the App Inventor players; PDF functionality is intentionally
out of scope.

### Conversion sequence

1. Inventory the uploaded MP3 assets and map their filenames to the legacy
   note/mode meanings.
2. Create the media catalog and safe file-serving routes.
3. Implement the ison controls and browser audio behavior.
4. Implement the recording menus.
5. Verify every mapping and test the page on desktop and mobile before
deployment.

### Current web implementation

- `src/isokratis.py` reads only direct `.mp3` files from `isokratis/` and
  `prosomia/`, rooted at `KIHEM_BYZ_DIR` (default `/var/lib/kihem/byz`).
- The main Kihem page contains the controls. It plays numeric ison filenames
  through `/isokratis/ison/<number>.mp3` and catalogued recording filenames
  through `/isokratis/prosomia/<filename>`; neither route exposes PDFs.
- The old pitch formula is retained: `number = note base + register +
  semitone × 6`, with register range −12…+12 and semitone range −3…+3.
- In the web UI, selecting a note is the only way to start ison playback. It
  loops continuously until «Διακοπή»; there are intentionally no separate
  start or reset buttons.
- The first eight numeric setup recordings (`1-1` through `1-4-1`) and the
  user-selected Β΄-ήχου exclusions are not listed in the public recording
  menus; this includes the numbered setup tracks, `gynaikes`, `mathites`,
  `mathitwn`, `oikos`, `poiois`, `sarki`, `stauros`, the selected `ta-anw`
  variants, and the requested Greek `γυναίκες`/`μαθητές` variants. Selecting
  an item in the recording list starts it immediately.
- The numbered Γ΄-ήχου setup recordings (`3-0` through `3-3-1`) are likewise
  not listed in the public menu.
- Uploaded workspace media is at `byz/isokratis` and `byz/prosomia`; do not
  stage these binaries in Git.

## Melodos heading parity

Kihem shows the same daily heading text as Melodos: its source date line,
weekly-tone line, and feast/saints title. The feast/saints title comes from
Melodos' public month-calendar response and is cached by month; it is not
guessed from the date. The former top-of-page music-insertion status and
book-link list are intentionally not displayed.

The reader uses fixed auto-scroll speed 1 only. Its sole control is a
pause/resume button; speed selection and keyboard speed controls are not part
of the interface. The Great Doxology excerpt is anchored after its late
“ἐν τῷ φωτί σου ὀψόμεθα φῶς” context, not the opening Trisagion.

The default page request is the current date's Orthros. `KIHEM_DEFAULT_DATE`
is an optional explicit override, not the normal production default.
