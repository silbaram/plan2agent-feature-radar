# Feature Radar

Feature Radar is being shaped as a skill/subagent research workflow, not primarily as a CLI, MCP server, or P2A exporter.

It supports two research modes:

- idea research: investigate a product idea from web, service, docs, changelog, GitHub, issue, PR, discussion, or community signals
- existing project research: inspect a local project read-only, compare the current implementation with external signals, and recommend next enhancement candidates

It also supports two research profiles:

- `general`: the default Feature Radar research method
- `tool-gap`: look for evidence-backed, independent tools that close repeated workflow or ecosystem gaps

Mode and profile are orthogonal. `mode` says what is being researched; `profile` says how the evidence will be interpreted. For example, `idea + tool-gap` looks for supporting-tool opportunities around an idea, while `existing-project + tool-gap` compares those opportunities with a local project's current capabilities. Adding a profile does not create a third run mode.

It also supports a handoff step:

- export to project: copy a completed Feature Radar run into a target project under agreed `.feature-radar` and/or `.plan2agent` directories

The current repo contains the first project-scoped authoring artifacts:

```text
.agents/skills/feature-radar-research/
  SKILL.md
  references/

.claude/skills/feature-radar-research/
  SKILL.md
  references/

.claude/agents/
  local-project-scanner.md
  radar-handoff-packager.md
  reference-discovery.md
  web-source-collector.md
  github-signal-scanner.md
  opportunity-synthesizer.md
  evidence-reviewer.md

.codex/agents/
  local-project-scanner.toml
  radar-handoff-packager.toml
  reference-discovery.toml
  web-source-collector.toml
  github-signal-scanner.toml
  opportunity-synthesizer.toml
  evidence-reviewer.toml
```

## Intended Flows

```text
user idea
  -> Feature Radar skill
  -> reference discovery subagent
  -> web source collector subagent
  -> GitHub signal scanner subagent
  -> opportunity synthesizer subagent
  -> evidence reviewer subagent
  -> Feature Radar native research output
```

```text
local project path
  -> Feature Radar skill
  -> local project scanner subagent
  -> reference discovery subagent
  -> web source collector subagent
  -> GitHub signal scanner subagent
  -> opportunity synthesizer subagent
  -> evidence reviewer subagent
  -> next iteration recommendation output
```

```text
completed Feature Radar run
  -> Feature Radar skill
  -> radar handoff packager subagent
  -> target project .feature-radar/runs/<project-slug>/
  -> optional target project .plan2agent/artifacts/<project-id>/preflight-research/
  -> handoff manifest
```

P2A export is optional and intentionally not part of the first research workflow.

For `profile: tool-gap`, discovery and collection still use the same flow. The profile then normalizes evidence, materializes accepted problem clusters, synthesizes opportunities, reviews alternatives and counter-evidence, applies a qualitative assessment, and completes final evidence review. It returns zero to three supporting-tool candidates without forcing a recommendation.

## Tool Gap Profile Boundary

The Tool Gap profile is an incremental specialization of the existing skill/subagent harness. It does not introduce a separate product, a standalone Node/TypeScript CLI, a database, a custom LLM provider, or required JSON artifacts.

The current implementation remains Markdown-native and uses the existing run lifecycle and handoff helpers. Direct GitHub API collection, versioned JSON schemas, deterministic numeric scoring, SQLite/DuckDB, scheduled refresh, and a web UI remain later-stage options. They should be added only after several human-reviewed runs establish stable evidence and scoring contracts.

Without a named, versioned deterministic scorer, opportunity and confidence scores are `not_scored`; a user request alone does not authorize numeric scoring. Agents use `strong | moderate | weak | unknown` for opportunity assessment and `high | medium | low | unknown` for evidence confidence, explain both with evidence and caveats, and preserve unknowns. GitHub evidence can support developer pain, recurrence, workarounds, and maintainer disposition, but does not by itself establish broad market size, monetization, or defensibility.

See [`docs/plns/02-tool-gap-profile-integration.md`](docs/plns/02-tool-gap-profile-integration.md) for the architecture decision, evidence trace, staged gates, and deferred scope.

## Reading A Run

Feature Radar run outputs are meant to be consumed in layers:

Each run includes a harness-generated `_INDEX.md` at the run root. It is a derived view regenerated from authoritative research artifact metadata, including during handoff. Start there to distinguish result documents (`collection-report.md`, `next-iteration-recommendations.md`) from evidence documents used to trace the recommendation rationale.

Use a readable English project slug for the output directory:

```text
.feature-radar/runs/<project-slug>/
```

Example:

```text
.feature-radar/runs/on-device-character-chat-app/
```

Prefer lowercase ASCII words joined with hyphens. Do not use a timestamp as the primary run directory name unless the same project needs multiple separate snapshots.

```text
research-plan.md
  -> scope and questions

collection-report.md
  -> final actionable synthesis

research-bundle.md
  -> analysis body behind the synthesis

signal-map.md
  -> evidence map for technical/product signals

source-candidates.md
  -> source registry and confidence labels

local-project-scan.md
  -> required read-only scan for existing-project runs

capability-gap-analysis.md
  -> required comparison for existing-project runs

next-iteration-recommendations.md
  -> required recommendation record for existing-project runs

handoff-manifest.md
  -> created during export to project; records source run, target path, run_mode, profile, handoff_mode, source_complete, copied files, missing required files, and the sole optional file (`p2a-context.json`)
```

For an existing-project run, keep all three local-project files even when a comparison or recommendation is not applicable; record an explicit `N/A` with the reason.

Use `collection-report.md` as the decision document: it should say what to do next, what architecture or MVP direction is recommended, and which risks must be tracked. Use `research-bundle.md` to understand the reasoning behind that decision.

Treat `signal-map.md` and `source-candidates.md` as the evidence layer. A strong recommendation in `collection-report.md` should be traceable to a claim in `research-bundle.md`, then to one or more signals in `signal-map.md`, then to canonical URLs and confidence notes in `source-candidates.md`.

For existing project research, treat `local-project-scan.md` as the local evidence layer. Recommendations in `next-iteration-recommendations.md` should be traceable to both local file references and external source signals whenever possible.

`research-plan.md` is not a result document. It is the contract for what was investigated and which questions remain in or out of scope.

### Tool Gap Artifact Mapping

The Tool Gap profile uses the current Radar-native artifacts instead of adding a parallel report set:

| Tool Gap concept | Current Radar-native representation |
| --- | --- |
| normalized idea, keywords, exclusions, seed repositories | `research-plan.md` |
| repository candidates and selection/exclusion reasons | `source-candidates.md` |
| ecosystem map and accepted ProblemCluster table | `research-bundle.md`, backed by `source-candidates.md` and `signal-map.md` |
| normalized evidence and counter-signals | `signal-map.md`, backed by canonical URLs in `source-candidates.md` |
| zero to three ranked opportunities, `insufficient_evidence`, or `no_supported_opportunity` | `collection-report.md` |
| local capability comparison and project-specific candidates | `capability-gap-analysis.md` and `next-iteration-recommendations.md` |
| final decision report | `collection-report.md` |
| run metadata | authoritative artifact headers and derived `_INDEX.md` |

`evidence.json`, `opportunities.json`, `run.json`, and `final-report.md` are not current canonical artifacts. If structured artifacts become useful after the profile is calibrated, they should be optional, versioned representations of the same evidence trace rather than competing sources of truth.

## Usage

In Codex, invoke the repo skill explicitly:

```text
$feature-radar-research 조사해줘: Jira 같은 시스템의 서비스/웹/GitHub 자료를 수집하고 근거를 정리해줘.
```

For delegated research, ask Codex to parallelize independent collection and then run synthesis and review after their inputs are ready:

```text
$feature-radar-research 를 사용해서 reference-discovery, web-source-collector, github-signal-scanner 수집을 나눠 실행하고, 입력이 준비되면 opportunity-synthesizer와 evidence-reviewer 순서로 결과를 합쳐줘.
```

For Tool Gap research, state the profile and allow a no-candidate outcome:

```text
$feature-radar-research profile: tool-gap으로 "AI agent debugging tool"을 조사해줘. 반복되는 문제를 독립 서브 도구 후보 0~3개로 정리하고, 각 후보의 대안과 반대 근거를 포함해줘.
```

For an existing local project, pass the project path and ask for read-only analysis:

```text
$feature-radar-research 로컬 프로젝트 /path/to/project 를 read-only로 확인하고, 외부 서비스/문서/GitHub 신호와 비교해서 다음 고도화 기능 후보를 추천해줘. 코드 수정은 하지 마.
```

For a local project research run that may later be handed off, create the run scaffold first:

```bash
python3 tools/radar_run.py init \
  --slug plan2agent-memory \
  --title "Plan2Agent Memory self-recovery and document management research" \
  --mode existing-project \
  --local-project /Users/qoo10/projects/plan2agent-memory
```

Select the Tool Gap profile when initializing either mode:

```bash
python3 tools/radar_run.py init \
  --slug agent-debugging-tool-gap \
  --title "AI agent debugging tool gaps" \
  --mode idea \
  --profile tool-gap
```

`--profile` defaults to `general`. Legacy runs are treated as `general` only when profile metadata is absent from every research artifact. Research artifact `mode`, `profile`, and `status` headers are authoritative and must be valid and coherent. `_INDEX.md` is derived from those headers. `init --overwrite` cannot change an existing run's mode; use a new slug or an explicit migration workflow instead.

Then fill the generated files under:

```text
.feature-radar/runs/plan2agent-memory/
```

The scaffold starts with `status: draft`. After the research content is complete, change each required artifact header to `status: complete`.

Validate the run before exporting it:

```bash
python3 tools/radar_run.py validate \
  --source-run plan2agent-memory \
  --mode existing-project
```

To hand off a completed run to a project, provide the run slug, target project path, and export mode:

```text
$feature-radar-research plan2agent-memory run을 /path/to/my-app 프로젝트로 handoff 해줘. mode는 both로 하고, P2A project id는 my-app으로 써줘.
```

Handoff modes:

```text
radar-native
  -> /path/to/my-app/.feature-radar/runs/<project-slug>/

p2a-preflight
  -> /path/to/my-app/.plan2agent/artifacts/<project-id>/preflight-research/

both
  -> both destinations
```

Optional helper script:

```bash
python3 tools/radar_handoff.py \
  --source-run plan2agent-memory \
  --target-project /path/to/my-app \
  --mode both \
  --project-id my-app
```

`radar_handoff.py` validates complete runs by default, infers source `run_mode` from coherent research artifact metadata, and regenerates `_INDEX.md` in each destination. It preserves source `profile` and records destination `handoff_mode` separately. The command-line `--mode both` selection creates two manifests, one with `handoff_mode: radar-native` and one with `handoff_mode: p2a-preflight`; no individual manifest stores `both`. A manifest `mode` field, when retained for compatibility, aliases `handoff_mode` and never means `run_mode`. `--run-type` is an expected-run-type assertion, not a source-header override. Use `--allow-incomplete` only when intentionally exporting draft research; such manifests set `source_complete: false` and separate missing required files from the sole optional file, `p2a-context.json`. `--overwrite` synchronizes only recognized managed artifacts, removing stale managed files that are absent from the source so the destination remains consistent with its manifest; self-handoff and non-file artifact conflicts are rejected before writing.

In Claude Code, invoke the project skill:

```text
/feature-radar-research Jira 같은 시스템에 대해 서비스와 GitHub 신호를 조사해줘.
```

The same mode/profile contract applies in Claude Code:

```text
/feature-radar-research profile: tool-gap으로 AI agent debugging tool을 조사하고 근거를 통과한 후보만 0~3개 제안해줘.
```

Claude Code can delegate to the project subagents in `.claude/agents/`.
