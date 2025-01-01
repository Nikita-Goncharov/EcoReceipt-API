FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# RUN sudo apt install libpq-dev python3-dev -y

RUN apt-get update -y && apt-get install libgl1 libpq-dev libglib2.0-0 -y
RUN pip install --upgrade pip setuptools wheel
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .


