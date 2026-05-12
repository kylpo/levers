# `.levers.yml` — format specification

Defines the format, schema, and ownership of `.levers.yml` — a per-project living config that declares the policy-level shape of a development pipeline in a form both humans and tools can read reliably.

Companion reference: [reference.md](./reference.md) enumerates the full tradeoff space behind each lever. This spec is the *encoding* — `reference.md` is the *rationale*.

## Purpose

Tools and skills route behavior based on project policy: "do migration planning apply?", "wait for CI before merge?", "must `main` be always-deployable?". Encoding those answers in a checked-in file gets you:

1. Consistent, unambiguous answers without re-asking.
2. Lever transitions become explicit, git-diffable events.
3. One place to reason about "how does this project actually work?"

## What it is not

- **Not a product description** — that's `PRODUCT.md`.
- **Not a how-to guide for agents** — that's `CLAUDE.md`.
- **Not a decision log** — `DECISIONS.md` captures the *why* of each lever choice. `.levers.yml` captures the *current value*. A lever flip should append a `DEC-P` record explaining the transition.
- **Not aspirational** — declare what is true today, not what will be true after the next milestone. Update on transition, not before.
- **Not a superset of [reference.md](./reference.md)** — only includes levers that route tool behavior and can't be inferred. Observable levers (greenfield/brownfield, contributor count) stay inferred by the consumers that care.

## Format: flat YAML

```yaml
# .levers.yml
lifecycle_stage: pre_launch
team_mode: solo
ci_gate: gates_merge
# ...
```

One key per declared lever, value is a strict enum string. No nesting, no prose body — rationale belongs in `DECISIONS.md`. The file is YAML so any parser (`yq`, Python's `pyyaml`, etc.) reads it without custom code.

Comments are preserved on roundtrip when written via `levers set` / `levers init` (uses `ruamel.yaml`), so users can keep inline notes above keys without the tool stomping them.

## Location

`.levers.yml` lives at the repo root. In a monorepo, the root file is still there, plus one `.levers.yml` per package directory (`apps/mobile/.levers.yml`, `packages/shared/.levers.yml`, etc.).

## Ownership

**Human-maintained. Tools should not write to it without explicit instruction.** This is deliberate: a tool that routes on `.levers.yml` values shouldn't also be able to flip them silently. Same rule as `CLAUDE.md`.

`levers set` / `levers init` are explicit, user-invoked writes — fine. Anything else (a skill auto-mutating values based on observed state) is not.

Update triggers:

- **Project bootstrap** — `levers init` walks the user through the lever set and writes the initial file.
- **Lifecycle transitions** — launch day, team growth from 1 to 3, compliance event, platform pivot.
- **Deliberate pipeline reshape** — user explicitly changes how they want the pipeline to run.

A lever flip should always be paired with a `DEC-P` record in `DECISIONS.md` (single-repo) or the relevant package's `DECISIONS.md` (monorepo, for `package`-scoped flips). Without the rationale trail, future-you won't know whether the flip was intentional or accidental.

## Schema

All keys required for their role (single / root / package) unless noted. Values are strict enums — unknown values fail validation. A project that doesn't have a confident answer should pick the closest enum and document the deviation in `DECISIONS.md`.

Source of truth: [`schema.yml`](../schema.yml). The tables below are kept in sync by hand; if they drift, `schema.yml` wins.

Every lever has a **scope** attribute — one of `repo`, `package`, or `either`:

- **`repo`** — declared only at the root `.levers.yml`. These describe how humans and tools operate on the whole repo (team shape, collaboration rules, branch model). Declaring a `repo`-scoped key at a package fails validation.
- **`package`** — declared only at per-package `.levers.yml` files in monorepos. These describe properties that vary per deliverable (lifecycle stage, release model, QA discipline). Declaring a `package`-scoped key at root fails validation. In a single-repo setup, the repo *is* the only package, and `package`-scoped keys are declared at the root file (validated under `--role single`).
- **`either`** — may be declared at root with a project-wide default, and optionally overridden per-package. Useful for levers that often apply repo-wide but sometimes need local override (test strategy, CI gate, auto-merge, design discipline).

See [Monorepo layout](#monorepo-layout) for how these resolve via `levers get`.

### Lifecycle & risk

| Key | Scope | Values |
|---|---|---|
| `lifecycle_stage` | `package` | `prototype` \| `pre_launch` \| `post_launch` \| `mature` |

### Team & collaboration

| Key | Scope | Values |
|---|---|---|
| `team_mode` | `repo` | `solo` \| `small_team` \| `large_team` |
| `review_cadence` | `repo` | `sync` \| `async` |

### Planning & execution

| Key | Scope | Values |
|---|---|---|
| `planning_horizon` | `either` | `big_bang` \| `phased` \| `just_in_time` |

### Quality

| Key | Scope | Values |
|---|---|---|
| `test_strategy` | `either` | `coverage_delta` \| `test_after` \| `manual_only` |
| `manual_qa_capture` | `package` | `captured` \| `not_captured` |
| `ci_gate` | `either` | `none` \| `advisory` \| `gates_merge` |
| `code_review` | `either` | `none` \| `inline` \| `subagent` \| `subagent_advisory` |

### Release & delivery

| Key | Scope | Values |
|---|---|---|
| `release_model` | `package` | `continuous` \| `batched_timeline` \| `batched_feature_scoped` \| `release_branch` |
| `branch_strategy` | `repo` | `trunk_based` \| `gitflow` \| `feature_branches_plus_trunk` |
| `release_cadence` | `package` | `on_demand` \| `weekly` \| `biweekly` \| `monthly` \| `milestone` |
| `versioning` | `package` | `semver` \| `calver` \| `adhoc` |

### Automation

| Key | Scope | Values |
|---|---|---|
| `agent_auto_merge` | `either` | `none` \| `low_risk_only` \| `all` |
| `bug_intake` | `repo` | `manual` \| `funneled` |

### Documentation

| Key | Scope | Values |
|---|---|---|
| `changelog_style` | `package` | `commit_log` \| `curated` |
| `doc_sync` | `either` | `none` \| `inline` \| `subagent` \| `subagent_advisory` |

### Workspace

| Key | Scope | Values |
|---|---|---|
| `workspace_isolation` | `repo` | `worktree` \| `branch` \| `none` |

### Scope summary

| Scope | Keys |
|---|---|
| `repo` | `team_mode`, `review_cadence`, `bug_intake`, `branch_strategy`, `workspace_isolation` |
| `package` | `lifecycle_stage`, `release_model`, `release_cadence`, `versioning`, `manual_qa_capture`, `changelog_style` |
| `either` | `test_strategy`, `ci_gate`, `agent_auto_merge`, `planning_horizon`, `doc_sync`, `code_review` |

## Monorepo layout

A monorepo has a root `.levers.yml` plus one `.levers.yml` per package. A single-repo setup carries everything in the root file (`repo` + `package` + `either`).

**Validator roles:**

- `levers validate --role root` — requires all `repo`-scoped keys; rejects `package`-scoped keys; accepts `either` with defaults.
- `levers validate --role package` — requires all `package`-scoped keys; rejects `repo`-scoped keys; accepts `either` as overrides.
- `levers validate --role single` (default) — requires all `repo` + all `package` keys in one file; `either` keys carry defaults.

**Effective values at a path** — consumer tools call:

```bash
levers get <key> --at <path>             # single raw value (no fences)
levers get --at <path>                   # full merged view, YAML with provenance header
levers get --at <path> --keys k1,k2      # narrow to a key list
```

Which:

1. Loads the root `.levers.yml`.
2. Finds the nearest-ancestor package `.levers.yml` (stopping at repo root; excluding root itself).
3. Merges: start with root; overlay package. `either` values override; `package` keys live only in the package file; `repo` keys only at root.
4. Narrows to the requested key list (if any) and emits YAML or a single raw value.

Consumers never traverse or merge themselves. The key list passed to `levers get` serves as an auditable declaration of which levers drive the consumer's behavior.

Reads are always inheritance-aware. Writes (`levers set`) are file-local: writes are explicit about *which* file changes; reads always return the value a consumer at that path would see.

**Cross-package changes** — when a ticket or commit touches files in multiple packages, use `levers detect-packages <paths...>` to enumerate the affected packages. Prefer per-package splitting; when a merged view is unavoidable (e.g., unattended automation), `levers merge-strictest <paths...>` returns the strictest value per lever per the rules below.

**Single-repo fallback** — on a repo that has no per-package `.levers.yml` files, `levers get` returns the root values unchanged. Adoption is package-by-package — a half-configured monorepo still works.

### Strictest-wins merge

When `levers merge-strictest` is called with paths spanning multiple packages, each lever's value is chosen by the rule below. The orderings reflect "which answer is safest if applied to the whole change set." For ties, the leftmost value in the table wins.

| Lever | Strictness order (strictest → loosest) |
|---|---|
| `agent_auto_merge` | `none` → `low_risk_only` → `all` |
| `ci_gate` | `gates_merge` → `advisory` → `none` |
| `test_strategy` | `coverage_delta` → `test_after` → `manual_only` |
| `lifecycle_stage` | `mature` → `post_launch` → `pre_launch` → `prototype` |
| `manual_qa_capture` | `captured` → `not_captured` |
| `release_model` | `release_branch` → `batched_timeline` → `batched_feature_scoped` → `continuous` |
| `planning_horizon` | `big_bang` → `phased` → `just_in_time` |
| `doc_sync` | `subagent_advisory` → `subagent` → `inline` → `none` |
| `code_review` | `subagent_advisory` → `subagent` → `inline` → `none` |

Levers not in the table (e.g., `versioning`, `release_cadence`) are not meaningfully comparable for strictness — `levers merge-strictest` fails with an error if asked to merge them across packages with diverging values, forcing the human to pick or split.

When all paths agree on a value, the strictness check is bypassed even for levers without a strictness order.

## Templates

Three starters depending on the repo shape:

- [`templates/single.yml`](../templates/single.yml) — **single-repo projects.** All keys in one file. `levers init` (default `--role single`) copies this.
- [`templates/root.yml`](../templates/root.yml) — **monorepo root.** `repo` + `either` keys. `levers init --role root` copies this.
- [`templates/package.yml`](../templates/package.yml) — **per-package in a monorepo.** `package` keys (required) + commented-out `either` overrides. `levers init --role package --at <path>` copies this once per detected package.

## Drift detection

Some levers are partially observable from the repo — `levers audit` compares declared vs observed state and surfaces inconsistencies. Failing the check doesn't block work; it flags a stale declaration for human attention.

See [drift.md](./drift.md) for the full check list. Run on demand:

```bash
levers audit                  # root + every nested package
levers audit --root           # only the root file
levers audit --package <dir>  # only that package
levers audit --strict         # exit non-zero on any warning (for CI)
```

## Validation

```bash
levers validate                                  # default role=single
levers validate --role root                      # monorepo root
levers validate --role package apps/mobile/.levers.yml
```

- Parses the YAML (fails on malformed input).
- Checks every required key is present for the role.
- Checks every value is in the allowed enum.
- Checks no forbidden-for-role keys appear (e.g., `package`-scoped keys in `--role root`).
- Emits actionable error messages.

The allowed-enum data lives in [`schema.yml`](../schema.yml) — canonical source of truth for both `validate` and `list-enums`.

## Listing the schema

`levers list-enums` reads `schema.yml` and emits the allowed enum values, grouped by category, with scope annotations. Useful when interviewing a user about lever choices or scripting a prompt.

```bash
levers list-enums                       # all keys, grouped by category
levers list-enums --key ci_gate         # one key
levers list-enums --role root           # filter to keys valid at root
levers list-enums --format yaml         # `key: [v1, v2, v3]` format
```

The self-consistency guarantee — every value emitted for every key validates under `levers validate` — is a hard property of the schema-driven design (same source).

---

## FAQ

### Why a separate `.levers.yml` instead of folding into `CLAUDE.md`?

`CLAUDE.md` is auto-loaded by Claude Code at session start, which is convenient. But it's also explicitly "agent conventions, kept small — no product detail." Project policy levers aren't agent conventions; folding them in blows past the discipline that keeps `CLAUDE.md` useful.

The decisive points:

- **Parseability.** `.levers.yml` validates cleanly with a static enum list. Lever values embedded in free-form `CLAUDE.md` prose would require LLM parsing — no reliable `validate`, no reliable drift detection.
- **Invisible dependencies.** A tool that reads `.levers.yml` declares that dependency explicitly. A tool that "reads `CLAUDE.md` because it's always loaded" has an implicit dependency that's harder to audit and change.
- **Mixed update cadences.** Coding conventions are stable; lever values flip on lifecycle transitions. One file with two cadences muddies git history and weakens the `DEC-P` pairing trail.
- **Accidental flips.** A human editing `CLAUDE.md` for a convention tweak can inadvertently touch a lever line. Separate files isolate the risk.

`CLAUDE.md` can carry a one-line pointer ("Policy levers are in `.levers.yml`") so agents discover the dependency without bloating `CLAUDE.md` or losing the validator.

### Why isn't this just another section in `DECISIONS.md`?

`DECISIONS.md` captures the *why* (with context, options, consequences) of each lever choice. `.levers.yml` captures the *current value*. A lever flip appends a new `DEC-P` record explaining the transition; `.levers.yml` reflects the new value. Reading `DECISIONS.md` to derive the current state would require scanning for the latest `DEC-P` record per lever — fragile and slow.

### Why strict enums instead of free-form strings?

Strict enums let a tool branch on values (`case`-friendly), catch typos at validation time, and produce useful error messages. Free-form strings push interpretation into each consumer, leading to inconsistent handling (`"pre_launch"` vs `"pre-launch"` vs `"Pre-Launch"`).

The cost of enum rigidity — real projects that don't fit — is handled by `DECISIONS.md`, where exceptions and overrides are explained. Widen the enum only when a third project hits the same wall.

### What happens when an enum doesn't fit a project?

Pick the closest value and explain the deviation in a `DECISIONS.md` `DEC-P` record. The validator's enum list is the "paved road"; `DECISIONS.md` is the escape valve.

### Does every project need `.levers.yml`?

Yes, any project that consumer tools touch should have one. The defaults are chosen so that a solo greenfield prototype can accept them wholesale without meaningful thought — the file exists to lock in the assumptions, not to force decisions that aren't needed yet. Projects that opt out of the tooling entirely don't need it.

### Can a tool write to `.levers.yml`?

Only via explicit user invocation (`levers set`, `levers init`). Same rule as `CLAUDE.md`: a tool that routes on lever values shouldn't also flip them autonomously — the resulting feedback loop ("tool decides to change policy so its own behavior changes") is dangerous. Tools surface drift via `levers audit`; humans decide what to update.

### What if I have a prose body in an old `LEVERS.md` file?

Migrate the format hand: the YAML keys/values move to `.levers.yml`, and the rationale prose moves to `DECISIONS.md` as `DEC-P` records (one per non-default choice). The new format deliberately drops the prose body — the rationale belongs in the decision log where it can be referenced, not duplicated.
