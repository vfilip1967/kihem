# Kihem music-source memory

Updated: 2026-09-09

## Persistent books

1. `ioannis-protopsaltis-1905`
   - Anastasimatarion of Ioannis Protopsaltis, Constantinople 1905.
   - Local file:
     `/var/lib/kihem/books/anastasimatarion-ioannou-protopsaltou-1905.pdf`
   - Official record: `https://repository.mmb.org.gr/digma/handle/123456789/5477/`
   - SHA-256: `225733d51233acf41294211368a8d15c1919535edbd15624af40e90a71a74eb9`

2. `ioannis-protopsaltis-eirmologion-1903`
   - Heirmologion of Katavasies for the whole year, slow and short, Ioannis
     Protopsaltis, Constantinople 1903; 504 scanned pages.
   - Local file:
     `/var/lib/kihem/books/eirmologion-katavasion-ioannou-protopsaltou-1903.pdf`
   - Official record: `https://repository.mmb.org.gr/digma/handle/123456789/5481/`
   - SHA-256: `0e31feb82dfa19cf627a9ca2c68ae7b0c511419cf43d2d6f7a75f52bceddb44b`

3. `pandekti-orthrou-1851`
   - Pandekti, volume II (Matins), Constantinople 1851.
   - Local file is a verified five-page source extract, not the entire volume:
     `/var/lib/kihem/books/pandekti-tomos-b-1851-pages-490-494.pdf`
   - Official record: `https://anemi.lib.uoc.gr/metadata/b/8/4/metadata-06-0000088.tkl`
   - SHA-256: `d1b5d5bc97f78841d7d489c1e640a661ae28e4e537dc2592599434304e8ea4b3`

4. `kypseli-stefanou-lampadariou-minaia`
   - Μουσικὴ Κυψέλη Στεφάνου Λαμπαδαρίου, Μηναία· ιδιόμελα, δοξαστικά,
     απολυτίκια και κοντάκια του όλου ενιαυτού.
   - Local file:
     `/var/lib/kihem/books/kypseli-stefanou-lampadariou-minaia.pdf`
   - Official category and source PDF:
     `https://melodos.com/bibliothiki/?cat=157`
   - SHA-256: `478195e43530092f0398c1ec6dcf7ff7714a7a48953a201cb71c2f70a3a14619`

## Verified mappings for 2026-09-13

- Anastasimatarion: resurrectional apolytikion, two kathisma groups,
  resurrectional Evlogitaria (printed pp. 17–20), anavathmoi, canon odes 1 and
  3, Timiotera in plagal fourth (pp. 418–419), first four Ainoi, Eothinon 4 and
  the great doxology.
- Pandekti: Psalm 50 in tone 2, printed pp. 490–494.
- Heirmologion: short Cross katavasies beginning “Σταυρὸν χαράξας Μωσῆς”.
  Use only the eight short heirmoi from printed pp. 225–235; the 13 crop regions
  deliberately omit the intervening troparia of the complete canon. Do not use
  the slower continuous setting on printed pp. 87–92 when a short setting is
  requested or available.

## Verified fixed-feast mappings for 8–9 September 2026

- 8 September: the Kypseli scan has the Nativity of the Theotokos
  apolytikion (printed p. 51), kontakion (p. 52) and doxastikon (p. 34).
- 9 September: the Kypseli scan has the Theopatores doxastikon on printed
  pp. 57–58. The 9/9 service also repeats the preceding feast's apolytikion
  and kontakion, so the corresponding Kypseli excerpts are attached there.
- The 9/9 Melodos note says the Cheroubikon, leitourgika and koinonikon are
  sung in fourth-tone agia on a simple Wednesday. The existing Pandekti
  fourth-tone excerpts are therefore enabled for that note; a non-matching
  special koinonikon is left unattached rather than guessed.

## Tone-specific Divine Liturgy core

Melodos publishes compact, localizable scans containing the three central
tone-dependent members. The application registers and lazily downloads these
PDFs under `/var/lib/kihem/books`:

- `melodos-liturgy-tone-1.pdf`, source post `?p=2063`;
- `melodos-liturgy-tone-2.pdf`, source post `?p=2087`;
- `melodos-liturgy-tone-3.pdf`, source post `?p=2167`;
- `melodos-liturgy-tone-4.pdf`, source category `?cat=157`;
- `melodos-liturgy-tone-5.pdf`, source post `?p=2238`;
- `melodos-liturgy-tone-6.pdf`, source post `?p=1932`;
- `melodos-liturgy-tone-7.pdf`, source post `?p=1967`;
- `melodos-liturgy-tone-8.pdf`, source post `?p=2037`.

Each has verified regions for the short Cheroubikon, the Litourgika, the two
Amens/«Σὲ ὑμνοῦμεν», the «Ἄξιον καὶ δίκαιον» response and the Sunday
«Αἰνεῖτε τὸν Κύριον» social. The regular fourth-tone days use the local
fourth-tone scan (Cheroubikon pp. 1–4, Litourgika pp. 5–10, Koinonikon pp.
11–12). The fourth-tone agia feast remains backed by the D΄ Pandekti scan,
with its separate «Καὶ μετὰ τοῦ πνεύματός σου» and «Ἄξιον καὶ δίκαιον»
responses. The D΄ volume also supplies the verified Thursday and Friday
socials (printed pp. 348–350 and 354–355).

The Melodos note is a hard gate: a tone-specific excerpt is attached only when
the note names that tone. No page from another tone is used as fallback. In
the 8–16 September 2026 verification window every Divine Liturgy has at
least 12 attachments; 10 September has 14, including the plagal-fourth
Thursday social «Εἰς πᾶσαν τὴν γῆν…».

## Exact-date Menaia policy

At composition time, inspect the Menaia for the exact selected date. Every
verified excerpt found for that date is attached to its matching position in
the Orthros, Divine Liturgy, or (once implemented) Vespers. A neighbouring
date is never used as a fallback, and a text or tone match alone is not enough.
The current Kypseli scan has no verified entry for 10 September 2026, so no
Kypseli page is attached for that day.

## Matching and rendering invariants

- Preserve exact polytonic source text; normalization is only for matching.
- Match a distinctive ending plus required section headings/incipit to avoid
  attaching a similarly worded hymn from another context.
- Insert a multi-ode excerpt after the final corresponding ode, not after the
  first incipit.
- Every PDF page and crop must be visually verified. At page transitions it is
  preferable to retain a minimal adjacent line rather than cut a Byzantine
  musical sign.
- Every attachment must expose a human-readable bookmark label and a stable
  in-page anchor; use the piece title as the related wording.
- Generated PNGs are temporary cache artifacts; source PDFs remain in the
  persistent books directory.
