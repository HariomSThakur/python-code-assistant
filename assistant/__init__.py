"""Python Code Assistant application package."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Flask, jsonify, request

from .db import init_db


def create_app(test_config: dict | None = None) -> Flask:
    """Build the Flask app and initialize its local SQLite database."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    repository_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        instance_path=str(repository_root / "instance"),
        instance_relative_config=True,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    production = os.environ.get("APP_ENV", "development").lower() == "production"
    secret = os.environ.get("SECRET_KEY")
    if production and (not secret or len(secret) < 32 or "replace" in secret.lower()):
        raise RuntimeError("Set SECRET_KEY to a private random value of at least 32 characters before production.")

    app.config.update(
        SECRET_KEY=secret or secrets.token_hex(32),
        MAX_CONTENT_LENGTH=64 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
        PERMANENT_SESSION_LIFETIME=60 * 60 * 12,
        ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME"),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD"),
        DATABASE=os.environ.get("DATABASE_PATH"),
    )
    if test_config:
        app.config.update(test_config)

    from .routes import api

    app.register_blueprint(api)
    init_db(app)

    @app.errorhandler(413)
    def request_too_large(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Request is too large."}), 413
        return "Request is too large.", 413

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
        )
        return response

    return app
