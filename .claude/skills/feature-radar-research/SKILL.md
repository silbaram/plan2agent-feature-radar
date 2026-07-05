---
description: Research product ideas or existing local projects through web/service/GitHub/local-code evidence, or hand off completed Feature Radar runs to target projects. Use when asked to investigate comparable services, docs, changelogs, GitHub issues, feature gaps, MVP direction, next enhancement candidates, or export run artifacts. Do not implement code or export to P2A unless explicitly requested.
---

# Feature Radar Research

This skill coordinates research and run handoff through subagents. It is not a coding task.

## When To Use

Use this skill for:

- product idea research
- comparable service discovery
- official website/docs/changelog collection
- GitHub issue, PR, discussion, release signal scan
- evidence-backed feature gap discovery
- initial MVP direction research
- existing local project read-only scan
- next enhancement recommendation for an existing project
- completed run handoff/export to a target project

Do not start by writing tools, CLIs, MCP servers, or P2A artifacts.

## Procedure

1. Define a small research plan.
2. Delegate to project subagents when useful:
   - `local-project-scanner`, only when a local project path is provided
   - `radar-handoff-packager`, only when exporting a completed run to a target project
   - `reference-discovery`
   - `web-source-collector`
   - `github-signal-scanner`
   - `evidence-reviewer`
3. Keep raw search noise out of the main conversation.
4. Return only source-backed summaries and URLs.
5. Store research outputs under `.feature-radar/runs/<project-slug>/` only when the user asks to create files. Use a readable English project slug, not a timestamp, unless the same project needs multiple snapshots.

If the user provides a local project path, inspect it read-only. Skip secrets, credentials, dependency directories, build outputs, generated artifacts, and large binary files unless explicitly requested. Compare the current implementation with external signals and recommend next enhancement candidates. Do not modify code unless explicitly requested.

If the user asks to hand off or export a completed run, read `references/handoff.md`. Identify the source run, target project path, and mode: `radar-native`, `p2a-preflight`, or `both`. Copy only agreed Feature Radar artifacts, create `handoff-manifest.md`, and do not overwrite existing files unless explicitly requested.

## Output Contract

For a completed collection run, produce:

```text
research-plan.md
source-candidates.md
research-bundle.md
signal-map.md
collection-report.md
```

For existing project research, also produce these outputs when useful:

```text
local-project-scan.md
capability-gap-analysis.md
next-iteration-recommendations.md
```

For handoff/export, create this file in each destination:

```text
handoff-manifest.md
```

P2A export is explicitly out of scope unless requested.

See `references/workflow.md`, `references/source-record.md`, and `references/handoff.md`.
