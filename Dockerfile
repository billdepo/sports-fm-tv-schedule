FROM python:3.9-alpine

ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Athens

RUN apk add --no-cache tzdata

WORKDIR /home/sport-fm-app/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Run at 08:00 Athens time daily
RUN echo "0 8 * * * cd /home/sport-fm-app && python scrape.py >> /var/log/sport-fm.log 2>&1" \
    > /etc/crontabs/root

CMD ["crond", "-f", "-d", "8"]
