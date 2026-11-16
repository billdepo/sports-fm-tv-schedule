#!/bin/sh
# Το cron δεν κληρονομεί το environment του container: ξεκινά τα jobs με ένα
# ελάχιστο env (HOME, PATH, SHELL, LOGNAME) και τίποτα από ό,τι πέρασε το
# docker-compose env_file. Το γράφουμε λοιπόν σε αρχείο που φορτώνει ο wrapper.
#
# Το quoting γίνεται με shlex.quote και όχι με printf, ώστε τιμές με κενά ή
# ειδικούς χαρακτήρες (π.χ. ένα API key με '$') να μη σπάνε το sourcing.
set -e

python - <<'PY' > /etc/sport-fm.env
import os
import shlex

KEYS = (
    "URL_TO_SCRAPE",
    "CALENDAR_ID",
    "CREDENTIALS_JSON_PATH",
    "ANTHROPIC_API_KEY",
    "CLAUDE_MODEL",
    "LOG_LEVEL",
)
for key in KEYS:
    value = os.environ.get(key)
    if value is not None:
        print(f"{key}={shlex.quote(value)}")
PY

chmod 600 /etc/sport-fm.env

missing=""
for key in URL_TO_SCRAPE CALENDAR_ID; do
    grep -q "^${key}=" /etc/sport-fm.env || missing="${missing} ${key}"
done
if [ -n "${missing}" ]; then
    echo "FATAL: λείπουν required env vars:${missing}" >&2
    echo "       Πέρασέ τα μέσω του env_file στο docker-compose.yml." >&2
    exit 1
fi

touch /var/log/sport-fm.log
echo "$(date -Is) entrypoint: cron ξεκινά (TZ=${TZ:-UTC}), επόμενο run στις 08:00"

cron
exec tail -F /var/log/sport-fm.log
