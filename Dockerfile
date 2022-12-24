FROM python:3.9-alpine

ENV PYTHONUNBUFFERED 1

COPY . /home/sport-fm-app/
WORKDIR /home/sport-fm-app/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt
