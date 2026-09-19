# Case Study — Evidence-Oriented Closed-Test QA Tracking

## Problem

A closed Android beta requires reliable human participation over a fixed 14-day window. The operational risk is not only finding a tester; it is losing continuity, receiving vague feedback, or being unable to show what was actually exercised when the final handoff is due.

## Approach

The solution is a local Flask companion that converts the engagement terms into a structured evidence workflow. A tester profile records device/OS context and affirmative consent. Each genuine-use day receives one session summary with duration and features exercised. Defects use a reproducible template: severity, steps, expected result, actual result, and reproducibility. Day-4 and day-14 feedback are stored as separate checkpoints. A status control records whether the participant reports being still opted in.

The code calculates completion from the local records rather than hard-coding a success badge. The checklist requires eight distinct usage days, both feedback checkpoints, and an opted-in status. Exports are produced directly from the SQLite database.

## Demonstration results

The deterministic demo generator creates **8 distinct session days**, **1 synthetic medium-severity issue**, and **2 feedback checkpoints** across a 14-day window. The export script calculates the metrics from those records and writes JSON, CSV, and Markdown evidence files. These numbers describe the repository's synthetic validation run only; they are not client outcomes or Google Play analytics.

## Validation

The automated test suite covers: invalid Google-account syntax, session dates outside the 14-day window, missing feature evidence, insufficient feedback detail, completion metrics, opted-out state, Flask page loading, profile creation, session recording, JSON/CSV exports, duplicate-session rejection, checkpoint upsert behaviour, and deletion confirmation.

## Limits

The repository cannot perform the client's human test by itself. It has no target APK, private Play opt-in URL, client analytics, or access to a physical device in this environment. It therefore does not claim interface findings about the undisclosed app. Actual mobile/interface testing begins only after the client supplies access and the tester installs the Play-distributed build on the stated physical Android device.