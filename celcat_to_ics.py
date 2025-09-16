# celcat_to_ics_fixed.py
import pytz
from ics import Calendar, Event
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import uuid

BASE_URL = (
    "https://celcat.u-bordeaux.fr/calendar/cal?"
    "vt=agendaWeek&et=group&fid0=MIASHS5ASC1&fid1=MIASHS5ASC2"
    "&fid2=MIASHS6ASC1&fid3=MIASHS6ASC2"
)

paris_tz = pytz.timezone("Europe/Paris")
cal = Calendar()

def escape_text(text):
    """Échappe les caractères spéciaux pour ICS"""
    text = text.replace("\\", "\\\\")
    text = text.replace(",", "\\,")
    text = text.replace(";", "\\;")
    text = text.replace("\n", "\\n")
    return text

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(BASE_URL)
    page.wait_for_timeout(5000)

    soup = BeautifulSoup(page.content(), "html.parser")

    for div in soup.select(".fc-content"):
        time_div = div.select_one(".fc-time")
        if not time_div or "data-full" not in time_div.attrs:
            continue

        start_str, end_str = time_div["data-full"].split(" - ")
        start_hour, start_minute = map(int, start_str.split(":"))
        end_hour, end_minute = map(int, end_str.split(":"))
        today = datetime.today()
        start_dt = paris_tz.localize(datetime(today.year, today.month, today.day, start_hour, start_minute))
        end_dt = paris_tz.localize(datetime(today.year, today.month, today.day, end_hour, end_minute))

        lines = [line.strip() for line in div.get_text(separator="\n").split("\n") if line.strip()]
        if len(lines) < 7:
            continue

        course_code_title = escape_text(lines[2])
        groups = escape_text(", ".join(lines[3:5]))
        teacher = escape_text(lines[5])
        room = escape_text(lines[6])

        event_title = f"{course_code_title} ({groups}) - {teacher} - {room}"

        e = Event()
        e.name = event_title
        e.begin = start_dt.astimezone(pytz.utc)  # toujours en UTC
        e.end = end_dt.astimezone(pytz.utc)
        e.created = datetime.now(pytz.utc)
        e.uid = str(uuid.uuid4()) + "@celcat"  # UID unique
        cal.events.add(e)

    browser.close()

# Écriture ICS avec pliage des lignes >75 caractères
with open("calendar.ics", "w", encoding="utf-8") as f:
    for line in cal.serialize_iter():
        while len(line) > 75:
            f.write(line[:75] + "\r\n ")
            line = line[75:]
        f.write(line + "\r\n")

print("✅ calendar.ics généré correctement avec DTSTAMP, UID et lignes pliées !")
