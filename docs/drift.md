# Drift detection

`levers audit` compares declared `.levers.yml` values against observable repo signals (git log, git tags, GitHub workflows) and emits warnings when they disagree. Drift is a human-attention signal, not a blocker — `audit` exits 0 even when warnings are present, unless `--strict` is passed.

Run on demand:

```bash
levers audit                  # root + every nested package
levers audit --root           # only the root file
levers audit --package <dir>  # only that package
levers audit --strict         # exit non-zero on any warning (intended for CI)
```

## Checks

### `team_mode` (root)

> declared `team_mode: solo`, observed N unique authors in the last 90 days

**Trigger:** `team_mode: solo` declared at root, but `git log --since='90 days ago' --format=%ae` shows more than one unique email.

**Action:** flip to `small_team` or `large_team`, or explain the deviation in `DECISIONS.md` if the extra authors are intentional (rebase squash artifacts, bot commits, etc.).

### `ci_gate` (root)

> declared `ci_gate: none`, observed push/pull_request workflows under .github/workflows

**Trigger:** `ci_gate: none` declared at root, and at least one file under `.github/workflows/` has a top-level `on: push:` or `on: pull_request:` trigger.

**Action:** if CI actually gates merges, flip to `advisory` or `gates_merge`. If CI runs but doesn't block (e.g., flaky tests intentionally non-blocking), keep `none` and document why in `DECISIONS.md`. To narrow the scope, override `ci_gate` per-package instead.

### `ci_gate` (package)

> declared `ci_gate: none`, observed a workflow referencing '\<rel\>' or '\<basename\>/'

**Trigger:** A package overrides `ci_gate: none`, push/pull_request workflows exist, and at least one workflow file textually references the package's relative path or basename (heuristic — substring match, not a full path-filter parser).

**Action:** if the workflow actually gates merges for this package, update the override. False positives are possible (the workflow might mention the package only in a comment) — when that's the case, ignore the warning.

### `lifecycle_stage` (package)

> declared `lifecycle_stage: \<stage\>`, observed `\<tag\>` (\<N\>d old)

**Trigger:** `lifecycle_stage` is `prototype` or `pre_launch`, and a package-tagged release of v1.0.0 or higher exists more than 30 days old. Package tags match `<basename>-v...` or `<basename>/v...`.

**Action:** if v1+ has been out for more than a month, the project has launched — flip to `post_launch` (or `mature` if it's been years).

### `versioning` (package)

> declared `versioning: semver`, latest package tag '\<tag\>' is not semver-shaped

**Trigger:** `versioning: semver` declared, but the latest matching package tag's version tail doesn't match `MAJOR.MINOR.PATCH[-prerelease][+build]`.

**Action:** if the project actually tags non-semver, flip to `calver` or `adhoc`. If the offending tag is a one-off mistake, retag and the warning goes away on next audit.

### `release_model` + `release_cadence` contradiction (package)

> declared `release_model: continuous` but `release_cadence: milestone` — these contradict

**Trigger:** internal contradiction in a single package's declaration. "Continuous" means ship as you go; "milestone" means ship on planned events. They can't both be true.

**Action:** pick the one that matches reality. Continuous → `on_demand` / `weekly` / `biweekly`. Milestone → `batched_timeline` / `release_branch`.

### `code_review` + `code_review_concurrency` contradiction (root or package)

> declared `code_review: apply` with `code_review_concurrency: parallel` — reviewers writing to the same files concurrently can produce conflicting edits

**Trigger:** `code_review: apply` (reviewers apply edits directly) combined with `code_review_concurrency: parallel`. Concurrent reviewers writing the same files race on overlapping edits.

**Action:** flip concurrency to `series` (reviewers run one at a time, each seeing the prior reviewer's fixes), or switch `code_review` to `advisory` (reviewers surface findings as comments rather than applying them — no write contention, so `parallel` is safe).

### `agent_breadcrumb_commits` + active pre-commit hook (root or package)

> declared `agent_breadcrumb_commits: on` with an executable `.git/hooks/pre-commit` installed

**Trigger:** `agent_breadcrumb_commits: on` declared, and `.git/hooks/pre-commit` exists and is executable. Git's bundled `pre-commit.sample` is ignored — only the literal `pre-commit` filename runs. Reviewer breadcrumb commits go through the same hook as every other commit, so a hook that aborts (lint failure, formatter rewrite, etc.) breaks review flows like `/review-all`.

**Action:** flip `agent_breadcrumb_commits` to `off`, or have the hook short-circuit on agent-authored commits (e.g., skip when the committer email matches a known agent, or when the commit message carries a breadcrumb marker).

## Tag-matching convention

Per-package tag checks (`lifecycle_stage`, `versioning`) use this convention to associate a tag with a package:

- `<basename>-vMAJOR.MINOR.PATCH` — e.g., `mobile-v1.2.3`
- `<basename>/vMAJOR.MINOR.PATCH` — e.g., `mobile/v1.2.3`

Tags that don't match this shape are ignored by per-package drift checks. Root-level drift checks (`team_mode`, `ci_gate`) are tag-agnostic.

## Caveats

- The workflow-mention check is a substring heuristic, not a full GitHub Actions parser. It's deliberately loose — false positives are cheaper than missed real problems, because drift output is advisory.
- `team_mode` drift uses email-uniqueness, which can split if a contributor uses two emails (work + personal). Document in `DECISIONS.md` if relevant.
- All checks run against the local git state. They won't catch drift introduced by pushed-but-not-pulled changes elsewhere.
