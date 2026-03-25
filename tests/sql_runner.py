"""Small helpers to execute multi-statement SQL files against PostgreSQL (psycopg v3)."""

from __future__ import annotations

from pathlib import Path


def split_sql_statements(sql: str) -> list[str]:
    """
    Split SQL text on semicolons, respecting single-quoted strings and `--` line comments.

    This is sufficient for the simple, beginner-authored SQL in this assignment.
    """
    statements: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(sql)
    in_single_quote = False

    def flush() -> None:
        text = "".join(buf).strip()
        buf.clear()
        if text:
            statements.append(text)

    while i < n:
        ch = sql[i]
        if not in_single_quote:
            if ch == "-" and i + 1 < n and sql[i + 1] == "-":
                while i < n and sql[i] != "\n":
                    i += 1
                continue
            if ch == "'":
                in_single_quote = True
                buf.append(ch)
                i += 1
                continue
            if ch == ";":
                flush()
                i += 1
                continue
        else:
            buf.append(ch)
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    buf.append(sql[i + 1])
                    i += 2
                    continue
                in_single_quote = False
            i += 1
            continue
        buf.append(ch)
        i += 1

    flush()
    return statements


def run_sql_file(conn, path: Path) -> None:
    """Execute every non-empty statement in a .sql file (DDL/DML)."""
    text = path.read_text(encoding="utf-8")
    statements = split_sql_statements(text)
    if not statements:
        raise ValueError(
            f"{path.name} does not contain any executable SQL yet. "
            "Did you remove the TODO placeholders without adding statements?",
        )
    with conn.cursor() as cur:
        for stmt in statements:
            cur.execute(stmt)
    conn.commit()


def run_select_file(conn, path: Path) -> tuple[list[str], list[tuple]]:
    """
    Execute statements in order; the final statement must be a SELECT that returns rows.

    If a file contains only one statement, it must be that SELECT.
    """
    text = path.read_text(encoding="utf-8")
    statements = split_sql_statements(text)
    if not statements:
        raise ValueError(
            f"{path.name} does not contain any SQL yet. Add your SELECT where the TODO says so.",
        )
    colnames: list[str] = []
    rows: list[tuple] = []
    with conn.cursor() as cur:
        for stmt in statements[:-1]:
            cur.execute(stmt)
        cur.execute(statements[-1])
        if cur.description is None:
            raise AssertionError(
                f"{path.name}: final SQL statement must be a SELECT that returns columns. "
                "Tests expect a query result set.",
            )
        colnames = [c.name for c in cur.description]
        rows = list(cur.fetchall())
    conn.rollback()
    return colnames, rows
