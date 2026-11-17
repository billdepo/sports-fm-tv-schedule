# Το 3.9 έφτασε EOL τον Οκτ 2025. Το slim (Debian) αντί για alpine γλιτώνει
# compile από source για τα google/anthropic wheels στο ARM του Raspberry Pi.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Athens

# procps δίνει ps/pgrep: χωρίς αυτά δεν μπορείς να ελέγξεις αν τρέχει το cron
# μέσα στο container, πράγμα που κάνει τη διάγνωση στο Pi δυσανάλογα δύσκολη.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata cron procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/sport-fm-app/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Τρέχει στις 08:00 ώρα Αθήνας. Τα αρχεία στο /etc/cron.d θέλουν πεδίο χρήστη,
# mode 0644, και όνομα χωρίς τελεία (αλλιώς το cron τα αγνοεί σιωπηλά).
RUN chmod +x docker/entrypoint.sh docker/run-job.sh \
    && echo "0 8 * * * root /home/sport-fm-app/docker/run-job.sh >> /var/log/sport-fm.log 2>&1" \
       > /etc/cron.d/sport-fm \
    && chmod 0644 /etc/cron.d/sport-fm \
    && touch /var/log/sport-fm.log

CMD ["./docker/entrypoint.sh"]
