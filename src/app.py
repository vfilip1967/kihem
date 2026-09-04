from flask import Flask, render_template_string, request
from datetime import datetime
from src.liturgical_calendar import LiturgicalCalendar
from src.rules import RuleEngine
from src.composer import Composer

app = Flask(__name__)

# Initialize components
calendar = LiturgicalCalendar()
rules = RuleEngine()
composer = Composer()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kihem - Λειτουργικός Συνθέτης</title>
    <style>
        body { font-family: "Times New Roman", serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #fdfdfd; color: #333; }
        h1 { color: #8b0000; border-bottom: 2px solid #8b0000; padding-bottom: 10px; text-align: center; }
        .date-info { text-align: center; font-style: italic; margin-bottom: 30px; font-size: 1.2em; }
        .service-text { white-space: pre-wrap; background: white; padding: 30px; border: 1px solid #ddd; box-shadow: 0 2px 5px rgba(0,0,0,0.1); font-size: 1.1em; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { margin: 0 10px; text-decoration: none; color: #8b0000; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Kihem - Λειτουργικός Συνθέτης</h1>
    <div class="nav">
        <a href="/">Σήμερα</a>
        <form style="display: inline-block; margin-left: 20px;" method="get" action="/">
            <input type="date" name="date" style="font-family: inherit;">
            <button type="submit" style="font-family: inherit;">Πήγαινε</button>
        </form>
    </div>
    <div class="date-info">{{ date_str }}</div>
    <div class="service-text">{{ service_text }}</div>
</body>
</html>
'''

@app.route('/')
def index():
    date_param = request.args.get('date')
    if date_param:
        try:
            date_obj = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD", 400
    else:
        date_obj = datetime.now().date()

    date_str = f"{date_obj.strftime('%d %B %Y')} ({calendar.get_day_name(date_obj)})"
    # For the purpose of current demonstration and the specific target date requested previously:
    # if date_obj == datetime(2026, 9, 6).date():
    #    ... (this is handled by the composer logic)
    
    # Synthesize the service
    structure = rules.get_orthros_structure(date_obj)
    service_text = composer.compose(structure)
    
    # If the result is empty (mock data missing), provide a fallback
    if not service_text or service_text.strip() == "":
        service_text = "Δεν βρέθηκαν κείμενα για την επιλεγμένη ημερομηνία. (Προσθήκη δεδομένων σε εξέλιξη)"

    return render_template_string(HTML_TEMPLATE, date_str=date_str, service_text=service_text)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
