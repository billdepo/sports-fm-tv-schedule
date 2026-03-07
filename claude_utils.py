import os
import anthropic

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def _read_prompt(filename: str) -> str:
    path = os.path.join(_PROMPTS_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def filter_with_claude(events_raw: str, preferences: str, api_key: str, model: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    system = _read_prompt("system.txt")
    user_message = _read_prompt("instructions.txt").format(
        preferences=preferences,
        events=events_raw,
    )

    with client.messages.stream(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user_message}]
    ) as stream:
        return stream.get_final_message().content[0].text.strip()
