# Feature Radar Research Workflow

Use this workflow for web, GitHub, and optional local project evidence collection. Completed runs can later be handed off to a target project with `handoff.md`.

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

1. Restate the idea and assumptions.
2. If a local project path is provided, inspect it read-only and summarize current capabilities.
3. Identify comparable services and source categories.
4. Search official sources first.
5. Search GitHub repositories and issue trackers second.
6. Search community/review sources only as supporting context.
7. Compare local capabilities with external signals when local project evidence exists.
8. Normalize source-backed evidence after collection inputs are ready.
9. Materialize problem clusters with stable IDs and evidence references.
10. Synthesize bounded opportunities from accepted clusters.
11. Review alternatives and counter-evidence.
12. Apply the qualitative opportunity and evidence-confidence rubric.
13. Complete final evidence review before writing `collection-report.md`.

For `profile: tool-gap`, opportunity synthesis returns zero to three candidates. Use `insufficient_evidence` when coverage is too weak to decide and `no_supported_opportunity` when sufficient evidence rejects all candidates. It does not pad weak recommendations. Use `strong | moderate | weak | unknown` for opportunity assessment and `high | medium | low | unknown` for evidence confidence. Numeric scores are allowed only when supplied by a named, versioned deterministic scorer. For `general`, do not impose the Tool Gap taxonomy or candidate limit.

For every profile, a user request alone does not authorize numeric scoring. Use numeric values only when a named, versioned deterministic scorer supplies them.

Keep these source categories separate:

- official product claims
- documented product capabilities
- pricing and packaging signals
- changelog/release direction
- GitHub developer pain
- community/user pain
- low-confidence comparison content
- local code evidence

For local project scans, skip secrets, credentials, dependency directories, build outputs, generated artifacts, caches, and large binaries unless the user explicitly asks. Do not modify files unless explicitly requested.

Default output location:

```text
.feature-radar/runs/<project-slug>/
```

`<project-slug>` should be a readable English project name in lowercase ASCII with hyphens, for example `on-device-character-chat-app`. Do not use a timestamp as the primary directory name unless creating a second snapshot for the same project.

Use the run artifacts as a layered decision record:

| Artifact | Role |
| --- | --- |
| `research-plan.md` | Scope contract: idea, assumptions, questions, source themes, and planned outputs. |
| `local-project-scan.md` | Required existing-project local evidence layer: current capabilities, architecture, constraints, tests, and file references. |
| `collection-report.md` | Final actionable synthesis: recommendation, implementation path, risks, and next tasks. |
| `research-bundle.md` | Analysis body: reasoning, comparisons, options, MVP shape, and tradeoffs. |
| `signal-map.md` | Evidence map: signals, URLs, implications, caveats, and confidence. |
| `source-candidates.md` | Source registry: official docs, comparable services, GitHub sources, relevance, and confidence. |
| `capability-gap-analysis.md` | Required existing-project comparison layer: already covered, partial, missing, risky, or not relevant. |
| `next-iteration-recommendations.md` | Required existing-project recommendation layer: add, strengthen, fix foundation, defer, and reject candidates. |

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

All three existing-project files are required by the current run contract. If a section is not applicable, keep its file and record `N/A` with a reason.

High-impact recommendations should be traceable through this path:

```text
collection-report recommendation
  -> research-bundle claim or comparison
  -> signal-map signal with confidence
  -> source-candidates canonical URL and source type
```

For existing project research, high-impact recommendations should also trace through:

```text
next-iteration recommendation
  -> capability-gap-analysis gap or opportunity
  -> local-project-scan capability with file path:line
  -> signal-map external signal with confidence
  -> source-candidates canonical URL and source type
```

If a recommendation cannot be traced through at least one medium-or-higher confidence signal, mark it as `needs more research`, weaken it, or move it to a follow-up question.

Use this shape for `next-iteration-recommendations.md`:

```text
rank | recommendation | action | why now | local evidence | external evidence | expected impact | cost/risk | confidence | next step
```

When the user asks to copy, export, hand off, or move a completed run into a target project, read `handoff.md`. Handoff creates `handoff-manifest.md` in each destination and must report:

```text
destination | run_mode | profile | handoff_mode | source_complete | copied files | missing required files | missing optional files | conflicts | manifest path
```

For handoff, the only optional copy-set file is `p2a-context.json`; `_INDEX.md` is regenerated in each destination.

Do not write P2A artifacts from this skill unless the user explicitly requests handoff mode `p2a-preflight` or `both`.

For P2A handoff, package each investigation under `.plan2agent/artifacts/<project-id>/preflight-research/<sequence>/`, using a sequence such as `001-kubernetes-users`. A `p2a-preflight` handoff does not create `.feature-radar/` in the target project.
