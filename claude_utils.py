"""Σημασιολογική επιλογή events με το Claude API.

Το μοντέλο κάνει **μόνο** κρίση: ποια events ταιριάζουν στις προτιμήσεις.
Δεν μετατρέπει ώρες (αριθμητική — events.to_target_tz), δεν βάζει emoji
(lookup — TvEvent.emoji) και δεν μορφοποιεί κείμενο (events.format_description).

Επιστρέφει indices μέσω structured outputs αντί για έτοιμο κείμενο, ώστε η
απάντηση να είναι validated και το output μικρό. Αυτό κρατά το LLM βήμα πίσω από
ένα στενό interface — list[TvEvent] -> list[int] — που μπορεί να υλοποιηθεί και
από άλλο provider χωρίς να αλλάξει τίποτα άλλο.
"""

from __future__ import annotations

import json
import logging
import os

import anthropic

from events import TvEvent

log = logging.getLogger(__name__)

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
_MAX_TOKENS = 1024

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "keep": {
            "type": "array",
            "description": "Τα index των events που ταιριάζουν στις προτιμήσεις.",
            "items": {"type": "integer"},
        }
    },
    "required": ["keep"],
    "additionalProperties": False,
}


def _read_prompt(filename: str) -> str:
    with open(os.path.join(_PROMPTS_DIR, filename), encoding="utf-8") as handle:
        return handle.read().strip()


def select_events(
    events: list[TvEvent],
    preferences: str,
    api_key: str,
    model: str,
) -> list[TvEvent]:
    """Γυρίζει το υποσύνολο των `events` που ταιριάζει στις προτιμήσεις."""
    if not events:
        return []

    numbered = "\n".join(f"{i}. {event.describe()}" for i, event in enumerate(events))
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=_MAX_TOKENS,
        system=_read_prompt("system.txt"),
        messages=[{
            "role": "user",
            "content": _read_prompt("instructions.txt").format(
                preferences=preferences,
                events=numbered,
            ),
        }],
        output_config={"format": {"type": "json_schema", "schema": _RESPONSE_SCHEMA}},
    )

    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            f"Claude hit max_tokens ({_MAX_TOKENS}); η απάντηση είναι κολοβή"
        )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude αρνήθηκε να απαντήσει στο request")

    text = next((block.text for block in response.content if block.type == "text"), None)
    if text is None:
        raise RuntimeError(f"Καμία text απάντηση από το Claude (stop_reason={response.stop_reason})")

    indices = json.loads(text)["keep"]

    valid = sorted({i for i in indices if 0 <= i < len(events)})
    if len(valid) != len(set(indices)):
        log.warning("Claude returned out-of-range indices: %s (events=%d)", indices, len(events))

    log.info(
        "Claude kept %d/%d events (in=%d tok, out=%d tok)",
        len(valid), len(events),
        response.usage.input_tokens, response.usage.output_tokens,
    )
    return [events[i] for i in valid]
