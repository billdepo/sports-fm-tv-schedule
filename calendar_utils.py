"""Δημιουργία του Google Calendar event."""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta

from gcsa.event import Event

from events import TARGET_TZ, TvEvent, format_description

log = logging.getLogger(__name__)

_GREEK_DAYS = ("Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή")
_GREEK_MONTHS = (
    "Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου",
    "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου",
)

# Ώρα του placeholder event, σε TARGET_TZ.
_EVENT_TIME = time(9, 0)
_EVENT_DURATION = timedelta(minutes=1)


def build_summary(day: date) -> str:
    return f"Αθλητικά – {_GREEK_DAYS[day.weekday()]} {day.day} {_GREEK_MONTHS[day.month - 1]}"


def create_google_cal_event(events: list[TvEvent], calendar, day: date) -> Event:
    """Γράφει ένα event στο calendar με τα αθλητικά της ημέρας `day`.

    Το start/end είναι timezone-aware σε TARGET_TZ, ώστε να μην εξαρτάται από το
    TZ του container ή από το default timezone του calendar.
    """
    start = datetime.combine(day, _EVENT_TIME, tzinfo=TARGET_TZ)
    event = Event(
        summary=build_summary(day),
        start=start,
        end=start + _EVENT_DURATION,
        description=format_description(events),
    )

    created = calendar.add_event(event)
    log.info("created calendar event %r at %s with %d entries",
             event.summary, start.isoformat(), len(events))
    return created
