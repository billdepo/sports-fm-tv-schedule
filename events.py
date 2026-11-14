"""Μοντέλο event, timezone, ντετερμινιστικό φιλτράρισμα και μορφοποίηση.

Ό,τι υπάρχει εδώ είναι ντετερμινιστικό — κανένα LLM. Οι κανόνες που είναι καθαρή
αριθμητική (μετατροπή ώρας, παράθυρο έναρξης) ή καθαρό lookup (emoji ανά άθλημα)
ζουν σε κώδικα και όχι σε prompt, ώστε να μην μπορούν να αποτύχουν σιωπηλά.

Στο LLM μένει μόνο σημασιολογική κρίση: «ταιριάζει αυτό το event στις
προτιμήσεις μου;» — δες claude_utils.select_events.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)

SOURCE_TZ = ZoneInfo("Europe/Athens")  # ό,τι δίνει το sport-fm.gr
TARGET_TZ = ZoneInfo("Europe/Zurich")  # ό,τι θέλω στο calendar

# Κανόνες που ήταν σε prompts/preferences.txt. Είναι σύγκριση ωρών και exact
# match ονόματος — τα κάνει ο κώδικας, όχι το μοντέλο.
WINDOW_START = time(10, 0)
WINDOW_END = time(23, 30)
EXCLUDED_TOURNAMENTS = re.compile(r"\bnba\b")

# Πρώτο ταίριασμα κερδίζει, οπότε το μπάσκετ πάει πριν το ποδόσφαιρο: το
# "EuroLeague" περιέχει "euro" και θα έπεφτε αλλιώς στο ποδοσφαιρικό \beuro\b.
_SPORT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("🏀", re.compile(r"μπασκετ|basket|euroleague|eurocup|\bnba\b")),
    ("⚽", re.compile(
        r"ποδοσφαιρ|champions league|europa league|conference league|super league|"
        r"superbet|premier league|\bfa cup\b|league cup|\bserie a\b|bundesliga|"
        r"\bla ?liga\b|\bligue 1\b|\beuro\b|world cup|μουντιαλ|κυπελλο ελλαδ|"
        r"\buefa\b|nations league|\befl\b|eredivisie|\bmls\b"
    )),
    ("🎾", re.compile(r"τενι|tennis|\batp\b|\bwta\b|challenger")),
    # ΠΡΟΣΟΧΗ: τα patterns πρέπει να είναι γραμμένα **χωρίς τόνους και
    # διαλυτικά**, γιατί συγκρίνονται με την έξοδο του normalize(): το "Βόλεϊ"
    # γίνεται "βολει", άρα ένα pattern "βολεϊ" δεν ταιριάζει ποτέ.
    ("🏐", re.compile(r"βολει|volley")),
    ("🤽", re.compile(r"\bπολο\b|water ?polo")),
    ("🏊", re.compile(r"κολυμβη|swimming")),
    ("🏃", re.compile(r"στιβο|athletics|μαραθων")),
    ("⛳", re.compile(r"γκολφ|\bgolf\b")),
    ("🏎", re.compile(r"formula|\bf1\b|moto ?gp|\bραλι")),
    ("🤾", re.compile(r"χειροσφαιρ|χαντμπολ|handball")),
    ("🥊", re.compile(r"\bufc\b|\bmma\b|πυγμαχ|boxing|kickbox")),
)
DEFAULT_EMOJI = "🏅"


def normalize(text: str) -> str:
    """Πεζά, χωρίς τόνους, με τελικό σίγμα κανονικοποιημένο.

    Χρειάζονται και τα τρία: "Τένις".lower() δίνει "τένις" (με τόνο, τελικό ς)
    ενώ "ΤΕΝΙΣ".lower() δίνει "τενισ" (χωρίς τόνο, κανονικό σ). Χωρίς
    normalization τα δύο δεν ταιριάζουν στο ίδιο keyword.
    """
    decomposed = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.replace("ς", "σ")


@dataclass(frozen=True)
class TvEvent:
    """Ένα event, με ώρα έναρξης ήδη σε TARGET_TZ και timezone-aware."""

    title: str
    tournament: str
    channel: str
    start: datetime

    @property
    def emoji(self) -> str:
        haystack = normalize(f"{self.tournament} {self.title}")
        for emoji, pattern in _SPORT_PATTERNS:
            if pattern.search(haystack):
                return emoji
        return DEFAULT_EMOJI

    def format_line(self) -> str:
        """Η γραμμή που μπαίνει στο description του calendar invite."""
        return (
            f"{self.emoji} {self.start:%H:%M} {self.title} | "
            f"{self.tournament}, {self.channel}"
        )

    def describe(self) -> str:
        """Η γραμμή που βλέπει το μοντέλο. Χωρίς emoji — δεν το κρίνει αυτό."""
        return f"{self.start:%H:%M} {self.title} | {self.tournament}, {self.channel}"


def to_target_tz(hhmm: str, day: date) -> datetime:
    """Μετατρέπει "HH:MM" της ημέρας `day` από SOURCE_TZ σε TARGET_TZ.

    Το zoneinfo χειρίζεται μόνο του EET/EEST και CET/CEST, οπότε δεν υπάρχει
    hardcoded offset που να σπάει στις αλλαγές θερινής ώρας.
    """
    hours, minutes = (int(part) for part in hhmm.split(":", 1))
    local = datetime.combine(day, time(hours, minutes), tzinfo=SOURCE_TZ)
    return local.astimezone(TARGET_TZ)


def prefilter(events: list[TvEvent]) -> list[TvEvent]:
    """Πετάει ό,τι αποκλείεται από ντετερμινιστικό κανόνα, πριν το LLM."""
    kept: list[TvEvent] = []
    for event in events:
        if EXCLUDED_TOURNAMENTS.search(normalize(event.tournament)):
            log.debug("excluded tournament: %s", event.describe())
            continue
        if not WINDOW_START <= event.start.time() <= WINDOW_END:
            log.debug("outside %s-%s window: %s", WINDOW_START, WINDOW_END, event.describe())
            continue
        kept.append(event)

    log.info(
        "prefilter: %d/%d events kept (%d dropped by rules in code)",
        len(kept), len(events), len(events) - len(kept),
    )
    return kept


def format_description(events: list[TvEvent]) -> str:
    """Το τελικό σώμα του calendar invite."""
    if not events:
        return "Δεν υπάρχουν events για σήμερα βάσει των προτιμήσεών σου."
    return "\n".join(event.format_line() for event in sorted(events, key=lambda e: e.start))
