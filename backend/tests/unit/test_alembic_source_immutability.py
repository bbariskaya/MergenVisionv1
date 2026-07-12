from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_SOURCE = REPO_ROOT / "backend" / "alembic" / "versions" / "0001_phase1_schema.py"


def test_initial_revision_source_is_independent_of_orm_metadata() -> None:
    assert MIGRATION_SOURCE.exists()
    source = MIGRATION_SOURCE.read_text()
    forbidden = ["Base.metadata", "create_all", "drop_all"]
    for token in forbidden:
        assert token not in source, f"Migration source must not contain {token!r}"


def test_initial_revision_uses_explicit_alembic_operations() -> None:
    source = MIGRATION_SOURCE.read_text()
    required = [
        "op.create_table",
        "op.create_index",
        "op.drop_table",
    ]
    for token in required:
        assert token in source, f"Migration source must contain {token!r}"
