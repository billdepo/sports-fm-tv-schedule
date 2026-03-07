# Sports FM TV Schedule → Google Calendar

Scrapes [sport-fm.gr/tv](https://www.sport-fm.gr/tv) daily, φιλτράρει τα events με Claude AI βάσει προσωπικών προτιμήσεων, και δημιουργεί ένα Google Calendar event με τα αθλητικά της ημέρας.

**Example event:**

    Title: Αθλητικά – Παρασκευή 7 Μαρτίου
    Date: Friday, March 7, 09:00 – 09:01
    Description:
    ⚽ 19:45 Arsenal - Manchester City | Champions League, TNT Sports
    🏀 21:00 Ολυμπιακός - Παναθηναϊκός | EuroLeague, Novasports Prime


## Subscribe to the Calendar

Αν δεν θέλεις να τρέξεις το project μόνος σου, μπορείς να κάνεις απευθείας subscribe στο calendar:

👉 [Subscribe στο Google Calendar](https://calendar.google.com/calendar/u/0?cid=NGI4YzBjY2RkMWZmNDM0ZmQzNjg0ZmQ2MTllZTFmZjYyNWE0NTBkNGU1OWI1NzQ1NDkzODgyMjU3MjM5ZTdiOEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t)

---

## Prerequisites

### 1. Google Cloud — OAuth Credentials

1. Πήγαινε στο [console.cloud.google.com](https://console.cloud.google.com)
2. Ενεργοποίησε το **Google Calendar API**: APIs & Services → Enable APIs
3. Δημιούργησε credentials: APIs & Services → Credentials → Create Credentials → **OAuth 2.0 Client ID** (Desktop app)
4. Κατέβασε το JSON → αποθήκευσε ως `.credentials/credentials.json`
5. Πρόσθεσε τον εαυτό σου ως test user στο OAuth consent screen
6. Βρες το **Calendar ID**: Google Calendar → Settings → (επίλεξε ημερολόγιο) → Calendar ID

### 2. Anthropic API Key (προαιρετικό)

Αν θέλεις φιλτράρισμα με Claude AI, δημιούργησε API key στο [console.anthropic.com](https://console.anthropic.com).
Αν δεν οριστεί, το script δημιουργεί event με όλα τα events χωρίς φιλτράρισμα.

### 3. Αρχείο `.env`

Αντέγραψε το `.env.example` σε `.env` και συμπλήρωσε:

```
URL_TO_SCRAPE=https://www.sport-fm.gr/tv
CREDENTIALS_JSON_PATH=.credentials/credentials.json
CALENDAR_ID=your-calendar-id@group.calendar.google.com
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-haiku-4-5
```

### 4. Προτιμήσεις φιλτραρίσματος

Επεξεργάσου το αρχείο `prompts/preferences.txt` με τις διοργανώσεις/ομάδες που σε ενδιαφέρουν.

---

## Local Development

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# ή: venv\Scripts\activate      # Windows

pip install -r requirements.txt
python scrape.py
```

Η πρώτη εκτέλεση ανοίγει browser για OAuth → δημιουργείται `token.pickle` στο `.credentials/`.

---

## Docker (Production — Raspberry Pi)

Το Docker image τρέχει αυτόματα κάθε μέρα στις **08:00 Athens time** (Europe/Athens timezone).

### Setup

```bash
# Clone
git clone https://github.com/<username>/sports-fm-tv-schedule.git
cd sports-fm-tv-schedule

# Αντέγραψε secrets από το laptop
scp .env pi@<RPi-IP>:~/sports-fm-tv-schedule/
scp -r .credentials/ pi@<RPi-IP>:~/sports-fm-tv-schedule/

# Build & start
docker compose up -d --build
```

### Χειροκίνητη εκτέλεση (test)

```bash
docker compose run --rm sport-fm python scrape.py
```

### Logs

```bash
docker compose logs -f
# ή μέσα στο container:
docker exec <container_id> cat /var/log/sport-fm.log
```

---

## Project Structure

```
├── scrape.py           # Entry point — scraping & orchestration
├── calendar_utils.py   # Google Calendar event creation
├── claude_utils.py     # Anthropic API filtering
├── prompts/
│   ├── preferences.txt # Προσωπικές προτιμήσεις (διοργανώσεις, ομάδες)
│   ├── instructions.txt# Prompt template
│   └── system.txt      # System prompt για Claude
├── Dockerfile          # Alpine + crond, τρέχει 08:00 Athens time
├── docker-compose.yml  # Volume mounts για .credentials/
└── .env.example        # Template για environment variables
```
