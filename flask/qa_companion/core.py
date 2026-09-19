import re
from datetime import date, timedelta

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
SEVERITIES = {'low', 'medium', 'high', 'critical'}
CHECKPOINTS = {'day4', 'day14'}


class ValidationError(ValueError):
    pass


def parse_iso_date(value: str, field='date') -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError(f'{field} must use YYYY-MM-DD format.')


def validate_tester(data):
    required = ['display_name', 'google_account', 'country', 'device_model', 'android_version', 'start_date']
    missing = [k for k in required if not str(data.get(k, '')).strip()]
    if missing:
        raise ValidationError('Missing required fields: ' + ', '.join(missing))
    email = data['google_account'].strip()
    if not EMAIL_RE.match(email):
        raise ValidationError('Google account must be a valid email address.')
    start = parse_iso_date(data['start_date'], 'start_date')
    return {**data, 'google_account': email, 'start_date': start.isoformat()}


def validate_session(data, start_date, max_minutes=180):
    session_date = parse_iso_date(data.get('session_date'), 'session_date')
    start = parse_iso_date(start_date, 'start_date')
    end = start + timedelta(days=13)
    if not start <= session_date <= end:
        raise ValidationError(f'session_date must fall within the 14-day window ({start} through {end}).')
    try:
        duration = int(data.get('duration_minutes', 0))
    except (TypeError, ValueError):
        raise ValidationError('duration_minutes must be an integer.')
    if not 1 <= duration <= max_minutes:
        raise ValidationError(f'duration_minutes must be between 1 and {max_minutes}.')
    features = str(data.get('features_used', '')).strip()
    if not features:
        raise ValidationError('features_used is required so the session is meaningful evidence.')
    return {
        'session_date': session_date.isoformat(),
        'duration_minutes': duration,
        'features_used': features,
        'notes': str(data.get('notes', '')).strip(),
    }


def validate_issue(data):
    severity = str(data.get('severity', '')).lower().strip()
    if severity not in SEVERITIES:
        raise ValidationError('severity must be one of: low, medium, high, critical.')
    required = ['reported_on', 'title', 'steps', 'expected', 'actual', 'reproducible']
    missing = [k for k in required if not str(data.get(k, '')).strip()]
    if missing:
        raise ValidationError('Missing required issue fields: ' + ', '.join(missing))
    reported_on = parse_iso_date(data['reported_on'], 'reported_on')
    return {k: str(data[k]).strip() for k in required} | {
        'reported_on': reported_on.isoformat(),
        'severity': severity,
    }


def validate_feedback(data):
    checkpoint = str(data.get('checkpoint', '')).lower().strip()
    if checkpoint not in CHECKPOINTS:
        raise ValidationError('checkpoint must be day4 or day14.')
    submitted_on = parse_iso_date(data.get('submitted_on'), 'submitted_on')
    summary = str(data.get('summary', '')).strip()
    if len(summary) < 20:
        raise ValidationError('summary must be at least 20 characters so the feedback is useful.')
    return {
        'checkpoint': checkpoint,
        'submitted_on': submitted_on.isoformat(),
        'summary': summary,
        'confusing': str(data.get('confusing', '')).strip(),
        'bugs': str(data.get('bugs', '')).strip(),
    }


def compute_metrics(tester, sessions, issues, feedback):
    start = parse_iso_date(tester['start_date'])
    end = start + timedelta(days=13)
    unique_days = len({s['session_date'] for s in sessions})
    total_minutes = sum(int(s['duration_minutes']) for s in sessions)
    severity_counts = {key: 0 for key in sorted(SEVERITIES)}
    for item in issues:
        severity_counts[item['severity']] = severity_counts.get(item['severity'], 0) + 1
    checkpoints = {f['checkpoint'] for f in feedback}
    required_sessions_met = unique_days >= 8
    complete = required_sessions_met and {'day4', 'day14'}.issubset(checkpoints) and bool(tester['opted_in'])
    return {
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
        'unique_session_days': unique_days,
        'session_target': 8,
        'remaining_session_days': max(0, 8 - unique_days),
        'total_minutes': total_minutes,
        'issue_count': len(issues),
        'severity_counts': severity_counts,
        'day4_feedback': 'day4' in checkpoints,
        'day14_feedback': 'day14' in checkpoints,
        'opted_in': bool(tester['opted_in']),
        'active': bool(tester['active']),
        'complete': complete,
    }