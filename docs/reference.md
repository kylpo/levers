# Pipeline Levers

A reference for shaping a product-development pipeline. Each lever is a design choice whose sides have concrete, mechanical consequences for how work flows, what artifacts you need, and where the bottlenecks end up. No pipeline can avoid these choices — defaulting is itself a choice, usually a bad one.

Use this document at the start of a project to justify the shape you land on, and later to diagnose why the pipeline feels wrong. Most pipeline pain comes from one of two sources: a lever set the wrong way for the actual context, or two levers that disagree with each other (e.g., "continuous delivery" + "async human review" — the combination is contradictory).

> **Where these levers get encoded.** The subset of levers that actually routes tool behavior is captured per-project in `.levers.yml` — see [`spec.md`](./spec.md) for the format. This document is the *tradeoff rationale* for every lever; `.levers.yml` is the *current value* for the levers a project declares. Observable levers (greenfield/brownfield, contributor count) stay inferred by the consumers that care and are not encoded in `.levers.yml`.
>
> **Temporary deviations: modes.** Need to flip a cluster of these levers for a throwaway spike or a touchy legacy refactor? `.levers.yml` supports named overlays — see the [Modes section in spec.md](./spec.md#modes). The seeded `prototype` / `greenfield` / `brownfield` modes are project-owned data; edit, rename, or replace as needed.

---

## At a glance

| Lever | Side A | Side B |
|---|---|---|
| **1. Project shape & lifecycle** | | |
| [1.1 Greenfield vs brownfield](#11-greenfield-vs-brownfield) | **Greenfield:** top-down design from scratch; interview mode | **Brownfield:** reverse-engineer from code; clarifying questions only |
| [1.2 Throwaway vs long-lived](#12-throwawayprototype-vs-long-lived) | **Throwaway:** skip artifacts, hold in head, direct commits | **Long-lived:** every doc pays off; decision logs survive years |
| [1.3 Pre-launch vs post-launch](#13-pre-launch-vs-post-launch) | **Pre-launch:** breaking changes free; no compat burden | **Post-launch:** change-impact gate; migrations and deprecations |
| [1.4 Deploy reversibility](#14-deploy-reversibility) | **Easy (SaaS):** ship liberally, rollback in minutes | **Hard (mobile/firmware/on-prem):** heavy preflight; feature flags mandatory |
| [1.5 Regulated vs unconstrained](#15-regulated-vs-unconstrained) | **Unconstrained:** informal, agent auto-merge fine | **Regulated:** named reviewers, audit trail, no AI-only merges |
| **2. Team & collaboration** | | |
| [2.1 Team size](#21-solo-vs-small-team-vs-large-team) | **Solo:** no roles, no review ceremony, informal decisions | **Team:** roles, review gates, collision mitigation, formal planning |
| [2.2 Sync vs parallel work](#22-synchronous-vs-parallel-work) | **Synchronous:** edit docs freely, no conflicts, one actor at a time | **Parallel:** append-only logs, atomic claims, isolation mandatory |
| [2.3 Sync vs async review](#23-sync-vs-async-review) | **Sync review:** small PRs, fast iteration, reviewer on critical path | **Async review:** PRs must be reviewable cold; richer ticket bodies |
| [2.4 Approval gating](#24-approval-gating) | **Direct / auto-merge:** max speed, tests substitute for review | **Required approver:** quality gate, reviewer is bottleneck |
| [2.5 Role encoding](#25-role-encoding) | **Agnostic:** anyone touches any artifact | **Encoded:** explicit ownership, formal handoffs |
| **3. Planning & design** | | |
| [3.1 Upfront vs emergent design](#31-upfront-design-vs-emergent-design) | **Upfront:** onboarding-friendly, roadmappable, agent-ready | **Emergent:** responsive to real difficulty; agents struggle without a target |
| [3.2 Planning horizon](#32-planning-horizon) | **Big-bang:** full visibility, stales fast | **Phased / just-in-time:** adaptive, weak long-range view |
| [3.3 Ticket granularity](#33-ticket-granularity) | **Fine-grained:** parallelism, reviewable PRs, agent-friendly | **Coarse:** single-context work, less planning overhead |
| [3.4 Layered vs all-at-once](#34-layered-vs-all-at-once-implementation) | **Layered (logic→wiring→polish):** per-layer quality strategy | **All-at-once:** single-PR feature shipping |
| [3.5 Container hierarchy](#35-container-hierarchy) | **Flat:** one object type, no grouping | **Epic/feature containers:** expresses batch vs capability |
| **4. Execution & ticketing** | | |
| [4.1 Formal vs informal tickets](#41-formal-ticket-system-vs-informal-task-list) | **Informal:** zero ceremony, not agent-pickable | **Formal:** agent-pickable, auditable, dependency-tracked |
| [4.2 Dependency expression](#42-dependency-expression) | **Implicit:** in the author's head | **Explicit (Blocked By):** safe parallel pickup |
| [4.3 Claim protocol](#43-claim-protocol) | **Advisory (label/assignment):** courteous only | **Atomic (earliest-wins):** race-safe under parallelism |
| [4.4 Priority expression](#44-priority-expression) | **Manual / none:** someone chooses by hand | **Tag-based or ranked:** programmatic pickup order |
| **5. Quality & verification** | | |
| [5.1 Test strategy](#51-test-first-vs-test-after-vs-manual-only) | **TDD:** clear agent loop, less code exploration | **Test-after / manual:** faster iteration, weaker regression safety |
| [5.2 Manual QA capture](#52-manual-qa-capture) | **Not captured:** flexible, tests lost between releases | **Accumulated log:** regression suite grows; preflight cost grows with it |
| [5.3 CI integration](#53-ci-integration) | **Local only:** fast merge, no multi-env coverage | **CI gates merges:** enforceable, adds latency floor to cycle time |
| [5.4 Doc-sync enforcement](#54-pre-merge-doc-sync-enforcement) | **None:** fast; docs drift and get ignored | **Enforced (hook):** docs-as-SoT is real, not aspirational |
| [5.5 Secrets / env](#55-environment--secrets-strategy) | **Committed (encrypted):** agents can run integration tests | **Human-hydrated:** secure; agents can't run integration tests |
| **6. Release & delivery** | | |
| [6.1 CD vs batched releases](#61-continuous-delivery-vs-batched-releases) | **Continuous delivery:** main always shippable; forces sync review | **Batched:** timeline, feature-scoped (solo-friendly), or release-branch — see section |
| [6.2 Branch strategy](#62-branch-strategy) | **Trunk-based:** simple; tags are releases | **Gitflow / release branches:** parallel-version support; cherry-pick tax |
| [6.3 Feature flags](#63-feature-flags) | **None:** simple; what's in main is shipped | **Flagged:** progressive rollout, A/B, kill switches; flag debt accrues |
| [6.4 Release cadence](#64-release-cadence) | **On-demand:** responsive, unpredictable for users | **Fixed cadence:** predictable, slips urgent changes without hotfix path |
| [6.5 Versioning](#65-versioning-discipline) | **SemVer:** downstream trust; every change needs classification | **Ad-hoc / CalVer:** fast; no compatibility signal |
| [6.6 PR merge method](#66-pr-merge-method) | **Merge:** full history + merge boundary; non-linear log | **Squash:** one commit per PR; loses per-commit intent. **Rebase:** linear + per-commit; no merge boundary, SHAs change |
| **7. Knowledge & documentation** | | |
| [7.1 SoT direction](#71-docs-as-source-of-truth-vs-code-as-source-of-truth) | **Docs-as-SoT:** rewrite-survivable; sync enforcement required | **Code-as-SoT:** fast; docs decay; readers stop trusting them |
| [7.2 Decision capture](#72-decision-capture) | **Informal (chat, heads):** no ceremony; "why" vanishes in months | **ADR log:** audit, supersession tracking, rejected-alternative memory |
| [7.3 Glossary](#73-domain-vocabulary-management) | **Emergent:** fast; same concept gets multiple names | **Formal:** coherent naming; critical for domain-heavy projects |
| [7.4 Changelog](#74-change-log-discipline) | **Commit log as changelog:** automated, developer-facing | **Curated (Keep-a-Changelog):** user-readable; needs curation |
| **8. Automation & autonomy** | | |
| [8.1 Agent share](#81-agent-heavy-vs-human-heavy-execution) | **Human-heavy:** infers loose context, judgment-rich | **Agent-heavy:** needs rigid artifacts; collision mitigation mandatory |
| [8.2 Auto-merge](#82-agent-auto-merge) | **No auto-merge:** universal review gate | **Split by lane:** safe changes auto-merge; needs reliable classifier |
| [8.3 Scheduled runs](#83-scheduled--unattended-runs) | **Invoke-only:** predictable; no overnight throughput | **Scheduled:** overnight work; needs graceful stop + alerting |
| [8.4 Bug intake](#84-bug-intake-source) | **Manual writeup:** simple, doesn't scale to multiple sources | **Funneled (Sentry, etc.):** comprehensive; maintenance cost |
| [8.5 Idea triage](#85-idea--backlog-triage) | **Synchronous:** no backlog debt; every idea interrupts | **Defer-to-queue:** focus preserved; queue bloats |
| **9. Feedback & iteration** | | |
| [9.1 Metrics culture](#91-metrics--experimentation-culture) | **Qualitative:** ship on instinct, fast | **Metrics / A-B:** evidence-based, slower cycles, infra cost |
| [9.2 User feedback loop](#92-user-feedback-loop) | **None:** vision-led; blind to real usage | **Wired channels:** ground-truth; can drag toward current-user asks |
| **10. Meta-levers** | | |
| [10.1 Bottleneck location](#101-bottleneck-location) | Identify which stage queues up — ideas, design, impl, review, QA, release — *before* optimizing elsewhere | |
| [10.2 Consistency vs speed](#102-consistency-vs-speed) | Consistency pays off over long horizons; speed pays off in low-uncertainty phases. Match to trajectory | |
| [10.3 Pipeline reversibility](#103-reversibility-of-the-pipeline-itself) | Prefer reversible lever choices early; lock in hard-to-reverse ones only when shape is clear | |

---

## How to use this document

1. **Read through to identify which levers apply.** Not every lever matters for every project. Regulated-industry levers are irrelevant to a weekend side project; agent-autonomy levers are irrelevant to a human-only workflow.
2. **For each relevant lever, pick a side and record it.** The pipeline's shape is downstream of this choice, not upstream.
3. **Check for contradictions.** Some lever combinations are incoherent (noted inline). If you've picked two incompatible sides, one has to give.
4. **Revisit when the project's context changes.** A prototype that becomes a product, a solo project that acquires a second contributor, or an unregulated tool that enters a regulated market — each is a trigger to re-evaluate.

---

# 1. Project shape & lifecycle

## 1.1 Greenfield vs brownfield

**The question:** is there existing code the pipeline must respect?

**Greenfield — starting from zero.**
- *Unlocks:* top-down authoring. You can run long design conversations that produce foundational docs (product brief, architecture, design system) before any code exists. Every decision is free.
- *Closes:* reality-grounded decisions. There's no existing system to constrain or contradict your ideas. Early choices have no feedback until code exists.
- *Pipeline implication:* doc-authoring skills can operate in "interview" mode — asking the user for direction — because no code-derived answer exists.

**Brownfield — adopting an existing codebase.**
- *Unlocks:* reverse-engineering discipline. Docs reflect reality, not aspirations. Ambiguities surface as questions ("this constant appears in two files with different values — which is canonical?").
- *Closes:* clean-slate design. Every proposed change has a migration cost. Forward-looking redesign must be channeled through a separate feature-planning path rather than mixed into doc authoring.
- *Pipeline implication:* doc-authoring skills need a distinct mode that reads code first and asks only clarifying questions. Interview-mode probes ("what's your vision?") are actively harmful — they invite the author to invent an aesthetic the code doesn't have.

**Both modes in one pipeline.** Possible and often necessary: a pipeline that works for new projects must also support adopting an existing one. The two modes are so different that they should be separate branches inside each authoring skill, not a merged path.

---

## 1.2 Throwaway/prototype vs long-lived

**The question:** will this code exist in six months?

**Throwaway.**
- *Unlocks:* skip most artifacts. No architecture doc, no test discipline, no decision log. One person holds the whole thing; direct commits to main are fine.
- *Closes:* knowledge durability. If the prototype succeeds and goes long-lived, you enter a debt period — every artifact you skipped now needs reverse-engineering.

**Long-lived.**
- *Unlocks:* every doc artifact pays off. Decision logs survive "why did we do this?" debates years later. New contributors (human or agent) can onboard from docs.
- *Closes:* fast iteration. Every meaningful change touches docs, tests, and review. The overhead is real and compounds for tiny changes.

**The trap: "might become long-lived."** Teams default to prototype discipline and discover months in that the project is now long-lived, without the artifacts it needs. If you're not sure, it's cheaper to assume long-lived and delete unused artifacts than to retrofit.

---

## 1.3 Pre-launch vs post-launch

**The question:** do live users depend on this code?

**Pre-launch.**
- *Unlocks:* breaking changes are free. You can rename everything, change the schema, delete features. No backward-compatibility burden.
- *Closes:* real user feedback. Every decision is still a guess.

**Post-launch.**
- *Unlocks:* ground-truth signals (usage, bug reports, support patterns).
- *Closes:* unilateral change. Breaking changes need migrations or versioning. Schema changes need backfills. Removing features needs deprecation cycles. The pipeline needs change-impact review, a "will this break users?" gate.

**Pipeline implication:** post-launch pipelines need a decision-capture habit, because "why did we make this backward-compatible?" recurs often and is expensive to reconstruct.

---

## 1.4 Deploy reversibility

**The question:** how fast can you undo a bad change?

**Easy reversal (SaaS, web).**
- *Unlocks:* willingness to ship unverified. Feature flags as a rollout tool. A/B tests as routine. Rollback is a deploy, often in minutes.
- *Closes:* nothing much. This is the permissive end.

**Hard reversal (mobile apps, firmware, installed software, released libraries).**
- *Unlocks:* nothing — this is a constraint.
- *Closes:* casual shipping. Every release needs serious pre-flight QA. App-store review adds days of rollback latency. Feature flags become mandatory for anything not 100% ready. Semver semantics matter more.

**No reversal (on-prem, offline, embedded, packaged libraries with long adoption cycles).**
- *Closes:* the ability to drop old versions. Backward compatibility becomes near-permanent. Release decisions are one-way doors.

**Pipeline implication:** the merge gate and the release gate look very different depending on reversal cost. SaaS can merge liberally and gate at release; mobile/firmware must gate harder at merge because release is expensive.

---

## 1.5 Regulated vs unconstrained

**The question:** does an external audit or compliance regime touch this code?

**Unconstrained.**
- *Unlocks:* informal merge paths, agent auto-merge, minimal approval ceremony, decisions can live in heads or chat.
- *Closes:* ability to sell into regulated industries later without retrofit.

**Regulated (SOC2, HIPAA, PCI, finance, healthcare).**
- *Unlocks:* nothing — constraints only.
- *Closes:* informal workflows. Every change needs an approval trail with a named human reviewer. Decisions must be captured for audit. CODEOWNERS and branch protection are non-negotiable. "An AI merged this" may be disqualifying; agent roles are limited to pre-review work.

**Pipeline implication:** regulated pipelines need formalized decision logs, mandatory human approvers, and evidence trails. The agent lane (if any) must terminate at PR-open, not merge.

---

# 2. Team & collaboration

## 2.1 Solo vs small team vs large team

**The question:** how many humans share the pipeline?

**Solo (one human, possibly many agents).**
- *Unlocks:* skip role boundaries, skip strategic-doc review cycles, skip CODEOWNERS, skip approval ceremonies. Decisions made in one head without formalization.
- *Closes:* ability to scale without retrofit. Handoff protocols don't exist. "PM owns the brief, eng owns architecture" isn't encoded anywhere.

**Small team (2–5 humans).**
- *Unlocks:* specialization (designer, PM, eng lead). Review as quality gate. Real parallelism.
- *Closes:* solo's informality. Strategic docs need draft + critique cycles. Parallel work requires collision mitigation.

**Large team (6+ humans, multiple sub-teams).**
- *Unlocks:* domain partitioning (teams own modules), formal planning cadence, dedicated QA/release roles.
- *Closes:* informality entirely. Everything needs a ticket, spec, review, milestone, and owner.

**Pipeline implication:** team size drives almost every other lever. Solo defaults are dangerously wrong for teams; team defaults are crushingly expensive for solo.

---

## 2.2 Synchronous vs parallel work

**The question:** can multiple actors (humans, agents) work on the repo simultaneously?

**Synchronous — one actor at a time on shared state.**
- *Unlocks:* no merge conflicts. Docs can be edited inline freely. Shared files (decision logs, glossaries) are safe to modify mid-session. Decisions can stay in conversation without formal capture.
- *Closes:* throughput. The bottleneck is whoever is currently working. Overnight or scheduled work can't interleave with live work.

**Parallel — multiple actors concurrently.**
- *Unlocks:* throughput. Agents work overnight; humans review during the day. Multiple tickets advance at once.
- *Closes:* freeform editing. You now need conventions and mechanisms:
  - **Append-only logs** (decision records, changelogs) — safe because new entries don't conflict.
  - **Prefer-append-over-edit** for living docs — adding a subsection conflicts less than rewording a paragraph.
  - **Atomic claim protocols** (labels + claim comments, file locks, worktree paths) so two actors don't start the same unit of work.
  - **Uniquely-scoped IDs** for records that might be created concurrently — derive from an atomically-allocated source (issue number, timestamp) rather than counting sequentially.
  - **Isolation boundaries** (worktrees, branches) so in-progress state doesn't stomp on other actors.

**Pipeline implication:** the choice cascades to every shared artifact. You can't pick "parallel" and then edit the decision log in the middle; you can't pick "synchronous" and then run an overnight batch worker. The mechanisms listed above are not optional once parallelism is chosen.

---

## 2.3 Sync vs async review

**The question:** how soon after a change lands must a human review it?

**Synchronous review (minutes to hours).**
- *Unlocks:* small PRs, fast iteration on feedback, tightly-chained work (next PR starts when prior lands).
- *Closes:* distributed teams, solo + overnight-agent workflows. The reviewer is a critical-path resource.

**Asynchronous review (hours to days).**
- *Unlocks:* distributed teams across time zones. Solo builders with agent workers that run while the human sleeps.
- *Closes:* fast iteration on review comments. Requires that the PR be self-contained enough to evaluate without a live conversation — which in practice means richer ticket bodies, better PR descriptions, and tests that speak for themselves.

**Pipeline implication:** async review is not a degraded version of sync review — it's a different mode that needs different artifacts. PRs must be reviewable cold.

---

## 2.4 Approval gating

**The question:** what must happen before code reaches main?

**Direct commit (no gate).**
- *Unlocks:* maximum speed. No review ceremony.
- *Closes:* the review quality gate. Only viable if automated tests + discipline substitute — or if the stakes are truly low.

**Self-approval (PR that you merge yourself).**
- Usually ceremony without benefit. Either commit directly, or require another reviewer.

**Required approver.**
- *Unlocks:* quality gate, shared knowledge (the reviewer learns the change), bus-factor mitigation.
- *Closes:* solo async work — unless an agent can be the reviewer, which is a distinct and strong design choice with its own tradeoffs.

**Split-by-lane.** Low-risk changes auto-merge; high-risk changes need human approval.
- *Unlocks:* balanced autonomy. Most work moves fast; risky work gets scrutiny.
- *Closes:* simplicity. The classifier — what's risky? — has to live somewhere, usually as labels on the ticket.

---

## 2.5 Role encoding

**The question:** does the pipeline model "who does what"?

**Role-agnostic.**
- *Unlocks:* fluid ownership, low ceremony. Anyone can touch any artifact.
- *Closes:* clarity about accountability. "Whose job is the brief?" has no pipeline-level answer.

**Role-encoded.**
- *Unlocks:* clear handoffs. A skill can say "this is PM work, this is eng work."
- *Closes:* solo-builder simplicity. Roles need humans to fill them.

**Pipeline implication:** solo pipelines are role-agnostic by definition. Team pipelines that don't encode roles quickly develop informal ones; whether the pipeline acknowledges them or not, they exist.

---

# 3. Planning & design

## 3.1 Upfront design vs emergent design

**The question:** do architecture and design docs precede or follow substantive code?

**Upfront.**
- *Unlocks:* contributor onboarding (agents especially — they read the design doc and build to it). Consistent patterns across the codebase. Roadmap-able work — a designed system can be decomposed into tickets.
- *Closes:* learning-from-code discovery. You commit before feedback exists. If the design is wrong, planning is wasted and potentially the wrong thing gets built.

**Emergent.**
- *Unlocks:* responsiveness to what turns out to be hard. No wasted design for things you didn't end up building.
- *Closes:* parallel execution. Without a documented target, multiple contributors make inconsistent choices. Agents struggle without a current-shape document. Roadmapping is impossible.

**Skeleton-plus-emergent middle.** Viable only with strong doc-sync discipline — code changes that deviate from the skeleton must update the skeleton as they happen, or the skeleton becomes a lie.

---

## 3.2 Planning horizon

**The question:** how far ahead do you plan at once?

**Big-bang (entire product planned upfront).**
- *Unlocks:* full roadmap visibility, resource allocation, stakeholder alignment.
- *Closes:* adaptation. Plans stale fast once real work starts.

**Phased (plan one phase ahead).**
- *Unlocks:* mid-course correction without throwing everything away. Focused planning effort per phase.
- *Closes:* long-range visibility to stakeholders.

**Continuous / just-in-time (plan each unit of work as it comes up).**
- *Unlocks:* maximum adaptation.
- *Closes:* any sense of direction. Hard to sell to stakeholders. Agents can't see "what's next" beyond the current ticket.

---

## 3.3 Ticket granularity

**The question:** how big is a single unit of work?

**Fine-grained (small tickets, often dependency-chained).**
- *Unlocks:* parallelism — multiple agents on independent tickets. Reviewable PRs — small diffs review well. Good match for agents, which benefit from tight scope.
- *Closes:* context amortization. Each ticket loads the full context afresh. Related tickets duplicate setup work.

**Coarse-grained (one ticket per feature or larger).**
- *Unlocks:* single-context work, less planning overhead per unit, natural feature-level commits.
- *Closes:* parallelism, review quality (giant PRs are reviewed shallowly), rollback granularity.

**Pipeline implication:** agent-heavy pipelines trend fine-grained; human-heavy pipelines can sustain coarser tickets because the human can hold more context.

---

## 3.4 Layered vs all-at-once implementation

**The question:** when a feature has logic, UI, and polish, do you build them together or in sequence?

**All-at-once per ticket.**
- *Unlocks:* single-context delivery. The feature ships complete from one PR. Natural for human developers with full context.
- *Closes:* the ability to gate by layer. TDD logic + manual polish can't share one test strategy; mixing them forces compromises on both.

**Layered (logic → wiring → polish, typically dependency-chained).**
- *Unlocks:* per-layer quality strategies. Logic can be TDD'd and auto-merged; UI wiring gets e2e tests; polish gets human review. The right people (or agents) can work on the right layers.
- *Closes:* single-PR shipping. A feature is now a chain of 2–3 PRs. The human experience of "where is feature X?" requires a container abstraction (epic/feature grouping).

**Pipeline implication:** layering is most valuable when you have a mix of agent-safe work (logic) and human-required work (polish), and you want to route them differently.

---

## 3.5 Container hierarchy

**The question:** do tickets have parents?

**Flat (ticket = unit of work, no parents).**
- *Unlocks:* simplicity. One object type.
- *Closes:* the ability to express "these three tickets deliver one capability" or "these ten tickets are a phase." The grouping has no home.

**Two-level (ticket + epic or ticket + feature).**
- *Unlocks:* a single grouping abstraction.
- *Closes:* expressing both phase-level and capability-level grouping at once.

**Three-level (epic ⊇ feature ⊇ ticket).**
- *Unlocks:* epics for batches/phases, features for user-visible capabilities, tickets for concrete work. Cascade-closing (all tickets done → feature done → epic done) makes progress visible at every level.
- *Closes:* simplicity. Three object types means three sets of rules. Worth it only if you actually use the middle layer.

---

# 4. Execution & ticketing

## 4.1 Formal ticket system vs informal task list

**The question:** how does work get queued?

**Informal (markdown todo, chat message, head).**
- *Unlocks:* speed, zero ceremony.
- *Closes:* parallelism — no claim protocol, no dependency graph. Impossible for an agent to reliably "find the next ticket." No audit trail.

**Formal (GitHub issues, Jira, Linear, etc.).**
- *Unlocks:* parallelism via claim protocols, dependency tracking, programmatic queues, audit trail. Required for agent pickup.
- *Closes:* speed for trivial changes. Overhead per unit of work — even a one-line fix needs a ticket.

**Pipeline implication:** agent-heavy pipelines require formal tickets. There's no way to have an agent "pick up the next piece of work" from a chat message.

---

## 4.2 Dependency expression

**The question:** how does "X must come before Y" get captured?

**Implicit (in commit order, in the author's head).**
- *Unlocks:* nothing; this is the default.
- *Closes:* parallelism. An agent can't know which tickets are safe to start.

**Explicit (Blocked By, prerequisite field, dependency graph).**
- *Unlocks:* correct pickup order, parallel work on independent branches of the graph.
- *Closes:* drift-free execution without discipline. When a ticket's scope changes, its dependencies often do too, and nothing reminds the planner.

---

## 4.3 Claim protocol

**The question:** how does an actor signal "I'm working on this"?

**No claim.**
- Only works if exactly one actor operates at a time.

**Advisory claim (label, assignment).**
- *Unlocks:* courteous coordination.
- *Closes:* race protection. Two agents can both see a "free" ticket and claim it simultaneously.

**Atomic claim (earliest-write-wins via timestamped comment, or OS-level lock).**
- *Unlocks:* true race safety under parallelism.
- *Closes:* nothing significant. This is the safe default when parallel actors exist.

**Pipeline implication:** if the claim mechanism isn't atomic, parallelism is a bug waiting to happen. The bug won't surface during development; it'll surface at 2am when two scheduled workers collide.

---

## 4.4 Priority expression

**The question:** how does "do this next" get encoded?

**Manual / none.**
- *Unlocks:* nothing.
- *Closes:* automated pickup. Someone has to choose.

**Tag-based (labels like P0..P3).**
- *Unlocks:* programmatic pickup order. P0 preempts, ties break by issue number or age.
- *Closes:* nuance. Priority is reduced to ~4 buckets; finer judgments need ticket-body context.

**Explicit ordering (backlog rank, sort field).**
- *Unlocks:* finer control.
- *Closes:* the scalability of tags. Someone has to maintain the ordering; multiple planners can reorder each other's rankings.

---

# 5. Quality & verification

## 5.1 Test-first vs test-after vs manual-only

**The question:** when do tests get written relative to code?

**Test-first (TDD).**
- *Unlocks:* unambiguous acceptance. Agents execute TDD tickets cleanly because "red → green" is a clear loop.
- *Closes:* exploration through code. Every behavior must be expressible as a test first.

**Test-after.**
- *Unlocks:* faster exploration. Tests cover final shape, not every dead-end.
- *Closes:* the forcing function TDD provides for testable design. Tests often end up worse-structured because the code was written without testability in mind.

**Manual-only.**
- *Unlocks:* UX and polish testing that's hard to automate.
- *Closes:* regression confidence. Every release re-runs everything, or risks regressions. Cost per release grows with surface area.

**Layered strategy (TDD for logic, manual for UX).**
- Common and sensible resolution. Different layers get different strategies. Requires the layered-implementation lever (§3.4) to be in place.

---

## 5.2 Manual QA capture

**The question:** do manual verification steps get recorded?

**Not captured (QA happens ad-hoc, results lost).**
- *Unlocks:* flexibility, no artifact.
- *Closes:* a regression suite. Manual tests done for feature X aren't available next release.

**Per-ticket captured + accumulated into a release-level regression log.**
- *Unlocks:* a growing manual-regression suite usable for release preflight.
- *Closes:* zero-overhead shipping. Someone (or something) must run the suite before release.

---

## 5.3 CI integration

**The question:** does CI run, and does it gate?

**Local-only tests.**
- *Unlocks:* speed — merges don't wait on CI.
- *Closes:* multi-environment coverage (matrix OS, integration environments), and trust that the author actually ran tests.

**Remote CI runs but doesn't gate.**
- *Unlocks:* post-merge visibility.
- *Closes:* nothing bad, but the signal is noisy — red CI post-merge gets normalized.

**Remote CI gates merges.**
- *Unlocks:* enforceability, cross-environment coverage.
- *Closes:* zero-latency merging. Agents must wait for CI to merge. If CI takes 20 minutes, that's the floor on cycle time.

**Pipeline implication:** an agent that auto-merges before CI reports creates a subtle reliability problem — red builds land on main silently. Either the agent waits for CI, or CI results get surfaced as deferred work.

---

## 5.4 Pre-merge doc-sync enforcement

**The question:** must living docs be updated in the same change as the code?

**No enforcement.**
- *Unlocks:* speed per change.
- *Closes:* trust in docs. Docs drift; readers learn to ignore them; drift accelerates.

**Enforced at commit time (precommit script or hook).**
- *Unlocks:* docs-as-source-of-truth becomes real, not aspirational.
- *Closes:* the ability to land a "quick fix" without touching docs. Requires mechanical enforcement (the hook), not discipline.

---

## 5.5 Environment / secrets strategy

**The question:** how do tests that need credentials get what they need?

**Committed env (encrypted, or dev-only stubs).**
- *Unlocks:* agents and new contributors can run code immediately.
- *Closes:* nothing if encryption is sound; serious security risk if done wrong.

**Human-hydrated env (`.env` never committed).**
- *Unlocks:* security.
- *Closes:* agent autonomy. Agents can't run integration tests without out-of-band setup. Integration tests become a class of work agents can't do.

**Pipeline implication:** if agents must run integration tests, one of three things is true: env is committed (encrypted), agents get credentials injected by the harness, or integration tests are skipped in the agent lane and deferred to humans.

---

# 6. Release & delivery

## 6.1 Continuous delivery vs batched releases

**The question:** when does code become a release?

**Continuous delivery — every merge to main is potentially shippable.**
- *Unlocks:* fast user feedback, small blast radius per change, easy rollback.
- *Closes:* merging unverified code. Everything on main must pass tests + manual QA before merge. **This forces human review to be synchronous with merge** — the reviewer is critical-path for every change.

**Batched, timeline-based — release cuts on a cadence (weekly, sprint-end).**
- Operates like CD for merge discipline: main must be always-deployable because the tag could be cut at any point. QA may accumulate in a pre-tag window.
- *Unlocks:* predictability for users ("new features ship Thursdays"). Reduces release ceremony per change.
- *Closes:* on-demand shipping of a single urgent change (though hotfix paths can work around this).

**Batched, feature-scoped / pre-determined — features merge as ready, release cut when a set is complete.**
- Main is **not** always-deployable. Features may land unverified and be held for QA.
- *Unlocks:* **solo-builder-friendly agent autonomy.** Agents land features overnight; humans review async later; releases happen when the set is verified. The reviewer is never the sequential bottleneck.
- *Closes:* ability to cut at any moment. Requires a pre-release QA sweep. Rollback is harder — a release bundles multiple features, so pinpointing the culprit of a regression takes investigation.

**Long-lived release branch (trunk for dev, branch for ship).**
- *Unlocks:* main can be messy. Release branch is the always-deployable artifact. Parallel-version support.
- *Closes:* simplicity. Cherry-picks, hotfix backports, and drift between branches become a steady tax.

**Pipeline implication:** this lever **directly contradicts** several others. Continuous delivery + async review is incoherent — something has to give. The right combination for a solo builder with agent workers is usually feature-scoped batching, because it's the only mode where async review doesn't block throughput.

---

## 6.2 Branch strategy

**The question:** what long-lived branches exist?

**Trunk-based — main is the only long-lived branch.**
- *Unlocks:* simplicity. No merge-back ceremony. Releases are tags, not branches.
- *Closes:* long-lived "this version only" fixes. Hotfixes from old tags need lazy-created branches.

**Gitflow — develop, release branches, main.**
- *Unlocks:* parallel-version support, clean hotfix flows, a staging branch.
- *Closes:* simplicity. Cherry-picking and merging back is constant.

**Feature branches only (short-lived) + trunk.**
- Most common modern default. Features branch off main, merge back quickly, main is always deployable.

---

## 6.3 Feature flags

**The question:** do runtime flags gate new features?

**No flags.**
- *Unlocks:* simplicity. What's in main is what's shipped.
- *Closes:* progressive rollout, A/B testing, kill switches, dark launches.

**Flags for risky or experimental features.**
- *Unlocks:* safer releases, experimentation capability, kill-switch safety.
- *Closes:* simplicity. Flags accumulate; stale flags become a cleanup problem. Testing matrix grows with each flag.

**Flags everywhere.**
- *Unlocks:* ultimate rollout control, continuous deployment decoupled from feature release.
- *Closes:* code simplicity entirely. Every feature lives behind a flag until it's "default-on" and then the flag must be cleaned up. Cleanup rarely happens.

---

## 6.4 Release cadence

**The question:** how often do releases go out?

**On-demand.**
- *Unlocks:* responsiveness to urgent needs.
- *Closes:* predictability. Users never know when new features arrive.

**Fixed cadence (weekly, bi-weekly, monthly).**
- *Unlocks:* predictability, forcing function for "let's finish this for the release."
- *Closes:* responsiveness. Urgent changes need a hotfix path.

**Milestone-driven.**
- *Unlocks:* version semantics that align with product meaning ("1.0 = feature-complete MVP").
- *Closes:* predictability. Milestones slip.

---

## 6.5 Versioning discipline

**The question:** how do version numbers get assigned?

**Ad-hoc (whatever feels right).**
- *Unlocks:* speed.
- *Closes:* meaning for downstream consumers. If you have library users, this is unacceptable.

**SemVer (major.minor.patch with strict semantics).**
- *Unlocks:* downstream trust. Automated bump detection from change labels (breaking → major, fix → patch, else → minor) is possible.
- *Closes:* tiny-change speed. Every change must be classified. Accidental breaking changes become a class of bug.

**Calendar versioning (2026.4.1 style).**
- *Unlocks:* freedom from classification. Version reflects date.
- *Closes:* backward-compat signaling. Users can't tell "is this safe to upgrade to?" from the version alone.

## 6.6 PR merge method

**The question:** when a PR lands, how do its commits enter the base branch?

**Merge (`gh pr merge --merge`).**
- *Unlocks:* full per-commit history preserved, plus an explicit merge-commit boundary. Tools that revert-a-feature or bisect-across-a-feature have a clean handle.
- *Closes:* a linear log. `git log --oneline main` shows merge commits interleaved with feature commits.

**Squash (`gh pr merge --squash`).**
- *Unlocks:* one commit per PR. `git log` reads like a ticket list. Easy to revert a feature with a single `git revert`.
- *Closes:* per-commit intent. Reviewer's commit-by-commit walkthrough is gone after merge. Tickets that reference individual commits lose those references.

**Rebase (`gh pr merge --rebase`).**
- *Unlocks:* linear history *and* per-commit intent. No merge commits cluttering `git log`.
- *Closes:* the merge-commit boundary (no clean "this PR" handle in `git log`). Commit SHAs change on land, so anyone with the pre-merge branch checked out has stale refs.

---

# 7. Knowledge & documentation

## 7.1 Docs-as-source-of-truth vs code-as-source-of-truth

**The question:** when docs and code disagree, which one is right?

**Docs-as-SoT.**
- *Unlocks:* durability. "If the code were lost, the docs reproduce the system." Agent onboarding reads fast. Decisions survive migrations.
- *Closes:* effort-free development. Every meaningful code change must update docs. Requires enforcement mechanisms (precommit sync, deviation reports) — not discipline alone.

**Code-as-SoT.**
- *Unlocks:* speed. No doc overhead per change.
- *Closes:* trust in docs. Docs lag code; readers learn to ignore them; ignored docs accelerate in drift. Agents that read docs for context get stale information.

**There is no neutral middle.** One must lead. The lever really sets the **direction of drift enforcement** — whichever is "truth" gets enforced, the other catches up periodically.

---

## 7.2 Decision capture

**The question:** how do "why did we choose X" conversations get preserved?

**Informal (slack, doc comments, heads).**
- *Unlocks:* no ceremony.
- *Closes:* future-self's ability to reconstruct "why." In 6 months, no one remembers why the threshold is 500ms instead of 1s.

**ADR-style log (append-only records, each with context, options, decision, consequences).**
- *Unlocks:* audit trail, onboarding, explicit tracking of rejected alternatives, supersession chains (Decision 12 supersedes Decision 7).
- *Closes:* speed per decision. "Is this significant enough to record?" is a judgment call that adds overhead.

**Embedded in living docs (rationale inside architecture/design doc).**
- *Unlocks:* contextual reading — reader sees decision + current state together.
- *Closes:* supersession tracking. When an architecture section gets rewritten, embedded rationale for the prior version is lost.

**Pipeline implication:** the append-only log is strictly better than embedded rationale for any long-lived project. The cost of recording is small; the cost of reconstructing lost rationale is enormous.

---

## 7.3 Domain vocabulary management

**The question:** is there a canonical glossary?

**Emergent (terms come and go with code).**
- *Unlocks:* speed.
- *Closes:* coherence. Same concept gets multiple names; readers and agents must triangulate. Onboarding time grows with domain complexity.

**Formal glossary (central definition file).**
- *Unlocks:* coherent naming across code, docs, tickets. Agents name things consistently. Domain complexity becomes explicit.
- *Closes:* freedom for terminology to drift. Requires maintenance — new terms must be added; renamed terms must be updated.

**Pipeline implication:** domain-heavy projects (finance, healthcare, multi-sided marketplaces) benefit enormously from formal glossaries. Domain-light projects (plain CRUD, standard categories) often don't need one.

---

## 7.4 Change log discipline

**The question:** how do users learn what changed?

**None.**
- *Unlocks:* no effort.
- *Closes:* user trust. Upgrades become scary.

**Commit log as changelog.**
- *Unlocks:* automation.
- *Closes:* readability. Commits are for developers; users need human-language summaries.

**Curated changelog (Keep-a-Changelog style).**
- *Unlocks:* human-readable release notes.
- *Closes:* automation fully. Something has to curate — either manual per release, or automated from PR-label hints + human review.

---

# 8. Automation & autonomy

## 8.1 Agent-heavy vs human-heavy execution

**The question:** what share of code is written by agents?

**Human-heavy (agents for pairing, short tasks, review).**
- *Unlocks:* judgment-rich implementation. Humans infer context from loose docs. Less need for rigid doc/test discipline.
- *Closes:* parallelism at low cost. Humans are the throughput ceiling.

**Agent-heavy (agents implement most tickets; humans plan, review, direct).**
- *Unlocks:* throughput per human-hour. Overnight/unattended work.
- *Closes:* informal coordination. Agents need unambiguous tickets, explicit docs, deterministic tooling. Collision mitigation is mandatory. Agents don't "notice" that a teammate is touching the same file.

**Pipeline implication:** agent-heavy pipelines are strictly more demanding on artifacts. You can't half-adopt agents — either your tickets and docs are agent-readable, or agents can't really help.

---

## 8.2 Agent auto-merge

**The question:** can an agent merge its own PR?

**No — every PR needs human review.**
- *Unlocks:* universal review gate.
- *Closes:* overnight throughput. Agent work queues behind the human reviewer.

**Yes, for low-risk changes (split-by-lane).**
- *Unlocks:* agents ship safe changes without waiting for humans.
- *Closes:* the uniform review gate. The classifier — what's safe? — must be reliable. Getting this wrong means unreviewed bad code on main.

**Yes, everything.**
- *Unlocks:* maximum throughput.
- *Closes:* human quality gate entirely. Only viable with strong automated tests + small blast radius + easy reversal.

---

## 8.3 Scheduled / unattended runs

**The question:** can agents run without a human attached?

**No — agents run only when invoked.**
- *Unlocks:* predictability; nothing happens unexpectedly.
- *Closes:* overnight and cron-style throughput.

**Yes — agents run on schedule or trigger.**
- *Unlocks:* overnight batches, scheduled maintenance, continuous ticket processing.
- *Closes:* the assumption that a human is watching. Requires graceful-stop signals, claim safety under concurrency, and alerting for failures.

---

## 8.4 Bug intake source

**The question:** where do bug reports come from?

**Manual (human writes up a report).**
- *Unlocks:* nothing special; default.
- *Closes:* scaling. Hard when bugs come from Sentry, app stores, support tickets, user email.

**Funneled (error-reporting tool → triage → ticket).**
- *Unlocks:* comprehensive coverage. Prioritize by frequency. Detect regressions.
- *Closes:* low-ceremony bug handling. Funnels need maintenance; noisy sources need filtering.

---

## 8.5 Idea / backlog triage

**The question:** what happens to "we should do X someday"?

**Synchronous / in-the-moment.**
- *Unlocks:* no backlog debt. Every idea either becomes work or gets dropped immediately.
- *Closes:* focus. Every shower thought interrupts.

**Defer-to-queue (ideas become lightweight tickets for later review).**
- *Unlocks:* focus (idea captured, not executed). Later review batches decisions.
- *Closes:* low-ceremony thinking. Every idea becomes a record; queue bloats; some ideas never get processed.

**Graveyard (rejected ideas kept separately for possible reconsideration).**
- *Unlocks:* memory across pivots. "We rejected X because of Y; Y no longer applies" is a real scenario.
- *Closes:* requires separate storage and a scan mechanism. Without those, the graveyard is vapor.

---

## 8.6 Agent breadcrumb posting (comments)

**The question:** when an agent runs a pipeline step that produces intermediate findings — a review report, a TDD verdict, a test-surface sketch, a hand-off summary — does that artifact get posted to the ticket/PR conversation, or does it live only in the agent's local transcript?

**Off — artifacts stay in the transcript.**
- *Unlocks:* quiet timelines. The issue and PR conversation reflect human discussion only, not agent step-by-step output.
- *Closes:* asynchronous review. A reviewer or downstream worker who didn't watch the agent run has no record of what it considered, what it ruled out, or what it deferred. Re-running to inspect is the only path back.

**On — every breadcrumb posts to the auto-discovered target (PR if one exists, else the issue).**
- *Unlocks:* traceable hand-off. The timeline shows TDD verdict, test-surface sketch, review findings, decisions consulted, and the final summary at the boundaries where they were produced. Humans picking up later, and downstream agents continuing the chain, can read the trail without replaying the session.
- *Closes:* signal-to-noise. Long-running tickets accumulate many comments; the human conversation gets diluted unless filtered. Requires that consumers (PR review tooling, notification preferences) cope with the volume.

## 8.7 Agent breadcrumb commits

**The question:** when an agent runs a multi-step pipeline (worker implementation, then one or more review passes), does each step land as its own commit, or do all the edits roll into one combined commit at the end?

**Off — one combined commit.**
- *Unlocks:* clean git history. One commit per ticket; the log reads as human-authored. Bisects and blame point at the ticket, not at intermediate reviewer fixes.
- *Closes:* per-step traceability in the log. Reviewers and humans can't see "this was the worker output, this was the correctness fix" from `git log` alone — the audit trail lives in the agent transcript or PR comments instead.

**On — per-step commits (worker, then one commit per reviewer that applied fixes).**
- *Unlocks:* per-step auditability in the log. `git log` shows exactly what the worker produced and what each reviewer changed on top. Pre-commit hooks fire on every step, catching regressions at the boundary where they were introduced rather than at the end.
- *Closes:* clean git history. The log grows reviewer-prefixed commits (`review-correctness: apply fixes`, …) that dilute the ticket-level narrative. Squash merges hide the breakdown; non-squash merges leak it into `main`.

---

# 9. Feedback & iteration

## 9.1 Metrics / experimentation culture

**The question:** is "did this work?" asked quantitatively?

**Qualitative only.**
- *Unlocks:* speed, shipping on instinct.
- *Closes:* evidence-based iteration. You'll ship features no one uses and not know for months.

**Metrics-driven (every feature has success metrics).**
- *Unlocks:* real learning about what works. Kill-failed-experiments discipline.
- *Closes:* speed. Metrics take build-time, and waiting for statistical significance extends cycles.

**A/B experimentation.**
- *Unlocks:* causal claims. "This change increased retention by 3%."
- *Closes:* simplicity. Experiment infrastructure is nontrivial. Many teams adopt A/B and use it as a crutch for "we don't know what to build."

---

## 9.2 User-feedback loop

**The question:** how does user feedback reach the pipeline?

**None.**
- *Unlocks:* speed.
- *Closes:* everything about validating the product is useful.

**Explicit channels (support, user interviews, analytics).**
- *Unlocks:* ground-truth. Most roadmap prioritization becomes "what are users asking for?"
- *Closes:* vision-led product development. Heavy user feedback can drag a product toward "what current users ask for" and away from "what would matter most."

---

# 10. Meta-levers

## 10.1 Bottleneck location

Every pipeline implicitly assumes a bottleneck and optimizes against it. Misidentifying the bottleneck wastes effort everywhere else.

**Ideas bottleneck.** Optimize intake, concept validation, idea triage.
**Design bottleneck.** Optimize doc authoring, decision capture, design reviews.
**Implementation bottleneck.** Optimize agent autonomy, ticket pipelining, parallel execution.
**Review bottleneck.** Optimize async review, minimize what requires human sign-off, split by risk lane.
**QA bottleneck.** Optimize accumulated regression suites, automated coverage at the right layers.
**Release bottleneck.** Optimize release ceremony, preflight automation, platform pipelines.

A pipeline that protects the wrong bottleneck wastes its investment. Solo builders almost always become review-bottlenecked; large teams are often design/coordination-bottlenecked; early-stage products are often ideas-bottlenecked.

**Check:** when work is slow, what are you waiting for? The answer is the true bottleneck, which may differ from the one the pipeline was designed around.

---

## 10.2 Consistency vs speed

Most levers trade consistency for speed or vice versa. Consistency investments (docs, decision logs, test discipline, review gates) pay off over long time horizons and many contributors. Speed investments (direct commits, informal comms, no artifacts) pay off in early-stage, low-uncertainty contexts.

A common failure: adopting consistency investments out of "best practice" culture when the project is in a speed-optimal phase, slowing down without gaining the long-term benefit because the project may not survive long enough to collect it.

Another common failure: sticking with speed investments long after the project has moved to a phase where consistency would pay off, accumulating an artifact debt that's painful to service.

**Check:** does the artifact investment you're making today have a credible payoff horizon given the project's trajectory?

---

## 10.3 Reversibility of the pipeline itself

Pipeline choices are themselves reversible or not. Some levers can flip mid-project with little cost (e.g., starting to capture decisions is additive). Others are structurally hard to reverse (e.g., moving from trunk-based to gitflow mid-project is painful; moving from code-as-SoT to docs-as-SoT requires backfilling every artifact).

Err toward reversible choices early, and lock in hard-to-reverse choices only when the project's shape is clearer.

---

# Checklist for a new project

Run through these questions before shaping the pipeline:

1. **Lifecycle:** greenfield or brownfield? Prototype or long-lived? Pre- or post-launch?
2. **Deploy risk:** how reversible is a bad release? Any regulatory burden?
3. **Team:** solo, small team, or large team? Sync or async? Role-encoded or fluid?
4. **Design discipline:** upfront, emergent, or skeleton-plus? Big-bang or phased planning?
5. **Ticketing:** formal or informal? Fine or coarse granularity? Layered implementation?
6. **Quality:** TDD, test-after, or manual? Is manual QA captured? Does CI gate?
7. **Release:** continuous or batched? If batched, timeline or feature-scoped? What's the cadence?
8. **Docs:** docs-as-SoT or code-as-SoT? ADR log or informal? Glossary?
9. **Automation:** agent-heavy or human-heavy? Auto-merge allowed? Scheduled runs?
10. **Feedback:** metrics-driven or qualitative? User feedback loop wired up?
11. **Bottleneck:** which stage will queue up? Is the pipeline optimized against it?

Record your answers. The pipeline's shape falls out of this set. When something feels wrong later, come back and check which answer has changed.
