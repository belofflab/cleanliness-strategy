from pathlib import Path
import re


def test_alembic_revision_ids_fit_version_table_limit():
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    revision_pattern = re.compile(r'^revision:\s*str\s*=\s*"([^"]+)"', re.MULTILINE)

    for migration_file in sorted(versions_dir.glob("*.py")):
        content = migration_file.read_text(encoding="utf-8")
        match = revision_pattern.search(content)
        assert match is not None, f"No revision id found in {migration_file.name}"
        assert len(match.group(1)) <= 32, (
            f"Revision id in {migration_file.name} exceeds 32 chars: {match.group(1)}"
        )