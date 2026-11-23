# HMS Mini Registry

A small practice project that mimics a hospital quality registry. All data is dummy.

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

## Issues I ran into and how I fixed them

**1. Export script crashed on an empty export**
After I deleted the bad response, the script failed with `_csv.Error: Could not determine delimiter`.
LimeSurvey returns a file with only the header row when there is nothing new, and my code tried to detect the delimiter from that.
Fix: if the file has fewer than 2 lines, print "No new responses" and stop. Otherwise pick the delimiter (`;` or `,`) by counting them in the header row.

**2. Failed check looked like "nothing happened"**
I entered a response with hospital ID 99, which does not exist. The script printed "Checks failed, nothing was loaded" and the row count stayed at 8. That is the intended behavior, but I first checked the wrong thing (a count query on the database, not the script).
Fix: I removed the bad response in LimeSurvey and reran the script.

**3. Django admin would not open**
`http://127.0.0.1:8000/admin/` did not load because the development server was not running (`python manage.py runserver`). Also, the seeded users `alice` and `bob` are not staff, so they cannot log in to the admin.
Fix: start the server and create an admin account with `python manage.py createsuperuser`.

**4. Several Python installs on my PC**
`where python` showed three Pythons. I created the virtual environment using the full path to Python 3.13 so the project uses the right one.

**5. Migration order matters (found while testing)**
Running `migrate cases 0002` on its own left Django's built-in user table only partly migrated, and the seed command failed with a "last_login" not-null error.
Fix: run `python manage.py migrate auth` first, then `migrate cases 0002`.

**6. Django version and Python 3.13**
I use Django 5.2 because older versions do not officially support Python 3.13. In that version `CheckConstraint` uses `condition=` instead of `check=`.

## How I tested it
- `python manage.py test` runs 4 tests: a user sees only their own hospital's cases, a logged-out user is blocked, a user with no hospital sees nothing, and a discharge before arrival is rejected by the database.
- I removed the hospital filter once to confirm the access test fails without it.
- I entered a response with a non-existent hospital to confirm the export script's checks block it.
- Before the backfill, `abx_within_3h` was false for all 600 seeded cases. After the backfill, the counts matched the antibiotic times, and true plus false added up to 600.

## What I would improve next
- Alert or email when the export checks fail
- Run the export on a schedule (cron or Airflow)
- Re-pull responses that were edited after they were first loaded
- Add a GitHub Actions workflow that runs the tests on every push
- Run the Django app in Docker as well
- Keep the 3-hour rule in one place (it is in both the migration and the script)

## Notes
- All data is dummy. No real patient or hospital information is used.
