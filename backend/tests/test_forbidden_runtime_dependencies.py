"""Ensure forbidden runtime dependencies do not leak into production source.

Forbidden dependencies (Phase 1 skeleton):
- deepface
- FaceAnalysis
- paddle
- nvidia.dali / DALI
- cv2.VideoCapture
- CPUExecutionProvider
- Old-repo absolute runtime paths (e.g. /home/user/...)

Only production source under backend/src and native/{include,src} is scanned.
Test tooling, docs, and reference scripts are intentionally excluded.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

FORBIDDEN_TOKENS = [
    "deepface",
    "FaceAnalysis",
    "paddle",
    "nvidia.dali",
    "DALI",
    "cv2.VideoCapture",
    "CPUExecutionProvider",
]

ABSOLUTE_PATH_PATTERN = re.compile(r"/home/user/")


def _production_source_files() -> list[Path]:
    files: list[Path] = []
    for ext in ("*.py", "*.pyi"):
        files.extend((REPO_ROOT / "backend" / "src").rglob(ext))
    for pattern in ("*.cpp", "*.cc", "*.c", "*.h", "*.hpp"):
        files.extend((REPO_ROOT / "native" / "include").rglob(pattern))
        files.extend((REPO_ROOT / "native" / "src").rglob(pattern))
    return files


def _check_forbidden_token(file_path: Path, token: str, source: str) -> list[str]:
    pattern = re.compile(re.escape(token), re.IGNORECASE)
    matches: list[str] = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        if pattern.search(line):
            matches.append(f"{file_path}:{line_number}: {line.strip()}")
    return matches


def test_forbidden_runtime_dependencies_absent():
    violations: list[str] = []
    for file_path in _production_source_files():
        source = file_path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            violations.extend(_check_forbidden_token(file_path, token, source))
        for line_number, line in enumerate(source.splitlines(), start=1):
            if ABSOLUTE_PATH_PATTERN.search(line):
                violations.append(f"{file_path}:{line_number}: {line.strip()}")

    if violations:
        message = "Forbidden runtime dependencies or absolute paths found:\n" + "\n".join(
            f"  - {v}" for v in violations
        )
        raise AssertionError(message)
