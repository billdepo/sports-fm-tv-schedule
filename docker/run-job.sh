#!/bin/sh
# Τρέχει από το cron. Φορτώνει το env που έγραψε το entrypoint και μετά το script.
set -e

LOG=/var/log/sport-fm.log
MAX_LOG_BYTES=1048576  # 1 MiB -- το Pi γράφει σε κάρτα SD, ο λογαριασμός δεν είναι άπειρος

if [ -f "${LOG}" ] && [ "$(wc -c < "${LOG}")" -gt "${MAX_LOG_BYTES}" ]; then
    mv "${LOG}" "${LOG}.1"
    : > "${LOG}"
fi

set -a
# shellcheck disable=SC1091
[ -f /etc/sport-fm.env ] && . /etc/sport-fm.env
set +a

cd /home/sport-fm-app
exec python scrape.py
