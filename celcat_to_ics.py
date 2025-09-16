import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta
import pytz

# URL Celcat pour la semaine courante
BASE_URL = "https://celcat.u-bordeaux.fr/calendar/cal?vt=agendaWeek&et=group&fid0=MIASHS5ASC1&fid1=MIASHS5ASC2&fid2=MIASHS6ASC1&fid3=MIASHS6ASC2"

paris_tz = pytz.timezone("Europe/Paris")

r = requests.get(BASE_URL)
r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")

cal = Calendar()

for div in soup.select(".fc-content"):
    # Heure de début et fin
    time_div = div.select_one(".fc-time")
    if not time_div or "data-full" not in time_div.attrs:
        continue

    start_str, end_str = time_div["data-full"].split(" - ")
    start_hour, start_minute = map(int, start_str.split(":"))
    end_hour, end_minute = map(int, end_str.split(":"))

    # Récupérer le jour à partir de la date actuelle ou data-date si disponible
    # Ici on prend today comme approximation
    today = datetime.today()
    start_dt = paris_tz.localize(datetime(today.year, today.month, today.day, start_hour, start_minute))
    end_dt = paris_tz.localize(datetime(today.year, today.month, today.day, end_hour, end_minute))

    # Récupérer le contenu textuel
    lines = [line.strip() for line in div.get_text(separator="\n").split("\n") if line.strip()]
    if len(lines) < 7:
        continue  # ignore si le format est inattendu

    course_code_title = lines[2]  # Ex: "4TSQ503U Connaissances et représentations..."
    groups = ", ".join(lines[3:5])
    teacher = lines[5]
    room = lines[6]

    event_title = f"{course_code_title} ({groups}) - {teacher} - {room}"

    e = Event()
    e.name = event_title
    e.begin = start_dt
    e.end = end_dt
    cal.events.add(e)

# Sauvegarde du fichier ICS
with open("calendar.ics", "w", encoding="utf-8") as f:
    f.writelines(cal.serialize_iter())

print("✅ calendar.ics généré pour la semaine !")
