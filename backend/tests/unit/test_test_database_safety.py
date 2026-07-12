import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check_test_database_safety.py"


def _run(url: str, *, allow_destructive: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["MERGENVISION_TEST_DATABASE_URL"] = url
    if allow_destructive:
        env["MERGENVISION_ALLOW_DESTRUCTIVE_TEST_DATABASE"] = "YES"
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_valid_test_prefixed_database_name_passes():
    result = _run("postgresql+asyncpg://user:pass@localhost:5432/test_mergenvision")
    assert result.returncode == 0, result.stderr


def test_valid_test_suffixed_database_name_passes():
    result = _run("postgresql+asyncpg://user:pass@localhost:5432/mergenvision_test")
    assert result.returncode == 0, result.stderr


def test_non_test_database_name_is_rejected():
    result = _run("postgresql+asyncpg://user:pass@localhost:5432/mergenvision")
    assert result.returncode != 0
    assert "test_" in result.stderr or "_test" in result.stderr


def test_non_asyncpg_postgresql_url_is_rejected():
    result = _run("postgresql://user:pass@localhost:5432/test_mergenvision")
    assert result.returncode != 0
    assert "asyncpg" in result.stderr


def test_destructive_override_allows_non_test_name():
    result = _run(
        "postgresql+asyncpg://user:pass@localhost:5432/mergenvision",
        allow_destructive=True,
    )
    assert result.returncode == 0, result.stderr
