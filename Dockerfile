# Το 3.9 έφτασε EOL τον Οκτ 2025. Το slim (Debian) αντί για alpine γλιτώνει
# compile από source για τα google/anthropic wheels στο ARM του Raspberry Pi.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Athens

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/sport-fm-app/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Τρέχει στις 08:00 ώρα Αθήνας. Το cron δεν κληρονομεί το environment του
# container, οπότε το γράφουμε σε αρχείο που φορτώνει το wrapper script.
RUN printf '#!/bin/sh\nset -a\n[ -f /etc/sport-fm.env ] && . /etc/sport-fm.env\nset +a\ncd /home/sport-fm-app && exec python scrape.py\n' \
    > /usr/local/bin/run-sportfm \
    && chmod +x /usr/local/bin/run-sportfm \
    && echo "0 8 * * * root /usr/local/bin/run-sportfm >> /var/log/sport-fm.log 2>&1" \
    > /etc/cron.d/sport-fm \
    && chmod 0644 /etc/cron.d/sport-fm \
    && touch /var/log/sport-fm.log

# Το env του container δεν φτάνει στο cron job από μόνο του: το γράφουμε σε
# /etc/sport-fm.env στο boot, και μετά δίνουμε τον έλεγχο στο cron.
CMD ["sh", "-c", "printenv | grep -E '^(URL_TO_SCRAPE|CALENDAR_ID|CREDENTIALS_JSON_PATH|ANTHROPIC_API_KEY|CLAUDE_MODEL|LOG_LEVEL)=' > /etc/sport-fm.env; cron -f & tail -f /var/log/sport-fm.log"]
