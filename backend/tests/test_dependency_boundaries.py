"""Enforce the architecture import-direction rules for production source."""

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "src" / "mergenvision"
INTERNAL_PREFIX = "mergenvision"

LAYER_ORDER = ("domain", "ports", "application", "infrastructure", "api")

FORBIDDEN = {
    "domain": {"application", "ports", "infrastructure", "api"},
    "ports": {"application", "infrastructure", "api"},
    "application": {"infrastructure", "api"},
    "api": {"infrastructure", "domain"},
    "infrastructure": {"application", "api"},
    "config": set(),
}


def _layer_from_module(module_path: str) -> str | None:
    parts = module_path.split(".")
    try:
        return parts[1] if parts[0] == "mergenvision" and len(parts) >= 2 else None
    except Exception:
        return None


def _resolve_import(module_file: Path, node: ast.Import | ast.ImportFrom) -> list[str]:
    """Return fully-qualified internal import module names referenced by *node*."""
    results: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            results.append(alias.name)
    elif isinstance(node, ast.ImportFrom):
        if node.module is None:
            return results
        base = node.module
        if node.level:
            relative_to_pkg = module_file.relative_to(PACKAGE_ROOT)
            parts = list(relative_to_pkg.with_suffix("").parts)
            module_parts = parts if parts[-1] != "__init__" else parts[:-1]
            base_parts = (
                module_parts[: -(node.level - 1)] if node.level > 1 else module_parts
            )
            if base:
                base_parts = list(base_parts) + [base]
            resolved = ".".join(base_parts)
        else:
            resolved = base
        results.append(resolved)
        for alias in node.names:
            if alias.name[0].isupper():
                continue
            results.append(f"{resolved}.{alias.name}")
    return results


def _production_files() -> list[Path]:
    return [p for p in PACKAGE_ROOT.rglob("*.py") if "__pycache__" not in p.parts]


def _file_to_module(file_path: Path) -> str:
    rel = file_path.relative_to(PACKAGE_ROOT)
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return f"{INTERNAL_PREFIX}." + ".".join(parts)


def _collect_violations_for_file(file_path: Path, source: str | None = None) -> list[str]:
    module_name = _file_to_module(file_path)
    layer = _layer_from_module(module_name)
    if layer is None:
        return []
    forbidden = FORBIDDEN.get(layer, set())
    if not forbidden:
        return []

    src = source if source is not None else file_path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(file_path))

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            for imported in _resolve_import(file_path, node):
                if not imported.startswith(INTERNAL_PREFIX):
                    continue
                imported_layer = _layer_from_module(imported)
                if imported_layer in forbidden:
                    violations.append(
                        f"{module_name} ({layer}) imports {imported} ({imported_layer})"
                    )
    return violations


def test_dependency_direction_rules():
    violations: list[str] = []
    for file_path in _production_files():
        violations.extend(_collect_violations_for_file(file_path))

    if violations:
        message = "Dependency direction violations found:\n" + "\n".join(
            f"  - {v}" for v in violations
        )
        raise AssertionError(message)


@pytest.mark.parametrize(
    ("layer", "forbidden_target"),
    [
        ("domain", "application"),
        ("domain", "ports"),
        ("domain", "infrastructure"),
        ("ports", "application"),
        ("ports", "infrastructure"),
        ("application", "infrastructure"),
        ("application", "api"),
        ("infrastructure", "application"),
        ("infrastructure", "api"),
        ("api", "infrastructure"),
        ("api", "domain"),
    ],
)
def test_dependency_violations_are_detected(layer: str, forbidden_target: str):
    synthetic_file = PACKAGE_ROOT / layer / "negative_test.py"
    source = f"import mergenvision.{forbidden_target}\n"
    violations = _collect_violations_for_file(synthetic_file, source)

    assert len(violations) == 1
    assert forbidden_target in violations[0]
    assert layer in violations[0]
