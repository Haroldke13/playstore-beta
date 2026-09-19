import csv
import io
import json
from datetime import datetime, timezone
from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from .core import ValidationError, compute_metrics, validate_feedback, validate_issue, validate_session, validate_tester
from .db import get_db

bp = Blueprint('main', __name__)


def _tester_or_404(tester_id):
    row = get_db().execute('SELECT * FROM testers WHERE id = ?', (tester_id,)).fetchone()
    if row is None:
        abort(404)
    return row


def _bundle(tester_id):
    db = get_db()
    tester = _tester_or_404(tester_id)
    sessions = db.execute(
        'SELECT * FROM sessions WHERE tester_id = ? ORDER BY session_date',
        (tester_id,),
    ).fetchall()
    issues = db.execute(
        'SELECT * FROM issues WHERE tester_id = ? ORDER BY reported_on DESC, id DESC',
        (tester_id,),
    ).fetchall()
    feedback = db.execute(
        'SELECT * FROM feedback WHERE tester_id = ? ORDER BY submitted_on',
        (tester_id,),
    ).fetchall()
    metrics = compute_metrics(tester, sessions, issues, feedback)
    return tester, sessions, issues, feedback, metrics


@bp.get('/')
def index():
    db = get_db()
    testers = db.execute('SELECT * FROM testers ORDER BY id DESC').fetchall()
    cards = []
    for tester in testers:
        sessions = db.execute(
            'SELECT * FROM sessions WHERE tester_id = ?',
            (tester['id'],),
        ).fetchall()
        issues = db.execute(
            'SELECT * FROM issues WHERE tester_id = ?',
            (tester['id'],),
        ).fetchall()
        feedback = db.execute(
            'SELECT * FROM feedback WHERE tester_id = ?',
            (tester['id'],),
        ).fetchall()
        cards.append((tester, compute_metrics(tester, sessions, issues, feedback)))
    return render_template('index.html', cards=cards)


@bp.post('/tester')
def add_tester():
    try:
        data = validate_tester(request.form)
        db = get_db()
        cur = db.execute(
            '''INSERT INTO testers
               (display_name, google_account, country, device_model,
                android_version, start_date, consent_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                data['display_name'].strip(),
                data['google_account'],
                data['country'].strip(),
                data['device_model'].strip(),
                data['android_version'].strip(),
                data['start_date'],
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        db.commit()
        flash('Tester profile created.', 'success')
        return redirect(url_for('main.report', tester_id=cur.lastrowid))
    except ValidationError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('main.index'))


@bp.get('/tester/<int:tester_id>')
def report(tester_id):
    tester, sessions, issues, feedback, metrics = _bundle(tester_id)
    return render_template(
        'report.html',
        tester=tester,
        sessions=sessions,
        issues=issues,
        feedback=feedback,
        metrics=metrics,
    )


@bp.post('/tester/<int:tester_id>/session')
def add_session(tester_id):
    tester = _tester_or_404(tester_id)
    try:
        data = validate_session(request.form, tester['start_date'])
        db = get_db()
        db.execute(
            '''INSERT INTO sessions
               (tester_id, session_date, duration_minutes, features_used, notes)
               VALUES (?, ?, ?, ?, ?)''',
            (
                tester_id,
                data['session_date'],
                data['duration_minutes'],
                data['features_used'],
                data['notes'],
            ),
        )
        db.commit()
        flash('Session recorded.', 'success')
    except ValidationError as exc:
        flash(str(exc), 'error')
    except Exception as exc:
        if 'UNIQUE constraint failed' in str(exc):
            flash(
                'A session is already recorded for that date; '
                'one evidence row per day is allowed.',
                'error',
            )
        else:
            raise
    return redirect(url_for('main.report', tester_id=tester_id))


@bp.post('/tester/<int:tester_id>/issue')
def add_issue(tester_id):
    _tester_or_404(tester_id)
    try:
        data = validate_issue(request.form)
        db = get_db()
        db.execute(
            '''INSERT INTO issues
               (tester_id, reported_on, severity, title, steps,
                expected, actual, reproducible)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                tester_id,
                data['reported_on'],
                data['severity'],
                data['title'],
                data['steps'],
                data['expected'],
                data['actual'],
                data['reproducible'],
            ),
        )
        db.commit()
        flash('Issue recorded.', 'success')
    except ValidationError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('main.report', tester_id=tester_id))


@bp.post('/tester/<int:tester_id>/feedback')
def add_feedback(tester_id):
    _tester_or_404(tester_id)
    try:
        data = validate_feedback(request.form)
        db = get_db()
        db.execute(
            '''INSERT INTO feedback
               (tester_id, checkpoint, submitted_on, summary, confusing, bugs)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(tester_id, checkpoint) DO UPDATE SET
                 submitted_on=excluded.submitted_on,
                 summary=excluded.summary,
                 confusing=excluded.confusing,
                 bugs=excluded.bugs''',
            (
                tester_id,
                data['checkpoint'],
                data['submitted_on'],
                data['summary'],
                data['confusing'],
                data['bugs'],
            ),
        )
        db.commit()
        flash(f"{data['checkpoint']} feedback saved.", 'success')
    except ValidationError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('main.report', tester_id=tester_id))


@bp.post('/tester/<int:tester_id>/status')
def update_status(tester_id):
    _tester_or_404(tester_id)
    opted_in = 1 if request.form.get('opted_in') == 'on' else 0
    active = 1 if request.form.get('active') == 'on' else 0
    db = get_db()
    db.execute(
        'UPDATE testers SET opted_in = ?, active = ? WHERE id = ?',
        (opted_in, active, tester_id),
    )
    db.commit()
    flash('Participation status updated.', 'success')
    return redirect(url_for('main.report', tester_id=tester_id))


@bp.get('/tester/<int:tester_id>/handoff.json')
def export_json(tester_id):
    tester, sessions, issues, feedback, metrics = _bundle(tester_id)
    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'tester': dict(tester),
        'metrics': metrics,
        'sessions': [dict(row) for row in sessions],
        'issues': [dict(row) for row in issues],
        'feedback': [dict(row) for row in feedback],
        'notice': (
            'Exported from tester-entered records. '
            'This file does not prove Google Play backend engagement.'
        ),
    }
    body = json.dumps(payload, indent=2)
    return Response(
        body,
        mimetype='application/json',
        headers={
            'Content-Disposition':
                f'attachment; filename=tester-{tester_id}-handoff.json'
        },
    )


@bp.get('/tester/<int:tester_id>/sessions.csv')
def export_csv(tester_id):
    tester, sessions, _issues, _feedback, _metrics = _bundle(tester_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'tester_id',
        'display_name',
        'session_date',
        'duration_minutes',
        'features_used',
        'notes',
    ])
    for row in sessions:
        writer.writerow([
            tester['id'],
            tester['display_name'],
            row['session_date'],
            row['duration_minutes'],
            row['features_used'],
            row['notes'],
        ])
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition':
                f'attachment; filename=tester-{tester_id}-sessions.csv'
        },
    )


@bp.post('/tester/<int:tester_id>/purge')
def purge(tester_id):
    _tester_or_404(tester_id)
    confirmation = request.form.get('confirmation', '')
    if confirmation != 'DELETE':
        flash(
            'Type DELETE exactly to purge this tester and all linked records.',
            'error',
        )
        return redirect(url_for('main.report', tester_id=tester_id))
    db = get_db()
    db.execute('DELETE FROM testers WHERE id = ?', (tester_id,))
    db.commit()
    flash('Tester data purged.', 'success')
    return redirect(url_for('main.index'))