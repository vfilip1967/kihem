from datetime import datetime

class LiturgicalCalendar:
    """
    Handles the Gregorian calendar for liturgical services.
    """
    
    def __init__(self, date_str=None):
        """
        :param date_str: Date in 'YYYY-MM-DD' format. If None, uses today.
        """
        if date_str:
            self.current_date = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            self.current_date = datetime.now()

    def get_day_of_week(self):
        """Returns the day of the week in Greek."""
        days = {
            0: "Δευτέρα",
            1: "Τρίτη",
            2: "Τετάρτη",
            3: "Πέμπτη",
            4: "Παρασκευή",
            5: "Σάββατο",
            6: "Κυριακή"
        }
        return days[self.current_date.weekday()]

    def __repr__(self):
        return f"Calendar({self.current_date.strftime('%Y-%m-%d')})"

