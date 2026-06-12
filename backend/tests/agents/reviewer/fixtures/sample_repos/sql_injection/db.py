"""Seeded OWASP A03 injection (CWE-89) — for scanner/hard-block demonstration."""

import sqlite3


def find_user(conn: sqlite3.Connection, username: str):
    cursor = conn.cursor()
    # VULNERABLE: user input interpolated directly into SQL (do NOT do this).
    cursor.execute("SELECT * FROM users WHERE name = '%s'" % username)  # noqa: S608
    return cursor.fetchone()
