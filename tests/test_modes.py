"""Tests for the modes overlay feature."""

from __future__ import annotations

from pathlib import Path


# ---------------------------------------------------------------------------
# init seeds modes into the template
# ---------------------------------------------------------------------------


def test_init_seeds_modes_block(run, tmp_repo: Path) -> None:
    run("init", cwd=tmp_repo).assert_ok()
    content = (tmp_repo / ".levers.yml").read_text()
    assert "modes:" in content
    for name in ("prototype", "greenfield", "brownfield"):
        assert name in content


def test_template_validates_with_modes(run, single_repo: Path) -> None:
    # The seeded template (single + root) must round-trip through validate.
    run("validate", cwd=single_repo).assert_ok()


# ---------------------------------------------------------------------------
# `levers mode list / set / clear / (bare)`
# ---------------------------------------------------------------------------


def test_mode_list_shows_seeded(run, single_repo: Path) -> None:
    r = run("mode", "list", cwd=single_repo).assert_ok()
    for name in ("prototype", "greenfield", "brownfield"):
        assert name in r.stdout


def test_mode_set_then_bare_mode_shows_active(run, single_repo: Path) -> None:
    run("mode", "set", "prototype", cwd=single_repo).assert_ok()
    r = run("mode", cwd=single_repo).assert_ok()
    assert "active: prototype" in r.stdout
    # planning_horizon: phased (declared) → just_in_time (overlay) — must
    # show declared→overlay arrow form for a key that actually changes.
    assert "planning_horizon: phased → just_in_time" in r.stdout


def test_mode_set_unknown_errors(run, single_repo: Path) -> None:
    r = run("mode", "set", "nosuch", cwd=single_repo).assert_fails(1)
    assert "nosuch" in r.stderr or "nosuch" in r.stdout


def test_mode_clear_restores_none(run, single_repo: Path) -> None:
    run("mode", "set", "prototype", cwd=single_repo).assert_ok()
    run("mode", "clear", cwd=single_repo).assert_ok()
    r = run("mode", cwd=single_repo).assert_ok()
    assert "active: (none)" in r.stdout


# ---------------------------------------------------------------------------
# `levers get` resolution with mode overlay
# ---------------------------------------------------------------------------


def test_get_applies_mode_overlay(run, single_repo: Path) -> None:
    # planning_horizon: phased declared; prototype mode overrides to just_in_time.
    run("mode", "set", "prototype", cwd=single_repo).assert_ok()
    r = run("get", "planning_horizon", cwd=single_repo).assert_ok()
    assert r.stdout.strip() == "just_in_time"
    # Stderr note appears when declared ≠ overlay.
    assert "from mode 'prototype'" in r.stderr
    assert "declared: phased" in r.stderr


def test_get_no_mode_bypasses_overlay(run, single_repo: Path) -> None:
    run("mode", "set", "prototype", cwd=single_repo).assert_ok()
    r = run("get", "planning_horizon", "--no-mode", cwd=single_repo).assert_ok()
    assert r.stdout.strip() == "phased"
    # Bypassed → no stderr note.
    assert "from mode" not in r.stderr


def test_get_full_view_includes_mode_provenance(run, single_repo: Path) -> None:
    run("mode", "set", "prototype", cwd=single_repo).assert_ok()
    r = run("get", cwd=single_repo).assert_ok()
    assert "# Mode: prototype" in r.stdout
    # Reserved keys must NOT leak into the emitted lever view.
    assert "\nmode:" not in r.stdout
    assert "\nmodes:" not in r.stdout


def test_get_full_view_no_mode_label_when_inactive(run, single_repo: Path) -> None:
    r = run("get", cwd=single_repo).assert_ok()
    assert "# Mode: (none)" in r.stdout


def test_get_silent_when_overlay_matches_declared(run, single_repo: Path) -> None:
    # Template declares ci_gate: none; prototype overlays ci_gate: none too.
    # Single-value form must NOT emit a stderr note when they coincide.
    run("mode", "set", "prototype", cwd=single_repo).assert_ok()
    r = run("get", "ci_gate", cwd=single_repo).assert_ok()
    assert r.stdout.strip() == "none"
    assert r.stderr.strip() == ""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_validate_rejects_unknown_mode_value(run, single_repo: Path) -> None:
    target = single_repo / ".levers.yml"
    content = target.read_text().replace("mode:\n", "mode: nosuch\n", 1)
    target.write_text(content)
    r = run("validate", cwd=single_repo).assert_fails(1)
    assert "nosuch" in r.stdout
    assert "modes:" in r.stdout or "defined" in r.stdout


def _swap_modes_block(target: Path, replacement: str) -> None:
    """Replace the seeded `modes:` block in `target` with `replacement`.

    Relies on the template layout: `modes:` block starts at a line beginning
    with `modes:` and ends at the blank line before `# --- Project context ---`.
    """
    lines = target.read_text().splitlines(keepends=True)
    start = next(i for i, ln in enumerate(lines) if ln.startswith("modes:"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("# --- Project context"))
    new_lines = lines[:start] + [replacement.rstrip() + "\n\n"] + lines[end:]
    target.write_text("".join(new_lines))


def test_validate_rejects_unknown_field_in_mode_entry(
    run, single_repo: Path
) -> None:
    _swap_modes_block(
        single_repo / ".levers.yml",
        "modes:\n"
        "  prototype:\n"
        "    note: garbage\n"
        "    overrides:\n"
        "      ci_gate: none\n",
    )
    r = run("validate", cwd=single_repo).assert_fails(1)
    assert "unknown field 'note'" in r.stdout


def test_validate_rejects_unknown_override_key(
    run, single_repo: Path
) -> None:
    _swap_modes_block(
        single_repo / ".levers.yml",
        "modes:\n"
        "  prototype:\n"
        "    overrides:\n"
        "      not_a_lever: foo\n",
    )
    r = run("validate", cwd=single_repo).assert_fails(1)
    assert "not_a_lever" in r.stdout
    assert "unknown lever key" in r.stdout


def test_validate_rejects_invalid_override_value(
    run, single_repo: Path
) -> None:
    _swap_modes_block(
        single_repo / ".levers.yml",
        "modes:\n"
        "  prototype:\n"
        "    overrides:\n"
        "      ci_gate: not_an_enum_value\n",
    )
    # mode: still points to "prototype" which now exists (with bad override).
    r = run("validate", cwd=single_repo).assert_fails(1)
    assert "not_an_enum_value" in r.stdout


def test_validate_rejects_override_of_reserved_key(
    run, single_repo: Path
) -> None:
    _swap_modes_block(
        single_repo / ".levers.yml",
        "modes:\n"
        "  prototype:\n"
        "    overrides:\n"
        "      mode: prototype\n",
    )
    r = run("validate", cwd=single_repo).assert_fails(1)
    assert "reserved" in r.stdout


def test_validate_rejects_mode_at_package_file(run, monorepo: Path) -> None:
    pkg = monorepo / "apps" / "mobile" / ".levers.yml"
    pkg.write_text("mode: prototype\n" + pkg.read_text())
    r = run("validate", "--role", "package", str(pkg)).assert_fails(1)
    assert "root-only" in r.stdout


# ---------------------------------------------------------------------------
# Reserved keys never leak into validation as "unknown"
# ---------------------------------------------------------------------------


def test_mode_and_modes_not_flagged_as_unknown_keys(
    run, single_repo: Path
) -> None:
    # Seeded template has both; validate must not flag either as unknown.
    r = run("validate", cwd=single_repo).assert_ok()
    assert "unknown key: mode" not in r.stdout
    assert "unknown key: modes" not in r.stdout


# ---------------------------------------------------------------------------
# Set comments preserved (ruamel roundtrip)
# ---------------------------------------------------------------------------


def test_mode_set_preserves_comments(run, single_repo: Path) -> None:
    before = (single_repo / ".levers.yml").read_text()
    run("mode", "set", "prototype", cwd=single_repo).assert_ok()
    after = (single_repo / ".levers.yml").read_text()
    # All comments from the template should still be present after the flip.
    for line in before.splitlines():
        if line.lstrip().startswith("#"):
            assert line in after, f"comment lost on mode set: {line!r}"
