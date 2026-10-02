"""SQLite schema and connection helpers for the assistant."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


DEFAULT_EXAMPLES = [
    {
        "title": "Fibonacci sequence",
        "keywords": ["fibonacci", "fibonacci sequence"],
        "description": "Generate the first n Fibonacci numbers.",
        "code": (
            "def fibonacci(count):\n"
            "    if count < 0:\n"
            "        raise ValueError('count must be non-negative')\n"
            "    values = []\n"
            "    first, second = 0, 1\n"
            "    for _ in range(count):\n"
            "        values.append(first)\n"
            "        first, second = second, first + second\n"
            "    return values\n\n"
            "print(fibonacci(10))\n"
        ),
    },
    {
        "title": "FizzBuzz",
        "keywords": ["fizzbuzz", "fizz buzz"],
        "description": "Print FizzBuzz values from 1 through 100.",
        "code": (
            "for number in range(1, 101):\n"
            "    if number % 15 == 0:\n"
            "        print('FizzBuzz')\n"
            "    elif number % 3 == 0:\n"
            "        print('Fizz')\n"
            "    elif number % 5 == 0:\n"
            "        print('Buzz')\n"
            "    else:\n"
            "        print(number)\n"
        ),
    },
    {
        "title": "Remove duplicates",
        "keywords": ["remove duplicates", "unique list"],
        "description": "Return unique values while preserving their order.",
        "code": (
            "def unique_in_order(values):\n"
            "    return list(dict.fromkeys(values))\n\n"
            "print(unique_in_order([1, 2, 1, 3, 2]))\n"
        ),
    },
]


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

CREATE TABLE IF NOT EXISTS snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    code TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    keywords_json TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    code TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    mode TEXT NOT NULL,
    input_length INTEGER NOT NULL DEFAULT 0,
    success INTEGER NOT NULL DEFAULT 1 CHECK (success IN (0, 1)),
    duration_ms INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    succeeded INTEGER NOT NULL DEFAULT 0 CHECK (succeeded IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_snippets_project ON snippets(project_id);
CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_events(created_at);
CREATE INDEX IF NOT EXISTS idx_login_ip_time ON login_attempts(ip_address, created_at);
"""


def connect_db() -> sqlite3.Connection:
    connection = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect_db()
    return g.db


def close_db(_error: BaseException | None = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db(app) -> None:
    configured_path = app.config.get("DATABASE") or os.environ.get("DATABASE_PATH")
    if configured_path:
        database_path = Path(configured_path).expanduser()
        if not database_path.is_absolute():
            database_path = Path(app.instance_path) / database_path
    else:
        database_path = Path(app.instance_path) / "assistant.sqlite3"

    database_path.parent.mkdir(parents=True, exist_ok=True)
    app.config["DATABASE"] = str(database_path)
    app.teardown_appcontext(close_db)

    with app.app_context():
        connection = connect_db()
        try:
            connection.executescript(SCHEMA)
            seed_examples(connection)
            seed_admin(connection, app.config.get("ADMIN_USERNAME"), app.config.get("ADMIN_PASSWORD"))
            connection.commit()
        finally:
            connection.close()


def seed_examples(connection: sqlite3.Connection) -> None:
    if connection.execute("SELECT 1 FROM examples LIMIT 1").fetchone():
        return
    connection.executemany(
        "INSERT INTO examples (title, keywords_json, description, code) VALUES (?, ?, ?, ?)",
        [
            (item["title"], json.dumps(item["keywords"]), item["description"], item["code"])
            for item in DEFAULT_EXAMPLES
        ],
    )


def seed_admin(connection: sqlite3.Connection, username: str | None, password: str | None) -> None:
    if not username and not password:
        return
    if not username or not password or len(password) < 12:
        raise RuntimeError("Set both ADMIN_USERNAME and ADMIN_PASSWORD; the password must be at least 12 characters.")

    existing = connection.execute(
        "SELECT id FROM users WHERE username = ? COLLATE NOCASE", (username,)
    ).fetchone()
    if existing:
        connection.execute("UPDATE users SET role = 'admin' WHERE id = ?", (existing["id"],))
    else:
        connection.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
            (username, generate_password_hash(password)),
        )
