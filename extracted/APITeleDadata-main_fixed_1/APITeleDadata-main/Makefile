PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

.PHONY: install run-prod run-telebot test

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run-prod:
	$(PY) bot.py

test:
	$(PY) -m pytest -q

run-telebot:
	$(PY) bot_telebot.py
