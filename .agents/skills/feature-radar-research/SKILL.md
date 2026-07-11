---
name: feature-radar-research
description: Research product ideas or existing local projects from web, docs, changelogs, GitHub, community, and local-code evidence; identify feature gaps, Tool Gap opportunities, and next enhancements; or hand off completed Feature Radar runs. Use for research and export, not implementation.
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

## Invocation Contract

Resolve each request before acting:

- `action`: default to `research`; use `handoff` when the user explicitly asks to export or copy an existing run.
- `research_mode`: use `existing-project` when the request names a local path or explicitly makes the current repository the research subject; otherwise use `idea`. Map this user-facing field to artifact header `mode`.
- `profile`: use `tool-gap` for an explicit Tool Gap, supporting-tool, independent-tool, CLI, plugin, adapter, testing-tool, debugging-tool, or observability-tool opportunity request; otherwise use `general`.
- `output`: default to `native-run`; use `chat-only` only when explicitly requested or file writes are forbidden.

Explicit valid values override inference. Do not silently repair an invalid explicit value; show its allowed values before creating files. Before starting, state the resolved contract in one concise line and include the planned run path when writing:

```text
Resolved: action=<research|handoff>, research_mode=<idea|existing-project>, profile=<general|tool-gap>, output=<native-run|chat-only> -> <run-path>
```

Do not ask merely because a field was omitted. Ask one concise question only when the research subject cannot be identified, multiple projects or runs are plausible, research versus handoff materially changes the requested artifacts, a handoff source or target cannot be resolved, or overwrite approval is required.

For handoff, require a source run and target path and default `handoff_mode` to `radar-native`. Derive a readable English run slug when omitted.

## Workflow

Read `references/workflow.md` before acting.

If the user requests `profile: tool-gap`, or asks specifically for independent supporting-tool opportunities, also read `references/tool-gap-profile.md` before planning the run. Keep `mode: idea | existing-project` unchanged and pass the profile to each subagent. Research artifact `mode`, `profile`, and `status` headers are authoritative and must be coherent; only legacy runs with no profile in any research artifact fall back to `general`. `_INDEX.md` is a derived view regenerated from those headers.

If the user asks to hand off or export an existing run to a project, also read `references/handoff.md`.

If the user asks to run research:

1. Clarify the product idea only when it is too vague to search.
2. Unless the user asks for a plan-only/chat-only answer or forbids file writes, create a native run directory under `.feature-radar/runs/<project-slug>/` before the final answer.
   - When working from this repository, prefer `python3 tools/radar_run.py init --slug <project-slug> --title <title> --mode idea`.
   - For existing local project research, use `--mode existing-project` and include `--local-project <path>`.
   - Add `--profile tool-gap` only for Tool Gap research. The default and legacy fallback are `general`.
   - Never use `init --overwrite` to change an existing run's mode; create a new slug or use an explicit migration workflow.
3. Define a short research plan with search themes and source types.
4. Use subagents when available:
   - local project scan, only when a local project path is provided
   - radar handoff packaging, only when exporting a completed run to a target project
   - reference discovery
   - web source collection
   - GitHub signal scan
   - opportunity synthesis, after its source and signal inputs are ready
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
3. Select the handoff mode: `radar-native`, `p2a-preflight`, or `both`. Default to `radar-native` when the user does not specify.
4. Copy only Feature Radar artifacts into the agreed destination directories.
5. Regenerate `_INDEX.md` from authoritative research artifact metadata in each destination and create `handoff-manifest.md`. Record `source_complete`; for intentional incomplete export, separate missing required files from the sole optional file, `p2a-context.json`.
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

For existing project research, all three of these outputs are required by the current run contract:

```text
local-project-scan.md
capability-gap-analysis.md
next-iteration-recommendations.md
```

When one of these files has no applicable content, keep it and record an explicit `N/A` with the reason.

For handoff/export, create this file in each destination:

```text
handoff-manifest.md
```

If the user only asks for a plan, do not create files. Return the plan in chat.

## Guardrails

- Preserve URLs for every concrete claim.
- Separate official service claims from community complaints.
- Treat GitHub issues as developer-heavy signals, not full market proof.
- For `profile: tool-gap`, return zero to three supported opportunities. Use `insufficient_evidence` when coverage is too weak to decide and `no_supported_opportunity` when sufficient evidence rejects every candidate; never pad weak candidates.
- Do not invent numeric opportunity or confidence scores without a named, versioned deterministic scorer.
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
