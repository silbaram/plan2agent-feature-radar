# Feature Radar

Feature Radar is being shaped as a skill/subagent research workflow, not primarily as a CLI, MCP server, or P2A exporter.

It supports two research modes:

- idea research: investigate a product idea from web, service, docs, changelog, GitHub, issue, PR, discussion, or community signals
- existing project research: inspect a local project read-only, compare the current implementation with external signals, and recommend next enhancement candidates

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
  evidence-reviewer.md

.codex/agents/
  local-project-scanner.toml
  radar-handoff-packager.toml
  reference-discovery.toml
  web-source-collector.toml
  github-signal-scanner.toml
  evidence-reviewer.toml
```

## Intended Flows

```text
user idea
  -> Feature Radar skill
  -> reference discovery subagent
  -> web source collector subagent
  -> GitHub signal scanner subagent
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

## Reading A Run

Feature Radar run outputs are meant to be consumed in layers:

Each run includes a harness-generated `_INDEX.md` at the run root. Start there to distinguish result documents (`collection-report.md`, `next-iteration-recommendations.md`) from evidence documents used to trace the recommendation rationale.

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
  -> optional read-only scan of the current local project

capability-gap-analysis.md
  -> optional comparison of current implementation vs external signals

next-iteration-recommendations.md
  -> optional prioritized enhancement candidates for an existing project

handoff-manifest.md
  -> created during export to project; records source run, target path, mode, copied files, and missing optional files
```

Use `collection-report.md` as the decision document: it should say what to do next, what architecture or MVP direction is recommended, and which risks must be tracked. Use `research-bundle.md` to understand the reasoning behind that decision.

Treat `signal-map.md` and `source-candidates.md` as the evidence layer. A strong recommendation in `collection-report.md` should be traceable to a claim in `research-bundle.md`, then to one or more signals in `signal-map.md`, then to canonical URLs and confidence notes in `source-candidates.md`.

For existing project research, treat `local-project-scan.md` as the local evidence layer. Recommendations in `next-iteration-recommendations.md` should be traceable to both local file references and external source signals whenever possible.

`research-plan.md` is not a result document. It is the contract for what was investigated and which questions remain in or out of scope.

## Usage

In Codex, invoke the repo skill explicitly:

```text
$feature-radar-research 조사해줘: Jira 같은 시스템의 서비스/웹/GitHub 자료를 수집하고 근거를 정리해줘.
```

For parallel research, ask Codex to spawn the project agents:

```text
$feature-radar-research 를 사용해서 reference-discovery, web-source-collector, github-signal-scanner, evidence-reviewer 에이전트를 나눠 실행하고 결과를 합쳐줘.
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

`radar_handoff.py` validates complete runs by default and infers the run type from the source run `mode:` header. Use `--run-type` only to override the detected type. Use `--allow-incomplete` only when intentionally exporting draft research.

In Claude Code, invoke the project skill:

```text
/feature-radar-research Jira 같은 시스템에 대해 서비스와 GitHub 신호를 조사해줘.
```

Claude Code can delegate to the project subagents in `.claude/agents/`.
