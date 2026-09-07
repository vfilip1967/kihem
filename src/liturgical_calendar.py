from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta


GREEK_DAYS = (
    "Δευτέρα",
    "Τρίτη",
    "Τετάρτη",
    "Πέμπτη",
    "Παρασκευή",
    "Σάββατο",
    "Κυριακή",
)

GREEK_MONTHS = (
    "",
    "Ιανουαρίου",
    "Φεβρουαρίου",
    "Μαρτίου",
    "Απριλίου",
    "Μαΐου",
    "Ιουνίου",
    "Ιουλίου",
    "Αυγούστου",
    "Σεπτεμβρίου",
    "Οκτωβρίου",
    "Νοεμβρίου",
    "Δεκεμβρίου",
)


@dataclass(frozen=True)
class LiturgicalCalendar:
    """Small Gregorian-calendar helper for the dates supported by Melodos."""

    current_date: date

    def __init__(self, value: date | datetime | str | None = None, *, date_str: str | None = None):
        value = date_str if date_str is not None else value
        if value is None:
            parsed = date.today()
        elif isinstance(value, datetime):
            parsed = value.date()
        elif isinstance(value, date):
            parsed = value
        elif isinstance(value, str):
            parsed = date.fromisoformat(value)
        else:
            raise TypeError("Η ημερομηνία πρέπει να είναι date, datetime ή YYYY-MM-DD")
        object.__setattr__(self, "current_date", parsed)

    @property
    def is_sunday(self) -> bool:
        return self.current_date.weekday() == 6

    def get_day_of_week(self) -> str:
        return GREEK_DAYS[self.current_date.weekday()]

    def get_day_name(self, value: date | None = None) -> str:
        target = value or self.current_date
        return GREEK_DAYS[target.weekday()]

    def format_long(self) -> str:
        day = self.current_date.day
        month = GREEK_MONTHS[self.current_date.month]
        return f"{self.get_day_of_week()} {day} {month} {self.current_date.year}"

    def nearest_sunday(self) -> date:
        """Return this date when Sunday, otherwise the next Sunday."""
        days_ahead = (6 - self.current_date.weekday()) % 7
        return self.current_date + timedelta(days=days_ahead)

    def __repr__(self) -> str:
        return f"LiturgicalCalendar({self.current_date.isoformat()})"
