#!/usr/bin/env python3
"""Validate MERGENVISION_TEST_DATABASE_URL before destructive migration tests.

Rejects non-PostgreSQL URLs and database names that do not start with ``test_``
or end with ``_test`` unless ``MERGENVISION_ALLOW_DESTRUCTIVE_TEST_DATABASE=YES``
is set explicitly.
"""

import os
import re
import sys
from urllib.parse import urlparse


def _database_name(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path.lstrip("/").split("?")[0]


def validate(url: str, *, allow_destructive: bool = False) -> None:
    if not re.match(r"^postgresql\+asyncpg://", url, re.IGNORECASE):
        raise ValueError(
            "MERGENVISION_TEST_DATABASE_URL must use the asyncpg driver "
            "(e.g., postgresql+asyncpg://...)"
        )

    db_name = _database_name(url)
    if not db_name:
        raise ValueError("MERGENVISION_TEST_DATABASE_URL does not contain a database name")

    if not (db_name.startswith("test_") or db_name.endswith("_test")):
        if not allow_destructive:
            raise ValueError(
                f"Database name '{db_name}' does not start with 'test_' or end with '_test'. "
                "Set MERGENVISION_ALLOW_DESTRUCTIVE_TEST_DATABASE=YES to override."
            )


def main() -> int:
    url = os.environ.get("MERGENVISION_TEST_DATABASE_URL")
    if not url:
        return 0

    allow_destructive = os.environ.get("MERGENVISION_ALLOW_DESTRUCTIVE_TEST_DATABASE") == "YES"
    try:
        validate(url, allow_destructive=allow_destructive)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
