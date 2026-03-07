from typing import Optional

from datetime import datetime as dt
from datetime import timedelta as dt_td
from gcsa.event import Event
from claude_utils import filter_with_claude


def create_google_cal_event(
    events: list,
    calendar,
    anthropic_api_key: Optional[str] = None,
    claude_model: Optional[str] = None,
    preferences: Optional[str] = None,
):
    """Creates a calendar event using Google Calendar API."""

    raw_lines = []

    for e in events:
        title, tournament, tv_channel, event_start = e
        raw_lines.append(f'{title} | {tournament} @ {event_start}, {tv_channel}')

    events_raw = '\n'.join(raw_lines)

    if anthropic_api_key and claude_model and preferences:
        print('Filtering events with Claude...')
        description = filter_with_claude(events_raw, preferences, anthropic_api_key, claude_model)
    else:
        description = events_raw

    today = dt.now()
    greek_days = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]
    greek_months = ["Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου",
                    "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου"]
    day_name = greek_days[today.weekday()]
    month_name = greek_months[today.month - 1]
    summary = f"Αθλητικά – {day_name} {today.day} {month_name}"
    selected_datetime = today.replace(hour=9, minute=0, second=0, microsecond=0)
    event = Event(
        summary=summary,
        start=selected_datetime,
        end=selected_datetime + dt_td(minutes=1),
        description=description,
    )
    calendar.add_event(event)
