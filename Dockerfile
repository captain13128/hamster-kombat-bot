FROM python:3.9-alpine

WORKDIR /app

ENV PYTHONBUFFERED 1

COPY requirements.txt requirements.txt

RUN apk add --no-cache build-base libffi-dev
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
