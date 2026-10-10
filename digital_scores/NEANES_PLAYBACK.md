# Ενσωματωμένη τεχνική ακρόαση Neanes

Ο ιδιωτικός player του Kihem χρησιμοποιεί το αμετάβλητο web build του
[Neanes](https://github.com/neanes/neanes), έκδοση **0.5.55**, commit
`ecd4bee1fa91ece1c0d05ca5f21e6f3652263baf`.

- Άδεια: [GPL-3.0-only](https://github.com/neanes/neanes/blob/ecd4bee1fa91ece1c0d05ca5f21e6f3652263baf/LICENSE).
- Πλήρης πηγαίος κώδικας: [Neanes repository, ίδιο commit](https://github.com/neanes/neanes/tree/ecd4bee1fa91ece1c0d05ca5f21e6f3652263baf).
- Το Kihem δεν τροποποιεί το Neanes. Το template
  `src/templates/digital_score_playback.html` λειτουργεί ως wrapper: αφού ο
  χρήστης έχει ήδη πιστοποιηθεί, διαβάζει το συγκεκριμένο ιδιωτικό `.byzx`
  και το παραδίδει στο κανονικό browser file input του Neanes.

Η συνθετική ακρόαση είναι εργαλείο τεχνικού ελέγχου. Δεν ισοδυναμεί με
ανθρώπινη εκτέλεση, ούτε πιστοποιεί ότι η ψηφιακή παρτιτούρα αποδόθηκε σωστά
από μια έντυπη σάρωση.

## Εγκατάσταση build

Το web build δεν αποθηκεύεται στο Git. Δημιουργείται από το παραπάνω commit
με Vite base `/kihem/review/neanes/app/` και εγκαθίσταται στο
`/var/lib/kihem/neanes-web` (ή στην τιμή του `KIHEM_NEANES_WEB_DIR`). Το
`LICENSE` του Neanes αντιγράφεται μαζί με το build.
