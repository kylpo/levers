# levers

A small file format and CLI for encoding the *policy-level shape* of a software project — the answers to "do we wait for CI?", "must `main` be always-deployable?", "is `agent_auto_merge` allowed here?" — in a checked-in file that tools and humans can both read reliably.

```yaml
# .levers.yml
lifecycle_stage: pre_launch
team_mode: solo
ci_gate: gates_merge
release_model: continuous
# ...
```

## Why

Tools and skills route behavior on project policy. Without a canonical encoding those answers get either hardcoded (defaults), re-derived from repo state each invocation, or re-asked of the user. Each option is worse than the others.

`.levers.yml` makes policy:

- **Explicit** — declared, not inferred.
- **Auditable** — git-diffable transitions, paired with `DECISIONS.md` entries.
- **Machine-readable** — strict enums; one parser, no fences, no LLMs.

## Install

```bash
git clone https://github.com/kylpo/levers ~/github/levers
bash ~/github/levers/install.sh
```

This symlinks `~/.local/bin/levers` to the script in the clone. Updates land via `git pull` automatically — no re-install needed. Use `--prefix <dir>` to install elsewhere.

The CLI is a single-file Python script with [PEP 723](https://peps.python.org/pep-0723/) inline dependencies, run via [`uv`](https://docs.astral.sh/uv/) — no separate `pip install` step, no virtualenv to manage.

Requirements: Python ≥ 3.12 and `uv` on `PATH`.

## Quickstart

```bash
# Bootstrap a new project
cd my-project
levers init                                  # interactive editor seeded from the template
levers init --no-interactive                 # or write the template verbatim
levers validate                              # confirm the schema is satisfied

# Read / write
levers get ci_gate                           # → none
levers set                                   # interactive editor over the whole file
levers set ci_gate gates_merge               # or set one key directly (preserves comments)
levers get ci_gate                           # → gates_merge

# Listing the schema (for prompts, interviews, scripting)
levers list-enums                            # all keys, grouped by category
levers list-enums --key ci_gate              # one key
levers list-enums --role root --format yaml  # filter + machine-readable

# Drift detection
levers audit                                 # warn on declared-vs-observed mismatch
levers audit --strict                        # exit 1 on any warning (for CI)
```

The interactive editor (`levers init`, `levers set` with no args) binds: ↑/↓ to select a row, ←/→ to cycle the selected lever through its enum, ENTER to save, ESC (or Ctrl-C) to cancel. Comments and ordering survive round-trips. When stdin isn't a TTY, `init` falls back to writing the template verbatim and `set` requires `<key> <value>`.

## Monorepos

A monorepo has a root `.levers.yml` plus one `.levers.yml` per package. Repo-wide levers (`team_mode`, `branch_strategy`) live at root; package-scoped levers (`lifecycle_stage`, `release_model`) live in each package. "Either" levers default at root and may be overridden per-package.

```bash
levers init --role root                       # root file (repo-wide policy)
levers add-package apps/mobile                # per-package file (one per deliverable)

# Effective view at any path (root + nearest-ancestor package, merged)
levers resolve apps/mobile/src                # all keys, YAML with provenance header
levers resolve apps/mobile --get ci_gate      # single raw value

# Cross-package change set
levers detect-packages apps/mobile/x.swift packages/shared/y.swift
# apps/mobile
# packages/shared

# Cross-package merge for unattended automation (strictest value wins per lever)
levers resolve --merge-strictest apps/mobile packages/shared --keys ci_gate,agent_auto_merge
```

Full mechanics in [docs/spec.md](./docs/spec.md).

## Concepts

The lever set is small (~17 keys) and chosen to cover policy that **can't be reliably inferred from the repo**. Each key has a strict enum of allowed values, a *scope* (`repo`, `package`, or `either`), and for the values that admit a "strictest" answer, a strictness ordering used for cross-package merges.

- **Lifecycle & risk** — `lifecycle_stage`
- **Team & collaboration** — `team_mode`, `review_cadence`
- **Planning & execution** — `planning_horizon`
- **Quality** — `test_strategy`, `manual_qa_capture`, `ci_gate`, `code_review`
- **Release & delivery** — `release_model`, `branch_strategy`, `release_cadence`, `versioning`
- **Automation** — `agent_auto_merge`, `bug_intake`
- **Documentation** — `changelog_style`, `doc_sync`
- **Workspace** — `workspace_isolation`

Schema tables with every enum value: [docs/spec.md § Schema](./docs/spec.md#schema). The full tradeoff space behind each lever (when to pick which value, and why): [docs/reference.md](./docs/reference.md).

## Drift detection

`levers audit` compares declared values against observable repo signals (git authors, tags, GitHub workflows) and emits warnings when they disagree. Drift is a human-attention signal, not a blocker — exit code is 0 even on warnings unless `--strict` is set.

```
⚠ drift (apps/mobile): declared `release_model: continuous` but
  `release_cadence: milestone` — these contradict.
```

The check list: [docs/drift.md](./docs/drift.md).

## Documentation

- [docs/spec.md](./docs/spec.md) — `.levers.yml` format, schema, monorepo resolution, validation, FAQ.
- [docs/reference.md](./docs/reference.md) — full pipeline-lever tradeoff space (the *rationale* behind every lever).
- [docs/drift.md](./docs/drift.md) — what `levers audit` checks, when each check fires, what to do about it.
- [schema.yml](./schema.yml) — single source of truth for keys, scopes, allowed values, and strictness orderings.

## License

MIT. See [LICENSE](./LICENSE).
