"""JSON API for authentication, assistant actions, projects, and admin tools."""

from __future__ import annotations

import ast
import json
import re
import secrets
import sqlite3
import time
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .llm import ModelError, ask_model, model_status
from .services import process_action

api = Blueprint("api", __name__)
MAX_INPUT_CHARS = 20_000
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
VALID_ACTIONS = {"generate", "review", "fix", "error_explain", "program_explain"}


def _json_error(message: str, status: int):
    return jsonify({"error": message}), status


def _body() -> dict:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


@api.before_app_request
def validate_csrf_header():
    if not request.path.startswith("/api/") or request.method not in UNSAFE_METHODS:
        return None
    expected = session.get("csrf_token")
    received = request.headers.get("X-CSRF-Token", "")
    if not expected or not secrets.compare_digest(expected, received):
        return _json_error("Your session token expired. Refresh the page and try again.", 400)
    return None


def current_user():
    if "current_user" not in g:
        user_id = session.get("user_id")
        g.current_user = (
            get_db().execute(
                "SELECT id, username, role, created_at FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if user_id
            else None
        )
        if user_id and g.current_user is None:
            session.clear()
    return g.current_user


def login_required(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return _json_error("Sign in to continue.", 401)
        return function(*args, **kwargs)

    return wrapped


def admin_required(function):
    @wraps(function)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user()["role"] != "admin":
            return _json_error("Administrator access is required.", 403)
        return function(*args, **kwargs)

    return wrapped


def _csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def _user_json(user) -> dict | None:
    if user is None:
        return None
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


@api.get("/")
def home():
    return render_template("index.html")


@api.get("/api/session")
def session_info():
    return jsonify(
        {
            "user": _user_json(current_user()),
            "csrf_token": _csrf_token(),
            "model": model_status(),
        }
    )


def _valid_login_ip(ip: str) -> bool:
    count = get_db().execute(
        "SELECT COUNT(*) AS total FROM login_attempts "
        "WHERE ip_address = ? AND succeeded = 0 "
        "AND created_at >= datetime('now', '-15 minutes')",
        (ip,),
    ).fetchone()["total"]
    return count < 10


@api.post("/api/register")
def register():
    payload = _body()
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", username):
        return _json_error("Use a username with 3–32 letters, numbers, dots, underscores, or hyphens.", 400)
    if not 10 <= len(password) <= 128:
        return _json_error("Choose a password between 10 and 128 characters.", 400)

    connection = get_db()
    try:
        cursor = connection.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        connection.rollback()
        return _json_error("That username is already in use.", 409)

    session.clear()
    session["user_id"] = cursor.lastrowid
    session.permanent = True
    return jsonify({"user": _user_json(current_user()), "csrf_token": _csrf_token()}), 201


@api.post("/api/login")
def login():
    payload = _body()
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    ip_address = request.remote_addr or "unknown"
    connection = get_db()
    connection.execute("DELETE FROM login_attempts WHERE created_at < datetime('now', '-1 day')")
    connection.commit()

    if not _valid_login_ip(ip_address):
        return _json_error("Too many sign-in attempts. Wait 15 minutes, then try again.", 429)

    user = connection.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = ? COLLATE NOCASE",
        (username,),
    ).fetchone()
    valid = bool(user and check_password_hash(user["password_hash"], password))
    if not valid:
        connection.execute("INSERT INTO login_attempts (ip_address, succeeded) VALUES (?, 0)", (ip_address,))
        connection.commit()
        return _json_error("Username or password is incorrect.", 401)

    connection.execute("DELETE FROM login_attempts WHERE ip_address = ?", (ip_address,))
    connection.commit()
    session.clear()
    session["user_id"] = user["id"]
    session.permanent = True
    return jsonify({"user": _user_json(current_user()), "csrf_token": _csrf_token()})


@api.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True, "csrf_token": _csrf_token()})


def _enabled_examples() -> list[dict]:
    rows = get_db().execute(
        "SELECT id, title, keywords_json, description, code FROM examples WHERE enabled = 1 ORDER BY title"
    ).fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "keywords": json.loads(row["keywords_json"]),
            "description": row["description"],
            "code": row["code"],
        }
        for row in rows
    ]


def _record_usage(user_id, action, mode, input_length, success, duration_ms):
    connection = get_db()
    connection.execute(
        "INSERT INTO usage_events (user_id, action, mode, input_length, success, duration_ms) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, action, mode, input_length, int(success), duration_ms),
    )
    connection.commit()


def _model_rate_limit(user_id: int) -> str | None:
    count = get_db().execute(
        "SELECT "
        "SUM(CASE WHEN created_at >= datetime('now', '-1 minute') THEN 1 ELSE 0 END) AS minute_count, "
        "SUM(CASE WHEN created_at >= datetime('now', '-1 day') THEN 1 ELSE 0 END) AS day_count "
        "FROM usage_events WHERE user_id = ? "
        "AND mode IN ('ollama', 'openai', 'ollama_error', 'openai_error')",
        (user_id,),
    ).fetchone()
    if (count["minute_count"] or 0) >= 8:
        return "minute"
    if (count["day_count"] or 0) >= 100:
        return "day"
    return None


def _extract_python(text: str) -> str:
    match = re.search(r"```(?:python|py)?\s*\n?(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else text.strip()


@api.post("/api/assist")
@login_required
def assist():
    payload = _body()
    action = str(payload.get("action", ""))
    text = str(payload.get("text", ""))
    level = str(payload.get("level", "beginner"))
    use_model = bool(payload.get("use_model", False))
    if action not in VALID_ACTIONS:
        return _json_error("Choose a supported assistant action.", 400)
    if not text.strip():
        return _json_error("Enter a prompt or paste Python code first.", 400)
    if len(text) > MAX_INPUT_CHARS:
        return _json_error(f"Keep input under {MAX_INPUT_CHARS:,} characters.", 413)
    if level not in {"beginner", "intermediate", "advanced"}:
        level = "beginner"

    started = time.perf_counter()
    user_id = current_user()["id"]
    if use_model:
        rate_limit = _model_rate_limit(user_id)
        if rate_limit == "minute":
            return _json_error("Model limit reached for this minute. Wait a moment and try again.", 429)
        if rate_limit == "day":
            return _json_error("Daily model request limit reached. Try again tomorrow.", 429)
    try:
        if use_model:
            result = ask_model(action, text, level)
            output = result["text"]
            syntax_valid = None
            if action == "generate":
                try:
                    ast.parse(_extract_python(output))
                    syntax_valid = True
                except SyntaxError:
                    syntax_valid = False
            _record_usage(user_id, action, result["provider"], len(text), True, result["duration_ms"])
            return jsonify(
                {
                    "output": output,
                    "mode": result["provider"],
                    "model": result["model"],
                    "syntax_valid": syntax_valid,
                    "usage": result["usage"],
                }
            )

        output = process_action(action, text, level, examples=_enabled_examples())
        duration_ms = round((time.perf_counter() - started) * 1000)
        _record_usage(user_id, action, "local", len(text), True, duration_ms)
        return jsonify({"output": output, "mode": "local", "model": None, "syntax_valid": None})
    except ModelError as error:
        provider = model_status()["provider"]
        _record_usage(user_id, action, f"{provider}_error", len(text), False, round((time.perf_counter() - started) * 1000))
        return _json_error(str(error), 503)
    except Exception:
        current_app.logger.exception("Assistant action failed (%s); source text omitted.", action)
        mode = f"{model_status()['provider']}_error" if use_model else "error"
        _record_usage(user_id, action, mode, len(text), False, round((time.perf_counter() - started) * 1000))
        return _json_error("The assistant could not complete that request. Try a shorter input.", 500)


@api.get("/api/projects")
@login_required
def list_projects():
    rows = get_db().execute(
        "SELECT p.id, p.name, p.created_at, COUNT(s.id) AS snippet_count "
        "FROM projects p LEFT JOIN snippets s ON s.project_id = p.id "
        "WHERE p.user_id = ? GROUP BY p.id ORDER BY p.created_at DESC",
        (current_user()["id"],),
    ).fetchall()
    return jsonify({"projects": [dict(row) for row in rows]})


@api.post("/api/projects")
@login_required
def create_project():
    name = str(_body().get("name", "")).strip()
    if not name or len(name) > 80:
        return _json_error("Project names must contain 1–80 characters.", 400)
    connection = get_db()
    try:
        cursor = connection.execute("INSERT INTO projects (user_id, name) VALUES (?, ?)", (current_user()["id"], name))
        connection.commit()
    except sqlite3.IntegrityError:
        connection.rollback()
        return _json_error("You already have a project with that name.", 409)
    return jsonify({"id": cursor.lastrowid, "name": name}), 201


@api.delete("/api/projects/<int:project_id>")
@login_required
def delete_project(project_id: int):
    connection = get_db()
    cursor = connection.execute(
        "DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, current_user()["id"])
    )
    connection.commit()
    if cursor.rowcount == 0:
        return _json_error("Project not found.", 404)
    return jsonify({"ok": True})


@api.get("/api/projects/<int:project_id>/snippets")
@login_required
def list_snippets(project_id: int):
    connection = get_db()
    owns_project = connection.execute(
        "SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, current_user()["id"])
    ).fetchone()
    if not owns_project:
        return _json_error("Project not found.", 404)
    rows = connection.execute(
        "SELECT id, project_id, title, code, created_at, updated_at FROM snippets "
        "WHERE project_id = ? AND user_id = ? ORDER BY updated_at DESC",
        (project_id, current_user()["id"]),
    ).fetchall()
    return jsonify({"snippets": [dict(row) for row in rows]})


@api.post("/api/projects/<int:project_id>/snippets")
@login_required
def save_snippet(project_id: int):
    payload = _body()
    title = str(payload.get("title", "")).strip()
    code = str(payload.get("code", ""))
    if not title or len(title) > 120:
        return _json_error("Snippet titles must contain 1–120 characters.", 400)
    if not code.strip() or len(code) > MAX_INPUT_CHARS:
        return _json_error(f"Code must contain text and stay under {MAX_INPUT_CHARS:,} characters.", 400)
    connection = get_db()
    owns_project = connection.execute(
        "SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, current_user()["id"])
    ).fetchone()
    if not owns_project:
        return _json_error("Project not found.", 404)
    cursor = connection.execute(
        "INSERT INTO snippets (user_id, project_id, title, code) VALUES (?, ?, ?, ?)",
        (current_user()["id"], project_id, title, code),
    )
    connection.commit()
    return jsonify({"id": cursor.lastrowid, "title": title}), 201


@api.delete("/api/snippets/<int:snippet_id>")
@login_required
def delete_snippet(snippet_id: int):
    connection = get_db()
    cursor = connection.execute(
        "DELETE FROM snippets WHERE id = ? AND user_id = ?", (snippet_id, current_user()["id"])
    )
    connection.commit()
    if cursor.rowcount == 0:
        return _json_error("Snippet not found.", 404)
    return jsonify({"ok": True})


@api.get("/api/admin/summary")
@admin_required
def admin_summary():
    connection = get_db()
    totals = connection.execute(
        "SELECT (SELECT COUNT(*) FROM users) AS users, "
        "(SELECT COUNT(*) FROM projects) AS projects, "
        "(SELECT COUNT(*) FROM snippets) AS snippets, "
        "(SELECT COUNT(*) FROM usage_events WHERE created_at >= datetime('now', '-7 days')) AS requests_7d"
    ).fetchone()
    modes = connection.execute(
        "SELECT mode, COUNT(*) AS requests, SUM(success) AS successes "
        "FROM usage_events WHERE created_at >= datetime('now', '-7 days') GROUP BY mode ORDER BY requests DESC"
    ).fetchall()
    actions = connection.execute(
        "SELECT action, COUNT(*) AS requests, SUM(success) AS successes "
        "FROM usage_events WHERE created_at >= datetime('now', '-7 days') GROUP BY action ORDER BY requests DESC"
    ).fetchall()
    users = connection.execute(
        "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    return jsonify(
        {
            "totals": dict(totals),
            "modes_7d": [dict(row) for row in modes],
            "actions_7d": [dict(row) for row in actions],
            "users": [dict(row) for row in users],
        }
    )


def _clean_keywords(value) -> list[str]:
    if isinstance(value, str):
        raw = value.split(",")
    elif isinstance(value, list):
        raw = value
    else:
        raw = []
    return list(dict.fromkeys(item.strip().lower() for item in raw if isinstance(item, str) and item.strip()))[:20]


@api.get("/api/admin/examples")
@admin_required
def admin_examples():
    rows = get_db().execute("SELECT * FROM examples ORDER BY title").fetchall()
    return jsonify(
        {
            "examples": [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "keywords": json.loads(row["keywords_json"]),
                    "description": row["description"],
                    "code": row["code"],
                    "enabled": bool(row["enabled"]),
                }
                for row in rows
            ]
        }
    )


@api.post("/api/admin/examples")
@admin_required
def create_example():
    payload = _body()
    title = str(payload.get("title", "")).strip()
    keywords = _clean_keywords(payload.get("keywords"))
    description = str(payload.get("description", "")).strip()
    code = str(payload.get("code", ""))
    if not title or len(title) > 100 or not keywords or len(code) > MAX_INPUT_CHARS or not code.strip():
        return _json_error("Provide a title, at least one keyword, and code under the input limit.", 400)
    try:
        ast.parse(code)
    except SyntaxError as error:
        return _json_error(f"The example has a syntax error on line {error.lineno}: {error.msg}.", 400)
    connection = get_db()
    cursor = connection.execute(
        "INSERT INTO examples (title, keywords_json, description, code) VALUES (?, ?, ?, ?)",
        (title, json.dumps(keywords), description[:300], code),
    )
    connection.commit()
    return jsonify({"id": cursor.lastrowid}), 201


@api.put("/api/admin/examples/<int:example_id>")
@admin_required
def update_example(example_id: int):
    payload = _body()
    title = str(payload.get("title", "")).strip()
    keywords = _clean_keywords(payload.get("keywords"))
    description = str(payload.get("description", "")).strip()
    code = str(payload.get("code", ""))
    enabled = int(bool(payload.get("enabled", True)))
    if not title or len(title) > 100 or not keywords or not code.strip() or len(code) > MAX_INPUT_CHARS:
        return _json_error("Provide a title, at least one keyword, and code under the input limit.", 400)
    try:
        ast.parse(code)
    except SyntaxError as error:
        return _json_error(f"The example has a syntax error on line {error.lineno}: {error.msg}.", 400)
    connection = get_db()
    cursor = connection.execute(
        "UPDATE examples SET title = ?, keywords_json = ?, description = ?, code = ?, enabled = ?, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (title, json.dumps(keywords), description[:300], code, enabled, example_id),
    )
    connection.commit()
    if cursor.rowcount == 0:
        return _json_error("Example not found.", 404)
    return jsonify({"ok": True})


@api.delete("/api/admin/examples/<int:example_id>")
@admin_required
def delete_example(example_id: int):
    connection = get_db()
    cursor = connection.execute("DELETE FROM examples WHERE id = ?", (example_id,))
    connection.commit()
    if cursor.rowcount == 0:
        return _json_error("Example not found.", 404)
    return jsonify({"ok": True})


@api.patch("/api/admin/users/<int:user_id>/role")
@admin_required
def update_user_role(user_id: int):
    role = _body().get("role")
    if role not in {"user", "admin"}:
        return _json_error("Role must be 'user' or 'admin'.", 400)
    connection = get_db()
    target = connection.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        return _json_error("User not found.", 404)
    if target["role"] == "admin" and role == "user":
        admin_count = connection.execute("SELECT COUNT(*) AS total FROM users WHERE role = 'admin'").fetchone()["total"]
        if admin_count <= 1:
            return _json_error("Keep at least one administrator account.", 400)
    connection.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    connection.commit()
    return jsonify({"ok": True})
