# Tool Gap Research Profile

Use this reference only when a run declares or the user requests:

```text
profile: tool-gap
```

The profile specializes Feature Radar's existing research workflow. It does not create a third run mode or a separate product.

```text
mode: idea | existing-project
profile: general | tool-gap
```

## Input Contract

Record these fields in `research-plan.md`:

- one-line idea
- target users and problem
- search keywords and exclusions
- optional seed repositories
- source scope and time window
- whether a local project is in scope

If the repository helper is available, initialize the normal artifact set with `--profile tool-gap`. Research artifact `mode`, `profile`, and `status` headers are authoritative and must be valid and coherent. Use `general` only when legacy runs have no profile in any research artifact. `_INDEX.md` is a derived view regenerated from those headers. Do not use `init --overwrite` to change an existing run's mode.

## Staged Workflow

```text
plan
  -> reference discovery
  -> web / GitHub / optional local collection
       (independent collection may run in parallel)
  -> evidence normalization
  -> problem clustering
  -> opportunity synthesis
  -> alternatives and counter-evidence review
  -> qualitative assessment
  -> final evidence review
  -> collection-report.md
```

Do not synthesize opportunities before source and signal inputs are ready.

## Signal Interpretation

When supported by the source, distinguish:

- `pain`
- `workaround`
- `duplicate`
- `out_of_scope`
- `wont_fix`
- `stale`
- `implemented`
- `unclear`

Record maintainer disposition, recurrence across repositories, engagement, recency, resolution state, alternatives, and counter-signals separately. A label is not conclusive by itself.

GitHub evidence can support developer pain, recurrence, workarounds, and maintainer stance. It does not by itself prove broad market size, monetization, or defensibility.

## Problem Cluster Contract

Before opportunity rows, write every accepted problem cluster to `research-bundle.md` using this shape:

```text
cluster id | representative problem | evidence refs | repository scope / recurrence | counter-signals | caveat
```

Cluster IDs must be unique, and every cluster reference in an opportunity must resolve to one of these rows. Keep rejected clusters in a separate table with their rejection reason.

## Opportunity Contract

Return zero to three retained opportunities. Zero is a valid result. Use:

- `insufficient_evidence` when collection quality or coverage is too weak to decide
- `no_supported_opportunity` when the evidence is sufficient but every candidate is already solved, contradicted, out of scope, or otherwise not worth retaining

Never pad the result with weak candidates.

Each retained opportunity must include:

- ID, title, category, and target users
- problem-cluster references
- supporting evidence references
- existing alternatives and their coverage
- counter-evidence references and uncertainty
- a narrow, testable MVP scope
- a qualitative assessment and confidence rationale

Allowed categories:

- plugin or extension
- cross-framework adapter
- testing or evaluation tool
- debugging or observability tool
- CLI or developer experience
- migration or compatibility tool
- security or permission management
- deployment or operations automation
- data transformation or visualization
- agent harness configuration

Candidates must be independent supporting tools, not unbounded rewrites of the source product.

## Evidence Trace

```text
collection-report recommendation
  -> Opportunity
  -> ProblemCluster
  -> Evidence / counter-evidence
  -> SourceRecord canonical URL
```

For existing-project runs, also trace local fit and constraints to `local-project-scan.md` with `path:line`.

Keep source facts separate from agent summaries and classifications. Keep local implementation evidence separate from external demand evidence.

## Native Artifact Mapping

Use the current Markdown-native artifacts:

| Tool Gap concern | Feature Radar artifact |
| --- | --- |
| idea, keywords, exclusions, seed repositories | `research-plan.md` |
| repository candidates and selection/exclusion reasons | `source-candidates.md` |
| ecosystem map and problem clusters | `research-bundle.md` |
| evidence and counter-signals | `signal-map.md` |
| zero to three opportunities, `insufficient_evidence`, or `no_supported_opportunity` | `collection-report.md` |
| existing-project local evidence and comparison | `local-project-scan.md`, `capability-gap-analysis.md`, `next-iteration-recommendations.md` |

`collection-report.md` remains the canonical final report. Do not add required `final-report.md`, `evidence.json`, `opportunities.json`, or `run.json` during the Markdown calibration stage.

For `mode: existing-project`, all three local-project artifacts are required by the current run contract. When a comparison or recommendation is not applicable, keep the file and record an explicit `N/A` with the reason instead of omitting it.

## Scoring Guardrail

Without a named, versioned deterministic scorer:

- set numeric opportunity and confidence scores to `not_scored`
- provide qualitative assessment with evidence and caveats
- keep unknown factors unknown
- treat Build/Prototype/Watch/Skip thresholds as calibration hypotheses

An agent must not invent precise scores. A high opportunity assessment must not erase low evidence confidence.

Use this qualitative rubric without translating it into hidden numbers:

| Dimension | Values | Meaning |
| --- | --- | --- |
| opportunity assessment | `strong`, `moderate`, `weak`, `unknown` | Strength of the unmet problem, alternative gap, and narrow MVP case after counter-evidence review. |
| evidence confidence | `high`, `medium`, `low`, `unknown` | Quality, independence, recency, and traceability of the evidence supporting the assessment. |

Explain both values with evidence references and caveats. `unknown` remains unknown and is never counted as positive evidence. Numeric scores are allowed only when the result of a named, versioned deterministic scorer is supplied.

## Done Criteria

- every concrete external claim has a canonical URL
- every local claim has `path:line` when possible
- each retained opportunity traces to supporting and counter evidence
- alternatives are explicitly checked
- stale, implemented, project-specific, and weak signals are not treated as unmet demand
- zero-candidate runs complete successfully with the correct `insufficient_evidence` or `no_supported_opportunity` outcome
- authoritative research artifact `mode`, `profile`, and `status` values are coherent, and `_INDEX.md` is regenerated from them
- the existing native artifacts, optional P2A boundary, and no-overwrite handoff policy remain intact
- no standalone CLI, database, custom LLM provider, or required JSON layer is introduced merely to execute this profile
