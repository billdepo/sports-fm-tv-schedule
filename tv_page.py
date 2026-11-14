"""Κατέβασμα και parsing του https://www.sport-fm.gr/tv.

Η σελίδα σερβίρει **πέντε ημέρες σε ένα HTML** (2 περασμένες, σήμερα, 2 επόμενες)
ως tab panels που εναλλάσσονται client-side:

    div.tv-tabs[role=tablist]
      button#tv-tab-2  "Σήμερα (29) 14/11"  aria-selected=true
    div.tv-days-multi
      div.tv-day#tv-day-2.is-active  -> h2.section-heading "Σήμερα, Σάββατο 14/11"

Ένα find_all σε όλο το document πιάνει και τα πέντε panels, οπότε κάθε selector
εδώ είναι scoped στο panel της ζητούμενης ημέρας. Η επιλογή panel γίνεται με
**ταίριασμα της ημερομηνίας dd/mm**, όχι με το `is-active`: αν μας σερβιριστεί
cached σελίδα, το `is-active` δείχνει λάθος μέρα σιωπηλά, ενώ η ημερομηνία όχι.
"""

from __future__ import annotations

import logging
import re
import time as time_module
import urllib.error
import urllib.request
from datetime import date

from bs4 import BeautifulSoup

from events import TvEvent, to_target_tz

log = logging.getLogger(__name__)

# Τα WordPress installs μπλοκάρουν το default python-urllib UA.
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_TIMEOUT_SECONDS = 30
_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 5

_EVENT_SELECTOR = "div.column.is-7"
_TITLE_SELECTOR = "h3.zonasemibold"
_TOURNAMENT_SELECTOR = "p.font-size-16"
_CHANNEL_SELECTOR = "span.post-category"
_TIME_SELECTOR = "time"


class PageStructureError(RuntimeError):
    """Το HTML δεν έχει τη δομή που περιμένουμε — η σελίδα άλλαξε ξανά."""


def fetch_page(url: str) -> str:
    """Κατεβάζει το HTML με timeout και retries.

    Χωρίς timeout, ένα hung socket κολλάει το cron job για πάντα. Το urlopen
    πετάει HTTPError για non-2xx, οπότε δεν χρειάζεται έλεγχος getcode().
    """
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    last_error: Exception | None = None

    for attempt in range(1, _RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                html = response.read().decode(charset, errors="replace")
            log.info("fetched %s (%d bytes)", url, len(html))
            return html
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            log.warning("fetch attempt %d/%d failed: %s", attempt, _RETRIES, error)
            if attempt < _RETRIES:
                time_module.sleep(_RETRY_BACKOFF_SECONDS * attempt)

    raise RuntimeError(f"Could not fetch {url} after {_RETRIES} attempts") from last_error


def _find_day_panel(soup: BeautifulSoup, day: date):
    """Επιστρέφει το div.tv-day που αντιστοιχεί στο `day`, αλλιώς raise."""
    wanted = f"{day:%d/%m}"

    # 1η επιλογή: το επιλεγμένο tab, αλλά μόνο αν η ημερομηνία του συμφωνεί.
    selected_tab = soup.select_one('button.tv-tab[aria-selected="true"]')
    if selected_tab is not None:
        tab_date = selected_tab.select_one("span.tv-tab-date")
        panel_id = selected_tab.get("aria-controls")
        if tab_date is not None and tab_date.get_text(strip=True) == wanted and panel_id:
            panel = soup.select_one(f"div.tv-day#{panel_id}")
            if panel is not None:
                return panel

    # 2η επιλογή: ταίριασμα της dd/mm στο heading κάθε panel. Πιάνει και τις
    # άλλες τέσσερις μέρες, όχι μόνο τη σημερινή.
    for panel in soup.select("div.tv-day"):
        heading = panel.select_one("h2.section-heading")
        if heading and re.search(rf"\b{re.escape(wanted)}\b", heading.get_text()):
            return panel

    available = [
        h.get_text(strip=True)
        for h in soup.select("div.tv-day h2.section-heading")
    ]
    raise PageStructureError(
        f"Δεν βρέθηκε panel για {wanted}. Διαθέσιμα panels: {available or 'κανένα'}"
    )


def parse_events(html: str, day: date) -> list[TvEvent]:
    """Βγάζει τα events **μόνο** της ημέρας `day`, με ώρες σε TARGET_TZ.

    Κάνει raise αντί να γυρίσει άδεια λίστα αν η δομή αλλάξει: ένα σιωπηλό
    "0 events" μοιάζει με ήσυχη μέρα και περνά απαρατήρητο.
    """
    soup = BeautifulSoup(html, features="html.parser")
    panel = _find_day_panel(soup, day)

    blocks = panel.select(_EVENT_SELECTOR)
    if not blocks:
        raise PageStructureError(
            f"Το panel της {day:%d/%m} δεν περιέχει '{_EVENT_SELECTOR}' blocks"
        )

    events: list[TvEvent] = []
    skipped = 0
    for block in blocks:
        title = block.select_one(_TITLE_SELECTOR)
        tournament = block.select_one(_TOURNAMENT_SELECTOR)
        channel = block.select_one(_CHANNEL_SELECTOR)
        start = block.select_one(_TIME_SELECTOR)

        if not (title and tournament and channel and start):
            skipped += 1
            continue

        hhmm = start.get_text(strip=True)
        if not re.fullmatch(r"\d{1,2}:\d{2}", hhmm):
            skipped += 1
            log.warning("unparseable time %r, skipping block", hhmm)
            continue

        events.append(TvEvent(
            title=title.get_text(strip=True),
            tournament=tournament.get_text(strip=True),
            channel=channel.get_text(strip=True),
            start=to_target_tz(hhmm, day),
        ))

    if skipped:
        log.warning("skipped %d/%d malformed event blocks", skipped, len(blocks))
    if not events:
        raise PageStructureError(
            f"Βρέθηκαν {len(blocks)} blocks για {day:%d/%m} αλλά κανένα δεν έγινε parse — "
            "άλλαξαν τα class names;"
        )

    log.info("parsed %d events for %s", len(events), day.isoformat())
    return events
