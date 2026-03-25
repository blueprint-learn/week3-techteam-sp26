"""Pytest fixtures and shared test setup for the Week 3 PostgreSQL workshop."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        pytest.fail(
            f"Missing environment variable {name}. Copy `.env.example` to `.env`, "
            "start Postgres with Docker Compose, then retry `pytest -q`.",
        )
    return value


@pytest.fixture(scope="session")
def db_config() -> dict[str, str | int]:
    return {
        "host": _require_env("POSTGRES_HOST"),
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        "dbname": _require_env("POSTGRES_DB"),
        "user": _require_env("POSTGRES_USER"),
        "password": _require_env("POSTGRES_PASSWORD"),
    }


@pytest.fixture
def db_conn(db_config):
    try:
        conn = psycopg.connect(
            host=db_config["host"],
            port=db_config["port"],
            dbname=db_config["dbname"],
            user=db_config["user"],
            password=db_config["password"],
            autocommit=False,
        )
    except psycopg.OperationalError as exc:
        pytest.fail(
            "Could not connect to PostgreSQL. Common fixes:\n"
            "  - Run: docker compose up -d\n"
            "  - Wait a few seconds for the database to become ready\n"
            "  - Confirm `.env` matches `docker-compose.yml`\n"
            f"Original error: {exc}",
        )
    try:
        yield conn
    finally:
        conn.close()
