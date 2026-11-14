"""Tests πάνω σε πραγματικό HTML snapshot του sport-fm.gr/tv.

Το fixture κατεβάστηκε στις 14/11/2026 και περιέχει πέντε tab panels:
    12/11 Πέμπτη (27) | 13/11 Χθες (25) | 14/11 Σήμερα (29) | 15/11 Αύριο (34) | 16/11 Δευτέρα (20)
συνολικά 135 event blocks. Το αρχικό bug ήταν ότι το scraping τα έπαιρνε και τα
135 αντί για τα 29 της σημερινής μέρας — το test_only_todays_events είναι
ακριβώς αυτό που θα το είχε πιάσει.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from events import DEFAULT_EMOJI, SOURCE_TZ, TARGET_TZ, normalize, prefilter, to_target_tz
from tv_page import PageStructureError, parse_events

FIXTURE = Path(__file__).parent / "fixtures" / "tv_2026-11-14.html"
FIXTURE_DAY = date(2026, 11, 14)

# Τα counts που διαφημίζει η σελίδα στα tabs, ανά ημερομηνία.
PANEL_COUNTS = {
    date(2026, 11, 12): 27,
    date(2026, 11, 13): 25,
    date(2026, 11, 14): 29,
    date(2026, 11, 15): 34,
    date(2026, 11, 16): 20,
}
TOTAL_BLOCKS_IN_PAGE = sum(PANEL_COUNTS.values())  # 135


@pytest.fixture(scope="module")
def html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


class TestPanelSelection:
    def test_only_todays_events(self, html):
        """Το regression test του αρχικού bug: 29, όχι 135."""
        events = parse_events(html, FIXTURE_DAY)
        assert len(events) == PANEL_COUNTS[FIXTURE_DAY]
        assert len(events) < TOTAL_BLOCKS_IN_PAGE

    @pytest.mark.parametrize("day,expected", sorted(PANEL_COUNTS.items()))
    def test_each_panel_is_addressable_by_date(self, html, day, expected):
        """Η επιλογή panel γίνεται με ημερομηνία, άρα δουλεύει και για τις άλλες μέρες."""
        assert len(parse_events(html, day)) == expected

    def test_unknown_date_raises(self, html):
        """Μέρα εκτός παραθύρου -> hard fail, όχι σιωπηλή άδεια λίστα."""
        with pytest.raises(PageStructureError, match="20/11"):
            parse_events(html, date(2026, 11, 20))

    def test_broken_structure_raises(self):
        with pytest.raises(PageStructureError):
            parse_events("<html><body><p>nothing here</p></body></html>", FIXTURE_DAY)


class TestEventParsing:
    def test_all_fields_populated(self, html):
        for event in parse_events(html, FIXTURE_DAY):
            assert event.title, event
            assert event.tournament, event
            assert event.channel, event
            assert event.start.tzinfo is not None, event

    def test_starts_are_in_target_tz(self, html):
        for event in parse_events(html, FIXTURE_DAY):
            assert event.start.utcoffset() == event.start.astimezone(TARGET_TZ).utcoffset()

    def test_known_event_is_parsed_exactly(self, html):
        """02:00 Αθήνα -> 01:00 Ζυρίχη, άρα και ένα end-to-end tz check."""
        events = parse_events(html, FIXTURE_DAY)
        first = min(events, key=lambda e: e.start)
        assert first.tournament == "Τένις"
        assert first.channel == "NOVASPORTS 6"
        assert first.start.strftime("%H:%M") == "01:00"

    def test_no_duplicate_identical_entries_within_a_day(self, html):
        events = parse_events(html, FIXTURE_DAY)
        keys = [(e.title, e.tournament, e.channel, e.start) for e in events]
        assert len(keys) == len(set(keys))


class TestTimezone:
    def test_november_athens_is_one_hour_ahead_of_zurich(self):
        assert to_target_tz("20:00", date(2026, 11, 14)).strftime("%H:%M") == "19:00"

    def test_july_offset_is_also_one_hour(self):
        """EEST->CEST: η διαφορά μένει 1 ώρα, δεν είναι hardcoded offset."""
        assert to_target_tz("20:00", date(2026, 7, 14)).strftime("%H:%M") == "19:00"

    def test_after_midnight_event_rolls_back_a_day(self):
        converted = to_target_tz("00:30", date(2026, 11, 14))
        assert converted.date() == date(2026, 11, 13)
        assert converted.strftime("%H:%M") == "23:30"

    def test_source_and_target_differ(self):
        assert SOURCE_TZ != TARGET_TZ


class TestNormalize:
    @pytest.mark.parametrize("raw", ["Τένις", "ΤΕΝΙΣ", "τένις", "Τένις ", "τενισ"])
    def test_accents_case_and_final_sigma_collapse(self, raw):
        assert normalize(raw.strip()) == "τενισ"


class TestEmoji:
    @pytest.mark.parametrize("tournament,expected", [
        ("Τένις", "🎾"),
        ("ATP Challenger 50", "🎾"),
        ("Ισπανικό πρωτάθλημα μπάσκετ", "🏀"),
        ("NBA", "🏀"),
        ("EuroLeague", "🏀"),            # περιέχει "euro" — δεν πρέπει να γίνει ⚽
        ("Champions League", "⚽"),
        ("Super League", "⚽"),
        ("Euro 2028", "⚽"),
        ("UEFA Nations League", "⚽"),
        ("EFL League One", "⚽"),
        ("Superbet League 2", "⚽"),
        ("Γκολφ", "⛳"),
        # Τονισμένα/με διαλυτικά: τα patterns συγκρίνονται με normalize()d
        # κείμενο, οπότε πρέπει κι αυτά να είναι χωρίς τόνους.
        ("Α1 Βόλεϊ Γυναικών", "🏐"),
        ("Volley League", "🏐"),
        ("Χάντμπολ", "🤾"),
        ("UFC Fight Night", "🥊"),
        ("Προκριματικά Eurobasket Γυναικών", "🏀"),
    ])
    def test_sport_lookup(self, tournament, expected):
        from events import TvEvent
        event = TvEvent("x", tournament, "ch", to_target_tz("12:00", FIXTURE_DAY))
        assert event.emoji == expected

    def test_unknown_sport_falls_back(self):
        from events import TvEvent
        event = TvEvent("x", "Κρίκετ", "ch", to_target_tz("12:00", FIXTURE_DAY))
        assert event.emoji == DEFAULT_EMOJI


class TestPrefilter:
    def test_drops_nba_and_out_of_window(self, html):
        events = parse_events(html, FIXTURE_DAY)
        kept = prefilter(events)

        assert len(kept) < len(events)
        assert not any("nba" in normalize(e.tournament) for e in kept)
        for event in kept:
            assert "10:00" <= event.start.strftime("%H:%M") <= "23:30"

    def test_drops_the_0100_tennis(self, html):
        """Το 02:00 Αθήνα / 01:00 Ζυρίχη event πρέπει να φύγει."""
        kept = prefilter(parse_events(html, FIXTURE_DAY))
        assert all(e.start.strftime("%H:%M") != "01:00" for e in kept)

    def test_empty_input(self):
        assert prefilter([]) == []
