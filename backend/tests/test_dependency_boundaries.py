"""Enforce the architecture import-direction rules for production source.

Rules:
- domain      -> must NOT import application, infrastructure, api
- ports       -> must NOT import infrastructure
- application -> must NOT import concrete infrastructure
- api         -> must NOT import infrastructure, domain
- config      -> no restriction (shared configuration constants)
- infrastructure -> allowed to implement ports/api contracts; must NOT import api
"""

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "src" / "mergenvision"
INTERNAL_PREFIX = "mergenvision"

LAYER_ORDER = ("domain", "ports", "application", "infrastructure", "api")

FORBIDDEN = {
    "domain": {"application", "infrastructure", "api"},
    "ports": {"infrastructure"},
    "application": {"infrastructure"},
    "api": {"infrastructure", "domain"},
    "infrastructure": {"api"},
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
            # Compute the package context of the importing file.
            relative_to_pkg = module_file.relative_to(PACKAGE_ROOT)
            parts = list(relative_to_pkg.with_suffix("").parts)
            # The file's own module path is e.g. mergenvision.domain.__init__
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
        # Also include imported submodules (e.g. from mergenvision import domain)
        for alias in node.names:
            if alias.name[0].isupper():
                continue  # likely a class, not a package
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


def test_dependency_direction_rules():
    violations: list[str] = []
    for file_path in _production_files():
        module_name = _file_to_module(file_path)
        layer = _layer_from_module(module_name)
        if layer is None:
            continue
        forbidden = FORBIDDEN.get(layer, set())
        if not forbidden:
            continue

        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for imported in _resolve_import(file_path, node):
                    if not imported.startswith(INTERNAL_PREFIX):
                        continue
                    imported_layer = _layer_from_module(imported)
                    if imported_layer in forbidden:
                        violations.append(
                            f"{module_name} ({layer}) imports {imported} ({imported_layer})"
                        )

    if violations:
        message = "Dependency direction violations found:\n" + "\n".join(
            f"  - {v}" for v in violations
        )
        raise AssertionError(message)
