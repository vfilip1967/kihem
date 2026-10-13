# Kihem working memory

Read [`README.md`](README.md) first; it is the full project documentation.
This file records only durable implementation decisions.

## Current application

- Kihem is a Flask app served at `/kihem/`. A request without `date` opens
  tomorrow's Orthros; `KIHEM_DEFAULT_DATE` is only an explicit override.
- Orthros and Divine Liturgy are separate page loads. Their sticky toolbar
  keeps the date in both links, has fixed auto-scroll speed 1 with an
  icon-only pause/resume control, and keeps the compact Isokratis controls.
  Its top navigation is a single non-wrapping compact row; the music bookmark
  buttons are labelled «Αναγνώσεις» and «Μουσικά» and stay beside the
  pause/resume icon. «Αναγνώσεις» contains anchors for «1ος Απόστολος» and
  «Ευαγγέλιο» whenever they occur.
- The heading copies Melodos' date, weekly tone and feast/saints text. The
  monthly calendar response is cached; it is never guessed.
- Sunday Orthros has verified, tone-specific clips for the Kathismata,
  Anavathmoi and resurrectional canon odes 1 and 3 in all eight tones.  Match
  every tone-specific clip against the «Ήχος εβδομάδος» heading returned by
  Melodos for that date; never derive it from the calendar. This tone changes
  on Sunday and governs the whole following week, so incidental feast tones
  must never select a different excerpt.
- Never infer Sunday Anavathmoi from a weekly tone plus «Προκείμενον» alone.
  Require Melodos' resurrectional-Evlogitaria marker; weekday Orthros may
  have that tone and a Prokeimenon without any Anavathmoi (as on 2026-09-22).
- Kathismata precede the Resurrectional Evlogitaria; Anavathmoi precede the
  Prokeimenon; Canon clips normally start at the named Ode A/G blocks. On
  the Holy-Fathers Sunday in tone 2, however, the Kathismata score follows
  the final «Τῶν Μαθητῶν σου… τὸ μέγα ἔλεος», while Odes 1 and 3 follow their
  complete resurrectional text and precede the corresponding Fathers' Canon.
  The plagal-
  second Great Doxology is inserted immediately before «Σήμερον σωτηρία».
  Sunday resurrectional Ainoi are always selected from Melodos' explicit
  weekly tone and placed immediately before the Eothinon Doxastikon. When a
  feast Sunday replaces it with its own Prosomoia/Doxastikon, place the same
  verified Ainoi immediately before that feast block instead; never omit
  them merely because the Eothinon-Doxastikon heading is absent. The
  verified Anastasimatario forms are invariant: tones 1, 2, 5 and 6 use the
  slow setting; tones 3, 4, 7 and 8 use the short setting. Verified printed
  ranges are respectively 39–43, 86–91, 244–251, 298–304 (slow) and
  138–145, 193–198, 360–365, 420–425 (short). Never infer this from the
  calendar date or substitute a partial Ainoi clip.
  The plagal-fourth
  Kathismata and Anavathmoi scans retain their openings (both Kathismata and
  all four antiphons respectively), rather than cropping the first phrases.
  For plagal-fourth Ode 1, retain the opening «Ἁρματηλάτην Φαραώ» and place
  the score after the full resurrectional Ode 1, before the following feast
  Canon.
  For plagal-fourth Ode 3, use the complete score (printed pp. 405–407) and
  place it immediately before the following feast Canon, never before the
  Melodos text of the Ode itself.
- The complete Cross katavasies scan is inserted before «Τὴν Θεοτόκον καὶ
  Μητέρα τοῦ Φωτός…»; the Timiotera follows its sixth refrain. A strict
  fallback supports feast-day documents that say the Timiotera is omitted.
  The fourth-tone Timiotera is attached at the same point and uses verified
  score regions on printed pages 191–192.
- The full fourth-tone Theotokos Katavasies «Ἀνοίξω τὸ στόμα μου» use the
  verified Eirmologion score on printed pages 51–56. When Melodos identifies
  that exact setting, attach it before «Τὴν Θεοτόκον…», before the Timiotera
  and ninth ode (as on 26 September). Add other Katavasies only after the
  exact setting and score pages have been verified.
- Timiotera tone rules must use the nearby «Καὶ ψάλλεται…» and its own tone
  label. Never choose πλ. δ΄ merely because that tone occurs elsewhere in the
  daily Orthros; 26 September's local label is explicitly «Ἦχος δ΄».
- The converse is equally mandatory: when the nearby rule says «στον ίδιο
  ήχο του Ειρμού · Ἦχος πλ δ΄», select the plagal-fourth Timiotera, never an
  earlier incidental fourth-tone mention. This is verified for 3 October
  2026 Orthros.
- `AttachmentRule.semantic_context` is the preferred mechanism for a rule
  whose musical decision depends on a local Melodos instruction. The first
  resolver is `timiotera`: it reads the last nearby instruction «Καὶ ψάλλεται
  ἡ Τιμιωτέρα στον ίδιο ήχο…», parses its immediately following explicit
  label, and selects the matching verified score. It must never use a tone
  elsewhere in the document or guess when the local instruction is absent.
- `src/typesafe_decisions.py` is an optional TypeSafe Jev pilot, enabled only
  by `TYPESAFE_API_KEY` and configured with `KIHEM_TYPESAFE_MODEL` (default
  `jev-latest`). It is a closed-set reviewer for that same local Timiotera
  instruction: `plagal4_timiotera`, `tone4_timiotera` or `no_score`; it never
  generates a score or substitutes for the Melodos rule. Cache successful
  answers in `KIHEM_CACHE_DIR/typesafe-decisions`. A high-confidence (>=0.95)
  disagreement blocks an unsafe insertion; an unavailable service keeps the
  deterministic local decision. Never store or log the API key.
- The same TypeSafe reviewer validates the Sunday-Ainoi form with the closed
  choices `slow_ainoi`, `short_ainoi` or `no_score`. It receives the parsed
  weekly tone and the local Eothinon boundary, not an arbitrary scan; the
  deterministic tone-to-form rule above remains authoritative.
- «Ὑπερευλογημένη» always uses the fixed second-tone Petros Lampadarios
  setting from the separate Pemptousia source, because the 1905 local
  Anastasimatario does not contain a usable engraved setting for it.
- When Melodos declares «ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ ΣΤ΄», attach the verified
  plagal-second score «Ἡ ὄντως εἰρήνη σὺ Χριστέ» (printed pp. 304–305) only
  after that specific Doxastikon's final «Κύριε δόξα σοι», before
  «Ὑπερευλογημένη».

## Scripture interpretations

- `src/scripture_interpretations.py` finds the Eothinon Gospel, first Apostle
  and Gospel for Orthros, and the first Apostle and Gospel for every Divine
  Liturgy, from Melodos' own headings. The same generated interpretation is
  inserted immediately after the corresponding reading, never gathered
  elsewhere on the page.
- The first Apostle and Gospel always receive direct top-toolbar bookmarks in
  Orthros and Divine Liturgy, on weekdays and Sundays. For an Orthros source
  that omits the explicit `ΕΥΑΓΓΕΛΙΟΝ` heading, use the recognised unlabelled
  Orthros/Eothinon Gospel as the Gospel bookmark rather than omitting it.
- An exact reading is generated once with `gpt-5.6-luna`, `reasoning.effort: none`
  and Responses `store: false`, then stored in
  `KIHEM_CACHE_DIR/scripture-interpretations/<sha256>.json`.  Reuse this disk
  cache for every later visit; it must not make another model call.  A lock
  prevents duplicate paid requests from concurrent page loads.
- A cache miss is generated by up to three background workers, so the
  Eothinon (including an unlabelled Orthros Gospel), first Apostle and first
  Gospel can be prepared in parallel; never make a page visit wait for the
  model. Until its first generation completes, do not render an incomplete
  interpretation; the next page load reads the completed cache.
- On days with optional second readings, interpret only the first Apostle and
  first Gospel. The Apostle ends at a standalone «Ἀλληλούϊα» node, never at a
  substring such as «ἀλλήλους» within the biblical text.
- Every interpretation must finish with «Θεολογικά μηνύματα», including a
  long Gospel. Each message quotes its full supporting ancient-Greek verse or
  sentence and its reference; cache versioning regenerates an incomplete entry.
- `OPENAI_API_KEY` enables generation; when absent, do not call an external
  model and leave the reading unchanged. `KIHEM_INTERPRETATION_MODEL` is the
  explicit model override.

## Melodos music

- Treat Melodos as untrusted HTML: never retain its scripts or event handlers.
- `src/melodos.py` rebuilds only its own `mousika/` selectors/buttons as safe
  local controls with the same labels and direct MP3 URLs. This includes the
  `___Επίλεξε ή PAUSE` selectors and one-click MP3 buttons.
- Playback of those controls goes through `/melodos-audio`: `src/audio_cache.py`
  accepts only HTTPS MP3 paths below `melodos.com/akolouthies/mousika/`, keeps
  the first successful download under `KIHEM_CACHE_DIR/audio`, and reuses it
  for both Orthros and Divine Liturgy. The browser also receives a one-year
  cache lifetime.
- If Melodos explicitly says the Great Doxology follows the Doxastikon or the
  day tone,
  preserve and label its supplied audio selector with that local tone. The
  tone comes from the nearby Doxastikon block, never from an unrelated later
  occurrence; 26 September is «Ἦχος πλ. δ΄». That exact case receives the
  verified visual score of the short Great Doxology by Manouel Protopsaltis
  (printed pp. 426–430), placed after the complete first textual section at
  «Παράτεινον τὸ ἔλεός σου τοῖς γινώσκουσί σε», with its own «Μουσικά»
  bookmark. Do not replace a scanned musical excerpt with only an audio
  selector.
- The first-tone Great Doxology is the verified Manouel Protopsaltis score on
  printed pp. 45–48. Attach it only when the parsed, nearby Melodos selector
  says `Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος α΄`; place it after
  «Παράτεινον τὸ ἔλεός σου…» and before the following hymn. This covers the
  Sunday 2026-10-04 Orthros without inferring the tone from the date.
- In Divine Liturgy, use the verified slow Trisagion with all three executions
  (printed pp. 43–45) after the third choir execution and before Dynamis;
  never substitute the short alternative on p. 45. The Antiphon A/B score
  pages follow the completed Antiphon (after the final A refrain and after
  B's «Δόξα... Καὶ νῦν...»), never their first refrain. These fixed Liturgy
  insertions apply equally on Sundays and weekdays; only the supplied
  date-specific readings and commemorations vary.
  The score for the two Amens / «Σὲ ὑμνοῦμεν» uses only its own consecutive
  scan regions, so it never begins on a continuation syllable or includes the
  following hymn. The complete «Ἄξιόν ἐστιν ὡς ἀληθῶς… σὲ μεγαλύνομεν» has a
  separate tone-specific bookmark immediately after its full Melodos text.
  A plagal-second Great Doxology likewise follows Melodos' explicit note that
  it is sung in the Doxastikon's tone, even if the weekly tone differs; place
  its score after the complete Doxology and before the following hymn.
  post-Cheroubikon Kyrie/Paraschou and Axion use the Melodos-recommended tone.
  Treat Sunday wording «στον κύριο ήχο της ημέρας, ήχο πλ δ΄» as the explicit
  plagal-fourth setting, alongside «ψάλλονται σε ήχο πλ δ΄». The Antiphon B
  score covers both «ὁ ἐν Ἁγίοις θαυμαστός» and «ὁ ἀναστάς ἐκ νεκρῶν».
  The Tuesday/saints `Εἰς μνημόσυνον` anthology supplies all eight tones.
  Verified excerpts are also attached for `Πληρωθήτω` and `Εἴη τὸ ὄνομα`.

- For first-tone Sunday Orthros, attach the complete slow resurrectional Ainoi
  immediately before the Eothinon (printed pp. 39–43),
  then attach Eothinon VII «Ἰδοὺ σκοτία καὶ πρωΐ» after its own full text
  and before «Ὑπερευλογημένη» (printed pp. 365–366). The first-tone Canon
  Ode 3 is printed pp. 24–25; do not reuse the following Ode 4 pages.
- Sunday Liturgy frequently says that the Cheroubikon, Litourgika and
  Koinonikon are sung «στον κύριο ήχο της ημέρας». Treat that wording as the
  normal tone-specific instruction for all eight tones, so Sunday receives
  the same core score bookmarks as a weekday Liturgy.
- The Sunday first-tone Koinonikon «Αἰνεῖτε τὸν Κύριον» uses all three pages
  15–17 of `melodos-liturgy-tone-1.pdf`; page 17 is the indispensable final
  «Ἀλληλούϊα», not a publisher-only closing page.

## Digital Byzantine scores (pilot)

- Do not claim that a scanned Byzantine score has been automatically and
  correctly interpreted. Image recognition may assist a later transcription
  workflow, but the authoritative source remains the scan and every
  performance-capable result needs named psaltis review.
- `src/digital_scores.py` is an intentionally small, source-agnostic local
  catalogue for Neanes `.byzx`, optional MusicXML and preview assets. Its
  public schema is `src/data/digital_scores.json`; assets live outside Git in
  `KIHEM_DIGITAL_SCORES_DIR` (default `/var/lib/kihem/digital-scores`).
- A score has one of `draft`, `needs_review`, `verified`. A `verified` score
  must identify its reviewer. No library item is an instructional playback
  candidate before that state. The first pilot is the Greek resurrectional
  apolytikion «Τοῦ λίθου σφραγισθέντος», tone 1, not a complex Cheroubikon.
  The external Greek Neanes example (`lithou-sfragisthentos-tone1.byzx`) has
  110 note positions and is `verified` by the named reviewer `vfilip`; it
  must never be called a Kihem scan conversion.
- A second, deliberately non-public candidate is the official Greek Neanes
  example «Ὅτε κατῆλθες πρὸς τὸν θάνατον» in tone 2
  (`ote-katilthes-tone2`). It is `needs_review`, has no named reviewer and
  must not be promoted until the full visual comparison and technical/audible
  check have been recorded. Its matching source spans printed pp. 65–66 of
  the *Anastasimatario Ioannou Protopsaltou* (1905), installed privately as
  `ote-katilthes-tone2-source-1.png` and `ote-katilthes-tone2-source-2.png`,
  because the apolytikion begins at the end of p. 65. Its review page must never reuse the
  first-tone source pages 13–14. PNG/MusicXML derivatives still do not exist,
  so it remains private and exposes the protected `.byzx` and embedded Neanes
  technical player.
- The first actual scan-to-score experiment is the separate private `draft`
  `ote-katilthes-tone2-ocr-draft`: exact crops from pp. 65–66 are joined
  before OCR, excluding the following Kathismata. Byzantine Chant OCR model
  v0.0.4 yields a `.byzocr` (86 interpreted groups, 6 lines) and the official
  Neanes OCR importer yields a `.byzx` (82 notes, 5 carried line breaks).
  The neume OCR does not recognise lyrics; a separate local Greek Tesseract
  pass supplies source-corrected text, temporarily attached to the successive
  note groups line by line. That syllable-to-neume mapping must remain a
  private draft until a psaltis checks it. The subsequent visual comparison
  found systematic neume errors, so this is a failed experiment, not a
  candidate score, a training example or a source for a glyph map. No claim
  of musical correctness is permitted.
  The external `needs_review` Neanes example remains an
  independent comparator and was not used to create this draft.
- A second, intentionally separate research path analyses born-digital PDF
  layout before any transcription. `src/vector_pdf.py` and
  `digital_scores/extract_vector_pdf.py` preserve each selected page's font,
  embedded font instance/subset, rendered glyph id, supporting codepoint,
  geometry and lyric text in a private JSON report. The pair `font instance +
  glyph id`, not a potentially misleading Unicode CMap value or visible font
  name, is the key for any font-specific mapping: the PDF can subset the same
  named font differently on another page. They do
  not raster-OCR, infer a Neanes note, create a `.byzx`, copy a source into
  Kihem or make it publishable. A future font-code-to-Neanes map must be
  explicit, tested and compatible with the source licence. Reports stay out
  of Git and outside the public digital-score catalogue.
- The optional second stage `write_neanes_glyph_suggestions` renders the
  official Neanes font vocabulary and ranks only visual outline similarity
  for each source `font instance + glyph id`. Its JSON rows are explicitly
  `visual-candidate-only`: they do not resolve composite/contextual neumes,
  lyrics or timing and can never directly generate a `.byzx`.
  The first real comparison against both Neanes and Neanes Stathis Series on
  the Iviron vector PDF page 12 produced only 0.51–0.70 top similarity, below
  the conservative 0.82 `reviewable-shape-only` threshold. Treat those rows
  as `insufficient-shape-evidence`, never as a font map.
- `src/pdf_font_forensics.py` and
  `digital_scores/inspect_embedded_fonts.py` provide a private feasibility
  report before further work on a vector PDF. They inspect only the embedded
  program/table metadata and PDF ToUnicode entries; font binaries are not
  stored or served. For the Iviron vector PDF, the PSALTIRIOUBodoni,
  isokratima3 and FTHOGOS2 subsets have anonymous glyph names and no `cmap`,
  `GSUB` or `GPOS`; their PDF ToUnicode tables merely map CIDs to Greek text.
  Therefore its embedded font data has no recoverable semantic music mapping.
- Public PDFs demonstrably written with St Anthony's **EZ Byzantine Music Font
  Package** are a better, separate path than anonymous embedded-font PDFs:
  the complete official fonts retain the same PUA code and glyph-id inventory
  as the PDF. `src/ez_font_mapping.py` and
  `digital_scores/build_ez_mapping_template.py` create a private evidence
  template keyed by `font instance + glyph id + PUA code`; every Neanes field
  remains `unconfirmed` and the tool cannot write `.byzx`. This prevents a
  precomposed EZ glyph, a supporting mark or a Word-macro layout instruction
  from being treated as an independently timed Neanes note. Keep EZ sources,
  fonts and templates out of Git and the public catalogue until the licence
  and semantic mapping are checked.
  The official EZ template and instructions give source semantics for a small
  initial set (`1` Oligon, `!` Apostrophos, `@` Elaphron, `)` Hyporoe,
  `S` Gorgon and specified Klasma/composite variants). These are attached as
  `source_definition` evidence only; `neanes.status` remains `unconfirmed`
  because attachment, timing and decomposition require the local score
  context. The template also records the official EZ character-table family;
  glyphs with no legacy keyboard key are treated as potential macro/secondary
  insertions and never receive an inferred Neanes value.
- The permitted next EZ stage is private, reviewer-confirmed phrase assembly:
  `src/ez_neanes_draft.py` and
  `digital_scores/build_ez_neanes_event_draft.py` turn a phrase plan into
  Neanes-compatible `Note` event JSON only when every event has
  `confirmed: true`, stable template anchors (`font instance + glyph id + PUA
  code`), exactly one documented quantitative base and a separately anchored
  gorgon/time/quality attachment. It fails closed on an unknown or mismatched
  glyph and on precomposed EZ glyph decomposition. It deliberately does **not**
  write a full `.byzx`, publish content, or claim a musical result is verified:
  score construction, lyrics and visual/auditory Neanes review remain separate.
- A subsequent private bridge, `src/neanes_byzx_bridge.py` and
  `digital_scores/build_ez_neanes_byzx.py`, can turn that checked event draft
  into a full `.byzx`. It requires an explicit local Neanes checkout and uses
  Neanes' own `Score`/`SaveService` classes inside a short-lived Vitest worker,
  then reopens the file as a technical validation. It never copies a generic
  JSON skeleton, cannot accept a non-private or non-`needs_review` event
  draft, and does not publish/register the result. An opening Martyria is
  included only when the phrase plan separately confirms note, root sign and
  scale; otherwise the file contains no inferred starting mode.
- The direct legacy-Word bridge applies the same rule more strictly:
  `src/ez_word_neanes_draft.py` permits `opening_martyria` only after a
  reviewer marks it confirmed, supplies a non-empty visual `source_evidence`
  reference, and supplies valid Neanes `note`, `rootSign`, and `scale`.
  A formula collection heading is never evidence for a formula's exact
  starting base.
- The separate official EZ sample *Anasta O Theos* has a reviewer-confirmed
  opening indication «Ἦχος βαρὺς · Γα», confirmed by the psaltis as «βαρύς
  εκ του Γα διατονικός»: its private review candidate records
  `note: Ga`, `rootSign: Varys`, `scale: Diatonic`. This is source-specific
  and must never become a blanket rule for every member in grave mode; its
  phrase itself remains unreviewed.
- To reduce the reviewer's lookup work before phrase confirmation,
  `src/ez_phrase_review.py` and
  `digital_scores/build_ez_phrase_review_sheet.py` join the vector-PDF report
  with the EZ evidence template into private, geometry-grouped notation lines.
  Each occurrence retains its exact `source_anchor`, geometry, keyboard/table
  category and documented source definition; nearby text is explicitly only a
  candidate and is never assigned to a note. The sheet has empty phrase/event
  review fields and cannot write `.byzx`. On the official public EZ sample it
  identified 215 notation-glyph occurrences in 10 review lines; this is a
  private organisation result, not a music transcription.
- `src/ez_review_packet.py` and
  `digital_scores/create_ez_line_review_packet.py` make the next human step
  usable: given a review-line id and the permitted local PDF, they create a
  private source crop, Markdown checklist and empty phrase-plan skeleton with
  all anchors still unassigned. The initial public-EZ demonstration packet is
  `/tmp/kihem-ez-pilot/reviews/anasta-o-theos-greek-line-1/` for
  `page-1-line-7`, the Greek line beginning «Ἀνάστα ὁ Θεός…». It has no
  musical events and must not be compiled until the reviewer provides them.
- The reviewer of the first Greek line confirmed that the red EZ Special-II
  glyphs above the melody are **isokratemata**, not missing ornamentation.
  The documented key-row plus visual packet now map `N`/`U+F04E` to
  `Ison.Ga` (Γ), `c`/`U+F063` to `Ison.Ni` (Ν) and `M`/`U+F04D` to
  `Ison.Thi` (Δι). `?`/`U+F03F` is the Μ instruction: the human isokratis
  stops ison and chants with the main singer. It is therefore `isonControl:
  Pause`, never a Neanes pitch; confirmed controls are retained in a separate
  `ison_controls` list in the private event draft, for a future continuous
  software ison to pause. Neanes itself has no such continuous second voice.
  Key `0` is now documented as the quantitative Neanes `Ison`. The review sheet
  exposes every gorgon, time mark and isokratema as an attachment candidate
  with nearest preceding/following **line positions** for reviewer selection,
  rather than silently associating or dropping later gorgons.
- The reviewer identified `z`/`U+F07A` of EZPsaltica as **βαρεία**: a modal,
  non-timed sign placed before and energising the following note. Its source
  definition maps to the Neanes boolean note property `vareia: true`; it is
  shown as an attachment candidate to the following confirmed base and is
  never emitted as an independent timed Neanes note.
- `'/U+F027` of EZPsaltica is a visually confirmed **ίσον** variant in the
  first private review packet. It is a quantitative `Ison`, not an attachment
  or an isokratema; its earlier absence was simply because the initial EZ
  source-definition table intentionally covered only a small documented set.
- `:`/`U+F03A` of EZPsaltica is visually confirmed as the **απλή χρονική**:
  Neanes `timeNeume: Hapli`, worth one time unit. It remains an attachment
  candidate until a reviewer confirms the base note it belongs to; it is not
  an independent note.
- The public St Anthony Formula Word archive is available locally under the
  private EZ pilot (`Formula1p.doc` … `Formula8p.doc` etc.). It is direct
  Word source evidence for EZ character sequences, not a source copy of the
  Greek `AnastaOTheos` PDF. The legacy `wvWare` route in `src/ez_word.py`
  remains an ordered-PUA diagnostic only. The authoritative private import
  route is now `digital_scores/extract_ez_word_runs.py`, backed by the local
  Apache POI/HWPF helper in `digital_scores/word_importer/`: it reads each
  Word `CharacterRun` and preserves the actual EZ font, so a PUA character is
  source-font-confirmed rather than inferred. It still never emits `.byzx`:
  layout attachments, timing and Neanes semantics require documented mapping
  plus psaltis review. PDF is only visual comparison for this path.
- A direct Word→Neanes bridge now exists in `src/ez_word_neanes_draft.py`
  and `digital_scores/build_ez_word_neanes_event_draft.py`. It uses only
  exact `word_occurrence + pua_codepoint` anchors from a POI font-run report;
  every event requires `confirmed: true`, a named psaltis reviewer and one
  documented quantitative EZ base. It rejects non-EZ runs, unsupported
  decompositions and unanchored attachments. Its output is still an internal
  `needs_score_and_auditory_review` event draft before the Neanes serializer
  writes any private `.byzx`.
- The direct-Word Formula1p pilot now has a second **private** `.byzx`
  rendition, `formula1p-ez-word-varys-ga-diatonic-pilot`, for the same five
  exact Word events (`Oligon → Ison → Apostrophos ×3`). It adds only the
  separately confirmed opening Martyria `Ga / Nana / Diatonic`, where the
  visible sign below the Γ is two small η (Neanes `martyriaNanaBelow`, U+E154).
  Earlier candidates were wrong: `Varys` (U+E150) renders as a wavy dash, and
  `DeltaDotted` (U+E155) has dots above. The named reviewer `vfilip` confirmed
  the rendered form visually and auditorily on the protected player, so the
  pilot is `verified` and published in the public catalogue (`.byzx` and
  player only; no PNG or MusicXML derivatives exist for it). The phrase
  anchors come from `Formula1p.doc` run 3322; the evidence for the Martyria
  comes separately from the visible `AnastaOTheos.pdf` heading and psaltis
  confirmation, so it must never be presented as inferred from that Word
  formula. The bridge writes this as a manual Neanes Martyria with
  `note: Ga`, `rootSign: Nana`, `scale: Diatonic`, `auto: false` and a
  retained `rootSignOverride`. This resets Neanes' analysis/playback state to
  the supplied base. Its exact visual form remains subject to the psaltis'
  check against the source; never infer visual acceptance from the serialized
  fields alone.
  A generic automatic Martyria on an otherwise empty staff starts at Pa and
  was prohibited for this pilot. It carries no lyrics. The `verified` status
  covers only this five-event technical formula, not a complete chant.
- The private Neanes player must version the **browser-side filename** as
  well as the authenticated `.byzx` URL. Neanes persists documents by
  filename; reusing `<score-id>.byzx` can retain an earlier tab and display
  its Pa martyria after the asset has changed. `digital_score_playback` now
  passes `<score-id>-<asset-mtime-ns>.byzx`, so every installed revision is
  opened as a new document. The bridge's Neanes worker must reopen the saved
  file and assert the explicit Martyria's `auto=false`, note, root sign and
  scale, so a serializer regression cannot silently turn the initial note
  back into Pa.
- For that pilot, the title, tone, complete text, neumes and timing have been
  visually checked against the Kihem *Anastasimatario Ioannou Protopsaltou*
  (1905), printed pp. 13–14. This is documented in
  `digital_scores/lithou-sfragisthentos-tone1-review.md`. The named reviewer
  `vfilip` also completed the technical/audible Neanes-player check, which
  makes the catalogued digital derivatives public; it does not turn the
  external example into a scan-to-score conversion.
- The official Neanes application has opened the pilot `.byzx` and produced
  PNG and MusicXML derivatives. Its `verified` public catalog entry exposes
  only `.byzx`, PNG and MusicXML; the source scans and review workspace stay
  private. The derivatives describe the existing external Neanes document and
  are never evidence of scan-to-score correctness.
- `/digital-scores` renders a public HTML catalogue for browsers, while API
  callers receive JSON. Each verified item has a public page at
  `/digital-scores/<score-id>/` with the preview and only the public digital
  derivatives; source scans never appear on that page. That page embeds the
  local Neanes player, automatically loads only its verified `.byzx`, and
  starts synthesis only when the visitor presses Neanes' ▶. The public Neanes
  asset route rewrites its compiled review-base paths at delivery; it exposes
  no review route, draft, source scan or arbitrary local file. The public
  reader closes Neanes' `neume-selector` and `properties` Dockview panes after
  loading. It also injects public-reader-only CSS that hides menus, editing
  toolbars and document tabs, while retaining the central score, zoom and
  playback/speed controls. The CSS directly hides the two pane-owning
  `.dv-groupview:has(...)` columns as the robust fallback when Neanes' own
  close-action cannot be invoked across the iframe; the script also directly
  sets those group elements to `display: none`. Public score pages are served
  with `Cache-Control: no-store` so mobile browsers cannot retain stale reader
  wrappers. Once the page has mounted, the reader sets the Neanes zoom to fit
  the available width and removes the canvas padding, so its empty left/right
  canvas is converted into usable score space on desktop and mobile.
- The private review workspace is `/review/digital-scores/<score-id>` and is
  deliberately disabled unless both `KIHEM_REVIEW_USERNAME` and
  `KIHEM_REVIEW_PASSWORD` exist. It uses HTTP Basic Auth, serves draft assets
  only after that authentication, and writes human checklists/notes under
  `KIHEM_DIGITAL_SCORES_REVIEW_DIR`; saving a note never switches a score to
  `verified`. The pilot's two source images correspond to printed pp. 13–14.
- The private workspace embeds an unmodified, local Neanes 0.5.55 web build
  at `/review/digital-scores/<score-id>/playback`. Its Kihem wrapper fetches
  the already authenticated `.byzx` on the same origin and programmatically
  passes it to Neanes' normal browser file input; no score appears in a URL
  or public route. The build lives outside Git in `KIHEM_NEANES_WEB_DIR`
  (default `/var/lib/kihem/neanes-web`) and its `/review/neanes/app/` assets
  require the same HTTP Basic protection. The wrapper, not Neanes, performs
  auto-loading; retain Neanes GPL-3.0-only attribution and source provenance.
  Playback is a technical synthesis, not an MP3 or a human chant recording,
  and can never alone satisfy a human review requirement. The current pilot is
  `verified` by `vfilip`: title, text, neumes and timing were visually checked,
  and technical listening was completed in the embedded player.
- A supervised reference-pair ledger is now the only permitted next step for
  exploiting that confirmation. `src/reference_alignment.py` and
  `digital_scores/create_reference_ledger.py` extract the ordered Neanes
  points of a **verified** score into a private JSON file with empty,
  human-confirmed `source_anchor` fields. It never reads the failed OCR draft
  as training data, never writes a `.byzx`, and never treats visual similarity
  as musical fact. Any future mapping remains edition-specific and needs
  several independently confirmed pairs.
- A second private, **verified** score `ananas-line7-pdf-private-draft` covers
  line 7 of page 1 of the public `AnastaOTheos.pdf` sample (16 events, `Ga /
  Nana / Diatonic`, text, isokrata Γ/Ν/Δ and the release Μ). It was confirmed
  visually and auditorily by `vfilip`, and is published without PNG/MusicXML.
  Lessons from building it, which are durable:
  - Neanes accepts only its own enum values. The gorgon is `Gorgon_Top` or
    `Gorgon_Bottom`; the plain `Gorgon` makes the whole document fail to load
    and the player shows an empty "Title" staff. Klasma is `Klasma_Top` or
    `Klasma_Bottom`; the klasma under a `PetastiPlusApostrophos` must be
    `Klasma_Bottom`, and the top form was not drawn there.
  - Isokrata are note attributes: `ison` = `Ison.Ga`, `Ison.Ni`, `Ison.Thi`;
    the release Μ is `Ison.Unison` on the note where the chanter joins the
    main reader. Pauses have no bridge path yet.
  - A sign written before a note belongs to that following note, except where
    the psaltis places it otherwise. The bridge only reads quantitative notes,
    their attachment fields and `lyrics`; the timing rules (gorgon halves the
    next note, hapli extends the previous one) are Neanes' own and must not be
    reimplemented in Kihem.
  - A Neanes note holds one `timeNeume`. Two time signs on the same note cannot
    both be represented, so the psaltis decides which note carries the klasma.
  - When the player shows "Title" and "Ἦχος · Πα" on an empty staff, the file
    did not load. Check the served JSON first; the title and first `Martyria`
    tell whether the current version is being served.
- A third, private **needs_review** entry `papline-cherubikon-lambadarios-line1-private-draft`
  (line 1 of the Lambadarios Cherubikon, mode 1, from papline.gr's public
  Cherubika collection) is the first **automatic** PDF→`.byzx` test. It is for
  private until psaltis-reviewed. **Permission (email reply from papline.gr,
  2026-10-13, answering the user's message of 2026-10-12):** the texts may be
  used freely if not for commercial use; credit papline and keep it
  non-commercial. This is an email, not a formal licence. The full Lambadarios
  Cherubikon (255 events, pages 7–8 of `cherubika_a4.pdf`) is a second private
  entry `papline-cherubikon-lambadarios-full-private-draft`; martyria,
  fthores and glyphs F06F/F077/F0A5/F04F/F0FA are not converted yet.
  papline also sent the original BZ Palaia/Xronos keyboard charts (private
  PDF, not in Git): Palaia = diastoles, isaki, gorgon, tsakismata, hyporoe/
  kentemata with oxeia, kataváseis/anaváseis, quality signs; Xronos = tempo
  "χ" marks (χρονική αγωγή), not neumes. Durable findings:
  - papline's PDFs (Word 2016/365, vector text, ~1 decorative image per page)
    use the open BZ fonts (`BZByzantina`, `BZIson`, `BZLoipa`, `BZFthores`,
    `BZPalaia`, `BZXronos`; OFL) published with the CTAN `byzantinemusic`
    package. The package's `byzantinemusic.sty` names ~494 (font, code) pairs
    and its fonts are glyph-identical to the PDF-embedded ones. BZ codes are
    **not** EZ codes: the same `U+F0xx` is a different sign.
  - **Key every mapping by (font, code).** `U+F066` is "oligon with kentima"
    in `BZByzantina` but the blue ΠΑ isokrata label in `BZIson`; ignoring the
    font produced a phantom note. `BZIson` holds the isokrata labels
    (ΠΑ, ΝΗ, ΓΑ, ΔΙ, ΚΕ, ΖΩ, ΒΟΥ, ΜΕΛ = release, ΔΙ↓/ΚΕ↓ = lower octave) and
    maps to Neanes `Ison.*`.
  - Martyria are two glyphs: a letter (`BZByzantina` `U+F031…F037` = Πα, Βου,
    Γα, Δι, Κε, Ζω, Νη, confirmed from the psaltis' book table) plus a root
    sign. Red `U+F0F9` is έτερον/σύνδεσμος.
    **Psaltis corrections (2026-10-13):** the martyria *letter* names the note;
    the sign below only sets scale/mode. Mid-piece martyria are converted as
    *automatic* Neanes martyria (they show what our notes produce) and
    compared by script with the source letters: this localises errors between
    two martyria. Two real conversion bugs were found that way: (1) the PDF
    embeds BZ glyphs newer than the CTAN fonts (e.g. `BZByzantina F0A2` =
    oligon+kentima below, +2) — the extractor used to *drop* glyphs without
    CTAN ink bounds; it now falls back to the PDF char box; (2) `F05F` is
    `OligonPlusIsonPlusKentemata` (net +1). With both fixes all 9 martyria of
    the Lambadarios Cherubikon match and the piece ends on Πα.
    The Sunday Koinonikon «Αἰνεῖτε» (Petros Lambadarios, `koinonika_sundays_a4.pdf`
    PDF pp. 12–14) needed more glyphs: BZLoipa bases (`F03F`, `F070`, `F061` =
    `OligonPlusKentemataPlusHypsiliRight`), BZByzantina `F067` (υψηλή right),
    `F07A` (+antikenoma), `F03B` (χαμηλή) and fthores. Fthores (BZFthores) are
    mapped by package name to Neanes `Fthora` (`padia`→DiatonicPa …, `nhdia`/
    `Nhdia`→NiLow/NiHigh, `paplab`/`diplagb`→HardChromaticPa/Thi, `dib`/`nhb`→
    SoftChromaticThi/Pa), checked against the psaltis' theory book; Top/Bottom
    from position, fthora next to a martyria goes on the martyria. The note-name
    sidecar records Neanes `virtualNote` (the sung name after a fthora). All 12
    martyria then match. Martyria letters ignore the octave when compared.
  - The PDF text stream is already in reading order and carries glyph origins:
    attachments are assigned to the base whose ink x-range overlaps them
    (a vareia belongs to the *next* base); gorgon/klasma Top/Bottom follows
    the glyph's vertical position; syllables go to the nearest base by x.
  - Glyph confirmations (≈70 BZ glyphs, covering ~96% of occurrences in the
    papline Cherubika/Koinonika PDFs) live in the private, gitignored
    `debug/bz-answers.json`; the extractor/converter prototype is in
    `digital_scores/bz_papline_prototype/` (hard-coded paths, not a supported
    importer).
  - The ison drone is a separate Neanes synth. A melody note on the drone's
    pitch merges with it and sounds missing (the "Χε" report); it was not a bug.
- Player (private and public templates): the playing neume gets a strong
  yellow highlight and a small floating **parallage** tag (Πα, Βου → Γα …)
  above it. Note names come from Neanes' own `PlaybackService` via
  `write_note_names` / `digital_scores/build_neanes_note_names.py`, stored as
  the optional private sidecar `<score>.notes.json` next to the `.byzx`
  (loaded by `DigitalScoreCatalog.note_labels`). The tag is positioned from the
  highlighted box in the same-origin iframe; it maps the `.element-box` DOM
  order to Neanes' element index. A switch "Ισοκράτημα: ναι/όχι" writes
  `volumeIson` into the shared `audioOptionsDefault` localStorage before the
  iframe loads (`null` = mute, Neanes' own serialisation of -Infinity) and
  reloads the page; the default drone volume is -8 dB.
- Deployment reminder: the auto-mode classifier blocks production writes by
  Claude even with the user's consent; the user ran the first deploy with `!`,
  and later identical deploys were allowed.

## Isokratis

- The legacy project is `oldapp/isokratis_new.aia`; the web version is inside
  the main page, not a separate route. PDFs are intentionally out of scope.
- `src/isokratis.py` catalogs numbered MP3 only for the Isokratis in
  `KIHEM_BYZ_DIR` (default `/var/lib/kihem/byz`). Its curated prosomia list
  can additionally use explicit M4A/AAC recordings; asset routes are explicit,
  and arbitrary paths and PDFs are never served.
- Ison filename formula: `note base + register + semitone × 6`. Note buttons
  start looping playback; only the icon-only `Ⅱ` control stops it. The visible
  adjustment steps are −1/+1 and −6/+6.
- Selecting a prosomia mode starts its first curated recording immediately;
  selecting a different MP3 also starts it immediately. Only the icon-only
  `Ⅱ` stop control remains. The fixed `isokratis.py` catalog follows the VLC
  playlist order and excludes historical numbered trials and duplicates without
  deleting source media. On mobile, the fixed audio controls use no more than three
  compact rows, and the mode/MP3 selectors have constrained widths.
  The source-maintained hidden-recording set in `isokratis.py` controls which
  uploaded tracks appear—do not delete source MP3s to change a menu.
- Workspace media is in `byz/isokratis` and `byz/prosomia`; never stage those
  binaries or `oldapp/` in Git.
