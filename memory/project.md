# Kihem project memory

Updated: 2026-09-07

## Product intent

- Compose the selected Gregorian-calendar date from the actual result returned by
  `https://melodos.com/akolouthies/`.
- Support Sundays, weekdays and major feasts; never reject a date merely because
  it is not a Sunday.
- Present Matins and the Divine Liturgy of Saint John Chrysostom while preserving
  the source's polytonic Greek and Melodos-like text colours/aesthetic.
- Attach scanned Byzantine-music excerpts immediately after the matching source
  text. Matching is content-driven, not based only on weekday or tone.
- Every inserted excerpt has a visible in-page bookmark with related wording and
  a stable `#music-{piece-id}-{instance}` anchor.
- The contents menu includes a dropdown of the current page's musical bookmarks,
  each linking directly to its inserted excerpt.
- When both slow and short settings exist, prefer the short setting.
- Future books must be additive: several verified settings may eventually be
  attached at the same textual position.
- For the special 8 September Orthros text, attach the first antiphon of the
  fourth-tone Anavathmoi after its final theotokion; its verified source is
  pp. 176–177 of the local Ioannis Protopsaltis Anastasimatarion.
- The first Liturgy pilot excerpts use the 1851 Pandekti fourth volume: the
  Eisodikon (p. 27) and short Trisagion (p. 29), each exposed as a bookmark.

## Current pilot

- Primary date: Sunday 2026-09-13, new calendar.
- Public URL:
  `https://book.milatos.com/kihem/?date=2026-09-13&services=both&view=melodos`
- Production code: `/var/www/kihem/src`
- Persistent books: `/var/lib/kihem/books`
- Temporary Melodos/PNG cache: `/tmp/kihem-cache`
- Service: `kihem.service` (Gunicorn on `127.0.0.1:5000`, proxied at `/kihem/`).

## Operational rules

- Run tests with:
  `/var/www/kihem/venv/bin/python -m unittest discover -s tests -v`
- Deploy source with the explicit destination:
  `rsync -a /root/projects/kihem/src/ /var/www/kihem/src/`
- Restart with `systemctl restart kihem.service`, then check the public page and
  the first/last PNG of every new excerpt.
- Do not use a multi-source rsync with trailing `src/` into `/var/www/kihem/`;
  that copies package contents into the production root.
- A previous deployment created unused top-level Python/test files plus
  `/var/www/kihem/static` and `/var/www/kihem/templates`. The active service uses
  `/var/www/kihem/src`; delete those redundant copies only with explicit user
  approval after verifying targets.

## Git state

- Branch: `master`.
- The repository originally had no remote. Keep work local unless the user
  explicitly requests a public/external repository.
- Completed feature commits through `6b07f67` include the persistent music
  library, Evlogitaria, Psalm 50, the Cross katavasies and preference for their
  short setting.
