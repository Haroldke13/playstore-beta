# Local QA Data Retention and Deletion Policy

## Data collected

The companion can store a tester's display name, Google account email, country, device model, Android version, test dates, manual session notes, issue reports, and checkpoint feedback in a local SQLite database.

## Purpose limitation

Use the data only to coordinate the closed test, prepare the tester's QA handoff, and resolve reported defects. Do not reuse the Google account email for marketing, unrelated profiling, or new projects without separate permission.

## Storage

The default deployment is local. The SQLite database lives under `instance/` and is excluded from Git. Do not commit real tester records, exported handoff files containing personal data, or screenshots that expose a Google account.

## Retention

Recommended default: retain personal QA records only until the client confirms receipt and any payment/dispute window requiring evidence has ended, then delete within 30 days. If the client contract or applicable law requires a different period, document that period before collection.

## Deletion

The Flask report page provides a purge action requiring the exact confirmation word `DELETE`. Because foreign keys use `ON DELETE CASCADE`, deleting the tester removes linked sessions, issues, and feedback from the local database. Backups and copied exports must be deleted separately.

## Portfolio rule

Portfolio artifacts must use only synthetic/demo data. Never publish a real tester's Google account, device identifier, private opt-in link, or target-app confidential information.