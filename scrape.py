"""Entry point: scrape -> ντετερμινιστικό prefilter -> LLM κρίση -> calendar."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from events import TARGET_TZ, prefilter  # noqa: E402
from tv_page import fetch_page, parse_events  # noqa: E402

log = logging.getLogger("sportfm")

_PREFERENCES_FILE = os.path.join(os.path.dirname(__file__), "prompts", "preferences.txt")


def _load_preferences() -> str:
    with open(_PREFERENCES_FILE, encoding="utf-8") as handle:
        return handle.read().strip()


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"No value given for the {name} environment variable")
    return value


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        stream=sys.stdout,
    )

    url = _require_env("URL_TO_SCRAPE")
    calendar_id = _require_env("CALENDAR_ID")
    credentials_path = os.environ.get("CREDENTIALS_JSON_PATH")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    model = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")

    # Η ημέρα ορίζεται στη ζώνη που μας ενδιαφέρει, όχι στη ζώνη του container.
    today = datetime.now(TARGET_TZ).date()

    events = parse_events(fetch_page(url), today)
    events = prefilter(events)

    if api_key:
        from claude_utils import select_events

        events = select_events(events, _load_preferences(), api_key, model)
    else:
        log.warning("ANTHROPIC_API_KEY not set — writing all %d events unfiltered", len(events))

    # Το import μένει εδώ ώστε ένα σφάλμα scraping να μην ανοίγει OAuth flow.
    from gcsa.google_calendar import GoogleCalendar

    from calendar_utils import create_google_cal_event

    calendar = GoogleCalendar(default_calendar=calendar_id, credentials_path=credentials_path)
    create_google_cal_event(events, calendar, today)
    log.info("Done.")


if __name__ == "__main__":
    main()
