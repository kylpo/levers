# Examples

Drop-in git hooks and a GitHub Actions workflow that wire `levers validate` + `levers audit` into your repo's quality gates.

Two different checks, two different blocking policies:

- **`levers validate`** — schema correctness (YAML well-formed, keys recognized, values in their enums, required keys present). A malformed `.levers.yml` is a bug, not drift. **Always blocking**, on every surface.
- **`levers audit`** — declared values vs. observable repo signals (git authors, tags, workflow triggers). Advisory by default; **`--strict` exits non-zero** on any drift warning.

## Files

| Path | Validate | Audit |
| --- | --- | --- |
| [`hooks/pre-commit`](./hooks/pre-commit) | blocks | advisory (warns only) |
| [`hooks/pre-push`](./hooks/pre-push) | blocks | blocks (`--strict`) |
| [`github-actions/levers-audit.yml`](./github-actions/levers-audit.yml) | blocks | blocks (`--strict`) |
| [`claude-code/settings.json`](./claude-code/settings.json) | n/a — agent read guard | n/a — agent read guard |

The split on audit: surface drift early at commit time so you see it while context is hot, but don't interrupt the local edit-commit loop. Block at push and on CI, where the cost of fixing is paid once instead of every commit. Validate is uniformly blocking — there's no reason to land a broken schema.

The pre-commit hook short-circuits unless the staged set includes a `.levers.yml` — other commits don't move the declared side of the diff, so the result hasn't changed since the last run.

## Install

### Git hooks

Symlink so updates to the example files propagate without re-copying:

```bash
ln -s "$(pwd)/examples/hooks/pre-commit" .git/hooks/pre-commit
ln -s "$(pwd)/examples/hooks/pre-push"   .git/hooks/pre-push
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

Or copy if you want to edit per-repo:

```bash
cp examples/hooks/pre-commit .git/hooks/pre-commit
cp examples/hooks/pre-push   .git/hooks/pre-push
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

Bypass either hook with `--no-verify` (`git commit --no-verify`, `git push --no-verify`).

If you already have a `pre-commit` / `pre-push` hook, chain to this one rather than overwriting it — call it as a step, or use a multiplexer like [`pre-commit`](https://pre-commit.com/) or [`lefthook`](https://github.com/evilmartians/lefthook).

### GitHub Actions

Drop the workflow into your repo:

```bash
mkdir -p .github/workflows
cp examples/github-actions/levers-audit.yml .github/workflows/
```

The workflow needs no secrets — it clones the public [`kylpo/levers`](https://github.com/kylpo/levers) repo and runs the script via `uv`. To make drift a merge blocker, add the `levers-audit` check to your branch protection rules.

### Claude Code hooks

Two `PreToolUse` hooks that intercept agent access to `.levers.yml` and redirect to `levers get`. Without them, a coding agent reading a package-level `.levers.yml` directly sees only the local overrides — not the merged effective view after inheritance from the root file. The hooks deny:

- **Bash** commands that reference `.levers.yml`, except when the command itself is one of `levers get | merge-strictest | validate | audit | set | init | detect-packages | list-enums`.
- **Read** of any path matching `.levers.yml`.

Merge [`claude-code/settings.json`](./claude-code/settings.json) into your project's `.claude/settings.json` (or `~/.claude/settings.json` for user-wide). If you already have `hooks.PreToolUse` entries, append these two matchers rather than overwriting the array.

## Monorepos

No special handling needed. Bare `levers validate` walks the tree from the repo root, finds every `.levers.yml`, and infers the role per file: root file → `root` if nested packages exist (or inferred from declared scopes otherwise), nested files → `package`. `levers audit` already auto-discovers the same way. The example hooks and workflow work unchanged for single-repo and monorepo layouts.

Override the inferred role only when you need to: `levers validate --role root` or `levers validate path/to/.levers.yml --role package`.

## Tradeoffs

These examples are starting points, not policy. Reasonable variations:

- **Run audit only when `.levers.yml` changes in CI too** — match the pre-commit gate by filtering the workflow on `paths: ['**/.levers.yml']`. Tightens cost; loosens coverage when observable signals (authors, tags) drift without the declared file changing.
- **Advisory in CI, strict at push** — keep the workflow as a comment-only signal (`levers audit` without `--strict`) and rely on the pre-push hook as the gate. Cheaper PR experience, weaker enforcement.
- **Strict at commit too** — use `levers audit --strict` in the pre-commit hook. Catches drift earliest; pays the cost on every relevant commit and can't be deferred without `--no-verify`.

Pick what matches your `team_mode` and `ci_gate` — solo developers usually want everything advisory; teams with `gates_merge` usually want strict CI plus an advisory pre-commit.
