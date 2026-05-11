# Migration plan — `kylpo/levers`

Standalone repo extracted from `kylpo/skills` (`protocol-levers/`, `LEVERS_REFERENCE.md`, `LEVERS_STANDARD.md`). Replaces the `LEVERS.md` (YAML frontmatter + markdown prose) format with `.levers.yml` (pure YAML). Replaces the bash scripts (`validate.sh`, `resolve.sh`, `audit.sh`, `detect-packages.sh`, `list-enums.sh`) with a single-file Python CLI invoked via PEP 723 `uv run --script`.

This doc is transient — delete it after Phase 1 lands.

## Locked decisions

| Decision | Choice |
|---|---|
| File format | `.levers.yml` (pure YAML, flat keys, same schema as today's `LEVERS.md`) |
| Prose body content (rationale, transitions, exceptions) | Dropped. Rationale belongs in `DECISIONS.md`. |
| Language | Python via uv |
| Code shape | Single self-contained `levers` script with PEP 723 inline deps |
| Install | `install.sh` symlinks `~/.local/bin/levers` → `<clone>/levers` |
| Doc shape | `README.md` + `docs/{spec,reference,drift}.md` |
| CLI scope (Phase 1) | `set`/`get`, `validate`/`resolve`/`audit`, `init`, `add-package`, `detect-packages`, `list-enums` |
| Migration of existing `LEVERS.md` files | Cold cutover — no migration helper. Hand-port. |
| LICENSE | MIT, 2026, Kyle Poole |
| Python | 3.12 |
| CLI framework | Typer |
| YAML lib | ruamel.yaml (comment-preserving roundtrip) |

## Phase overview

| Phase | Goal | Touches |
|---|---|---|
| **1. Stand up the new repo** | This repo has docs, schema, Python CLI scaffold with working subcommands, runnable via the shebang `levers` script. No consumer cutover. | `kylpo/levers` only |
| **2. Validate on a real project** | Use the CLI in one downstream project (likely tron) — hand-port its `LEVERS.md` to `.levers.yml`, iterate on CLI UX. | One downstream repo |
| **3. (conditional) Retire `skills/protocol-levers/`** | Migrate skill consumers from `~/.claude/skills/protocol-levers/<script>.sh` shell-outs to `levers <verb>` CLI calls. Hand-port remaining `LEVERS.md` files. Delete `skills/protocol-levers/`, `LEVERS_REFERENCE.md`, `LEVERS_STANDARD.md`. Update inbound markdown links. | `kylpo/skills` + remaining consumers |

Phase boundaries are chosen so that the existing `skills/protocol-levers/` install remains the working code path until Phase 3. Phase 1 produces nothing the existing pipeline depends on.

---

## Phase 1 — detailed plan

### 1.1 Target repo layout

```
/Users/kylpo/github/levers/
├── README.md
├── LICENSE                # MIT
├── install.sh             # symlinks ~/.local/bin/levers → ./levers
├── .gitignore
├── .python-version        # 3.12
├── levers                 # the single-file CLI (PEP 723 shebang)
├── schema.yml             # single source of truth for keys/values/scope/strictness
├── templates/
│   ├── single.yml
│   ├── root.yml
│   └── package.yml
├── docs/
│   ├── spec.md            # ported + deskilled from protocol-levers/SKILL.md
│   ├── reference.md       # ported from LEVERS_REFERENCE.md (light edits)
│   └── drift.md           # short reference for audit rules
└── tests/
    ├── conftest.py
    ├── fixtures/          # canned .levers.yml files (valid + invalid)
    └── test_*.py          # subprocess-based integration tests
```

### 1.2 Script shape

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer",
#   "ruamel.yaml",
# ]
# ///
"""levers — manage .levers.yml configuration files."""
```

Expected size: ~1000–1500 lines. Organization: top imports → schema loader → I/O helpers → resolve → audit → CLI commands → `if __name__ == "__main__": app()`.

### 1.3 Schema as single source of truth

`schema.yml` replaces the legacy `schema.txt`:

```yaml
levers:
  ci_gate:
    scope: either
    values: [none, advisory, gates_merge]
    strictness: [gates_merge, advisory, none]
    category: quality
    routes: "..."
  lifecycle_stage:
    scope: package
    values: [prototype, pre_launch, post_launch, mature]
    strictness: [mature, post_launch, pre_launch, prototype]
    category: lifecycle
  # ... ~17 keys total
```

One file drives: enum validation, scope checks, `list-enums` output, `--merge-strictest` order, the spec.md schema tables (generated, not hand-maintained), and Typer choice constraints.

### 1.4 CLI surface

```
levers init   [--role single|root|package] [--at PATH] [--force]
levers add-package PATH [--inherit-only]
levers validate [PATH] [--role single|root|package]
levers resolve PATH [KEYS...] [--get KEY] [--format yaml|text]
levers resolve --merge-strictest PATH... KEY [KEY...]
levers audit [PATH] [--root | --package PATH] [--strict]
levers set   KEY VALUE [--at PATH]
levers get   KEY        [--at PATH]
levers detect-packages PATH...
levers list-enums [--key KEY] [--role single|root|package] [--format yaml|text]
```

Logic ports:
- `validate` ← `protocol-levers/validate.sh`
- `resolve` ← `protocol-levers/resolve.sh`
- `audit` ← merged `protocol-levers/audit.sh` + `tron/scripts/levers-audit.sh` (adds `--strict` + warning summary)
- `detect-packages` ← `protocol-levers/detect-packages.sh`
- `list-enums` ← `protocol-levers/list-enums.sh`
- `set` / `get` / `init` / `add-package` — new, schema-driven

`set` and `init` use `ruamel.yaml` for comment-preserving roundtrip. `get`, `validate`, `resolve` use plain pyyaml-style reads.

### 1.5 `install.sh`

```
Usage: bash install.sh [--prefix DIR]   # default: ~/.local/bin
```

- Creates `<prefix>/levers` as a symlink to `$(realpath <repo>/levers)` so `git pull` updates pick up automatically
- Verifies `uv` is on PATH (warn-then-continue if missing; shebang will fail at runtime otherwise)
- Idempotent; refuses to overwrite a non-symlink without `--force`
- Prints what it did

### 1.6 Doc port — non-mechanical edits required

| Source | Target | Edits needed |
|---|---|---|
| `skills/protocol-levers/SKILL.md` | `docs/spec.md` | Strip skill frontmatter. Rewrite "LEVERS.md frontmatter + markdown" → ".levers.yml flat YAML". Drop "Prose body" section. Drop "Format" + "Alternatives considered" sub-sections. Replace "Validation" / "Rendering the schema" sections with CLI subcommand references. Rewrite "Who references this protocol" table. |
| `skills/LEVERS_REFERENCE.md` | `docs/reference.md` | Light: rewrite the "Where these levers get encoded" callout to point at `docs/spec.md`. Otherwise verbatim. |
| `skills/LEVERS_STANDARD.md` | (dropped) | Diff against current SKILL.md → fold any unique content into `docs/spec.md`, then drop. |
| `skills/protocol-levers/audit.sh` + `tron/scripts/levers-audit.sh` drift rules | `docs/drift.md` | New short doc enumerating each drift check. |

### 1.7 Execution order

1. **Skeleton** — `git init`, LICENSE, `.gitignore`, `.python-version`, empty `levers` with PEP 723 header + Typer hello-world
2. **install.sh** — symlink mechanic; smoke `levers --help` from PATH
3. **schema.yml** — hand-authored from `schema.txt` + SKILL.md schema tables + strictness order
4. **templates/** — three starter `.levers.yml` files
5. **Read-only commands** — `validate`, `list-enums`, `get`
6. **Write commands** — `set`, `init`, `add-package`
7. **`resolve`** — including `--merge-strictest`
8. **`audit`** — merged drift logic; `--strict` + summary
9. **`detect-packages`**
10. **docs/** — `spec.md`, `reference.md`, `drift.md`
11. **README.md**
12. **tests/** — fixtures + pytest, subprocess-based integration tests
13. **End-to-end smoke** — `bash install.sh` → run each subcommand against a fixture

Each step is one logical commit. Local-only until `gh repo create` is OKed.

### 1.8 Deferred to later phases

- `gh repo create` (public, MIT, description)
- Adoption in tron (Phase 2)
- Retirement of `skills/protocol-levers/` (Phase 3)
- Tron's local `scripts/levers-audit.sh` — superseded once the new CLI is installed; address in Phase 2 or 3
- PyPI publish (not needed; shebang script + symlink covers distribution)
