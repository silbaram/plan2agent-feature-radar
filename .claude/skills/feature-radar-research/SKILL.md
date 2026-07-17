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

For handoff, require a source run and target path and default `handoff_mode` to `radar-native`. For `p2a-preflight` or `both`, also require `preflight_sequence` in numeric-prefix kebab form such as `001-kubernetes-users`. Derive a readable English run slug when omitted.

## Procedure

Read `references/workflow.md` before acting. If the user requests `profile: tool-gap`, or asks specifically for independent supporting-tool opportunities, also read `references/tool-gap-profile.md`. Keep `mode: idea | existing-project` unchanged and pass the profile to each subagent. Research artifact `mode`, `profile`, and `status` headers are authoritative and must be coherent; only legacy runs with no profile in any research artifact fall back to `general`. `_INDEX.md` is a derived view regenerated from those headers.

1. Define a small research plan.
2. Unless the user asks for a plan-only/chat-only answer or forbids file writes, create a native run directory under `.feature-radar/runs/<project-slug>/` before the final answer.
   - When working from this repository, prefer `python3 tools/radar_run.py init --slug <project-slug> --title <title> --mode idea`.
   - For existing local project research, use `--mode existing-project` and include `--local-project <path>`.
   - Add `--profile tool-gap` only for Tool Gap research. The default and legacy fallback are `general`.
   - Never use `init --overwrite` to change an existing run's mode; create a new slug or use an explicit migration workflow.
3. Delegate to project subagents when useful:
   - `local-project-scanner`, only when a local project path is provided
   - `radar-handoff-packager`, only when exporting a completed run to a target project
   - `reference-discovery`
   - `web-source-collector`
   - `github-signal-scanner`
   - `opportunity-synthesizer`, after its source and signal inputs are ready
   - `evidence-reviewer`
4. Keep raw search noise out of the main conversation.
5. Return only source-backed summaries and URLs.
6. Store research outputs under `.feature-radar/runs/<project-slug>/` for completed research, local-project research, or handoff-prep requests unless the user explicitly asks for plan-only/chat-only output. Use a readable English project slug, not a timestamp, unless the same project needs multiple snapshots.
7. Before handoff/export, validate the completed run. When working from this repository, prefer `python3 tools/radar_run.py validate --source-run <project-slug> --mode <idea|existing-project>`.

If the user provides a local project path, inspect it read-only. Skip secrets, credentials, dependency directories, build outputs, generated artifacts, and large binary files unless explicitly requested. Compare the current implementation with external signals and recommend next enhancement candidates. Do not modify code unless explicitly requested.

If the user asks to hand off or export a completed run, read `references/handoff.md`. Identify the source run, target project path, and handoff mode: `radar-native`, `p2a-preflight`, or `both`. For `p2a-preflight` or `both`, require a safe sequence such as `001-kubernetes-users` and export to `preflight-research/<sequence>/`. A P2A-only handoff must not create a target `.feature-radar/` copy. Copy only agreed Feature Radar artifacts, regenerate `_INDEX.md` from authoritative metadata in each destination, and create `handoff-manifest.md` with `source_complete`, `preflight_sequence`, and separate missing-required and missing-optional sections. The sole optional file is `p2a-context.json`. Do not overwrite existing files unless explicitly requested; different sequences coexist without overwrite.

## Output Contract

For a completed collection run, produce:

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

P2A export is explicitly out of scope unless requested. For `profile: tool-gap`, return zero to three supported opportunities. Use `insufficient_evidence` when coverage is too weak to decide and `no_supported_opportunity` when sufficient evidence rejects every candidate; never pad weak candidates. Across all profiles, numeric scores are allowed only when supplied by a named, versioned deterministic scorer; a user request alone is not sufficient.

See `references/workflow.md`, `references/source-record.md`, `references/tool-gap-profile.md`, and `references/handoff.md`.
