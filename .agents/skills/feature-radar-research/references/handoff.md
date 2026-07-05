# Feature Radar Handoff Workflow

Use this workflow when the user asks to copy, export, hand off, or move a completed Feature Radar run into a target project.

Handoff is a packaging step. It does not change research conclusions, approve P2A gates, or implement code.

## Inputs

Required:

- source run path or project slug under `.feature-radar/runs/<project-slug>/`
- target project path

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
  -> <target-project>/.plan2agent/artifacts/<project-id>/preflight-research/

both
  -> both destinations
```

## Copy Set

Copy these files when they exist:

```text
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
mode:
p2a_project_id:
created_at:
overwrite_policy:

## Copied Files

- ...

## Missing Optional Files

- ...

## Caveats

- ...
```

## Procedure

1. Resolve the source run.
2. Verify that the source run contains at least one expected Feature Radar artifact.
3. For completed research handoff, validate that the source run has the expected artifact set for `idea` or `existing-project` mode and is not still marked `status: draft`.
4. Resolve the target project path.
5. Select destination directories from the mode.
6. Check for existing destination files.
7. If conflicts exist and the user did not explicitly request overwrite, stop and report the conflicts.
8. Create destination directories when safe.
9. Copy the copy set, preserving file contents.
10. Create `handoff-manifest.md`.
11. Report destination paths, copied files, missing optional files, and any conflicts.

If the target path is outside the current writable workspace, request the required filesystem approval before writing.

## Optional Helper Script

When working from this repository, Codex can use the dependency-free helper:

```bash
python3 tools/radar_handoff.py \
  --source-run <project-slug-or-path> \
  --target-project <target-project> \
  --mode radar-native
```

Use `--mode both` to create both destinations, and `--dry-run` to preview without writing. Complete validation is the default, and the helper infers `idea` or `existing-project` from the source run `mode:` header. Use `--run-type` only to override the detected type. Use `--allow-incomplete` only when the user intentionally asks to export draft or incomplete research. Use `--overwrite` only when the user explicitly requested replacement.

## Acceptance Rules

- Handoff must be traceable from source run to target project.
- Handoff must not silently overwrite existing research artifacts.
- Handoff must not rewrite research conclusions.
- P2A preflight output is created only when the user requests `p2a-preflight` or `both`.
- The final response must include the destination path or explain why no files were copied.
