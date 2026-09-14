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

Implement the replacement as a mobile-first Flask page at
`/kihem/isokratis` (within the existing Kihem deployment), linked from the
main Kihem page. Use a server-side media catalog and safe, explicit asset
routes. Do not expose arbitrary server filesystem paths. Browser audio will
replace the App Inventor players, and approved catalogued PDFs will replace
the Android file-viewer intents.

### Conversion sequence

1. Inventory the uploaded MP3 and PDF assets and map their filenames to the
   legacy note/mode/document meanings.
2. Create the media catalog and safe file-serving routes.
3. Implement the ison controls and browser audio behavior.
4. Implement the recording menus and PDF library.
5. Verify every mapping and test the page on desktop and mobile before
   deployment.
