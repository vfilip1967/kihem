import unittest
from datetime import date

from src.liturgical_calendar import LiturgicalCalendar


class CalendarTests(unittest.TestCase):
    def test_greek_sunday_and_next_sunday(self):
        sunday = LiturgicalCalendar("2026-09-06")
        self.assertTrue(sunday.is_sunday)
        self.assertEqual(sunday.get_day_of_week(), "Κυριακή")
        self.assertEqual(sunday.format_long(), "Κυριακή 6 Σεπτεμβρίου 2026")

        monday = LiturgicalCalendar("2026-09-07")
        self.assertFalse(monday.is_sunday)
        self.assertEqual(monday.nearest_sunday(), date(2026, 9, 13))
