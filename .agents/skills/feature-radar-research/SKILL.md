---
name: feature-radar-research
description: Use when the user wants Feature Radar to research a product idea, research an existing local project, or hand off a completed run to a target project from web, service, docs, changelog, GitHub, issue, PR, discussion, community, local code, or existing run artifacts using skill/subagent workflow.
---

# Feature Radar Research

This skill is for research orchestration and run handoff, not implementation.

Use it when the user asks to investigate a product idea, comparable services, user pain points, GitHub signals, feature gaps, MVP direction, next enhancement candidates for an existing local project, or export a completed Feature Radar run into a target project.

Do not start by creating TypeScript/Python tools, MCP servers, CLI wrappers, or P2A artifacts. Those are optional later implementation details.

## Operating Model

Feature Radar is a skill/subagent workflow:

```text
skill = decides research scope, subagent split, and output contract
subagents = search, collect, compare, scan, and review evidence
tools = only supporting mechanisms such as web search, fetch, read-only file inspection, file copy/write for requested outputs, or GitHub access
```

## Workflow

Read `references/workflow.md` before acting.

If the user asks to hand off or export an existing run to a project, also read `references/handoff.md`.

If the user asks to run research:

1. Clarify the product idea only when it is too vague to search.
2. Unless the user asks for a plan-only/chat-only answer or forbids file writes, create a native run directory under `.feature-radar/runs/<project-slug>/` before the final answer.
   - When working from this repository, prefer `python3 tools/radar_run.py init --slug <project-slug> --title <title> --mode idea`.
   - For existing local project research, use `--mode existing-project` and include `--local-project <path>`.
3. Define a short research plan with search themes and source types.
4. Use subagents when available:
   - local project scan, only when a local project path is provided
   - radar handoff packaging, only when exporting a completed run to a target project
   - reference discovery
   - web source collection
   - GitHub signal scan
   - evidence review
5. Search the web and GitHub through the available environment tools.
6. Store or summarize only source-backed findings.
7. Produce Feature Radar native outputs, not P2A outputs, unless the user explicitly asks for P2A export.
8. Before handoff/export, validate the completed run. When working from this repository, prefer `python3 tools/radar_run.py validate --source-run <project-slug> --mode <idea|existing-project>`.

If the user provides a local project path:

1. Inspect the project read-only.
2. Skip secrets, credentials, dependency directories, build outputs, generated artifacts, and large binary files unless explicitly requested.
3. Identify implemented, partial, missing, risky, and unknown capabilities from local evidence.
4. Compare local capabilities with external service, docs, changelog, GitHub, and community signals.
5. Recommend next enhancement candidates, but do not modify code or create implementation tasks unless explicitly requested.
6. If the request is a completed research/recommendation pass, write the existing-project outputs to `.feature-radar/runs/<project-slug>/` unless the user explicitly requested chat-only output.

If the user asks to hand off or export a completed run:

1. Identify the source run path or project slug.
2. Identify the target project path.
3. Select the mode: `radar-native`, `p2a-preflight`, or `both`. Default to `radar-native` when the user does not specify.
4. Copy only Feature Radar artifacts into the agreed destination directories.
5. Create `handoff-manifest.md` in each destination.
6. Do not overwrite existing files unless the user explicitly requests overwrite or replace.

## Output

For a research run, produce these outputs in `.feature-radar/runs/<project-slug>/` when file writing is appropriate. Use a readable English project slug such as `on-device-character-chat-app`, not a timestamp, unless the same project needs multiple snapshots.

File writing is appropriate for a completed research, local-project research, or handoff-prep request unless the user explicitly asks for plan-only/chat-only output or forbids file writes.

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

If the user only asks for a plan, do not create files. Return the plan in chat.

## Guardrails

- Preserve URLs for every concrete claim.
- Separate official service claims from community complaints.
- Treat GitHub issues as developer-heavy signals, not full market proof.
- Mark weak or stale evidence.
- Do not overfit to SEO comparison pages.
- Do not create P2A artifacts unless requested.
- Do not modify local project files unless the user explicitly asks for implementation.
- Do not read secret files such as `.env`, credentials, private keys, tokens, or local secret config.
- Keep local code evidence separate from external market or community evidence.
- Reference local evidence with file paths and line numbers when possible.
- During handoff, preserve artifact content and copy only agreed Feature Radar outputs.
- During handoff, write to `.plan2agent` only when the user asks for `p2a-preflight` or `both`.
- During handoff, ask before overwriting existing destination files.
