import pytest
from qa_companion.core import (
    ValidationError,
    compute_metrics,
    validate_feedback,
    validate_session,
    validate_tester,
)


def test_rejects_invalid_google_account():
    with pytest.raises(ValidationError, match='valid email'):
        validate_tester({
            'display_name': 'Tester',
            'google_account': 'not-an-email',
            'country': 'KE',
            'device_model': 'Phone',
            'android_version': '14',
            'start_date': '2026-09-01',
        })


def test_session_must_be_inside_14_day_window():
    with pytest.raises(ValidationError, match='14-day window'):
        validate_session(
            {
                'session_date': '2026-09-15',
                'duration_minutes': '5',
                'features_used': 'login',
            },
            '2026-09-01',
        )


def test_session_requires_meaningful_feature_text():
    with pytest.raises(ValidationError, match='features_used'):
        validate_session(
            {
                'session_date': '2026-09-03',
                'duration_minutes': '5',
                'features_used': '  ',
            },
            '2026-09-01',
        )


def test_feedback_requires_minimum_detail():
    with pytest.raises(ValidationError, match='at least 20'):
        validate_feedback({
            'checkpoint': 'day4',
            'submitted_on': '2026-09-04',
            'summary': 'fine',
        })


def test_metrics_require_eight_days_both_feedback_and_opt_in():
    tester = {
        'start_date': '2026-09-01',
        'opted_in': 1,
        'active': 1,
    }
    sessions = [
        {
            'session_date': f'2026-09-{d:02d}',
            'duration_minutes': 5,
        }
        for d in range(1, 9)
    ]
    issues = [{'severity': 'medium'}]
    feedback = [
        {'checkpoint': 'day4'},
        {'checkpoint': 'day14'},
    ]

    metrics = compute_metrics(tester, sessions, issues, feedback)

    assert metrics['unique_session_days'] == 8
    assert metrics['total_minutes'] == 40
    assert metrics['issue_count'] == 1
    assert metrics['complete'] is True


def test_metrics_not_complete_if_opted_out():
    tester = {
        'start_date': '2026-09-01',
        'opted_in': 0,
        'active': 1,
    }
    sessions = [
        {
            'session_date': f'2026-09-{d:02d}',
            'duration_minutes': 5,
        }
        for d in range(1, 9)
    ]
    feedback = [
        {'checkpoint': 'day4'},
        {'checkpoint': 'day14'},
    ]

    assert compute_metrics(tester, sessions, [], feedback)['complete'] is False