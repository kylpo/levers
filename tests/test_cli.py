"""Integration tests for the levers CLI subcommands."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# --version / --help
# ---------------------------------------------------------------------------


def test_version(run) -> None:
    r = run("--version").assert_ok()
    assert "levers" in r.stdout
    assert r.stdout.strip().split()[-1].count(".") == 2  # x.y.z


def test_help_lists_subcommands(run) -> None:
    r = run("--help").assert_ok()
    for cmd in ["validate", "list-enums", "get", "set", "init", "merge-strictest", "audit", "detect-packages"]:
        assert cmd in r.stdout, f"--help missing subcommand: {cmd}"
    # `resolve` was folded into `get` (with inheritance) + `merge-strictest`.
    assert "resolve" not in r.stdout


# ---------------------------------------------------------------------------
# init / validate / get / set
# ---------------------------------------------------------------------------


def test_init_creates_file(run, tmp_repo: Path) -> None:
    run("init", cwd=tmp_repo).assert_ok()
    assert (tmp_repo / ".levers.yml").is_file()


def test_init_refuses_overwrite_without_force(run, single_repo: Path) -> None:
    run("init", cwd=single_repo).assert_fails(1)


def test_init_force_overwrites(run, single_repo: Path) -> None:
    run("init", "--force", cwd=single_repo).assert_ok()


def test_validate_passes_on_template(run, single_repo: Path) -> None:
    r = run("validate", cwd=single_repo).assert_ok()
    assert "valid" in r.stdout


def test_validate_walks_monorepo_with_inferred_roles(run, monorepo: Path) -> None:
    # Bare `validate` should discover the root file plus every nested
    # package file and infer the right role for each — root + 2 packages.
    r = run("validate", cwd=monorepo).assert_ok()
    assert "role=root" in r.stdout
    assert r.stdout.count("role=package") == 2


def test_validate_walk_reports_per_file_failure(run, monorepo: Path) -> None:
    # Corrupt one package file. Walk mode should validate the rest and
    # exit non-zero with a per-file failure summary.
    (monorepo / "apps" / "mobile" / ".levers.yml").write_text("ci_gate: bogus\n")
    r = run("validate", cwd=monorepo).assert_fails(1)
    assert "invalid value" in r.stdout
    assert "1 file failed" in r.stdout


def test_validate_explicit_role_single_still_fails_on_monorepo_root(
    run, monorepo: Path
) -> None:
    # The override path remains: forcing --role single on a root-style
    # file still surfaces the missing package-scoped keys.
    r = run("validate", "--role", "single", cwd=monorepo).assert_fails(1)
    assert "missing required key" in r.stdout


def test_validate_root_role(run, monorepo: Path) -> None:
    run("validate", "--role", "root", cwd=monorepo).assert_ok()


def test_validate_package_role(run, monorepo: Path) -> None:
    target = monorepo / "apps" / "mobile" / ".levers.yml"
    run("validate", str(target), "--role", "package").assert_ok()


def test_validate_detects_enum_violation(run, single_repo: Path) -> None:
    (single_repo / ".levers.yml").write_text("ci_gate: bogus\n")
    r = run("validate", cwd=single_repo).assert_fails(1)
    assert "invalid value" in r.stdout


def test_get_existing_key(run, single_repo: Path) -> None:
    r = run("get", "ci_gate", cwd=single_repo).assert_ok()
    assert r.stdout.strip() == "none"


def test_get_unknown_key_errors(run, single_repo: Path) -> None:
    run("get", "no_such_key", cwd=single_repo).assert_fails(2)


def test_get_inherits_root_value_at_package_path(run, monorepo: Path) -> None:
    # ci_gate lives only at root in the monorepo fixture — reading at a
    # package path should return the inherited value, not error.
    r = run("get", "ci_gate", "--at", "apps/mobile", cwd=monorepo).assert_ok()
    assert r.stdout.strip() == "none"


def test_get_package_override_wins(run, monorepo: Path) -> None:
    # Override ci_gate at the package; root keeps `none`.
    run("set", "ci_gate", "gates_merge", "--at", "apps/mobile", cwd=monorepo).assert_ok()
    r = run("get", "ci_gate", "--at", "apps/mobile", cwd=monorepo).assert_ok()
    assert r.stdout.strip() == "gates_merge"
    r = run("get", "ci_gate", "--at", "packages/shared", cwd=monorepo).assert_ok()
    assert r.stdout.strip() == "none"


def test_get_no_key_returns_full_view(run, monorepo: Path) -> None:
    r = run("get", "--at", "apps/mobile", cwd=monorepo).assert_ok()
    assert "ci_gate:" in r.stdout
    assert "lifecycle_stage:" in r.stdout


def test_get_descends_to_nearest_package(run, monorepo: Path) -> None:
    (monorepo / "apps" / "mobile" / "src").mkdir()
    r = run("get", "--at", "apps/mobile/src", cwd=monorepo).assert_ok()
    assert "ci_gate:" in r.stdout


def test_get_keys_filter(run, monorepo: Path) -> None:
    r = run(
        "get", "--at", "apps/mobile", "--keys", "ci_gate,lifecycle_stage", cwd=monorepo
    ).assert_ok()
    assert "ci_gate:" in r.stdout
    assert "lifecycle_stage:" in r.stdout
    assert "team_mode" not in r.stdout


def test_get_keys_rejects_with_positional_key(run, monorepo: Path) -> None:
    r = run(
        "get", "ci_gate", "--at", "apps/mobile", "--keys", "ci_gate", cwd=monorepo
    ).assert_fails(2)
    assert "--keys" in r.stderr


def test_get_format_json(run, monorepo: Path) -> None:
    r = run(
        "get",
        "--at",
        "apps/mobile",
        "--keys",
        "ci_gate,lifecycle_stage",
        "--format",
        "json",
        cwd=monorepo,
    ).assert_ok()
    data = json.loads(r.stdout)
    assert data["ci_gate"] == "none"
    assert data["lifecycle_stage"] == "pre_launch"


def test_get_no_repo_root_errors(run, tmp_path_factory) -> None:
    """Reading from a path with no .git ancestor (and no --repo-root) errors."""
    outside = tmp_path_factory.mktemp("levers_outside")
    r = run("get", "--at", str(outside))
    # Either it errors (no .git anywhere up) OR the user's filesystem has a .git
    # somewhere up — but no .levers.yml at that root, which also errors.
    r.assert_fails()


def test_set_changes_value(run, single_repo: Path) -> None:
    run("set", "ci_gate", "gates_merge", cwd=single_repo).assert_ok()
    assert run("get", "ci_gate", cwd=single_repo).stdout.strip() == "gates_merge"


def test_set_rejects_invalid_value(run, single_repo: Path) -> None:
    r = run("set", "ci_gate", "bogus", cwd=single_repo).assert_fails(2)
    assert "invalid value" in r.stderr


def test_set_rejects_unknown_key(run, single_repo: Path) -> None:
    run("set", "nope", "x", cwd=single_repo).assert_fails(2)


def test_set_preserves_comments(run, single_repo: Path) -> None:
    """Top-matter and section-divider comments must survive a set."""
    run("set", "ci_gate", "gates_merge", cwd=single_repo).assert_ok()
    text = (single_repo / ".levers.yml").read_text()
    assert "# .levers.yml" in text
    assert "# --- Project context ---" in text


# ---------------------------------------------------------------------------
# Interactive editor — non-interactive escape hatches and TTY guards
# ---------------------------------------------------------------------------


def test_init_no_interactive_flag(run, tmp_repo: Path) -> None:
    """--no-interactive writes the template verbatim, identical to the template."""
    r = run("init", "--no-interactive", cwd=tmp_repo).assert_ok()
    target = tmp_repo / ".levers.yml"
    assert target.is_file()
    template = (Path(__file__).resolve().parent.parent / "templates" / "single.yml").read_bytes()
    assert target.read_bytes() == template
    assert "wrote" in r.stdout


def test_set_no_args_requires_tty(run, single_repo: Path) -> None:
    """Without a TTY, `levers set` (no args) must error rather than hang."""
    r = run("set", cwd=single_repo).assert_fails(2)
    assert "tty" in r.stderr


def test_set_only_key_arg_errors(run, single_repo: Path) -> None:
    """`set <key>` (no value) must error — half-specified is ambiguous."""
    r = run("set", "ci_gate", cwd=single_repo).assert_fails(2)
    assert "both" in r.stderr or "value" in r.stderr


# ---------------------------------------------------------------------------
# list-enums
# ---------------------------------------------------------------------------


def test_list_enums_default(run) -> None:
    r = run("list-enums").assert_ok()
    assert "ci_gate" in r.stdout
    assert "Project context" in r.stdout


def test_list_enums_key(run) -> None:
    r = run("list-enums", "--key", "ci_gate").assert_ok()
    assert r.stdout.strip() == "ci_gate (repo): none | advisory | gates_merge"


def test_list_enums_role_filter(run) -> None:
    r = run("list-enums", "--role", "root").assert_ok()
    # Package-only keys must not appear.
    assert "lifecycle_stage" not in r.stdout
    # Repo-scoped keys must appear.
    assert "team_mode" in r.stdout
    assert "ci_gate" in r.stdout


def test_list_enums_format_yaml(run) -> None:
    r = run("list-enums", "--format", "yaml", "--key", "ci_gate").assert_ok()
    assert "ci_gate: [none, advisory, gates_merge]" in r.stdout


def test_list_enums_shows_numeric_values(run) -> None:
    r = run("list-enums", "--key", "ci_retry").assert_ok()
    assert r.stdout.splitlines()[0] == (
        "ci_retry (repo): off | 1 | 2 | 3 | until_fixed"
    )


def test_list_enums_shows_dependency_annotation(run) -> None:
    r = run("list-enums", "--key", "ci_retry").assert_ok()
    assert "enabled when ci_gate in [gates_merge]" in r.stdout


# ---------------------------------------------------------------------------
# Numeric value handling (ci_retry)
# ---------------------------------------------------------------------------


def test_set_accepts_numeric_value(run, single_repo: Path) -> None:
    run("set", "ci_gate", "gates_merge", cwd=single_repo).assert_ok()
    run("set", "ci_retry", "3", cwd=single_repo).assert_ok()
    r = run("get", "ci_retry", cwd=single_repo).assert_ok()
    assert r.stdout.strip() == "3"


def test_set_accepts_off_and_until_fixed(run, single_repo: Path) -> None:
    run("set", "ci_gate", "gates_merge", cwd=single_repo).assert_ok()
    run("set", "ci_retry", "until_fixed", cwd=single_repo).assert_ok()
    assert run("get", "ci_retry", cwd=single_repo).stdout.strip() == "until_fixed"
    run("set", "ci_retry", "off", cwd=single_repo).assert_ok()
    assert run("get", "ci_retry", cwd=single_repo).stdout.strip() == "off"


def test_set_rejects_out_of_range_numeric(run, single_repo: Path) -> None:
    r = run("set", "ci_retry", "9", cwd=single_repo).assert_fails(2)
    assert "invalid value" in r.stderr


def test_get_disabled_lever_returns_disabled_default(run, single_repo: Path) -> None:
    # Stash a non-default ci_retry on disk, then verify reads see the
    # gated-off override (`off`) while ci_gate is not gates_merge.
    run("set", "ci_retry", "3", cwd=single_repo).assert_ok()
    assert run("get", "ci_retry", cwd=single_repo).stdout.strip() == "off"
    # Flip ci_gate to gates_merge → the saved value becomes live.
    run("set", "ci_gate", "gates_merge", cwd=single_repo).assert_ok()
    assert run("get", "ci_retry", cwd=single_repo).stdout.strip() == "3"


# ---------------------------------------------------------------------------
# init --role package
# ---------------------------------------------------------------------------


def test_init_package_succeeds(run, monorepo: Path) -> None:
    (monorepo / "apps" / "web").mkdir()
    run("init", "--role", "package", "--at", "apps/web", cwd=monorepo).assert_ok()
    assert (monorepo / "apps" / "web" / ".levers.yml").is_file()


def test_init_package_rejects_at_root(run, monorepo: Path) -> None:
    r = run("init", "--role", "package", "--at", ".", cwd=monorepo).assert_fails(1)
    assert "refusing" in r.stderr or "root" in r.stderr


def test_init_package_requires_root_levers(run, tmp_repo: Path) -> None:
    (tmp_repo / "apps").mkdir()
    r = run("init", "--role", "package", "--at", "apps", cwd=tmp_repo).assert_fails(2)
    assert "no root .levers.yml" in r.stderr


# ---------------------------------------------------------------------------
# merge-strictest
# ---------------------------------------------------------------------------


def test_merge_strictest_picks_strictest(run, monorepo: Path) -> None:
    run("set", "ci_gate", "gates_merge", "--at", "apps/mobile", cwd=monorepo).assert_ok()
    run("set", "ci_gate", "none", "--at", "packages/shared", cwd=monorepo).assert_ok()
    r = run(
        "merge-strictest",
        "apps/mobile",
        "packages/shared",
        "--keys",
        "ci_gate",
        cwd=monorepo,
    ).assert_ok()
    assert "ci_gate: gates_merge" in r.stdout


def test_merge_strictest_same_value_shortcut(run, monorepo: Path) -> None:
    """If all paths agree, non-strictness-mergeable keys still resolve."""
    r = run(
        "merge-strictest",
        "apps/mobile",
        "packages/shared",
        "--keys",
        "versioning",
        cwd=monorepo,
    ).assert_ok()
    assert "versioning: semver" in r.stdout


def test_merge_strictest_diverging_unsupported_key_errors(run, monorepo: Path) -> None:
    run("set", "versioning", "semver", "--at", "apps/mobile", cwd=monorepo).assert_ok()
    run("set", "versioning", "calver", "--at", "packages/shared", cwd=monorepo).assert_ok()
    r = run(
        "merge-strictest",
        "apps/mobile",
        "packages/shared",
        "--keys",
        "versioning",
        cwd=monorepo,
    ).assert_fails(1)
    assert "not strictness-mergeable" in r.stderr


# ---------------------------------------------------------------------------
# detect-packages
# ---------------------------------------------------------------------------


def test_detect_packages_single(run, monorepo: Path) -> None:
    r = run("detect-packages", "apps/mobile/src/x.swift", cwd=monorepo).assert_ok()
    assert r.stdout.strip() == "apps/mobile"


def test_detect_packages_distinct(run, monorepo: Path) -> None:
    r = run(
        "detect-packages", "apps/mobile/x", "packages/shared/y", cwd=monorepo
    ).assert_ok()
    lines = sorted(r.stdout.strip().splitlines())
    assert lines == ["apps/mobile", "packages/shared"]


def test_detect_packages_dedupe(run, monorepo: Path) -> None:
    r = run(
        "detect-packages",
        "apps/mobile/a",
        "apps/mobile/b",
        cwd=monorepo,
    ).assert_ok()
    assert r.stdout.strip() == "apps/mobile"


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------


def test_audit_clean_repo(run, monorepo: Path) -> None:
    subprocess.run(["git", "add", "."], cwd=monorepo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"], cwd=monorepo, check=True
    )
    r = run("audit", cwd=monorepo).assert_ok()
    assert "no drift detected" in r.stdout


def test_audit_flags_contradiction(run, monorepo: Path) -> None:
    run(
        "set", "release_model", "continuous", "--at", "apps/mobile", cwd=monorepo
    ).assert_ok()
    run(
        "set", "release_cadence", "milestone", "--at", "apps/mobile", cwd=monorepo
    ).assert_ok()
    r = run("audit", cwd=monorepo).assert_ok()
    assert "contradict" in r.stdout


def test_audit_strict_exits_nonzero_on_drift(run, monorepo: Path) -> None:
    run(
        "set", "release_model", "continuous", "--at", "apps/mobile", cwd=monorepo
    ).assert_ok()
    run(
        "set", "release_cadence", "milestone", "--at", "apps/mobile", cwd=monorepo
    ).assert_ok()
    run("audit", "--strict", cwd=monorepo).assert_fails(1)


def test_audit_root_only(run, monorepo: Path) -> None:
    # Contradiction at package; --root should ignore it.
    run(
        "set", "release_model", "continuous", "--at", "apps/mobile", cwd=monorepo
    ).assert_ok()
    run(
        "set", "release_cadence", "milestone", "--at", "apps/mobile", cwd=monorepo
    ).assert_ok()
    r = run("audit", "--root", cwd=monorepo).assert_ok()
    assert "no drift detected" in r.stdout


def test_audit_ci_gate_drift(run, monorepo: Path) -> None:
    wf = monorepo / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text(
        "on:\n  push:\n    branches: [main]\njobs:\n  t:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hi\n"
    )
    r = run("audit", "--root", cwd=monorepo).assert_ok()
    assert "ci_gate" in r.stdout


def test_audit_flags_subagent_parallel_root(run, monorepo: Path) -> None:
    run("set", "code_review", "apply", cwd=monorepo).assert_ok()
    run("set", "code_review_concurrency", "parallel", cwd=monorepo).assert_ok()
    r = run("audit", "--root", cwd=monorepo).assert_ok()
    assert "code_review_concurrency" in r.stdout
    assert "conflicting edits" in r.stdout


def test_audit_subagent_advisory_parallel_is_safe(run, monorepo: Path) -> None:
    run("set", "code_review", "advisory", cwd=monorepo).assert_ok()
    run("set", "code_review_concurrency", "parallel", cwd=monorepo).assert_ok()
    r = run("audit", "--root", cwd=monorepo).assert_ok()
    assert "code_review_concurrency" not in r.stdout


def test_audit_flags_subagent_parallel_package(run, monorepo: Path) -> None:
    run(
        "set", "code_review", "apply", "--at", "apps/mobile", cwd=monorepo
    ).assert_ok()
    run(
        "set", "code_review_concurrency", "parallel", "--at", "apps/mobile",
        cwd=monorepo,
    ).assert_ok()
    r = run("audit", cwd=monorepo).assert_ok()
    assert "code_review_concurrency" in r.stdout
