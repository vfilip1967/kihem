from liturgical_calendar import LiturgicalCalendar
from composer import ServiceComposer
from rules import RuleEngine

def run_composition():
    print("--- KIHEM Liturgical Composer ---")
    
    # 1. Setup Date (Only Gregorian)
    cal = LiturgicalCalendar(date_str="2026-09-06")
    print(f"Date: {cal.current_date.date()} ({cal.get_day_of_week()})")
    
    # 2. Get Structure from Rule Engine
    rules = RuleEngine()
    structure = rules.get_orthros_structure(cal)
    
    # 3. Compose Final Text
    composer = ServiceComposer()
    service_text = composer.compose(structure)
    
    print("\n--- ASSEMBLED SERVICE ---")
    print(service_text)
    print("\n-------------------------")

if __name__ == "__main__":
    run_composition()
