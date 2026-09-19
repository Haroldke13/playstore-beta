# Google Play Closed-Test QA Companion

A small, runnable Flask application for organizing **real human Android closed-test evidence** across a 14-day engagement. It records consented tester/device metadata, genuine-use session summaries, issues, day-4/day-14 feedback, opt-in continuity, and exportable QA evidence.

It does **not** automate Google Play usage, emulate devices, fake tester engagement, or certify production-access eligibility. The actual Play track, target application, physical Android device, and client-side analytics remain external dependencies.

## Why this repository exists

The posted engagement requires a real tester to remain enrolled for 14 consecutive days, use the app on at least 8 days, and send useful feedback twice. This repository converts those operational requirements into a reproducible manual-QA workflow so the tester can avoid missed days, vague bug reports, and incomplete handoff evidence.

## Features

- Tester profile with Google account, country, physical-device model, Android version, start date, and consent timestamp.
- One evidence summary per test day to discourage inflated activity logging.
- 14-day date-window validation and configurable maximum session duration.
- Structured bug reports: severity, steps, expected, actual, reproducibility.
- Day-4/day-14 feedback with upsert behaviour so corrections do not create duplicates.
- Dashboard metrics calculated from stored records: unique session days, remaining target days, minutes, issues, feedback state, opt-in state.
- CSV and JSON handoff exports.
- Purge action with confirmation plus cascade deletion.
- Seeded synthetic demo generator and reproducible evidence export.
- Automated pytest coverage of successful and failing cases.

## Repository layout

```text
.
├── app.py
├── qa_companion/
│   ├── __init__.py
│   ├── core.py
│   ├── db.py
│   ├── routes.py
│   └── schema.py
├── templates/
├── static/
├── scripts/
│   ├── generate_demo_data.py
│   └── export_demo_evidence.py
├── tests/
├── compliance/
├── docs/
├── portfolio/
├── outputs/
├── data/
├── requirements.txt
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.10+
- pip
- No paid API or external service is required for the companion itself.
- For a real client test: a client-provided private Play opt-in link, the eligible physical Android device, and the participant's normal Google account.

## Installation

```bash
git clone <repository>
cd google_play_closed_test_qa_companion
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`.

## Configuration

`.env.example` documents optional settings. The basic local app works without a `.env` loader because values can be exported by the shell.

```bash
export SECRET_KEY='replace-with-random-value'
export DATABASE_PATH="$PWD/instance/qa_companion.sqlite3"
export PORT=5000
python app.py
```

For production deployment, run behind a proper WSGI server, use HTTPS, restrict access, set a strong secret key, protect the host filesystem, and define an explicit backup/deletion policy. This repository intentionally does not include public-cloud deployment credentials.

## Generate deterministic demo data

The demo is synthetic and exists only to validate and showcase the workflow.

```bash
python scripts/generate_demo_data.py --database instance/demo.sqlite3
DATABASE_PATH="$PWD/instance/demo.sqlite3" python app.py
```

The seeded demo creates 8 session days, 1 synthetic issue, and both feedback checkpoints.

## Export demo evidence

```bash
python scripts/export_demo_evidence.py --database instance/demo.sqlite3 --output outputs
```

Generated files:

- `outputs/demo_handoff.json`
- `outputs/demo_sessions.csv`
- `outputs/demo_evidence_summary.md`

The export note explicitly labels the records synthetic.

## Verify repository integrity

```bash
python scripts/verify_repository.py
```

This checks required files, compiles Python sources, validates generated demo invariants when present, and scans for a small set of obvious secret markers.

## Run tests

```bash
pytest -q
```

The suite includes negative cases for invalid email, out-of-window sessions, missing feature evidence, insufficient feedback detail, duplicate day entries, opted-out completion, and unsafe purge confirmation.

## Real engagement workflow

1. Obtain the participant's affirmative consent and record the physical device/OS context.
2. Share the tester's normal Google account with the client privately so it can be allow-listed.
3. Use the client's private Play opt-in link and install the actual closed-test build.
4. Use the app genuinely and log one daily evidence summary on each active test day.
5. File defects using reproducible steps rather than vague comments.
6. Send the day-4 checkpoint feedback.
7. Remain opted in across the full agreed window.
8. Send day-14 feedback and, if useful, export JSON/CSV evidence for the client.
9. Apply the retention/deletion policy after handoff and any applicable dispute window.

## Data expectations

The companion stores personal QA coordination data locally in SQLite. Do not commit the database. Do not use real Google accounts in demo/portfolio material. The `.gitignore` excludes `instance/`, `.env`, and generated outputs containing potential personal data.

## Validation boundaries

This repository can validate its own calculations, forms, persistence, exports, and deletion workflow. It cannot validate the undisclosed target app because no APK, Play test link, app credentials, or client analytics are present. It also cannot perform 14 days of real-world device use inside a code execution environment.

Accordingly, the project exercises **Software Testing**, **Beta Testing process design**, and **Mobile QA evidence management** directly. **Mobile App Testing** and **Interface Testing of the client's app** cannot be truthfully claimed until the target build is available on the real Android device; the included Flask interface itself is route- and form-tested.

## Compliance artifacts

- `compliance/CONSENT_AND_PARTICIPATION.md`
- `compliance/QA_RUBRIC.md`
- `compliance/RETENTION_POLICY.md`

These are part of the operating workflow, not placeholder paperwork.

## Deployment considerations

The default development server is for local use. For multi-user deployment, add authentication/authorization, CSRF protection, encrypted backups, HTTPS, structured access logging that avoids personal content, database migration tooling, and an organization-specific retention schedule. Do not expose the local companion directly to the public internet in its current form.

## License

MIT for the repository code. Client app binaries, private Play links, participant data, and third-party target-app content are not covered by this repository's license.