import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
import pytz
import re

# URL Celcat groupe
GROUPS = [
    "MIASHS5ASC1",
    "MIASHS6ASC2",
    "MIASHS6ASC1",
    "MIASHS6ASC2",
]

BASE_URL = "https://celcat.u-bordeaux.fr/calendar/cal?vt=agendaMonth&et=module&fid0={}&dt={}"

# On part de la date du jour
today = datetime.today()
paris_tz = pytz.timezone("Europe/Paris")

def is_group1(note):
    if not note:
        return False
    return bool(re.search(r"(grp\s*1|groupe\s*1|\b1\b)", note.lower()))

cal = Calendar()

for group in GROUPS:
    url = BASE_URL.format(group, today.strftime("%Y-%m-%d"))
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Exemple de parsing (à adapter selon la structure HTML)
    for div in soup.select(".fc-event"):
        title = div.get("title", "")
        # Vérifie TD/TP + groupe 1 dans le title ou notes
        if ("TD" in title or "TP" in title) and not is_group1(title):
            continue

        # Pour l'exemple, on prend la date et l'heure à partir du titre (à adapter)
        # Ici il faudra extraire start/end réels
        e = Event()
        e.name = title
        e.begin = paris_tz.localize(today)
        e.end = paris_tz.localize(today)  # à remplacer par la vraie fin
        cal.events.add(e)

# Sauvegarde du fichier ICS
with open("calendar.ics", "w", encoding="utf-8") as f:
    f.writelines(cal.serialize_iter())

print("✅ calendar.ics généré !")

