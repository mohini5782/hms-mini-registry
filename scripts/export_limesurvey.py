import base64
import csv
import io
import os
import sys

import psycopg
import requests
from dotenv import load_dotenv

load_dotenv()

LS_URL = os.getenv('LS_URL', 'http://localhost:8080/index.php/admin/remotecontrol')
LS_USER = os.getenv('LS_USER', 'admin')
LS_PASSWORD = os.getenv('LS_PASSWORD', 'admin_pw_123')
SURVEY_ID = int(os.getenv('LS_SURVEY_ID', '0'))
DB_DSN = os.getenv('REGISTRY_DSN', 'postgresql://registry:registry_pw@localhost:5433/registry')

STAGE_SQL = """
create temp table stg_responses (
    response_id int,
    hospital_id int,
    arrival_time timestamp,
    abx_time timestamp,
    hypotension text,
    discharge_time timestamp
) on commit drop
"""

MERGE_SQL = """
insert into cases_sepsiscase
    (source_response_id, hospital_id, arrival_time, first_antibiotic_time,
     hypotension, discharge_time, abx_within_3h)
select response_id, hospital_id, arrival_time, abx_time,
       hypotension = 'Y', discharge_time,
       coalesce(abx_time - arrival_time <= interval '3 hours', false)
from stg_responses
on conflict (source_response_id) do update set
    hospital_id = excluded.hospital_id,
    arrival_time = excluded.arrival_time,
    first_antibiotic_time = excluded.first_antibiotic_time,
    hypotension = excluded.hypotension,
    discharge_time = excluded.discharge_time,
    abx_within_3h = excluded.abx_within_3h
"""


def rpc(method, *params):
    resp = requests.post(
        LS_URL,
        json={'method': method, 'params': list(params), 'id': 1},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get('error'):
        raise RuntimeError(f'{method} failed: {body["error"]}')
    return body['result']


def fetch_rows(after_id):
    key = rpc('get_session_key', LS_USER, LS_PASSWORD)
    if isinstance(key, dict):
        raise RuntimeError(f'login failed: {key}')
    try:
        result = rpc(
            'export_responses', key, SURVEY_ID,
            'csv', None, 'complete', 'code', 'short', after_id + 1,
        )
    finally:
        rpc('release_session_key', key)

    if isinstance(result, dict):
        # LimeSurvey sends a status message instead of data when nothing matches
        print('No new responses:', result.get('status'))
        return []

    text = base64.b64decode(result).decode('utf-8-sig')
    lines = text.strip().splitlines()
    if len(lines) < 2:
        # header row only, so nothing new to load
        print('No new responses')
        return []

    delim = ';' if lines[0].count(';') > lines[0].count(',') else ','
    return list(csv.DictReader(io.StringIO(text), delimiter=delim))


def blank_to_none(value):
    value = (value or '').strip()
    return value or None


def clean(row):
    hosp = blank_to_none(row['hospitalId'])
    return (
        int(row['id']),
        int(float(hosp)) if hosp else None,
        blank_to_none(row['arrivalTime']),
        blank_to_none(row['abxTime']),
        blank_to_none(row['hypotension']),
        blank_to_none(row['dischargeTime']),
    )


def run_checks(cur, exported_n):
    problems = []

    staged_n = cur.execute('select count(*) from stg_responses').fetchone()[0]
    if staged_n != exported_n:
        problems.append(f'row count: exported {exported_n}, staged {staged_n}')

    dupes = cur.execute(
        'select count(*) - count(distinct response_id) from stg_responses'
    ).fetchone()[0]
    if dupes:
        problems.append(f'{dupes} duplicate response ids')

    bad = cur.execute("""
        select count(*)
        from stg_responses s
        left join cases_hospital h on h.id = s.hospital_id
        where s.hospital_id is null or s.arrival_time is null
           or s.hypotension is null or h.id is null
    """).fetchone()[0]
    if bad:
        problems.append(f'{bad} rows with missing required fields or an unknown hospital')

    return problems


def main():
    if not SURVEY_ID:
        sys.exit('Set LS_SURVEY_ID in your .env file')

    with psycopg.connect(DB_DSN) as conn:
        cur = conn.cursor()
        last_id = cur.execute(
            'select coalesce(max(source_response_id), 0) from cases_sepsiscase'
        ).fetchone()[0]

        raw_rows = fetch_rows(last_id)
        if not raw_rows:
            return
        rows = [clean(r) for r in raw_rows]

        cur.execute(STAGE_SQL)
        cur.executemany('insert into stg_responses values (%s, %s, %s, %s, %s, %s)', rows)

        problems = run_checks(cur, len(rows))
        if problems:
            print('Checks failed, nothing was loaded:')
            for p in problems:
                print(' -', p)
            sys.exit(1)

        cur.execute(MERGE_SQL)
        print(f'Loaded {len(rows)} responses (after response id {last_id})')


if __name__ == '__main__':
    main()