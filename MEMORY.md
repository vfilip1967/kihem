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
  «Ευαγγέλιο» whenever they occur. Music bookmark labels are shortened for
  phones (e.g. «Κοιν. α΄ ψηφ.»); the full piece title stays as the link tooltip.
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
  them merely because the Eothinon-Doxastikon heading is absent.
  The Archangels' Sunday (2026-11-08, weekly tone plagal second) is the first
  concrete case: the feast prints «Στιχηρὰ Προσόμοια τῶν Ἀρχιστρατήγων» and no
  Eothinon heading, so the tone-6 Ainoi are anchored on that feast block and
  excluded whenever a «ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ» heading is present, which keeps a
  normal Sunday from receiving the score twice.
- The plagal-second Great Doxology instruction is recognised in both Melodos
  wordings: «ψάλλεται στον ήχο του δοξαστικού» and «ψάλλεται στην ήχο της
  ημέρας δηλαδή ήχο πλ β΄ … κατα το ΤΜΕ στον ήχο του δοξαστικού» (the
  Archangels' Sunday wording). Both must still be accompanied by an explicit
  πλ. β΄ tone marker; the setting is never guessed from the weekday. The
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
- The short tone-1 Papachristos katavasies of the Sunday before Christmas
  (`papline-kat-kyrpx-s-1/3/4/6/7/8/9-private-draft`; ode 5 is intentionally
  absent) trigger on «Καταβασίες» plus the first eirmos «Χριστὸς ἐν πόλει
  Βηθλεὲμ βρεφουργεῖται» and are inserted, in ode order, before «Τὴν
  Θεοτόκον…». `_normalized()` ignores accents and punctuation, so comma and
  breathing variants need no separate trigger. As with the other digital
  rules, they appear only when the catalogue ids are approved for display.
- All short katavasies of the year are data-driven. `tools/build_katavasies_json.py`
  reads `kat_registry_src.json`, keeps only `pass*` odes whose ids exist in
  `src/data/digital_scores.json`, and writes `src/data/katavasies.json`
  de-duplicated by normalized incipit (prefer eis/eisp/kyrpx, then `pass`
  over `pass-with-warnings`, then registry order). `anastasimatarion.py`
  generates one Orthros rule per entry at the «Τὴν Θεοτόκον…» anchor with
  `required_text=("Καταβασίες",)` and both the set's first eirmos and the
  ode incipit as triggers. The eisp/Theotokos entries keep the full scan
  (`replace_scan=False`); other entries are excluded on the scanned
  Cross/Theotokos headings. Generated rules precede the scanned settings.
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
    sidecar records the sung name after a fthora. Neanes' own `virtualNote` is
    not enough: in hard/soft chromatic `LayoutService.getShift` keeps the shift
    modulo 4 (right for pitch), so hard-chromatic Pa on Ke still read "Ke, Zo…".
    User report 2026-10-14. The worker now keeps its own shift: the chromatic
    fthora renames its note to Pa/Thi (or `chromaticFthoraNote`) at the
    nearest octave (kept by user decision 2026-10-14: the άνω/κάτω suffix
    shows roughly where the pitch lies, even after renaming; do not strip
    it); other fthores use Neanes' virtualNote. All 12 martyria
    then match. Martyria letters ignore the octave when compared.
  - 2026-10-14 user: "after the Ke→Pa fthora the transcription is wrong"
    (their screenshots never reached this server). Found silently dropped
    signs: the red yfesis (BZByzantina F074/F079 `\yfesh`/`\yfeshD` →
    Neanes `Flat_2_Right`, which with chrysanthineAccidentals is half the
    interval; BZFthores digrammos → Flat_6_Right, unverified) and the dotted
    gorgon (BZLoipa F060 `\pg` → GorgonDottedLeft; F021 `\gpPD` →
    GorgonDottedRight). Koinonikon now has flats at 148/243/348, all on Di;
    martyria still 12/12. Triargon (BZLoipa F071) has no Neanes equivalent
    and stays a warning.
  - Second Koinonikon «Αἰνεῖτε» (Lambadarios, ήχος α΄, PDF pp. 15–16,
    Pandekti 1851 p. 492): 336 neumes, 13/13 martyria **including the octave**.
    Lesson: the octave-blind martyria check hid a −4 +7 error: two dropped
    glyphs cancelled modulo 7. Always also look at the octave (e.g. a mode-1
    martyria sung PaLow, or note names out of Neanes range, are red flags).
    Fixes: BZByzantina F047 (`\ypspet`) is a base, PetastiPlusHypsiliRight (+4);
    F043 is not hyporoe here but a slanted kentima at the oligon's right end,
    read as OligonPlusKentimaBelow (+2) — both chosen so the martyria agree,
    psaltis must confirm. BZFthores F06E (`\dieshMD`) → Sharp_2_Left.
  - Third Koinonikon «Αἰνεῖτε» (Lambadarios, ήχος α΄, PDF pp. 17–20, Pandekti
    p. 506): 597 neumes, 25/26 martyria with octave. New BZLoipa bases:
    F029 `\apooli` OligonPlusApostrophos, F064 `\kypsoli` OligonPlusHypsiliPlus-
    KentimaHorizontal (+6), F073 `\ypsAoli` OligonPlusHypsiliLeft (+5), F03D
    `\elaapooli` OligonPlusElaphronPlusApostrophos. BZFthores F061 = martyria
    letter Di; F029/F06F `\zwanwyfesh` → GeneralFlat; BZLoipa F0A8 Trigorgon;
    BZByzantina F03F syndesmos → HeteronConnecting. Open: martyria Ga on p. 19
    line 10 (after spathi + kliton F050) is sung Zo' — kliton/spathi naming or
    a neume, for the psaltis. → Resolved 2026-10-15: the neumes were right
    (written notes fall to Ni after the 2nd spathi and rise to Ga); the names
    were wrong. Rule now in the note-name worker: Zygos/Kliton/Spathi are
    chroai — they do not rename and they end an earlier chromatic renaming
    (sungShift = 0). Neanes' own virtualNote re-anchors at them (kliton gave
    +3). 26/26 martyria. The sidecar also stores `physical` (written notes)
    for diagnosis; the catalogue ignores it.
  - 2026-10-15: vfilip verified (visual + auditory) the Cherubikon and the
    three Lambadarios Koinonika; they are public. Next: Koinonikon «Αἰνεῖτε»
    of Daniel Protopsaltis (PDF pp. 21–23, Pandekti p. 456), 450 neumes, 18/18
    martyria with octave, private draft. BZLoipa F031 `\gpBMusic` →
    GorgonDottedRight. Next piece starts on PDF p. 24.
  - 2026-10-20: the Sunday Orthros plan is one papline **Great Doxology** per
    week in the Melodos weekly tone (25 Oct 2026 = tone 4; the Melodos selector
    says «Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος δ΄»). Source: papline's
    «Δοξολογίαι» (Tablet) collection, 838-page BZ PDF, tones 1–8 in order
    (printed pp. 7, 74, 156, 225, 310, 414, 515, 646; first piece of each tone
    is «Σύντομοι - Ἀργοσύντομοι»). PDF page = printed page + 1. Its BZ font
    names carry a space («BZ Byzantina»); `bz_extract.py` now strips it. The
    permission email covered the texts asked for earlier, not explicitly the
    Doxologies: ask papline before any public release. First piece: Manuel
    Protopsaltis I, tone 4, PDF pp. 240–245 (printed 239–244, Anastasimatarion
    1905 p. 200), `papline-doxologia-manuel1-tone4-private-draft`,
    **`verified` by `vfilip` on 2026-10-21** (they heard it with the hidden
    pauses and said it sounds right; the id keeps its old name so links hold;
    still ask papline about the Doxologies licence before wide release); it was
    `needs_review`: 635 notes, 41/41 martyria (Vou/Thi) with octave. Opening
    note Vou was found by trying all seven notes (only Vou fits; the page header
    also reads «Βου»); its `rootSign: Delta` is provisional. BZLoipa `F053`
    (`\ypsApet`) is a base, `PetastiPlusHypsiliLeft`: dropping it left a −2
    (≡ +5 mod 7) drift. Not converted: BZFthores `F027`/`F022` (stavros, the
    «+» signs) and BZLoipa `F0E1`. Always check martyria against the *preceding
    note*: the note-name sidecar holds notes only, so a martyria at element `i`
    is compared with element `i-1`. The prototype's working directories under
    `/tmp` (`/tmp/kihem-ez-pilot/ctan-byz`, `/tmp/kihem-neanes-source`) vanish;
    rebuild them from CTAN `support/byzantinemusic.zip` and the Neanes v0.5.55
    tag (`npm ci --ignore-scripts`).
  - Ainoi tone 4 (2026-10-21, user asked for next Sunday's Ainoi): papline
    publishes a day book per Sunday (e.g. `Εσπερινός, Όρθρος και Θεία Λειτουργία
    25-10-2026 …` on the front page, 804 pp., public download; the first ~64
    pp. are text, music follows, section headings sit at the *bottom* of the
    page that precedes the section). Ainoi stichera of Lambadarios (Ephesios
    1820 p.110) = PDF pp. 319–328 line 1 (4 anastasima + 4 anatolika with their
    Αἰνεῖτε verses; the verses on p.318 and the Eothinon doxastikon from
    p.328 line 2 belong to other pieces). Private
    `papline-ainoi-lambadarios-tone4-private-draft`, `needs_review`: 1348
    notes, 56/56 martyria with opening Pa (header «Πα»). Line breaks only after each
    martyria (user 2026-10-21: the source's own line ends left orphan syllables
    such as a lone «α» or «δυ» in the narrower Neanes page; let the text flow).
    A BZLoipa `F030` standing alone between bases is an Ison with Tripli
    (`bz_convert.py`, unconfirmed). Stavros `F027` is now a hidden pause (2026-10-28, see below). A hidden 1-time pause
    after each of the 56 martyria. Tempo (user 2026-10-21: 115 bpm; the verses
    «Αἰνεῖτε…» start very fast and slow down): papline's tempo signs are the
    font `MKXronos2016` (not BZXronos): `F06C` = Neanes `Quicker` (208 bpm),
    `F066` = `Quick` (168 bpm); each verse has Quicker then Quick, ends at a
    martyria, where a hidden `Tempo` element (Moderate, bpm 115) returns to the
    sticheron tempo; `playback_speed` stays 1. The bridge accepts
    `elementType: 'Tempo'` events. Not yet attached to the Orthros.
  - Pasapnoaria (2026-10-21, user: they belong at the start, before the Ainoi):
    the Ainoi file now begins with Lambadarios' «Εἰς τοὺς Αἴνους · Πασαπνοάρια»
    (PDF p.302 lines 6–7, p.303 lines 0–6; the «Στιχολογία» sections that follow
    on pp.303–317 are other composers' alternative Pasapnoaria, not psalm verses),
    then an explicit Martyria «Πα» (new `explicit: true` Martyria event of the
    bridge: manual, resets the note) and the stichera. 1407 notes, 63/63
    martyria, 24 tempo signs, 71 hidden elements. Scans 12–13 are the new pages.
    User 2026-10-22: no forced line break after the Pasapnoaria's martyria (they
    flow on); only the explicit «Πα» starts a new line for the stichera.
  - Tone-4 Ainoi verified by vfilip and attached to the Sunday Orthros
    (2026-10-22, rule before «ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ», ahead of the scanned I. Protopsaltis setting).
  - Eothinon Doxastikon 10 (pl. 2, «Μετὰ τὴν εἰς ᾍδου κάθοδον», Lambadarios, PDF pp. 351–353
    of the 25-10 book; nav bars sit at the END of a block) is `papline-doxastikon-eothinon10-lambadarios-private-draft`,
    needs_review, 272 notes, not attached to the Orthros. Glyphs identified by comparing with Neanes'
    own glyphs: BZByzantina F025 = yfesis2 (Flat_2_Right), F024 = diesis2 (Sharp_2_Left); F043 on
    OligonPlusKentemata = OligonKentimaMiddleKentimata (+3). 11/12 martyria; the last differs because
    Neanes renames notes after a hard-chromatic Thi fthora (the source does not). A diatonic Ke fthora
    over a Pa martyria (p.352 l.8) is left unapplied (Neanes would rename later notes by it).
    Checking martyria in a scratch script: element index = event index + 1 (opening martyria is 0).
    The Doxastikon was verified by vfilip on 2026-10-24 ("είναι") and attached to the Sunday Orthros after
    «ἐντρυφῆσαι φιλάνθρωπε Κύριε.» (`required_text` «τὴν εἰς ᾍδου κάθοδον»: Melodos splits the drop-cap «Μ ετὰ»).
  - Embedded digital scores (2026-10-24, user: unreadable on the phone, too much text): the service-page
    embed no longer shows the "ελεγμένη"/vfilip/synthetic-playback lines (only «Πηγή: papline.gr»); inside an
    iframe (`html.embedded`) the public page hides its header, card and intro text. On screens < 700px the
    loader patches the fetched `.byzx` in memory (pageSize Custom, width 520, 12px margins) so Neanes' Page
    Width zoom shows readable notation; a Letter page with 1-inch margins zoomed to ~40%. Flask caches templates:
    restart the local test server after editing them.
  - Theotokos Katavasies (Lambadarios, Papagiannis' version, Ἦχος βαρύς, PDF pp. 266–271 of the 25-10 book;
    `papline-katavasies-theotokos-lambadarios-private-draft`, needs_review, not attached). Seven odes
    (α γ δ ε ς ζ η), each its own line; opening martyria Vou/Varys; ode δ needs an explicit Pa martyria (each
    ode is a separate piece, the source frames differ by one step); 36/36 martyria; fthoras dropped; the
    boxed short alternative endings and label-only duplicate lines are skipped. Neanes `lineBreak` means a
    break AFTER the element. MKXronos F064 = Moderate (115), F066 = Quick (168), F06C = Quicker (208).
    Unresolved: BZLoipa F050 (p.268 l.1) and F032 (p.269 l.9). Other Katavasia settings: Protopsaltis
    pp. 259–261, Kountiadis 262–265 and 271–275.
  - Neanes quirk (found 2026-10-21 from the user's report that the later
    verses started slow and the sticheron kept the verse tempo): `AudioService.play`
    never resets the transport tempo for an event whose bpm equals the bpm
    playback *started* with, so a tempo that recurs after another one is
    ignored. Hence every Tempo element of a score must carry a unique bpm
    (the Ainoi use 208.00, 168.01, 115.02, 208.03 …, a hundredth apart).
    Verified in headless Chrome by timing the played elements per section.
  - Live speed (2026-10-21, user: judge the tempo while it sounds):
    `_neanes_speed.html` (both players) changes speed during playback: Neanes
    plans a playback at start and disables its speed field while playing, so
    the wrapper clicks Pause, types the percentage into `#audio-speed-input`,
    clicks the `.audio-selected` element (the click selects it) and Play, which
    resumes from that element; `−`/`+` buttons add 5%. Tested in headless
    Chrome (playwright in a scratchpad venv, `/usr/bin/google-chrome`, the app
    served under a `/kihem` DispatcherMiddleware because the Neanes bundle is
    built for that prefix). Ainoi line breaks: only after a martyria that is
    followed by new text, never before a bare melisma note.
  - Sunday Orthros integration (2026-10-21, user: papline is fine as long as
    use is non-commercial): `AttachmentRule.digital_title` marks a rule whose
    `piece_id` is a *catalogue score id*, not a scanned piece. It is attached
    only if `enrich_service_html(..., verified_digital_scores=)` (app.py passes
    `verified_scores()` ids) contains it, so a score that is not `verified`
    never appears. Markup is a `music-attachment` aside with a lazy iframe of
    the public `digital-scores/<id>/` page, after «Παράτεινον τὸ ἔλεός σου…»
    and before «Σήμερον σωτηρία», with its own bookmark. The tone-4 rule needs
    Melodos' selector «Μουσικό απόσπασμα Μεγάλης Δοξολογίας · Ἦχος δ΄» and a
    Sunday. Next weeks: convert the next tone's Doxology (papline PDF
    offsets above), verify it, and add a rule alike; keep non-commercial.
  - Line breaks (2026-10-20, user: the Doxology is sung with the left chanter,
    so it must read line by line like the source): every music line of the
    source PDF ends with `lineBreak: true` on its last element (52 breaks for
    the 53 lines of Manuel I). The bridge copies it onto automatic Martyria
    too, since a line can end on one. Use this for any piece chanted from the
    left stand; the user saw the first draft and found it correct, with no
    remarks (visual look only; not yet recorded as `verified`).
  - Neanes draws a small icon at every line break (`.line-break`,
    `.line-break-2`); both readers hide it with CSS, the breaks stay
    (2026-10-20, user request).
  - Pause after each Martyria (2026-10-20, user: «μισού χρόνου», then settled
    on one simple 1-time pause "to see if it is better"). Neanes has no
    half-time rest: its rests are `Vareia(Dotted)` 1–4 times, so the draft has
    a `VareiaDotted` note after every Martyria (it carries the line's
    `lineBreak`, so the line layout is unchanged). It must sound but not be
    drawn: the sidecar's optional `hidden` list (element indices; written by
    `write_note_names(..., hidden_elements=)`, read by
    `DigitalScoreCatalog.hidden_elements`) makes both readers inject
    `#element-<idBase+index> { visibility: hidden }`. Re-running
    `build_neanes_note_names.py` without it drops the list. A pause becomes
    the "previous temporal node" of the next note, so a gorgon on a line's
    first note halves the pause instead of the last note before it (one case
    in this piece, element 408); time neumes lengthen their own note and are
    not affected.
  - Default tempo (2026-10-20, user: 100 bpm): Neanes plays at 120 bpm times
    `audioOptions.speed` when no Tempo sign is written, so `playback_speed` is
    `100/120 = 0.8333333333` rather than a tempo sign that would change the
    notation.
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
  order to Neanes' element index. A switch "Ίσον: ναι/όχι" writes
  `volumeIson` into the shared `audioOptionsDefault` localStorage before the
  iframe loads (`null` = mute, Neanes' own serialisation of -Infinity) and
  reloads the page; the default drone volume is -8 dB.
- Parallage tag index (fixed 2026-10-15, user: wrong names when playing a span
  of the 3rd Koinonikon): Neanes virtualises pages, so only visible pages'
  `.element-box`es exist (top: element-1..302; scrolled: from element-303).
  The tag used to take the DOM position as the element index, which is wrong
  once the first page is unrendered. Now index = id number − the id of the
  first box right after loading (the opening martyria). Verified headless by
  playing spans from 300 and 440 against the sidecar.
- Playback speed (2026-10-14, user: "στα κοινωνικά παίζει πιο αργά"): the
  shared partial `_neanes_speed.html` adds a "Ταχ." select (40–125%) the
  same way, writing Neanes' `audioOptions.speed` (tempo multiplier, 0.1–3)
  before the iframe loads. The default comes from the optional catalogue field
  `playback_speed` (Koinonikon «Αἰνεῖτε» = 0.6); a student's choice is kept
  per score under `kihem-speed-<id>`.
- Weekday Liturgy batch (2026-10-26, user: transcribe whatever papline offers for the weekday Liturgies
  from Tue 27 Oct on and attach it). papline has day books only for feasts (26-10, 28-10 …), so the
  weekday music comes from its collections (public downloads under `/index.php/bibliotheke-downloads/56-theia-leitourgia/…`):
  Cherubika (a4, 375 pp., per tone; TOC page = PDF page, the heading of a piece sits at the bottom of the
  previous page and the piece ends at the next composer's heading) and «Κοινωνικά του ενιαυτού και της
  εβδομάδος» (a4, 931 pp.; «Τῆς Ἑβδομάδος» p. 875 maps Mon–Sat to sections), Kontakia (a4). Melodos' own
  sentence names the tone of the day («απλή Τρίτη, ψάλλονται σε ήχο βαρύ», Wed «δ΄ άγια», Thu «πλ δ΄»,
  Fri «πλ α΄», Sat «πλ α΄»), so the rules are keyed on weekday + that sentence (`_WEEKDAY_LITURGY_DRAFTS`).
  Drafts (all `needs_review` + `public_draft`, Lambadarios unless noted): Cherubikon varys (pp. 243–245,
  Zo 16/16), tone 4 (124–126, opening Δι = Neanes `Thi`, 12/12), pl.4 (283–285, Ni 16/16), pl.1 reused;
  Koinonika Tue «Ἀγαλλιᾶσθε δίκαιοι» (the Melodos text is the All-Saints one, not «Εἰς μνημόσυνον»;
  Konstantinos Protopsaltes varys, pp. 447–449, 12/12), Wed «Ποτήριον» t4 (726–728, 10/10), Thu «Εἰς πᾶσαν τὴν γῆν»
  pl.4 (856–858, 10/11: soft-chromatic fthora BZFthores F027 not applied), Fri «Σωτηρίαν εἰργάσω» pl.1 (876–877, 9/9),
  Sat «Μακάριοι» pl.1 (890–892, 13/14: BZFthores F04F not applied); speed 0.6; Kontakion «Ὁ ὑψωθείς» (Prygos,
  Kont. pp. 16–17, Thi 9/9) for Wed and Fri. New glyph readings: BZLoipa F074 \ypokkoli =
  OligonPlusHyporoePlusKentemata, BZByzantina F04B \elapet = PetastiPlusElaphron (chosen so the martyria agree).
  Converter additions (scratch `gen_run.py`; `bz_extract.SKIP_BOXES` for the pale-grey 0.95 boxes — but those
  boxes can be part of the melody, so it was NOT used) and `drop_first_martyria` (a pickup line that starts
  with a martyria duplicating the opening one). Not done: Saturday nekrosimon Kontakion (Stanitsas pl.4, p. 131
  of the Kontakia PDF: 2/4 martyria, chromatic fthora), Tue Kontakion of the Prodromos, Thursday Apostles'
  Kontakion, Apolytikia, Alleluia, Leitourgika, Trisagion. Not heard by a psaltis.
  Follow-up (2026-10-26): Thursday Apostles Kontakion «Τοὺς ἀσφαλεῖς» (tone 2, same text as the Peter & Paul
  Kontakion, kont.pdf p.110, Papachristou) added as `papline-kontakion-apostolon-papachristou-tone2-private-draft`
  (martyria 3/3, root Beta, Δι=Thi); rule weekdays=(3,). Papline has NO Kontakion «Προφῆτα Θεοῦ» (Tuesday Prodromos,
  tone 2 «Τὰ ἄνω ζητῶν») and the Saturday nekrosimon failed (see above). Leitourgika (Trisagion, Axion, Patera...) already
  exist as pandekti scores and attach on weekdays.
  2026-10-27: digital Monogenes (Lambadarios, Pandekti 1851, from papline Antiphonarion pp.6-7, tone 2 Δι, martyria 5/5,
  attached every day beside the scan) and Axion Estin drafts: varys Nikolaidis (leit.pdf p.194-195, 10/11) for Tuesday,
  pl.1 «Τὸ Πατριαρχικόν» (pp.132-133, 9/9 after reading BZLoipa F074 as OligonPlusHyporoePlusKentemata) for Fri/Sat/Sunday pl.1.
  NOT done: tone 4 agia (Nikolaidis p.100-101, best 7/14) and pl.4 («τὸ συνειθισμένον» p.224, 8/11): martyria disagree,
  probably an unapplied Δι fthora. BZFthores F027 is a small "+" mark, not a fthora (the "fthora-unmapped" warnings are harmless).
  Papline's Antiphonarion (ntifonarion-syllogi.pdf) pp.18-21: the weekday Prokeimena/Alleluia/Koinonika are TEXT ONLY (no
  notation); only the Sunday ones (pp.8-17) are notated. 2026-10-27: Monday (2 Nov, Melodos prints «Ἀγαλλιᾶσθε» as the
  feast koinonikon, tone 1) -> Tsiknopoulos tone 1 `papline-koinonikon-agalliasthe-tsiknopoulos-tone1-private-draft`
  (koin-week.pdf p.426-429, martyria 11/13: two late ones off, unapplied fthoras). Archangels' «Ὁ ποιῶν τοὺς ἀγγέλους»
  (Lambadarios p.505-507, 9/9) was converted but is not attached (Melodos did not print it for 2 Nov).
- Rewind (2026-10-25, user: teaching tool, go back a line after a wrong
  variation): `_neanes_practice.html` has «↩ Πίσω μία γραμμή» and the ←
  key (top page and iframe): jump to the start of the current printed line
  (`.line` > first `.element-box`), or the previous one if already within 2
  elements of it or pressed again within 2.5 s; double-click a neume = play
  from there. Plays on when stopped. Right-click was rejected (no touch,
  browser menu). Verified in headless Chrome with a dispatched dblclick; a
  real mouse hit on the narrow `.element-box` centre misses (hits `.page`),
  and iPhone is untested.
- Pitch colours (2026-10-27, user: can't see which note he is on while
  singing): `_neanes_pitch_colors.html`, included after the practice bar on
  the public and review pages. Every `.syllable-box` in the Neanes frame is
  coloured by its first note from the `.notes.json` sidecar via an injected
  stylesheet (`#element-<base+index>`, `!important` over the inline black);
  the floating parallage tag and a legend take the same colours. Scale
  position low Zo 0 … Ga 4 … Zo 7, high Ni 8: brown, orange (Ni), magenta (Pa),
  golden yellow (Vou; was lime until 2026-10-31, too close to Ga), bright cyan (Ga) and dark green (Di) (swapped on request 2026-10-31), blue, purple, red (high Ni); Pa leaves the rainbow
  on purpose (user: Ni, Pa, Vou looked alike as orange/gold/lime). 0.4px text
  stroke; notes beyond the nine are darker. Martyria
  and red accessory signs keep their colour. Toggle remembered in
  localStorage `kihem-pitch-colors`. Needs `window.kihemElementBase`, set in
  `rememberElementIdBase` of both player templates. Seen in headless Chrome
  on two drafts; untested on phones. Switching the toggle restyles the tag at
  the next note.
- Empty player / wrong piece (2026-10-27, user: a Cherubikon where the
  Monogenes should be): two causes. (1) The Monogenes and Apostles Kontakion
  were built with martyria root sign `Beta`, which is not a Neanes `RootSign`;
  Neanes' layout throws `reading 'text'` and the player stays empty (valid
  names: Delta, Alpha, Legetos, Nana, Tilt, Varys, Squiggle, Zygos,
  SoftChromaticSquiggle, DeltaDotted, AlphaDotted, SoftChromaticPaRootSign and
  their `…Low`). Tone 2 first used `Tilt`+Diatonic, WRONG (2026-10-31, user: the Monogenes
  sounded wrong): `Tilt` is the HARD-chromatic Di sign and tone 2 is SOFT chromatic; now
  `SoftChromaticSquiggle` + `SoftChromatic` (the Δι martyria with dots and curl in
  papline's header; rebuilt both pieces, the martyria glyphs now match the source); `NEANES_ROOT_SIGNS` in the bridge rejects unknown names.
  Never trust "martyria agree" alone: open the player and check boxes > 0.
  (2) The web Neanes reopens every `workspace-*` localStorage entry as a tab and
  shows the first, so a frame that failed to load showed another piece or one
  left by an earlier visit; `_neanes_isolate.html` clears those keys before the
  player boots and until its score is ready. A scan of all 34 pages shows
  every public draft now renders.
- Scripture interpretations stopped on 2026-10-26 (OpenAI 429
  `insufficient_quota`). Fixed 2026-10-28 on the user's request: if
  `OPENROUTER_API_KEY` is set (production drop-in
  `/etc/systemd/system/kihem.service.d/openrouter.conf`, mode 600) the service
  calls OpenRouter chat completions with `openai/<model>`
  (`openai/gpt-5.6-luna`, same prompt and cache); otherwise OpenAI as before.
- Practice bar (2026-10-14, user: replay difficult passages):
  `_neanes_practice.html` sets a start/end neume from the Neanes selection
  (`.element-box .selected`, ids `element-N`) and plays/loops that span.
  Neanes facts verified in headless Chrome: clicking `.neume` selects; while
  playing, selecting jumps there; when stopped/paused, selecting stops and the
  single play toggle starts at the first event ≥ the selection. The toggle's
  aria-label can stay "Pause audio" after a pause, so the page uses the
  `.audio-selected` highlight as the playing signal. The contextual neume
  keyboard (`.contextual-toolbar-panel`) is hidden in reader mode.
- Deployment reminder: the auto-mode classifier blocks production writes by
  Claude even with the user's consent; the user ran the first deploy with `!`,
  and later identical deploys were allowed.
- Plagal-second (tone 6) Divine Liturgy: `_LITURGY_DIGITAL_DRAFTS` rows are
  `(anchor, score_id, title, preceding_text, weekdays)`. The tone-6
  `papline-cher-pl2-gregorios-private-draft` (Cheroubikon) attaches at
  «Οἱ τὰ Χερουβεὶμ μυστικῶς εἰκονίζοντες» and replaces the tone-6 scan; the
  Sunday `papline-koin-pl2-karakasis-private-draft` (Koinonikon) attaches at
  «Αἰνεῖτε τὸν Κύριον ἐκ τῶν οὐρανῶν» with `weekdays=(6,)` and the
  «Τῇ Κυριακῇ ψάλλεται το Κοινωνικόν» gate, so weekday tone-6 liturgies get
  no Koinonikon digital. Tones 1 and 2 keep their empty weekday tuples.

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
- Digital-score ison marks (2026-11-07): the public score page exposes the
  private `.byzx` `ison` marks only as `[[element index, "Ison.X"], …]` via
  `DigitalScoreCatalog.ison_marks`; the index is the zero-based
  `staff.elements` position, matching the Neanes `element-N` offset and the
  `.notes.json` sidecar keys. `ISON_MARK_NUMBERS` in `isokratis.py` maps
  Pa 102, Ni 90, Zo 82, Vou 112, Ga 120, Thi 132, Ke 144, KeLow 72,
  ThiLow 60 at register/semitone 0; unknown names are ignored. The page shows
  «Ίσον mp3: όχι/ναι» (`kihem-ison-mp3`) only when marks exist;
  ON forces Neanes' `volumeIson = null` before the iframe boots and a 150 ms
  watcher follows the last mark at or before `.audio-selected`. It follows
  Neanes' own rules: no drone before the first mark, a mark lasts until the
  next mark, `Ison.Unison` silences the mp3 drone until the next pitch mark,
  and the `src` changes only when the pitch mark changes (no per-note
  retrigger); stopping/hiding pauses it and resuming uses the mark in force.
  The «Ένταση» slider (default 70, persisted) is shown whenever mp3 mode is
  on. Since iOS/iPadOS Safari ignores `HTMLMediaElement.volume`, support is
  probed by writing/reading `0.5`; when unsupported the element is routed
  through a lazily created Web Audio `GainNode` (`createMediaElementSource`,
  `AudioContext.resume()`) only after a pointerdown/click/keydown or the
  slider's `input`, so a suspended context cannot mute it.
- Automatic ison default (2026-11-07; genus refinement ISON5): when a digital
  score has no real `ison` marks, `isokratis.default_ison_for` returns the
  editorial default from the mode plus the optional genus/start record in
  `src/data/ison_genus.json` (303 entries, read by
  `digital_scores.load_ison_genus` / the cached `ison_genus_table`; a missing
  file is `{}`). Modes 1/5 Pa, 3 Ga, 4 Vou stay fixed. Modes 2/6:
  hard-chromatic Pa, soft-chromatic Thi; without a genus the old defaults
  (2 Thi, 6 Pa) apply. Mode 7: enharmonic Ga, diatonic Zo (else Ga). Mode 8:
  Ni, except a label «ἐκ τοῦ Γα» (accent/spacing/Latin Ga tolerant) or start
  Ga → Ga. `mode_key_from_tone_label` parses the Greek `tone_label` (plagal
  before plain; barys = 7). `DigitalScoreCatalog.auto_ison_marks` marks the
  first note element with that default and splits at `Martyria` elements.
  Only in modes 4 and 8 (`DI_RULE_MODES` in `isokratis.py`), and only when
  the default is below Δι, it uses `Ison.Thi` for a segment whose median
  written note (sidecar `physical`) is above Δι. Modes 1, 2, 3, 5, 6 and 7
  keep the single mode/genus default for the whole piece; the hard-chromatic
  Pa default therefore no longer switches. Evidence (22 real-marked papline
  scores, 5109 notes): the rule raised agreement in mode 4 (0.15->0.44,
  0.19->0.52) and πλ. δ΄ (0.17->0.22, 0.20->0.41) but lowered it in πλ. α΄
  (0.83->0.61, 0.69->0.58) and πλ. β΄ (0.66->0.51), where the real ison
  stays on Πα in high segments. Real marks always win; a missing sidecar
  yields only the single default mark and never raises. The page keeps the
  short control «Ίσον mp3: ναι/όχι» and the tooltip says the drone is an
  automatic default, not from the PDF.
- The public player keeps speed, Neanes ison and mp3 ison on one compact
  flex row (`.player-controls`, wrapping only on narrow screens); the mp3
  volume slider uses a 🔊 label and is shown only in mp3 mode, and
  `#ison-mp3-status` stays as a small line below the row.
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
  - Next-Sunday batch (2026-10-25, user: transcribe next Sunday's Cherubikon, Koinonikon, Doxology, Katavasies,
    Doxastikon and show them in the Orthros/Liturgy even if unreviewed and public). Source: papline book
    `01-11-2026` (Κυριακή ΚΒ΄ Λουκά, πλ. α΄, Εωθινὸν ΙΑ΄; 817 pp.; its PDF bookmarks give the page of every
    piece, section headings sit at the bottom of the previous page). New catalogue flag `public_draft: true`
    (only on `needs_review`): `DigitalScore.is_public`, `public_scores()`; the service pages and the public
    player accept it (404 otherwise), label it «αυτόματη μεταγραφή, δεν έχει ελεγχθεί από ψάλτη», and the
    public catalogue still lists verified scores only. Drafts: Cherubikon Lambadarios pl.1 (PDF pp. 562–566,
    Pa, 20/20 martyria), Koinonikon Lambadarios I (746–748, Pa, 11/11, speed 0.6), Doxology Manuel I pl.1
    (419–424, opening Ke, 38/38, 20 Pa/Ke fthoras dropped because Neanes renames notes; line break per source
    line; speed 0.8333), Eothinon Doxastikon 11 Lambadarios pl.4 (378–380, Ni, root Legetos, 9/9). The
    Theotokos Katavasies are the same piece as the 25-10 draft (now `public_draft`). Glyphs resolved by martyria
    brute force: BZByzantina F022 `\ypopet` = PetastiPlusHyporoe; BZLoipa F07B = OligonPlusHamiliPlusKentemata;
    BZLoipa F041 = OligonPlusKentemataPlusHypsiliLeft; BZLoipa F071 (triargon) = Diargon. Unmapped: BZIson F044,
    BZLoipa F0A3. Rules: digital Orthros rules (Katavasies before the scanned one, Doxastikon after «ἐκ λύκων
    λυμαινομένων αὐτήν.», Doxology after «Παράτεινον…») and Liturgy rules appended after the tone rules so the
    digital score sits above the scanned setting. The converter used was a scratchpad `gen_run.py` (config-driven).
- Stavros = pause (user 2026-10-28): the cross «+» (BZFthores `F027`) used to be
  dropped. `bz_convert.convert()` now emits a rest `{'Note','VareiaDotted','stavros':True}`
  where the cross stands (between two bases by x); the runner scripts add its
  element index to the sidecar `hidden` list (same as the pause after a martyria),
  and the bridge worker drops the `stavros` key. Only 6 public pieces have a
  cross: Axion Estin Nikolaidis varys (5) and Patriarchal pl.1 (8), Koinonikon
  Thursday pl.4 (1) and Wednesday tone 4 (2), Ainoi tone 4 (8), Doxologia Manuel
  tone 4 (8); regenerated/patched and installed 2026-10-28 (names of every other
  element unchanged). The other drafts have no cross in their lines. Not pause: the
  glyph `F022` (blank in BZFthores). For a piece made from an old draft use a
  patch (insert the rests into the saved draft by matching the source lines).
- Digital score replaces the scan (owner 2026-10-30): `enrich_service_html` now removes the
  scanned excerpts attached to the same hymn text node as a shown digital (Neanes) score
  (`placed` list). The scan stays when the digital score is not shown (not approved/verified).
  Sunday 2026-11-01: Doxastikon 11, Doxologia, Katavasies, Cherubikon, Monogenis, Axion Estin and
  Koinonikon show only the Neanes player.
- Sunday pl.1 Ainoi (2026-10-31, user: «Ξεκίνα το πασαπνοάριο και τους Αίνους της Κυριακής 1/11»):
  `papline-ainoi-byzantios-pl1-private-draft` (assets `papline-ainoi-byzantios-pl1.*`), needs_review,
  public draft. Source: papline 01-11-2026 book (`d1101.pdf`) pp.337 line 8–338 (Pasapnoaria of Petros
  Byzantios, Ephesios 1820 p.140) and pp.352 line 8–358 line 1 (the 4 anastasima stichera, p.141 ff.),
  explicit Martyria Pa (`Alpha`) before the stichera; 858 notes, 44/44 martyria with octave, 11 tempo
  signs, stavros pauses hidden; the Menaion stichera after it are not included. Composer choice
  (Petros Byzantios, the only anastasima setting in that section) is mine; the Lambadarios settings used
  for tone 4 do not exist for pl.1 in that book. New glyphs: BZByzantina `F04B` = `\elapet`
  `PetastiPlusElaphron`; BZFthores `F030` = GeneralFlat (like F029). A diatonic Ni fthora over a Pa
  martyria is left unapplied (it would rename the later notes). Orthros rule `ΔΟΞΑΣΤΙΚΟΝ ΕΩΘΙΝΟΝ`,
  weekly_tone 5, Sunday only; it replaces the scanned Ioannis Protopsaltis Ainoi (see the scan rule).

- 2026-11-01 Trisagion (user: slow and short; **the Trisagion after the Eisodikon is ALWAYS tone 2**, not the weekly tone).
  Source: papline «Τρισάγιος ὕμνος» collection `wk/dl/trisagios.pdf` (printed p. N = PDF page N+4). Installed tone 2
  (soft chromatic, Di) `papline-trisagion-progakis-tone2-private-draft` (short, Progakis, p. 22, martyria 10/10) and
  `papline-trisagion-klasika-tone2-private-draft` (slow «κλασικά», pp. 23–24, 12/12). Rules: any day, `match_number=3`,
  `following_text="Δύναμις"`; they replace the tone-4 Pandekti scan. Unattached flats (BZ F025) are skipped. A first pl.1
  attempt (Ioannidis) was removed. In this PDF the heading line («Ἦχος Δι» + martyria) counts as a line: skip it.
