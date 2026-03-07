import os

from dotenv import load_dotenv
load_dotenv()

import urllib.request
from bs4 import BeautifulSoup
from gcsa.google_calendar import GoogleCalendar
from calendar_utils import create_google_cal_event

_PREFERENCES_FILE = os.path.join(os.path.dirname(__file__), "prompts", "preferences.txt")


def _load_preferences() -> str:
    with open(_PREFERENCES_FILE, encoding="utf-8") as f:
        return f.read().strip()


def main() -> None:
    URL = os.environ.get('URL_TO_SCRAPE')
    CALENDAR_ID = os.environ.get('CALENDAR_ID')
    CREDENTIALS_JSON_PATH = os.environ.get('CREDENTIALS_JSON_PATH')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', 'claude-haiku-4-5')

    if not URL:
        raise ValueError('No value given for the URL_TO_SCRAPE environment variable')
    if not CALENDAR_ID:
        raise ValueError('No value given for the CALENDAR_ID environment variable')

    with urllib.request.urlopen(URL) as web_url:
        if web_url.getcode() != 200:
            raise Exception(f'3rd party server error {URL}')
        html_data = web_url.read().decode("utf-8")

    soup = BeautifulSoup(html_data, features="html.parser")

    events_list = []
    for event in soup.find_all("div", {"class": "column is-7"}):
        try:
            title = event.find("h3", {"class": "semiblack-c zonasemibold font-size-24 minus-2 lin1"}).string.strip()
            tournament = event.find("p", {"class": "font-size-16"}).string
            tv_channel = event.find("span", {"class": "post-category lightred-c zonanormal"}).string
            time = event.find("time").string
        except AttributeError:
            print("Warning: skipping malformed event block")
            continue
        events_list.append((title, tournament, tv_channel, time))

    calendar = GoogleCalendar(default_calendar=CALENDAR_ID, credentials_path=CREDENTIALS_JSON_PATH)

    create_google_cal_event(
        events_list,
        calendar,
        anthropic_api_key=ANTHROPIC_API_KEY,
        claude_model=CLAUDE_MODEL,
        preferences=_load_preferences(),
    )
    print('Done.')


if __name__ == '__main__':
    main()
