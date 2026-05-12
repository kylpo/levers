# Contributing

Thanks for your interest in levers. This file covers the dev-side: how to run the code from a clone, run the tests, and where to look when changing the schema.

## Prerequisites

- Python ≥ 3.12
- [`uv`](https://docs.astral.sh/uv/) on `PATH`

There is no `pip install` step and no virtualenv to manage. The CLI is a single-file script with [PEP 723](https://peps.python.org/pep-0723/) inline dependencies; `uv` resolves and caches them on first run.

## Running the CLI from a clone

```bash
git clone https://github.com/kylpo/levers
cd levers
./levers --help
```

For a wired-up install that tracks the clone, run `bash install.sh` — it symlinks `~/.local/bin/levers` to `./levers`, so edits in the clone are picked up immediately.

## Running the tests

The test suite uses `pytest`. Run it through `uv` so dependencies are resolved on the fly:

```bash
uv run --with pytest --with pyyaml --with jsonschema pytest
```

Verbose, with per-test names:

```bash
uv run --with pytest --with pyyaml --with jsonschema pytest -v
```

Single file or single test:

```bash
uv run --with pytest --with pyyaml --with jsonschema pytest tests/test_cli.py
uv run --with pytest --with pyyaml --with jsonschema pytest tests/test_cli.py::test_validate_passes_on_template
```

The suite is two files:

- `tests/test_cli.py` — end-to-end CLI behavior (`init`, `validate`, `get`, `set`, `list-enums`, `merge-strictest`, `detect-packages`, `audit`).
- `tests/test_schema.py` — invariants on `schema.yml` and that the bundled templates validate against it.

## Repo layout

- `levers` — single-file CLI script (PEP 723 inline deps).
- `schema.yml` — single source of truth for keys, scopes, allowed values, strictness orderings. Most behavior changes start here.
- `templates/` — `single.yml`, `root.yml`, `package.yml` written by `levers init` for each role.
- `docs/` — spec, reference (lever rationale), drift checks.
- `examples/` — drop-in hooks, GitHub Actions, and Claude Code wiring.
- `tests/` — pytest suite.

## Changing the schema

`schema.yml` is the single source of truth. When you add, rename, or change a lever:

1. Edit `schema.yml` — keep `scope`, `values`, and (if applicable) `strictness` consistent.
2. Update the relevant template(s) in `templates/` so `init` still emits a valid file.
3. Update `docs/spec.md` (schema table) and `docs/reference.md` (rationale) to match.
4. If the lever has an observable repo signal, add or update its check in `docs/drift.md` and the `audit` command.
5. Run the full test suite. `test_schema.py` will catch most structural drift; `test_cli.py` covers behavior.

## Style

- Match the surrounding code. The CLI is intentionally a single file — keep it that way unless there is a strong reason not to.
- Comments explain *why*, not *what*. The schema and enum names already say *what*.
- Preserve comments and key ordering on writes (`ruamel.yaml` round-trip mode). Tests guard this.

## Submitting changes

- Open a PR against `main`.
- Include a short rationale for schema changes — what policy gap the new value covers, or why an existing value is being renamed/removed.
- Make sure `uv run --with pytest --with pyyaml --with jsonschema pytest` is green locally.
