import os

import urllib.request
from bs4 import BeautifulSoup
from gcsa.google_calendar import GoogleCalendar
from calendar_utils import create_google_cal_event


def main() -> None:
    # get environment variables
    URL = os.environ.get('URL_TO_SCRAPE')
    CALENDAR_ID = os.environ.get('CALENDAR_ID')
    CREDENTIALS_JSON_PATH = os.environ.get('CREDENTIALS_JSON_PATH')

    if not URL:
        raise ValueError('No value given for the URL_TO_SCRAPE environment variable')

    # open a connection to a URL using urllib
    with urllib.request.urlopen(URL) as web_url:

        # get the request's response code
        response_code = web_url.getcode()
        if response_code != 200:
            raise Exception(f'3rd party server error {URL}')

        # read the data from the URL
        html_data = web_url.read()
        decoded_html_data = html_data.decode("utf-8")

    # parse HTML document with BeautifulSoup
    soup = BeautifulSoup(decoded_html_data, features="html.parser")

    # populate a list of event tuples from the HTML parsing
    events_list = []
    for event in soup.find_all("div", {"class": "column is-7"}):
        title = event.find("h3", {"class": "semiblack-c zonasemibold font-size-24 minus-2 lin1"}).string.strip()
        tournament = event.find("p", {"class": "font-size-16"}).string
        tv_channel = event.find("span", {"class": "post-category lightred-c zonanormal"}).string
        time = event.find("time").string
        events_list.append((title, tournament, tv_channel, time))

    # create google calendar object
    calendar = GoogleCalendar(default_calendar=CALENDAR_ID,
                              credentials_path=CREDENTIALS_JSON_PATH)

    create_google_cal_event(events_list, calendar)
    print('Successfully created one event!')


if __name__ == '__main__':
    main()
