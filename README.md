# Project Kihem

A liturgical service composer that reconstructs the Orthodox services (Orthros, Vespers, Divine Liturgy) using a "day-by-day" incremental build approach.

## Approach
- **Incremental Build:** The system is built manually, day by day, verifying each service against a reference.
- **Source of Truth:** All structures and sequences are based strictly on [melodos.com/akolouthies/](https://melodos.com/akolouthies/).
- **Calendar:** Only the Gregorian (New) calendar is supported.

## Goals
- Automated assembly of daily services.
- Use a rule-based engine to handle the complexity of the Typikon.

## Architecture
- **Data Layer:** Storage of liturgical fragments in `data/fragments.json`.
- **Rule Engine:** Logic in `src/rules.py` to determine the sequence for a specific date.
- **Composer:** Logic in `src/composer.py` to assemble fragments into a final text.
