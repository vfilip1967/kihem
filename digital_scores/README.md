# Ψηφιακές παρτιτούρες

Ο κατάλογος των μεταγραφών είναι το `src/data/digital_scores.json`. Τα
πραγματικά αρχεία `.byzx`, MusicXML και οι προεπισκοπήσεις δεν αποθηκεύονται στο Git·
εγκαθίστανται στο `KIHEM_DIGITAL_SCORES_DIR` (προεπιλογή:
`/var/lib/kihem/digital-scores`).

Κάθε εγγραφή του `catalog.json` περιλαμβάνει ταυτότητα μέλους, incipit, ήχο,
πηγή, μεταγραφέα και `review_state`: `draft`, `needs_review` ή `verified`.
Για `verified` είναι υποχρεωτικό το `reviewed_by`: ο ψάλτης που έλεγξε την
αντιστοίχιση με την αρχική παρτιτούρα και την ακρόαση.

Προαιρετικά αρχεία:

```json
{
  "byzx_filename": "score-id.byzx",
  "ocr_filename": "score-id.byzocr",
  "musicxml_filename": "score-id.musicxml",
  "preview_filename": "score-id.png"
}
```

Το Kihem δεν παρουσιάζει μια μεταγραφή ως εκτελέσιμη ή διδακτικά έγκυρη πριν
γίνει `verified`. Η σάρωση παραμένει πάντοτε η αυθεντική πηγή ελέγχου.

Το πρώτο δοκιμαστικό δελτίο ελέγχου βρίσκεται στο
[`lithou-sfragisthentos-tone1-review.md`](lithou-sfragisthentos-tone1-review.md).
Καταγράφει χωριστά όσα έχουν ταυτιστεί (προς το παρόν μόνο τίτλος/ήχος και
πλήρες κείμενο) από όσα απαιτούν ακόμη οπτικό και ψαλτικό έλεγχο.

## OCR από σάρωση

Για πραγματική μεταγραφή από έντυπη εικόνα, το Kihem χρησιμοποιεί πιλοτικά
το επίσημο [Byzantine Chant OCR του Neanes](https://github.com/neanes/byzantine-chant-ocr).
Η αλυσίδα είναι `σάρωση → .byzocr → εισαγωγή Neanes → .byzx`. Το OCR
αναγνωρίζει νεύματα αλλά όχι λεκτικό· κάθε παράγωγο αρχείο είναι αρχικά
`draft`, καταγράφει την ακριβή περικοπή της πηγής και δεν δημοσιεύεται.

Το πρώτο πλήρες τεχνικό ίχνος είναι το
[`ote-katilthes-tone2-ocr-draft.md`](ote-katilthes-tone2-ocr-draft.md).
Η μεταγενέστερη οπτική σύγκριση έδειξε συστηματικά λάθη νευμάτων· συνεπώς
αυτό είναι αποτυχημένο τεχνικό πείραμα και όχι υποψήφια παρτιτούρα, δείγμα
εκπαίδευσης ή βάση αντιστοίχισης.

## Παλαιά Word `.doc` με EZ Byzantine Music Font Package

Όταν διαθέτουμε το **αυθεντικό Word** ενός μουσικού κειμένου, αυτό είναι η
πρώτη πηγή εργασίας και όχι το PDF. Ο ιδιωτικός αναγνώστης
`digital_scores/extract_ez_word.py` ανακτά απευθείας από το `.doc` τη σειρά
των χαρακτήρων ιδιωτικής περιοχής (PUA) που πληκτρολόγησε ο συντάκτης και
ελέγχει ότι το αρχείο δηλώνει τις γραμματοσειρές EZ:

```bash
venv/bin/python digital_scores/extract_ez_word.py SOURCE.doc \
  --source-label 'source and permitted private research purpose' \
  --output /private/source-ez-word.json
```

Το `wvWare` παραμένει χρήσιμο μόνο ως αρχικός έλεγχος της σειράς των κωδικών,
επειδή δεν διατηρεί το font-run κάθε χαρακτήρα. Για την πραγματική εισαγωγή
χρησιμοποιούμε τον ιδιωτικό importer Apache POI/HWPF
`digital_scores/extract_ez_word_runs.py`: διαβάζει το `CharacterRun` του
παλαιού `.doc` και καταγράφει την πραγματική γραμματοσειρά για κάθε PUA
χαρακτήρα. Έτσι, όταν το Word γράφει π.χ. `EZ Psaltica`, το report το
κανονικοποιεί ως `EZPsaltica` χωρίς εικασία.

```bash
mvn -q -Dmaven.repo.local=/tmp/kihem-m2 \
  -f digital_scores/word_importer/pom.xml package

venv/bin/python digital_scores/extract_ez_word_runs.py SOURCE.doc \
  --source-label 'source and permitted private research purpose' \
  --importer-jar digital_scores/word_importer/target/ez-word-font-runs-1.0.0.jar \
  --output /private/source-ez-word-font-runs.json
```

Η έξοδος παραμένει αυστηρά ιδιωτική και φέρει
`source-font-confirmed; no-neanes-event`: ο importer επιβεβαιώνει **μόνο**
τον χαρακτήρα και τη γραμματοσειρά που χρησιμοποίησε ο συντάκτης. Δεν αποφασίζει
τη θέση ενός σημαδιού, τη χρονική του εξάρτηση ή το αντίστοιχο Neanes event,
και δεν δημιουργεί `.byzx`. PUA χαρακτήρες από μη-EZ font (π.χ.
`SymbolGreek`) σημαίνονται `non-ez-font; excluded-from-ez-conversion` και
δεν μπαίνουν στην αλυσίδα μουσικής μετατροπής. Το PDF μένει μόνο για οπτική
σύγκριση.

Για ελεγμένη **μικρή, πλήρη ακολουθία** Word χαρακτήρων, ο δεύτερος ιδιωτικός
compiler `build_ez_word_neanes_event_draft.py` χρησιμοποιεί anchors
`word_occurrence + pua_codepoint` αντί για PDF glyph ids. Απαιτεί ρητό
`confirmed: true` και ονομασμένο ελεγκτή σε κάθε plan, και έπειτα το
`build_ez_neanes_byzx.py` καλεί τον serializer του Neanes. Ένα τέτοιο αρχείο
μένει `needs_review` και προσφέρεται μόνο από την προστατευμένη σελίδα
ελέγχου· δεν είναι δημοσιεύσιμη παρτιτούρα.

Οι φόρμουλες Word συχνά δεν έχουν τη δική τους αρχική μαρτυρία· η επικεφαλίδα
μιας συλλογής («πρώτος ήχος» κτλ.) δεν αρκεί για να επιλεγεί βάση εκτέλεσης.
Αν ο ψάλτης τη διαβάσει σε ορατή πρωτογενή πηγή, το Word phrase plan μπορεί
να περιέχει χωριστό `opening_martyria` με `confirmed: true`, μη κενό
`source_evidence.reference` και τα τρία ελεγχόμενα πεδία Neanes `note`,
`rootSign`, `scale`. Μόνο τότε περνά στο ιδιωτικό `.byzx`; σε κάθε άλλη
περίπτωση η βάση παραμένει σκόπιμα ακαθόριστη.

Τα δημόσια Word της Μονής Αγίου Αντωνίου που περιέχουν μουσικές φόρμουλες
είναι χρήσιμα ως σώμα τεκμηρίωσης της κωδικοποίησης EZ. Δεν παρουσιάζουμε
όμως μια φόρμουλα ως μεταγραφή διαφορετικού ύμνου PDF και δεν δημοσιεύουμε
τα Word ή τα ιδιωτικά reports στον κατάλογο Kihem.

## Διανυσματικά PDF νεότερης στοιχειοθεσίας

Για νεότερες παρτιτούρες που είναι εξαρχής διανυσματικά PDF, υπάρχει ο
ιδιωτικός αναλυτής `digital_scores/extract_vector_pdf.py`. Εξάγει ανά
χαρακτήρα τη γραμματοσειρά, τη θέση, τον κώδικα glyph και το πραγματικό glyph
id που απέδωσε το PDF, ώστε να μπορεί να
κατασκευαστεί και να ελεγχθεί ρητά αντιστοίχιση ειδικής μουσικής
γραμματοσειράς προς στοιχεία Neanes. Δεν κάνει raster OCR και δεν υποθέτει
μόνος του ότι ένα glyph είναι συγκεκριμένο νεύμα.

Παράδειγμα (η έξοδος πρέπει να μείνει εκτός Git και εκτός δημόσιου
καταλόγου):

```bash
venv/bin/python digital_scores/extract_vector_pdf.py /ιδιωτική/πηγή.pdf \
  --pages 11-12 --output /tmp/kihem-vector-report.json \
  --glyph-atlas-dir /tmp/kihem-glyph-atlas \
  --font PSALTIRIOUBodoni --font isokratima3 --font FTHOGOS2
```

Το εργαλείο δεν αντιγράφει το PDF στην εφαρμογή, δεν παράγει `.byzx` και δεν
παρέχει δικαίωμα αναδημοσίευσης της πηγής. Παραγωγή παρτιτούρας θα εξεταστεί
μόνο αφού τεκμηριωθεί η αντιστοίχιση glyph και η άδεια χρήσης της πηγής.
Ο προαιρετικός άτλαντας είναι απλώς οπτική δειγματοληψία των glyph της
πρωτογενούς πηγής· μένει επίσης ιδιωτικός και δεν αποτελεί μεταγραφή.

Με τα επίσημα αρχεία του Neanes μπορεί προαιρετικά να παραχθεί δεύτερο JSON
με τις πέντε οπτικά πλησιέστερες ονομασίες Neanes για κάθε
`ενσωματωμένο font instance + glyph id`. Το instance είναι απαραίτητο: ένα
PDF μπορεί να κάνει διαφορετικό subset της ίδιας ονομαζόμενης γραμματοσειράς
σε άλλη σελίδα.
Για σταθερή χρήση μνήμης η πρώτη σύγκριση χρησιμοποιεί τα πρώτα 96 βασικά
glyph της επίσημης λίστας· το όριο αλλάζει μόνο συνειδητά με
`--reference-glyph-limit`:

```bash
venv/bin/python digital_scores/extract_vector_pdf.py /ιδιωτική/πηγή.pdf \
  --pages 11-12 --output /tmp/kihem-vector-report.json \
  --font PSALTIRIOUBodoni \
  --neanes-font /ιδιωτικά/Neanes.otf \
  --neanes-glyph-names /ιδιωτικά/glyphnames.json \
  --suggestions-output /tmp/kihem-neanes-candidates.json
```

Ο δείκτης `visual_similarity` συγκρίνει μόνο την εικόνα ενός glyph. Δεν
αναγνωρίζει σύνθετα νεύματα, συμφραζόμενα ή χρόνο και δεν είναι μουσική
πιστοποίηση. Τιμές κάτω από `0.82` επισημαίνονται ως
`insufficient-shape-evidence`; ακόμη και οι υψηλότερες τιμές είναι μόνο
`reviewable-shape-only`. Καμία πρόταση δεν χρησιμοποιείται από την εφαρμογή
ή από δημιουργία `.byzx`.

### PDF με EZ Byzantine Music Font Package

Για δημόσιο PDF που τεκμηριώνεται ότι γράφτηκε με το **EZ Byzantine Music Font
Package** της Μονής Αγίου Αντωνίου, χρησιμοποιούμε ιδιωτικά τα πλήρη επίσημα
TTF και δημιουργούμε ένα ελεγκτέο template:

```bash
venv/bin/python digital_scores/extract_vector_pdf.py SOURCE.pdf \
  --output /private/source-vector.json
venv/bin/python digital_scores/build_ez_mapping_template.py \
  /private/source-vector.json \
  --ez-font-dir /private/ByzMusicFonts/Fonts \
  --source-label 'source and permitted purpose' \
  --output /private/ez-to-neanes-template.json
```

Το template επιβεβαιώνει `PDF font instance + glyph id + PUA κωδικό` έναντι
της πλήρους EZ γραμματοσειράς και αφήνει σκόπιμα τα πεδία Neanes κενά. Τα
σύνθετα νεύματα, τα υποστηρικτικά σημεία και η θέση που επιβάλλουν οι Word
macros δεν γίνονται μουσικά γεγονότα από οπτική ομοιότητα. Το εργαλείο δεν
παράγει `.byzx`. Κρατούμε PDF, Word, fonts και templates ιδιωτικά ώσπου να
ελεγχθούν άδεια και μουσική σημασία.

Για λίγους βασικούς κωδικούς, οι επίσημες οδηγίες του πακέτου ονομάζουν
ρητά το σύμβολο (π.χ. `1` = ολίγον, `!` = απόστροφος, `@` = ελαφρόν,
`)` = υπορροή και `S` = γοργόν). Αυτή η τεκμηρίωση εμφανίζεται ως
`source_definition` στο template· δεν αλλάζει το `neanes.status` από
`unconfirmed`. Η ακριβής πάνω/κάτω προσάρτηση, η χρονική αξία και η διάσπαση
ενός προ-συντεθειμένου glyph εξαρτώνται από το συμφραζόμενο της γραμμής.
Το template σημειώνει επίσης την επίσημη οικογένεια του character table
(`ascending`, `descending`, `time`, `qualitative`, `martyria_measure_or_breath`
ή `support_combinations`). Glyph χωρίς κανονικό πλήκτρο είναι πιθανό προϊόν
macro/ειδικής εισαγωγής και δεν μετατρέπεται χωρίς ξεχωριστό κανόνα.

### Καρτέλα ελέγχου από το PDF

Πριν συμπληρωθεί οποιοδήποτε phrase plan, το Kihem μπορεί να οργανώσει την
εξαγωγή του διανυσματικού PDF σε γραμμές σημειογραφίας. Αυτό αφαιρεί την
αναζήτηση των κωδικών από τον έλεγχο, χωρίς να μετατρέπει τη γεωμετρική
γειτνίαση σε μουσική απόφαση:

```bash
venv/bin/python digital_scores/build_ez_phrase_review_sheet.py \
  /private/source-vector.json \
  /private/ez-to-neanes-template.json \
  --output /private/ez-phrase-review.json
```

Η ιδιωτική καρτέλα περιέχει, ανά σελίδα και οπτική γραμμή, όλες τις
εμφανίσεις με `source_anchor`, θέση στο PDF, πλήκτρο/οικογένεια του EZ
character table και τυχόν τεκμηριωμένο `source_definition`. Τα γειτονικά
λεκτικά εμφανίζονται μόνο ως `nearby_text_candidates`, ποτέ ως αυτόματη
αντιστοίχιση συλλαβής σε νεύμα. Ο ελεγκτής ορίζει εκεί τα όρια των φράσεων και
τα `note_events`, και μόνο μετά μεταφέρει τα επιβεβαιωμένα γεγονότα στο phrase
plan της επόμενης ενότητας.

Γοργά, χρονικά σημάδια και ισοκρατήματα παρουσιάζονται χωριστά ως
`attachment_candidates`: για καθένα η καρτέλα δείχνει την αμέσως προηγούμενη
και την αμέσως επόμενη τεκμηριωμένη βάση **της ίδιας γραμμής**. Είναι βοήθημα
επιλογής του ελεγκτή, όχι αυτόματη προσάρτηση. Στο πρώτο ελεγμένο δείγμα EZ,
οι κόκκινοι δείκτες Γ/Ν/Δ του `EZSpecial-II` αναγνωρίζονται αντίστοιχα ως
`Ison.Ga`/`Ison.Ni`/`Ison.Thi`. Ο δείκτης Μ είναι `isonControl: Pause`: ο
ισοκράτης σταματά και ψάλλει με τον κύριο ψάλτη, άρα δεν μετατρέπεται σε
φθόγγο Neanes. Το control διατηρείται στο ιδιωτικό event draft για μελλοντικό
software ισοκράτη· ο Neanes δεν έχει συνεχή δεύτερη φωνή ισοκρατήματος ώστε
να την παύσει ο ίδιος.

Η EZ βαρεία (`z` / `U+F07A`) καταγράφεται ως άχρονη τροπική ιδιότητα
`vareia: true` του επόμενου επιβεβαιωμένου `Note`. Δεν εμφανίζεται ως
ανεξάρτητη, χρονομετρημένη νότα· η καρτέλα δείχνει στον ελεγκτή την προηγούμενη
και την επόμενη βάση για να δηλώσει τη σωστή προσάρτηση.

Το `'` / `U+F027` του `EZPsaltica` είναι επιβεβαιωμένη παραλλαγή του
ποσοτικού **ίσον** (`quantitativeNeume: Ison`).

Το `:` / `U+F03A` του `EZPsaltica` είναι η **απλή χρονική**:
`timeNeume: Hapli`, με αξία μίας χρονικής μονάδας. Όπως κάθε χρονικό
σημάδι, διατηρείται στην καρτέλα ως προσάρτημα ώσπου ο ελεγκτής να
επιβεβαιώσει σε ποιο βασικό νεύμα της γραμμής ανήκει.

Για να γίνει ο οπτικός έλεγχος σε πραγματική εικόνα και όχι σε αριθμούς PDF,
παράγεται ιδιωτικό πακέτο μίας γραμμής:

```bash
venv/bin/python digital_scores/create_ez_line_review_packet.py \
  /private/ez-phrase-review.json \
  --line page-1-line-7 \
  --source-pdf /private/source.pdf \
  --output-dir /private/reviews/first-line
```

Το πακέτο έχει το `source-crop.png` της ακριβούς περικοπής, `review.md` με
checklist, συνοπτικό τμήμα «Όσα έχουν ήδη επιβεβαιωθεί από τον ψάλτη» και
`phrase-plan.json` με **κενά** events και όλα τα αταξινόμητα anchors. Δεν
περιέχει προτεινόμενη μελωδία ή επιβεβαίωση της υπόλοιπης γραμμής. Μετά τον οπτικό
έλεγχο, ο ψάλτης συμπληρώνει τις ομάδες events· τότε και μόνο τότε ακολουθεί
η παραγωγή και η ακουστική επιβεβαίωση του ιδιωτικού `.byzx`.

### Επιβεβαιωμένη φράση EZ → γεγονότα Neanes

Το επόμενο, επίσης ιδιωτικό, στάδιο είναι **φράση προς φράση**. Ο ψάλτης
δένει το βασικό glyph και κάθε προσάρτημα με τα ακριβή
`pdf_font_instance + pdf_glyph_id + pua_codepoint` του template και δηλώνει
τη λύση Neanes. Μόνο με `confirmed: true` για ολόκληρο το μουσικό γεγονός
μπορεί να τρέξει:

```bash
venv/bin/python digital_scores/build_ez_neanes_event_draft.py \
  /private/ez-to-neanes-template.json \
  /private/confirmed-phrase-plan.json \
  --output /private/neanes-note-events.json
```

Κάθε event του plan έχει τη μορφή:

```json
{
  "confirmed": true,
  "source_anchors": [
    {"pdf_font_instance": "14:EZPsaltica", "pdf_glyph_id": 49, "pua_codepoint": "U+F031"}
  ],
  "resolution": {"quantitativeNeume": "Oligon", "lyrics": "συλλαβή"}
}
```

Για γοργόν, κλάσμα ή ποιοτικό σημάδι προστίθεται δικό του `source_anchor`
και η αντίστοιχη τιμή στο `resolution` (π.χ. `gorgonNeume:
"Gorgon_Top"`). Το εργαλείο απορρίπτει όλη τη φράση αν λείπει anchor, αν το
glyph id δεν συμφωνεί με την πλήρη EZ γραμματοσειρά, αν δεν υπάρχει ρητή
επιβεβαίωση ή αν ζητείται διάσπαση προ-συντεθειμένου glyph. Η έξοδος είναι
μόνο Neanes `Note` events, όχι πλήρες `.byzx`: χρειάζονται ακόμη οι ιδιότητες
του score, το λεκτικό/η συλλαβοποίηση και οπτικός-ακουστικός έλεγχος στο
Neanes. Έτσι ένα λάθος δεν μπορεί να περάσει σιωπηρά ως εκτελέσιμη παρτιτούρα.

### Ιδιωτικό `.byzx` με τον serializer του Neanes

Όταν το phrase plan έχει επιβεβαιωθεί και έχει παραχθεί το event draft, το
επόμενο εργαλείο γράφει κανονικό `.byzx` **μέσω του ίδιου του Neanes**, όχι με
αντιγραφή ενός αβέβαιου JSON template:

```bash
venv/bin/python digital_scores/build_ez_neanes_byzx.py \
  /private/neanes-note-events.json \
  --title 'Τίτλος ιδιωτικού μουσικού draft' \
  --neanes-source /private/neanes-source \
  --output /private/title-ez-draft.byzx
```

Το `--neanes-source` είναι το τοπικό checkout του Neanes με τα `node_modules`
του. Το Kihem δημιουργεί εκεί ένα εφήμερο test worker, δίνει στα μοντέλα
`Score`/`Note` του Neanes μόνο τα ήδη επιβεβαιωμένα στοιχεία και ζητά από το
`SaveService` του Neanes να αποθηκεύσει το αρχείο. Αμέσως το ξανανοίγει για
τεχνικό έλεγχο και αφαιρεί τον εφήμερο worker. Το παραγόμενο `.byzx` έχει
τίτλο/δημιουργό που το δηλώνουν ιδιωτικό EZ draft και δεν προστίθεται στον
κατάλογο ή σε δημόσιο URL. Αρχική μαρτυρία εισάγεται μόνο εφόσον το phrase
plan περιέχει δική της επιβεβαιωμένη δήλωση (`note`, `rootSign`, `scale`).

## Επιθεώρηση ενσωματωμένων γραμματοσειρών

Πριν γίνει δουλειά σε νέο διανυσματικό PDF, ο παρακάτω ιδιωτικός έλεγχος
δείχνει αν τα font subsets κρατούν `cmap`, αναγνωρίσιμα ονόματα glyph και
κανόνες OpenType (`GSUB`/`GPOS`) που θα επέτρεπαν τεκμηριωμένη σημασιολογική
αντιστοίχιση:

```bash
venv/bin/python digital_scores/inspect_embedded_fonts.py /ιδιωτική/πηγή.pdf \
  --pages 11-12,19 --font-name PSALTIRIOU --font-name isokratima \
  --output /tmp/kihem-font-forensics.json
```

Το report δεν αποθηκεύει ούτε εξυπηρετεί τα binaries των fonts. `ToUnicode`
σημαίνει μόνο εξαγώγιμο κείμενο· δεν αρκεί ως μουσικό λεξικό. Αν λείπουν
`cmap`, σημασιολογικά glyph names και `GSUB`/`GPOS`, η συγκεκριμένη πηγή δεν
μπορεί να δώσει αυτόματη σημασιολογική μεταγραφή από τα embedded fonts μόνα
τους.

## Επιβλεπόμενα ζεύγη αναφοράς

Μια ήδη **επαληθευμένη** παρτιτούρα Neanes μπορεί να γίνει ιδιωτικό ζεύγος
αναφοράς για την ίδια έντυπη πηγή. Το εργαλείο δημιουργεί ένα JSON ledger με
τη διαδοχή των σημείων Neanes (λεκτικό, ποσοτικό νεύμα και χρονικά/γοργά
στοιχεία) και κενές θέσεις `source_anchor`. Δεν αναγνωρίζει από μόνο του
νεύματα στη σάρωση, δεν παράγει `.byzx` και δεν μετατρέπει οπτική ομοιότητα
σε μουσική αντιστοίχιση.

```bash
venv/bin/python digital_scores/create_reference_ledger.py \
  --catalog src/data/digital_scores.json \
  --storage /var/lib/kihem/digital-scores \
  --score-id lithou-sfragisthentos-tone1 \
  --output /var/lib/kihem/digital-score-reviews/reference-pairs/lithou-sfragisthentos-tone1.json
```

Ο ψάλτης συμπληρώνει κατόπιν, φράση προς φράση, το `source_anchor` και θέτει
`confirmed: true` μόνο όπου η οπτική σύγκριση είναι βέβαιη. Ακόμη και τότε η
γνώση αυτή είναι περιορισμένη στη συγκεκριμένη έκδοση και στοιχειοθεσία:
απαιτούνται περισσότερα ανεξάρτητα επιβεβαιωμένα ζεύγη πριν χρησιμοποιηθεί
για πρόταση αντιστοίχισης σε νέο μέλος.

Για το πρώτο ζεύγος, το
`digital_scores/reference_plans/lithou-sfragisthentos-tone1.json` καταγράφει
επτά διαδοχικές μουσικές φράσεις, με ακριβή εύρη από τα 110 σημεία Neanes
και το αντίστοιχο τμήμα της σάρωσης. Χρησιμοποιείται προαιρετικά ως εξής:

```bash
venv/bin/python digital_scores/create_reference_ledger.py \
  --catalog src/data/digital_scores.json \
  --storage /var/lib/kihem/digital-scores \
  --score-id lithou-sfragisthentos-tone1 \
  --phrase-plan digital_scores/reference_plans/lithou-sfragisthentos-tone1.json \
  --output /var/lib/kihem/digital-score-reviews/reference-pairs/lithou-sfragisthentos-tone1.json
```

Οι επτά φράσεις δηλώνουν λεκτική/δομική αντιστοίχιση, όχι ακόμη επιβεβαίωση
κάθε μεμονωμένου τυπογραφικού glyph ή χρονικού σημείου.
