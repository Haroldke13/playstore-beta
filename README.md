# Playstore Beta

> **For viewing and review only.** A self-directed practice build on synthetic
> data. No client commissioned it, nothing was delivered to anyone, and no real
> person, employer or customer appears in it.
>
> **Comments are encouraged** — open an issue, or comment on any line in a pull
> request.

**Status:** does not start — imports `qa_companion.db`, `qa_companion.schema`, `a Flask application object — nothing here constructs one`, which the answer never wrote. Bundled anyway so the gap is visible.

## Layout

```
flask/          the application — edit here, this is the source of truth
cpanel_extra/   the cPanel-only files the build folds in
build_cpanel.sh regenerates cpanel/ from flask/
cpanel/         GENERATED for hosting. Never edit; it is overwritten.
```

## Run it locally

```bash
cd flask
python3 -m venv .venv
.venv/bin/pip install -r ../cpanel_extra/requirements.txt
.venv/bin/flask --app app:app run
```

## Deploy it

```bash
./build_cpanel.sh --publish      # rebuild, then stage into ~/Desktop/CPANEL/playstore-beta
~/Desktop/CPANEL_PUSH.sh check playstore-beta
```

Then follow [`cpanel/DEPLOY_STEPS.md`](cpanel/DEPLOY_STEPS.md). Intended
subdomain: **playstore-beta.harold-datascience.co.ke**

## Provenance

`flask/` is the application exactly as the model produced it, copied from `CHATGPT_SOLUTIONS/android-beta-tester-for-the-google-play-store-14-ab2057f4bed0/files/` and not edited.

Everything under `cpanel_extra/` and the generated `cpanel/` folder is packaging added so it can be hosted.
