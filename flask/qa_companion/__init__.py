"""Application factory for the Play Store closed-test QA companion.

WRITTEN TO FILL A GAP, 2026-09-20
---------------------------------
`app.py` has always done `from qa_companion import create_app`, but the
package had no `__init__.py`, so the import failed and the application never
started. The signature here is the one app.py already calls: a single
optional mapping of config overrides.
"""
from __future__ import annotations

import os

from flask import Flask

from . import db as _db
from .routes import bp

__all__ = ["create_app"]


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True,
                template_folder="../templates")

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
        DATABASE=os.path.join(app.instance_path, "qa_companion.sqlite3"),
    )
    if config:
        app.config.update(config)

    # instance/ is not in the repo (it holds the database), so create it
    # before SQLite is asked to open a file inside it.
    os.makedirs(os.path.dirname(app.config["DATABASE"]) or ".", exist_ok=True)

    _db.init_app(app)
    _db.init_db(app)          # CREATE TABLE IF NOT EXISTS; no migration step
    app.register_blueprint(bp)
    return app
