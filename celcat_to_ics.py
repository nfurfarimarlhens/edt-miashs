# celcat_to_ics.py
import pytz
from ics import Calendar, Event
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# URL Celcat pour la semaine
BASE_URL = (
    "https://celcat.u-bordeaux.fr/calendar/cal?"
    "vt=agendaWeek&et=group&fid0=MIASHS5ASC1&fid1=MIASHS5ASC2"
    "&fid2=MIASHS6ASC1&fid3=MIASHS6ASC2"
)

paris_tz = pytz.timezone("Europe/Paris")
cal = Calendar()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(BASE_URL)
    page.wait_for_timeout(5000)  # attendre 5 secondes que JS charge le calendrier

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    for div in soup.select(".fc-content"):
        time_div = div.select_one(".fc-time")
        if not time_div or "data-full" not in time_div.attrs:
            continue

        start_str, end_str = time_div["data-full"].split(" - ")
        start_hour, start_minute = map(int, start_str.split(":"))
        end_hour, end_minute = map(int, end_str.split(":"))
        today = datetime.today()
        start_dt = paris_tz.localize(
            datetime(today.year, today.month, today.day, start_hour, start_minute)
        )
        end_dt = paris_tz.localize(
            datetime(today.year, today.month, today.day, end_hour, end_minute)
        )

        lines = [line.strip() for line in div.get_text(separator="\n").split("\n") if line.strip()]
        if len(lines) < 7:
            continue

        course_code_title = lines[2]
        groups = ", ".join(lines[3:5])
        teacher = lines[5]
        room = lines[6]

        event_title = f"{course_code_title} ({groups}) - {teacher} - {room}"

        e = Event()
        e.name = event_title
        e.begin = start_dt
        e.end = end_dt
        cal.events.add(e)

    browser.close()

# Sauvegarde ICS
with open("calendar.ics", "w", encoding="utf-8") as f:
    f.writelines(cal.serialize_iter())

print("✅ calendar.ics généré avec tous les événements !")
