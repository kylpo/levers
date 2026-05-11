"""Sanity checks on schema.yml — must hold for the CLI to behave correctly."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

# We intentionally don't `import yaml` at module level because the testing
# environment uses `uv run --with pytest pytest`. PyYAML is loaded via a
# subprocess invocation through the script under test for the cross-file
# sanity checks; for the in-module tests below we use a small loader.

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema.yml"


@pytest.fixture(scope="module")
def schema() -> dict:
    import yaml  # provided via `uv run --with pytest --with pyyaml`

    with SCHEMA_PATH.open() as f:
        return yaml.safe_load(f)


def test_schema_has_categories_and_levers(schema: dict) -> None:
    assert "categories" in schema
    assert "levers" in schema
    assert len(schema["levers"]) > 0
    assert len(schema["categories"]) > 0


def test_every_lever_has_required_fields(schema: dict) -> None:
    for name, cfg in schema["levers"].items():
        assert "scope" in cfg, f"{name}: missing scope"
        assert cfg["scope"] in ("repo", "package", "either"), f"{name}: bad scope {cfg['scope']}"
        assert "category" in cfg, f"{name}: missing category"
        assert cfg["category"] in schema["categories"], (
            f"{name}: unknown category {cfg['category']}"
        )
        assert "values" in cfg and len(cfg["values"]) >= 2, (
            f"{name}: needs >= 2 enum values"
        )


def test_strictness_lists_match_values(schema: dict) -> None:
    """Every strictness list must be a permutation of the lever's values."""
    for name, cfg in schema["levers"].items():
        order = cfg.get("strictness")
        if order is None:
            continue
        assert set(order) == set(cfg["values"]), (
            f"{name}: strictness {order} != values {cfg['values']}"
        )
        assert len(order) == len(cfg["values"]), f"{name}: strictness has duplicates"


def test_templates_validate_against_schema(schema: dict, tmp_path: Path) -> None:
    """Each template must validate under its matching role."""
    import shutil

    cases = [
        ("templates/single.yml", "single"),
        ("templates/root.yml", "root"),
        ("templates/package.yml", "package"),
    ]
    for tpl, role in cases:
        target = tmp_path / ".levers.yml"
        shutil.copy(REPO_ROOT / tpl, target)
        result = subprocess.run(
            [str(REPO_ROOT / "levers"), "validate", str(target), "--role", role],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"{tpl} failed validation under role={role}\n{result.stdout}\n{result.stderr}"
        )
