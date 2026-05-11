"""Shared pytest fixtures for levers CLI tests.

Tests exercise the `levers` script via subprocess — that's how users hit it,
and it avoids re-importing the script (which is a single executable file
with a `uv run --script` shebang, not a Python package).

Run with:
    uv run --with pytest pytest
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LEVERS_BIN = REPO_ROOT / "levers"
TEMPLATES_DIR = REPO_ROOT / "templates"


@dataclass
class Result:
    """Subprocess result with assertion helpers."""

    returncode: int
    stdout: str
    stderr: str

    def assert_ok(self) -> "Result":
        assert self.returncode == 0, (
            f"expected exit 0, got {self.returncode}\nstdout:\n{self.stdout}\nstderr:\n{self.stderr}"
        )
        return self

    def assert_fails(self, code: int | None = None) -> "Result":
        assert self.returncode != 0, f"expected non-zero exit, got 0\nstdout:\n{self.stdout}"
        if code is not None:
            assert self.returncode == code, (
                f"expected exit {code}, got {self.returncode}\nstdout:\n{self.stdout}\nstderr:\n{self.stderr}"
            )
        return self


@pytest.fixture(scope="session")
def levers_bin() -> Path:
    assert LEVERS_BIN.is_file(), f"missing levers script at {LEVERS_BIN}"
    return LEVERS_BIN


@pytest.fixture
def run(levers_bin: Path) -> object:
    """Return a callable that runs `levers <args...>` in a given cwd."""

    def _run(*args: str, cwd: Path | None = None, check: bool = False) -> Result:
        result = subprocess.run(
            [str(levers_bin), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        out = Result(result.returncode, result.stdout, result.stderr)
        if check:
            out.assert_ok()
        return out

    return _run


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """A tmp directory initialized as a git repo (for resolve / audit tests)."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    return tmp_path


@pytest.fixture
def single_repo(tmp_repo: Path) -> Path:
    """A tmp git repo with a valid single-role .levers.yml at root."""
    shutil.copy(TEMPLATES_DIR / "single.yml", tmp_repo / ".levers.yml")
    return tmp_repo


@pytest.fixture
def monorepo(tmp_repo: Path) -> Path:
    """A tmp git repo with root + two package .levers.yml files."""
    shutil.copy(TEMPLATES_DIR / "root.yml", tmp_repo / ".levers.yml")
    (tmp_repo / "apps" / "mobile").mkdir(parents=True)
    (tmp_repo / "packages" / "shared").mkdir(parents=True)
    shutil.copy(TEMPLATES_DIR / "package.yml", tmp_repo / "apps" / "mobile" / ".levers.yml")
    shutil.copy(TEMPLATES_DIR / "package.yml", tmp_repo / "packages" / "shared" / ".levers.yml")
    return tmp_repo
