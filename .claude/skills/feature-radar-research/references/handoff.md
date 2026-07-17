# Feature Radar Handoff Workflow

Use this workflow when the user asks to copy, export, hand off, or move a completed Feature Radar run into a target project.

Handoff is a packaging step. It does not change research conclusions, approve P2A gates, or implement code.

## Inputs

Required:

- source run path or project slug under `.feature-radar/runs/<project-slug>/`
- target project path
- preflight sequence for `p2a-preflight` or `both`, for example `001-kubernetes-users`

Optional:

- handoff mode: `radar-native`, `p2a-preflight`, or `both`
- P2A project id
- overwrite policy

Defaults:

- mode: `radar-native`
- P2A project id: readable kebab-case name derived from the target project directory
- overwrite policy: do not overwrite existing files

## Destinations

```text
radar-native
  -> <target-project>/.feature-radar/runs/<project-slug>/

p2a-preflight
  -> <target-project>/.plan2agent/artifacts/<project-id>/preflight-research/<sequence>/

both
  -> both destinations
```

## Copy Set

Copy these files when they exist:

```text
_INDEX.md
research-plan.md
source-candidates.md
research-bundle.md
signal-map.md
collection-report.md
local-project-scan.md
capability-gap-analysis.md
next-iteration-recommendations.md
p2a-context.json
```

`p2a-context.json` is copied only if it already exists or the user explicitly asks to generate it.

Among the copy-set entries, only `p2a-context.json` is optional. `_INDEX.md` is derived and regenerated in each destination rather than treated as a required source artifact.

Do not copy:

- `.env`, secrets, credentials, private keys, tokens, or local secret config
- dependency directories
- build outputs
- generated caches
- raw crawl logs
- unrelated project files

## Manifest

Create `handoff-manifest.md` in each destination.

Use this shape:

```text
# Feature Radar Handoff Manifest

source_run:
project_slug:
target_project:
run_mode:
profile:
handoff_mode:
mode: # compatibility alias for handoff_mode when emitted by older helpers
source_complete:
p2a_project_id:
preflight_sequence: # sequence for p2a-preflight; none for radar-native
created_at:
overwrite_policy:

## Copied Files

- ...

## Missing Required Files

- ...

## Missing Optional Files

- ...

## Caveats

- ...
```

Set `source_complete: true` only when every required artifact is present, non-empty, and `status: complete`; otherwise an explicitly allowed incomplete handoff records `source_complete: false`.

## Procedure

1. Resolve the source run.
2. Verify that the source run contains at least one expected Feature Radar artifact.
3. Infer `run_mode` as `idea` or `existing-project` and validate the expected artifact set; authoritative research artifact `mode`, `profile`, and `status` headers must be valid and coherent. All three local-project artifacts are required for `existing-project`, with explicit `N/A` content allowed where appropriate.
4. Use `general` only for legacy runs with no profile in any research artifact. Reject invalid, duplicate, mixed, or conflicting authoritative metadata. Ignore `_INDEX.md` as metadata authority.
5. Resolve the target project path.
6. Select destination directories from `handoff_mode`. For P2A output, validate that the sequence is one safe lowercase directory component with a numeric prefix; reject traversal and nested paths.
7. Check for existing destination files.
8. If conflicts exist and the user did not explicitly request overwrite, stop and report the conflicts. Treat recognized stale destination artifacts as conflicts too.
9. Before writing, reject the source run itself and non-file managed destination paths. With explicit overwrite, synchronize only recognized managed artifacts: replace transferred files and remove stale managed files that are absent from the source.
10. Copy the research artifacts, preserving their contents.
11. Regenerate `_INDEX.md` in each destination from authoritative research artifact metadata.
12. Create `handoff-manifest.md` with separate source `run_mode`, source `profile`, destination `handoff_mode`, `preflight_sequence`, and `source_complete`. A CLI selection of `both` creates two manifests whose `handoff_mode` values are `radar-native` and `p2a-preflight`, respectively.
13. For intentional incomplete export, set `source_complete: false` and list missing required files separately from missing optional files. The only optional file is `p2a-context.json`. Report destination paths, copied files, missing files, and any conflicts.

If the target path is outside the current writable workspace, request the required filesystem approval before writing.

## Optional Helper Script

When working from this repository, Codex can use the dependency-free helper:

```bash
python3 tools/radar_handoff.py \
  --source-run <project-slug-or-path> \
  --target-project <target-project> \
  --mode p2a-preflight \
  --sequence 001-<research-topic>
```

`--sequence` is required for `p2a-preflight` and `both`. Use `--mode both` only when a target-side Radar archive is also wanted; `p2a-preflight` alone creates no target `.feature-radar/` directory. Use `--dry-run` to preview without writing. The command-line `--mode` flag is the handoff destination mode. Complete validation is the default, and the helper infers source `run_mode` (`idea` or `existing-project`) from coherent research artifact headers. It preserves the source `profile:`, regenerates `_INDEX.md` in each destination, and treats only a legacy run with no profile in any research artifact as `general`. A manifest `mode:` field, when retained for compatibility, aliases `handoff_mode`; it never means source `run_mode`. `--run-type` is an expected-run-type assertion, not an override of source headers. Use `--allow-incomplete` only when the user intentionally asks to export draft or incomplete research; the manifest must then set `source_complete: false` and separate missing required files from the sole optional file, `p2a-context.json`. Use `--overwrite` only when the user explicitly requested replacement within the same sequence; it synchronizes recognized managed artifacts and removes stale managed files so the destination matches the manifest.

## Acceptance Rules

- Handoff must be traceable from source run to target project.
- The manifest must keep `run_mode`, `profile`, and `handoff_mode` semantically separate.
- The manifest must record `source_complete` and distinguish missing required files from missing optional files.
- A P2A manifest must record the selected `preflight_sequence`.
- Handoff must not silently overwrite existing research artifacts.
- Handoff must not rewrite research conclusions.
- P2A preflight output is created only when the user requests `p2a-preflight` or `both`.
- `p2a-preflight` output must not create a target `.feature-radar/` copy.
- The final response must include the destination path or explain why no files were copied.
