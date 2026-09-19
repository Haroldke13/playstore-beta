import pytest

pytest.importorskip(
    'flask',
    reason='Flask must be installed to execute route tests.',
)

from qa_companion.db import get_db


def create_tester(client):
    return client.post(
        '/tester',
        data={
            'display_name': 'Route Tester',
            'google_account': 'route.tester@example.com',
            'country': 'Kenya',
            'device_model': 'Android Device',
            'android_version': '14',
            'start_date': '2026-09-01',
        },
        follow_redirects=True,
    )


def test_index_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Closed Test QA Companion' in response.data


def test_create_profile_and_report(client):
    response = create_tester(client)
    assert response.status_code == 200
    assert b'Route Tester' in response.data
    assert b'0/8' in response.data


def test_session_and_exports(client, app):
    create_tester(client)

    with app.app_context():
        tester_id = get_db().execute(
            'SELECT id FROM testers'
        ).fetchone()['id']

    response = client.post(
        f'/tester/{tester_id}/session',
        data={
            'session_date': '2026-09-03',
            'duration_minutes': '7',
            'features_used': 'sign in, navigation, settings',
            'notes': 'No crash',
        },
        follow_redirects=True,
    )

    assert b'Session recorded.' in response.data

    csv_response = client.get(f'/tester/{tester_id}/sessions.csv')
    assert csv_response.status_code == 200
    assert b'sign in, navigation, settings' in csv_response.data

    json_response = client.get(f'/tester/{tester_id}/handoff.json')
    assert json_response.status_code == 200
    assert json_response.get_json()['metrics']['unique_session_days'] == 1


def test_duplicate_session_day_is_rejected(client, app):
    create_tester(client)

    with app.app_context():
        tester_id = get_db().execute(
            'SELECT id FROM testers'
        ).fetchone()['id']

    payload = {
        'session_date': '2026-09-03',
        'duration_minutes': '7',
        'features_used': 'feature A',
    }

    client.post(f'/tester/{tester_id}/session', data=payload)

    response = client.post(
        f'/tester/{tester_id}/session',
        data=payload,
        follow_redirects=True,
    )

    assert b'already recorded for that date' in response.data


def test_feedback_upsert(client, app):
    create_tester(client)

    with app.app_context():
        tester_id = get_db().execute(
            'SELECT id FROM testers'
        ).fetchone()['id']

    payload = {
        'checkpoint': 'day4',
        'submitted_on': '2026-09-04',
        'summary': (
            'The core workflow is understandable and completed '
            'without a crash.'
        ),
        'confusing': 'None',
        'bugs': 'None',
    }

    client.post(f'/tester/{tester_id}/feedback', data=payload)

    payload['summary'] = (
        'Updated feedback after retesting the same '
        'core workflow successfully.'
    )

    client.post(f'/tester/{tester_id}/feedback', data=payload)

    with app.app_context():
        count = get_db().execute(
            'SELECT COUNT(*) AS c FROM feedback WHERE tester_id = ?',
            (tester_id,),
        ).fetchone()['c']

        summary = get_db().execute(
            'SELECT summary FROM feedback WHERE tester_id = ?',
            (tester_id,),
        ).fetchone()['summary']

    assert count == 1
    assert summary.startswith('Updated feedback')


def test_purge_requires_exact_confirmation(client, app):
    create_tester(client)

    with app.app_context():
        tester_id = get_db().execute(
            'SELECT id FROM testers'
        ).fetchone()['id']

    response = client.post(
        f'/tester/{tester_id}/purge',
        data={'confirmation': 'delete'},
        follow_redirects=True,
    )

    assert b'Type DELETE exactly' in response.data

    with app.app_context():
        assert get_db().execute(
            'SELECT COUNT(*) AS c FROM testers'
        ).fetchone()['c'] == 1

    client.post(
        f'/tester/{tester_id}/purge',
        data={'confirmation': 'DELETE'},
    )

    with app.app_context():
        assert get_db().execute(
            'SELECT COUNT(*) AS c FROM testers'
        ).fetchone()['c'] == 0