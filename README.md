# HMS Mini Registry

A small practice project that mimics a hospital quality registry. All data is fake.

## What it does
- Collects sepsis case data through a LimeSurvey form
- A Python script pulls new responses through the RemoteControl API, runs three checks, and loads them into PostgreSQL
- A Django + REST API app serves each hospital only its own cases

## Stack
Python 3.13, Django 5.2, Django REST Framework, PostgreSQL 16, LimeSurvey 6, Docker Compose

## Run it
1. `docker compose up -d`
2. `python -m venv .venv`, activate it, then `pip install -r requirements.txt`
3. `python manage.py migrate auth`, then `python manage.py migrate cases 0002`
4. `python manage.py seed_cases`, then `python manage.py migrate` (runs the backfill)
5. Build the survey in LimeSurvey (fields below), set `LS_SURVEY_ID` in `.env`
6. `python scripts/export_limesurvey.py`
7. `python manage.py test`

## Design notes
- Migrations 0002 to 0004 add a column in three steps: nullable, backfill, then required
- Row-level access: users only see their own hospital (tested)
- Export script: staging table, three checks (row count, duplicates, required fields and known hospitals), then upsert

## Survey fields
hospitalId, arrivalTime, abxGiven, abxTime (shown only if abxGiven = Y), hypotension, dischargeTime (must not be before arrival)

## Known limits
Only completed new responses are loaded; no failure alerts; fake data only.
