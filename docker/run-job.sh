#!/bin/sh
# Τρέχει από το cron. Φορτώνει το env που έγραψε το entrypoint και μετά το script.
set -e

# Το Debian cron ΔΕΝ κληρονομεί το PATH του container -- ορίζει δικό του
# minimal PATH=/usr/bin:/bin. Στα επίσημα python images ο interpreter είναι στο
# /usr/local/bin/python, οπότε ένα γυμνό "python" δίνει "not found" και το job
# πεθαίνει σιωπηλά κάθε πρωί. (Το busybox crond του alpine κληρονομούσε το
# PATH, γι' αυτό δεν φαινόταν πριν τη μετάβαση σε Debian.)
PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin
export PATH

LOG=/var/log/sport-fm.log
MAX_LOG_BYTES=1048576  # 1 MiB -- το Pi γράφει σε κάρτα SD, ο λογαριασμός δεν είναι άπειρος

if [ -f "${LOG}" ] && [ "$(wc -c < "${LOG}")" -gt "${MAX_LOG_BYTES}" ]; then
    mv "${LOG}" "${LOG}.1"
    : > "${LOG}"
fi

# Timestamp σε κάθε run: χωρίς αυτό, μια γραμμή σφάλματος στο log δεν λέει
# πότε (ή αν) πυροδότησε το cron.
echo "=== $(date -Is) run-job: ξεκινά ==="

PYTHON=$(command -v python3 || command -v python || true)
if [ -z "${PYTHON}" ]; then
    echo "FATAL: δεν βρέθηκε python interpreter στο PATH=${PATH}" >&2
    exit 127
fi

set -a
# shellcheck disable=SC1091
[ -f /etc/sport-fm.env ] && . /etc/sport-fm.env
set +a

cd /home/sport-fm-app
exec "${PYTHON}" scrape.py
