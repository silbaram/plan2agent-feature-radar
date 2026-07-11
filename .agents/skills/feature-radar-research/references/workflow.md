# Feature Radar Research Workflow

## Purpose

Collect web, GitHub, and optional local project evidence so Feature Radar can later identify feature opportunities, priorities, and next enhancement candidates. Completed runs can later be handed off to a target project with `handoff.md`.

The first milestone is evidence collection and qualitative assessment, not deterministic numeric scoring, coding, or P2A integration.

## Run-First Rule

Completed research should leave a native Feature Radar run behind. When the user asks for research, local-project analysis, next enhancement candidates, or handoff preparation, create or update:

```text
.feature-radar/runs/<project-slug>/
```

before the final answer, unless the user explicitly asks for plan-only/chat-only output or forbids file writes.

When working from this repository, initialize the expected artifact set first:

```bash
python3 tools/radar_run.py init \
  --slug <project-slug> \
  --title "<research title>" \
  --mode existing-project \
  --local-project /path/to/project
```

Use `--mode idea` for idea-only research. Validate before handoff:

```bash
python3 tools/radar_run.py validate \
  --source-run <project-slug> \
  --mode existing-project
```

Run scaffolds start with `status: draft`. Completed artifacts must be updated to `status: complete` before validation and handoff unless the user intentionally asks to hand off draft research.

Research artifact `mode`, `profile`, and `status` headers are authoritative metadata and must be valid and coherent across the expected artifact set. `_INDEX.md` is derived from them. Do not use `init --overwrite` to change an existing run's mode; use a new slug or an explicit migration workflow.

If a run is not created, state the reason explicitly in the final response.

## Research Profiles

`mode` and `profile` are independent:

```text
mode: idea | existing-project
profile: general | tool-gap
```

`general` is the default and the fallback only for legacy runs with no profile in any research artifact. Invalid, duplicate, mixed, or conflicting authoritative metadata makes the run inconsistent. `_INDEX.md` should be regenerated from the research artifact headers when stale. For `tool-gap`, initialize the same native artifact set with `--profile tool-gap` and follow `tool-gap-profile.md`. A profile does not add a third mode or change which Markdown files are required.

For `profile: tool-gap`, preserve this dependency order:

```text
discovery and collection
  -> evidence normalization
  -> problem clustering
  -> opportunity synthesis
  -> alternatives and counter-evidence review
  -> qualitative assessment
  -> final evidence review and collection-report.md
```

## Source Types

Prioritize sources in this order:

1. Official product website
2. Official docs
3. Official changelog or release notes
4. Pricing and plan pages
5. Integration pages
6. Help center and support docs
7. Public GitHub repositories
8. GitHub issues, PRs, discussions, and releases
9. Community posts and reviews
10. SEO comparison pages, only as low-confidence context

When the user provides a local project path, inspect local sources before or in parallel with external research:

1. README, docs, and product notes
2. package/build/config files that describe stack and commands
3. source routes, screens, API handlers, models, schemas, jobs, and integrations
4. tests, fixtures, examples, stories, and sample data
5. TODO, FIXME, disabled code, placeholders, and open local notes

Do not inspect secrets, credentials, dependency directories, build outputs, generated artifacts, caches, or large binaries unless the user explicitly asks.

## Subagent Split

Use separate subagents or clearly separated passes:

### Local Project Scan

Use this pass only when the user provides a local project path.

Inspect the current project read-only and identify:

- product purpose and target workflow
- implemented capabilities
- partial or placeholder capabilities
- missing capabilities implied by docs, tests, routes, or UI
- architecture and stack constraints
- test, quality, deployment, and observability signals
- local leverage for next enhancements

Output:

```text
capability | status | local evidence path:line | implication | confidence | follow-up
```

Use status values:

```text
implemented
partial
missing
risky
unknown
```

### Reference Discovery

Find comparable services, official sites, docs, changelogs, and public repositories.

Output:

```text
service | source type | URL | why relevant | confidence
```

### Web Source Collection

Read official service pages, docs, pricing, changelog, help center, and integration pages.

Output:

```text
source id | URL | observed capabilities | target users | notable gaps | evidence quote/paraphrase
```

### GitHub Signal Scan

Inspect repositories, issues, PRs, discussions, releases, README, and labels.

Output:

```text
source id | repo/issue/PR URL | signal type | repeated request or pain | recency | intensity | confidence
```

### Opportunity Synthesis

Run this pass only after its source and normalized signal inputs are ready. First materialize accepted problem clusters, then preserve supporting and counter evidence, check alternatives, and produce bounded opportunities without padding weak recommendations.

For `profile: tool-gap`, follow `tool-gap-profile.md` and return zero to three candidates. Use `insufficient_evidence` when coverage is too weak to decide and `no_supported_opportunity` when sufficient evidence rejects all candidates. For `general`, do not impose the Tool Gap taxonomy or candidate limit.

Output accepted clusters before opportunity rows:

```text
cluster id | representative problem | evidence refs | repository scope / recurrence | counter-signals | caveat
```

Then output:

```text
rank | opportunity | problem cluster refs | evidence refs | alternatives | counter-evidence refs | MVP scope | opportunity assessment | evidence confidence | caveat
```

Use `strong | moderate | weak | unknown` for opportunity assessment and `high | medium | low | unknown` for evidence confidence. Numeric scores are allowed only when supplied by a named, versioned deterministic scorer.

### Evidence Review

Check whether conclusions are overclaimed.

Output:

```text
claim | supporting sources | confidence | caveat | keep/defer/drop
```

### Handoff Packaging

Use this pass only when the user asks to copy, export, hand off, or move a completed run into a target project.

Read `handoff.md` before packaging.

Output:

```text
destination | run_mode | profile | handoff_mode | source_complete | copied files | missing required files | missing optional files | conflicts | manifest path
```

For handoff, the only optional copy-set file is `p2a-context.json`; `_INDEX.md` is regenerated in each destination.

## Native Artifact Shape

Use Markdown first. JSON schemas can come later.

```text
.feature-radar/runs/<project-slug>/
  research-plan.md
  local-project-scan.md                 # required in existing-project mode
  source-candidates.md
  research-bundle.md
  signal-map.md
  capability-gap-analysis.md            # required in existing-project mode
  next-iteration-recommendations.md     # required in existing-project mode
  collection-report.md
```

Handoff creates `handoff-manifest.md` in each destination, not in the source run by default.

All three existing-project files are required by the current run contract. If a section is not applicable, keep its file and record `N/A` with a reason.

`<project-slug>` should be a readable English project name in lowercase ASCII with hyphens, for example `on-device-character-chat-app`. Do not use a timestamp as the primary directory name unless creating a second snapshot for the same project.

## Artifact Roles

Use the run artifacts as a layered decision record, not as five equal reports.

| Artifact | Role | Read When |
| --- | --- | --- |
| `research-plan.md` | Scope contract. Defines the product idea, assumptions, research questions, source themes, and planned outputs. | Before judging whether the run answered the right question. |
| `local-project-scan.md` | Local evidence layer. Summarizes the current implementation, architecture, constraints, tests, and local file references. | When the run is based on an existing local project. |
| `collection-report.md` | Final actionable synthesis. States the recommended direction, implementation path, risks, and next tasks. | First, when deciding what to do. |
| `research-bundle.md` | Analysis body. Explains the reasoning, model/service options, comparisons, MVP shape, and tradeoffs. | When validating or expanding the final recommendation. |
| `signal-map.md` | Evidence map. Connects technical/product signals to URLs, implications, caveats, and confidence. | When auditing whether a recommendation is supported. |
| `source-candidates.md` | Source registry. Lists official docs, comparable services, GitHub sources, source type, relevance, and confidence. | When checking source quality, freshness, or coverage gaps. |
| `capability-gap-analysis.md` | Comparison layer. Classifies local capabilities against external signals as already covered, partial, missing, risky, or not relevant. | When deciding which gaps matter. |
| `next-iteration-recommendations.md` | Enhancement recommendation layer. Prioritizes add, strengthen, fix foundation, defer, and reject candidates. | When preparing a next iteration or P2A handoff. |

Default interpretation:

```text
result = collection-report.md
reasoning = research-bundle.md
evidence = signal-map.md + source-candidates.md
local evidence = local-project-scan.md
gap analysis = capability-gap-analysis.md
next iteration = next-iteration-recommendations.md
scope = research-plan.md
```

`collection-report.md` may include a source list, but it is still a decision document. The stronger evidence trail should live in `signal-map.md` and `source-candidates.md`.

## Evidence Trace

High-impact recommendations should be traceable through this path:

```text
collection-report recommendation
  -> research-bundle claim or comparison
  -> signal-map signal with confidence
  -> source-candidates canonical URL and source type
```

For existing project research, high-impact recommendations should also be traceable through local evidence:

```text
next-iteration recommendation
  -> capability-gap-analysis gap or opportunity
  -> local-project-scan capability with file path:line
  -> signal-map external signal with confidence
  -> source-candidates canonical URL and source type
```

If a recommendation cannot be traced through at least one medium-or-higher confidence signal, mark it as `needs more research`, weaken it, or move it to a follow-up question.

If a recommendation is based only on local code inspection and has no external source, mark it as `local-only` and explain why it is still worth considering.

## Existing Project Recommendation Shape

Classify enhancement candidates with these actions:

| Action | Meaning |
| --- | --- |
| `add` | A new capability that is missing locally and supported by external or strategic evidence. |
| `strengthen` | A capability that exists locally but needs product, UX, reliability, integration, or test depth. |
| `fix_foundation` | A prerequisite in architecture, data model, quality, performance, security, observability, docs, or test coverage. |
| `defer` | A plausible candidate that is too costly, risky, weakly supported, or poorly timed. |
| `reject` | A signal that does not fit the project direction or should not be pursued. |

Use this table shape for `next-iteration-recommendations.md`:

```text
rank | recommendation | action | why now | local evidence | external evidence | expected impact | cost/risk | confidence | next step
```

Use this scoring guidance qualitatively. A user request alone does not authorize numeric scoring; numeric values are allowed only when supplied by a named, versioned deterministic scorer:

```text
next_iteration_score =
  external_demand
  + pain_intensity
  + competitive_gap
  + strategic_fit
  + local_code_fit
  + implementation_leverage
  + testability
  - architecture_risk
  - scope_size
```

Use this acceptance rule before turning a run into implementation work:

- product/architecture decisions require official docs, official product pages, changelogs, or directly observed repository evidence
- market or UX assumptions can use community and review signals, but must be labeled as weaker than official capability claims
- GitHub issues can support developer pain and technical risk, but not broad market demand by themselves
- stale or low-confidence sources can inspire follow-up research, but should not drive MVP scope alone

## Done Criteria

A collection run is good enough when:

- official sources are separated from community sources
- each service has at least one canonical URL
- each GitHub signal has a repo/issue/PR/discussion URL
- local project claims cite a local file path and line number when possible
- local implementation claims are separated from external product, market, or community claims
- weak sources are marked
- stale sources are marked
- the report can be read without raw crawl logs
- every existing-project run contains the three required local-project artifacts, using explicit `N/A` where necessary

A handoff run is good enough when:

- the source run and target project path are recorded
- the source run was validated for the expected run type before copying
- authoritative `mode`, `profile`, and `status` metadata is coherent
- destination directories match the selected mode
- copied files are listed
- missing required files are separated from missing optional files for intentional incomplete handoff
- the sole optional file, `p2a-context.json`, is listed when missing
- no existing file was overwritten without explicit user approval
- `handoff-manifest.md` exists in each destination
