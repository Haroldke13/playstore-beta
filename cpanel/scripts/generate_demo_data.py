import argparse
import sqlite3
import sys
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
from faker import Faker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_companion.schema import SCHEMA


def generate(database_path, seed=2644):
    Faker.seed(seed)
    fake = Faker('en_US')
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(database_path)
    db.execute('PRAGMA foreign_keys = ON')
    db.executescript(SCHEMA)

    start = date.today() - timedelta(days=13)
    db.execute('DELETE FROM testers')

    cur = db.execute(
        '''INSERT INTO testers
           (display_name, google_account, country, device_model,
            android_version, start_date, consent_at, opted_in, active)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)''',
        (
            'Demo Tester',
            fake.email(),
            'Demo Country',
            'Pixel Demo Device',
            '14',
            start.isoformat(),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    tester_id = cur.lastrowid

    session_offsets = [0, 1, 3, 4, 6, 8, 10, 13]
    feature_sets = [
        'onboarding, sign in, home navigation',
        'search, filters, detail view',
        'create flow, validation',
        'settings, notification preferences',
        'offline/online transition',
        'back navigation, rotation check',
        'repeat primary workflow, error recovery',
        'final regression of core flows',
    ]

    for idx, offset in enumerate(session_offsets):
        db.execute(
            '''INSERT INTO sessions
               (tester_id, session_date, duration_minutes, features_used, notes)
               VALUES (?, ?, ?, ?, ?)''',
            (
                tester_id,
                (start + timedelta(days=offset)).isoformat(),
                4 + idx,
                feature_sets[idx],
                'Synthetic demonstration record; not Google Play evidence.',
            ),
        )

    db.execute(
        '''INSERT INTO issues
           (tester_id, reported_on, severity, title, steps,
            expected, actual, reproducible)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            tester_id,
            (start + timedelta(days=4)).isoformat(),
            'medium',
            'Validation message is easy to miss',
            'Open the demo form, submit an invalid value, '
            'observe the top-of-page message.',
            'Validation feedback should remain visually associated '
            'with the failed action.',
            'Message appears at top and can require scrolling '
            'on a small screen.',
            'Always in synthetic QA scenario',
        ),
    )

    db.execute(
        '''INSERT INTO feedback
           (tester_id, checkpoint, submitted_on, summary, confusing, bugs)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (
            tester_id,
            'day4',
            (start + timedelta(days=3)).isoformat(),
            'Core workflows were exercised on multiple days; navigation '
            'was understandable and one validation presentation issue '
            'was recorded.',
            'The validation message location can be easy to overlook '
            'on a smaller display.',
            'No synthetic crashes recorded.',
        ),
    )

    db.execute(
        '''INSERT INTO feedback
           (tester_id, checkpoint, submitted_on, summary, confusing, bugs)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (
            tester_id,
            'day14',
            (start + timedelta(days=13)).isoformat(),
            'Eight distinct usage days were recorded in the demo dataset '
            'and the final regression covered the primary workflow '
            'and recovery paths.',
            'No additional synthetic confusion recorded.',
            'No synthetic crashes recorded.',
        ),
    )

    db.commit()
    db.close()
    return tester_id


def main():
    parser = argparse.ArgumentParser(
        description='Create deterministic synthetic demo data for the QA companion.'
    )
    parser.add_argument('--database', default='instance/demo.sqlite3')
    parser.add_argument('--seed', type=int, default=2644)
    args = parser.parse_args()

    tester_id = generate(Path(args.database), args.seed)
    print(
        f'Created synthetic demo database at '
        f'{args.database} with tester_id={tester_id}'
    )


if __name__ == '__main__':
    main()