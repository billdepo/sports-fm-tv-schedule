from typing import List

from datetime import datetime as dt
from datetime import timedelta as dt_td
from gcsa.event import Event


def format_date(time: str) -> dt:
    h, m = [int(x) for x in time.split(':')]
    current_date = dt.now()
    fixed_date = dt(year=current_date.year,
                    month=current_date.month,
                    day=current_date.day,
                    hour=h,
                    minute=m)
    return fixed_date


def filter_events_time(event_objs: List[Event]) -> List[Event]:
    new_list = [event for event in event_objs if event.start.hour >= 10]  # exclude events before 10am
    return new_list


def create_google_cal_event(events: list, calendar):
    """Creates a calendar event using Google Calendar API."""

    event_objs = []
    tournaments_set = set()
    description = ''

    for e in events:
        title, tournament, tv_channel, event_start = e

        if tournament.strip() in ['NCAA', 'NBA', 'Super League', 'Super League 2']:  # exclude Super League games
            continue

        summary = f'{title} | {tournament} @ {event_start}, {tv_channel}'
        event_start = format_date(event_start)
        event_end = event_start + dt_td(minutes=1)

        event = Event(
            summary=summary,
            start=event_start,
            end=event_end
        )
        event_objs.append(event)
        tournaments_set.add(tournament)
        description += f'{event.summary}\n'

    event_objs = filter_events_time(event_objs)

    summary = f"Sport Events Tournaments: {', '.join(list(tournaments_set))}"
    selected_datetime = dt.now().replace(hour=10, minute=0)
    event = Event(
        summary=summary,
        start=selected_datetime,
        end=selected_datetime + dt_td(minutes=1),
        description=description
    )
    calendar.add_event(event)
