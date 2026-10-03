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
  Prokeimenon; Canon clips start at the named Ode A/G blocks.  The plagal-
  second Great Doxology is inserted immediately before «Σήμερον σωτηρία».
  Sunday resurrectional Ainoi are always selected from Melodos' explicit
  weekly tone and placed immediately before the Eothinon Doxastikon. The
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
