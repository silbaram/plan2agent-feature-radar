# Feature Radar Research Workflow

Use this workflow for web, GitHub, and optional local project evidence collection. Completed runs can later be handed off to a target project with `handoff.md`.

1. Restate the idea and assumptions.
2. If a local project path is provided, inspect it read-only and summarize current capabilities.
3. Identify comparable services and source categories.
4. Search official sources first.
5. Search GitHub repositories and issue trackers second.
6. Search community/review sources only as supporting context.
7. Compare local capabilities with external signals when local project evidence exists.
8. Review source quality before drawing conclusions.

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
| `local-project-scan.md` | Optional local evidence layer: current capabilities, architecture, constraints, tests, and file references. |
| `collection-report.md` | Final actionable synthesis: recommendation, implementation path, risks, and next tasks. |
| `research-bundle.md` | Analysis body: reasoning, comparisons, options, MVP shape, and tradeoffs. |
| `signal-map.md` | Evidence map: signals, URLs, implications, caveats, and confidence. |
| `source-candidates.md` | Source registry: official docs, comparable services, GitHub sources, relevance, and confidence. |
| `capability-gap-analysis.md` | Optional comparison layer for existing project mode: already covered, partial, missing, risky, or not relevant. |
| `next-iteration-recommendations.md` | Optional recommendation layer for existing project mode: add, strengthen, fix foundation, defer, and reject candidates. |

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
destination | mode | copied files | missing optional files | conflicts | manifest path
```

Do not write P2A artifacts from this skill unless the user explicitly requests handoff mode `p2a-preflight` or `both`.
