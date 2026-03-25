"""Automated checks for the Intro to PostgreSQL assignment (GitHub Classroom)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import psycopg
import pytest
from psycopg import errors

from tests.sql_runner import run_select_file, run_sql_file

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "schema"
QUERIES_DIR = REPO_ROOT / "student_queries"

CREATE_TABLES_SQL = SCHEMA_DIR / "01_create_tables.sql"
SEED_DATA_SQL = SCHEMA_DIR / "02_seed_data.sql"


EXPECTED_RESOURCES: list[tuple] = [
    (1, "Community Food Pantry", "Food", "100 Main St", "pantry@example.org"),
    (2, "Harbor Health Clinic", "Healthcare", "200 Bay Rd", "intake@harborhealth.example"),
    (3, "Riverside Family Shelter", "Housing", "45 River Ave", "frontdesk@riverside.example"),
    (4, "Open Hands Legal Aid", "Legal", "88 Court St", "help@openhands.example"),
    (5, "Job Ready Training Center", "Education", "12 Workshop Ln", "info@jobready.example"),
]

EXPECTED_REFERRALS: list[tuple] = [
    (1, "Miguel", 1, date(2026, 1, 10), "Needs weekly groceries"),
    (2, "Nishit", 1, date(2026, 1, 12), "Returning family"),
    (3, "Esther", 2, date(2026, 1, 15), "New patient intake"),
    (4, "Emilio", 3, date(2026, 2, 1), "Temporary housing"),
    (5, "Dominic", 3, date(2026, 2, 5), "Follow-up visit"),
    (6, "Lucas", 5, date(2026, 2, 20), "Career counseling"),
]


def _reset_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS referrals CASCADE;")
        cur.execute("DROP TABLE IF EXISTS resources CASCADE;")
    conn.commit()


def _apply_schema_and_seed(conn) -> None:
    run_sql_file(conn, CREATE_TABLES_SQL)
    run_sql_file(conn, SEED_DATA_SQL)


def _fetch_all(conn, sql: str) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(sql)
        return list(cur.fetchall())


def _fetch_one(conn, sql: str) -> tuple:
    rows = _fetch_all(conn, sql)
    assert len(rows) == 1, f"Expected exactly 1 row for probe query, got {len(rows)}: {sql}"
    return rows[0]


def test_foreign_key_constraint_is_enforced(db_conn):
    """
    referrals.resource_id must reference resources.id.
    Inserting a non-existent resource_id should fail with a foreign key violation.
    """
    _reset_schema(db_conn)
    _apply_schema_and_seed(db_conn)
    with pytest.raises(errors.ForeignKeyViolation):
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO referrals (family_name, resource_id, referral_date, notes)
                VALUES ('StudentTest', 99999, DATE '2026-03-01', 'should fail');
                """,
            )
        db_conn.commit()
    db_conn.rollback()


def test_not_null_constraint_on_resources_name(db_conn):
    """
    resources.name is required (NOT NULL).

    Students must add NOT NULL to resources.name in 01_create_tables.sql.
    """
    _reset_schema(db_conn)
    run_sql_file(db_conn, CREATE_TABLES_SQL)
    with pytest.raises(errors.NotNullViolation):
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO resources (category, address, contact_email)
                VALUES ('Food', '1 Test St', 'noop@example.org');
                """,
            )
        db_conn.commit()
    db_conn.rollback()


def test_referrals_table_has_foreign_key_metadata(db_conn):
    _reset_schema(db_conn)
    run_sql_file(db_conn, CREATE_TABLES_SQL)
    row = _fetch_one(
        db_conn,
        """
        SELECT COUNT(*)::int
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'referrals'
          AND constraint_type = 'FOREIGN KEY';
        """,
    )
    assert row[0] >= 1, (
        "Expected at least one FOREIGN KEY constraint on public.referrals. "
        "Double-check referrals.resource_id REFERENCES resources(id) in 01_create_tables.sql.",
    )


def test_seed_data_matches_assignment_story(db_conn):
    _reset_schema(db_conn)
    _apply_schema_and_seed(db_conn)

    resources = _fetch_all(db_conn, "SELECT id, name, category, address, contact_email FROM resources ORDER BY id;")
    assert resources == EXPECTED_RESOURCES, (
        "resources table does not match the required seed rows. "
        "Copy the exact values from schema/02_seed_data.sql into your INSERT statements."
    )

    referrals = _fetch_all(
        db_conn,
        "SELECT id, family_name, resource_id, referral_date, notes FROM referrals ORDER BY id;",
    )
    assert referrals == EXPECTED_REFERRALS, (
        "referrals table does not match the required seed rows. "
        "Re-read the table in schema/02_seed_data.sql and insert all six rows with correct ids."
    )


def test_query_01_returns_all_resources_ordered(db_conn):
    _reset_schema(db_conn)
    _apply_schema_and_seed(db_conn)

    colnames, rows = run_select_file(db_conn, QUERIES_DIR / "01_get_all_resources.sql")
    expected_cols = {"id", "name", "category", "address", "contact_email"}
    assert rows == EXPECTED_RESOURCES, (
        "01_get_all_resources.sql should return all five resources with every column, ordered by id ascending. "
        f"Expected {EXPECTED_RESOURCES}, got {rows}."
    )
    assert expected_cols.issubset(set(colnames)), (
        f"01_get_all_resources.sql should select all resource columns. Missing: "
        f"{expected_cols - set(colnames)}. Found columns: {colnames}"
    )


def test_query_02_filters_food_category_only(db_conn):
    _reset_schema(db_conn)
    _apply_schema_and_seed(db_conn)

    _, rows = run_select_file(db_conn, QUERIES_DIR / "02_filter_food_resources.sql")
    expected = [EXPECTED_RESOURCES[0]]
    assert rows == expected, (
        "02_filter_food_resources.sql should return only the Food pantry row (category must match exactly 'Food'), "
        f"ordered by id. Expected {expected}, got {rows}."
    )


def test_query_03_case_insensitive_name_search(db_conn):
    _reset_schema(db_conn)
    _apply_schema_and_seed(db_conn)

    colnames, rows = run_select_file(db_conn, QUERIES_DIR / "03_search_name.sql")
    assert {"id", "name", "category"} == set(colnames), (
        "03_search_name.sql must return columns id, name, category (in any order in results, but names must match). "
        f"Got columns: {colnames}"
    )
    rows_by_id = sorted(rows, key=lambda r: r[colnames.index("id")])
    expected = [(1, "Community Food Pantry", "Food")]
    simplified = []
    for r in rows_by_id:
        d = dict(zip(colnames, r))
        simplified.append((d["id"], d["name"], d["category"]))
    assert simplified == expected, (
        "03_search_name.sql should perform a case-insensitive search that finds the pantry row "
        "(name contains 'pantry'). "
        f"Expected {expected}, got {simplified}."
    )


def test_query_04_join_returns_family_and_resource_name(db_conn):
    _reset_schema(db_conn)
    _apply_schema_and_seed(db_conn)

    colnames, rows = run_select_file(db_conn, QUERIES_DIR / "04_referrals_with_resource_names.sql")
    assert ["family_name", "resource_name"] == colnames, (
        "04_referrals_with_resource_names.sql must alias columns exactly as "
        "`family_name` and `resource_name` (in that order). "
        f"Got: {colnames}"
    )
    expected = [
        ("Miguel", "Community Food Pantry"),
        ("Nishit", "Community Food Pantry"),
        ("Esther", "Harbor Health Clinic"),
        ("Emilio", "Riverside Family Shelter"),
        ("Dominic", "Riverside Family Shelter"),
        ("Lucas", "Job Ready Training Center"),
    ]
    assert rows == expected, (
        "04_referrals_with_resource_names.sql should JOIN referrals to resources and ORDER BY referrals.id. "
        f"Expected {expected}, got {rows}."
    )


def test_query_05_counts_include_zero_referrals(db_conn):
    _reset_schema(db_conn)
    _apply_schema_and_seed(db_conn)

    colnames, rows = run_select_file(db_conn, QUERIES_DIR / "05_count_referrals_per_resource.sql")
    assert ["resource_id", "resource_name", "referral_count"] == colnames, (
        "05_count_referrals_per_resource.sql must return columns "
        "`resource_id`, `resource_name`, and `referral_count` (in that order). "
        f"Got: {colnames}"
    )

    normalized = [(int(r[0]), r[1], int(r[2])) for r in rows]
    expected = [
        (1, "Community Food Pantry", 2),
        (2, "Harbor Health Clinic", 1),
        (3, "Riverside Family Shelter", 2),
        (4, "Open Hands Legal Aid", 0),
        (5, "Job Ready Training Center", 1),
    ]
    assert normalized == expected, (
        "05_count_referrals_per_resource.sql should include all resources and count referrals per resource "
        "(Legal should be 0). ORDER BY resource_id. "
        f"Expected {expected}, got {normalized}."
    )
