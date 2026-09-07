from __future__ import annotations

import argparse

from src.composer import ServiceComposer
from src.liturgical_calendar import LiturgicalCalendar


def main() -> None:
    parser = argparse.ArgumentParser(description="Σύνθεση ακολουθιών ημερομηνίας από τον Μελωδό")
    parser.add_argument("date", nargs="?", default="2026-09-13", help="Ημερομηνία σε μορφή YYYY-MM-DD")
    parser.add_argument(
        "--service",
        choices=("orthros", "litourgia", "both"),
        default="both",
        help="Ακολουθία προς σύνθεση",
    )
    args = parser.parse_args()

    calendar = LiturgicalCalendar(args.date)
    services = ("orthros", "litourgia") if args.service == "both" else (args.service,)
    result = ServiceComposer().compose(calendar.current_date, services=services)
    print(calendar.format_long())
    for document in result.documents:
        print(f"\n--- {document.label} ---\n")
        print(document.plain_text)


if __name__ == "__main__":
    main()
