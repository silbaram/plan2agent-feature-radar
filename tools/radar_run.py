#!/usr/bin/env python3
"""Initialize and validate Feature Radar run artifact directories."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


CORE_ARTIFACTS = [
    "research-plan.md",
    "source-candidates.md",
    "research-bundle.md",
    "signal-map.md",
    "collection-report.md",
]

EXISTING_PROJECT_ARTIFACTS = [
    "local-project-scan.md",
    "capability-gap-analysis.md",
    "next-iteration-recommendations.md",
]

MODE_ARTIFACTS = {
    "idea": CORE_ARTIFACTS,
    "existing-project": CORE_ARTIFACTS + EXISTING_PROJECT_ARTIFACTS,
}

TEMPLATE_TITLES = {
    "research-plan.md": "Research Plan",
    "source-candidates.md": "Source Candidates",
    "research-bundle.md": "Research Bundle",
    "signal-map.md": "Signal Map",
    "collection-report.md": "Collection Report",
    "local-project-scan.md": "Local Project Scan",
    "capability-gap-analysis.md": "Capability Gap Analysis",
    "next-iteration-recommendations.md": "Next Iteration Recommendations",
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def resolve_run(source_run: str) -> Path:
    direct = Path(source_run).expanduser()
    if direct.exists():
        return direct.resolve()

    by_slug = Path(".feature-radar") / "runs" / source_run
    if by_slug.exists():
        return by_slug.resolve()

    raise FileNotFoundError(
        f"run not found: {source_run} (also checked {by_slug.as_posix()})"
    )


def has_draft_status(text: str) -> bool:
    return any(line.strip().lower() == "status: draft" for line in text.splitlines()[:12])


def has_complete_status(text: str) -> bool:
    return any(line.strip().lower() == "status: complete" for line in text.splitlines()[:12])


def artifact_template(
    *,
    name: str,
    title: str,
    slug: str,
    mode: str,
    local_project: str | None,
) -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    heading = TEMPLATE_TITLES[name]
    local_project_line = local_project or "not provided"

    body_by_name = {
        "research-plan.md": """## Scope

- Product/project:
- User request:
- Research mode:
- In scope:
- Out of scope:

## Questions

- 

## Planned Outputs

- research-plan.md
- source-candidates.md
- research-bundle.md
- signal-map.md
- collection-report.md
""",
        "source-candidates.md": """| source id | source type | URL or local path | why relevant | confidence | notes |
| --- | --- | --- | --- | --- | --- |
| LOCAL-1 | local_project |  |  |  |  |
""",
        "research-bundle.md": """## Summary

## Local Evidence

## External Evidence

## Comparison

## Open Questions
""",
        "signal-map.md": """| signal id | signal | source ids | implication | caveat | confidence |
| --- | --- | --- | --- | --- | --- |
""",
        "collection-report.md": """## Verdict

## Recommended Direction

## Key Evidence

## Risks

## Next Steps
""",
        "local-project-scan.md": """| capability | status | local evidence path:line | implication | confidence | follow-up |
| --- | --- | --- | --- | --- | --- |
""",
        "capability-gap-analysis.md": """| area | local status | external/reference signal | gap | recommendation | confidence |
| --- | --- | --- | --- | --- | --- |
""",
        "next-iteration-recommendations.md": """| rank | recommendation | action | why now | local evidence | external evidence | expected impact | cost/risk | confidence | next step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
""",
    }

    return f"""# {heading}

run_slug: {slug}
title: {title}
mode: {mode}
local_project: {local_project_line}
created_at: {now}
status: draft

{body_by_name[name]}"""


def init_run(args: argparse.Namespace) -> int:
    slug = slugify(args.slug)
    run_dir = Path(".feature-radar") / "runs" / slug
    artifacts = MODE_ARTIFACTS[args.mode]

    existing = [run_dir / name for name in artifacts if (run_dir / name).exists()]
    if existing and not args.overwrite:
        print("error: run artifact files already exist; rerun with --overwrite to replace")
        for path in existing:
            print(f"- {path}", file=sys.stderr)
        return 3

    run_dir.mkdir(parents=True, exist_ok=True)
    for name in artifacts:
        path = run_dir / name
        if path.exists() and not args.overwrite:
            continue
        path.write_text(
            artifact_template(
                name=name,
                title=args.title,
                slug=slug,
                mode=args.mode,
                local_project=args.local_project,
            ),
            encoding="utf-8",
        )
        print(f"wrote {path}")

    print(f"run_dir: {run_dir}")
    return 0


def validate_run(args: argparse.Namespace) -> int:
    try:
        run_dir = resolve_run(args.source_run)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    required = MODE_ARTIFACTS[args.mode]
    missing = [name for name in required if not (run_dir / name).is_file()]
    artifact_texts = {
        name: (run_dir / name).read_text(encoding="utf-8")
        for name in required
        if (run_dir / name).is_file()
    }
    empty = [
        name
        for name, text in artifact_texts.items()
        if not text.strip()
    ]
    draft = [
        name
        for name, text in artifact_texts.items()
        if has_draft_status(text)
    ]
    incomplete = [
        name
        for name, text in artifact_texts.items()
        if not has_complete_status(text)
    ]
    non_draft_incomplete = [
        name
        for name in incomplete
        if name not in draft
    ]

    if missing or empty or (draft and not args.allow_draft) or non_draft_incomplete:
        print(f"run invalid: {run_dir}")
        if missing:
            print("missing files:")
            for name in missing:
                print(f"- {name}")
        if empty:
            print("empty files:")
            for name in empty:
                print(f"- {name}")
        if draft and not args.allow_draft:
            print("draft files:")
            for name in draft:
                print(f"- {name}")
        if non_draft_incomplete:
            print("missing complete status:")
            for name in non_draft_incomplete:
                print(f"- {name}")
        if (draft and not args.allow_draft) or non_draft_incomplete:
            print("hint: complete the research content and set status: complete")
        return 1

    print(f"run valid: {run_dir}")
    print("checked files:")
    for name in required:
        print(f"- {name}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Initialize or validate Feature Radar run artifact directories."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a run artifact scaffold.")
    init_parser.add_argument("--slug", required=True, help="Readable run slug.")
    init_parser.add_argument("--title", required=True, help="Human-readable run title.")
    init_parser.add_argument(
        "--mode",
        choices=["idea", "existing-project"],
        default="idea",
        help="Run artifact set to initialize. Default: idea.",
    )
    init_parser.add_argument(
        "--local-project",
        help="Local project path recorded in artifact headers.",
    )
    init_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing run artifact files.",
    )
    init_parser.set_defaults(func=init_run)

    validate_parser = subparsers.add_parser("validate", help="Validate a run artifact set.")
    validate_parser.add_argument(
        "--source-run",
        required=True,
        help="Run path or slug under .feature-radar/runs/.",
    )
    validate_parser.add_argument(
        "--mode",
        choices=["idea", "existing-project"],
        default="idea",
        help="Expected run artifact set. Default: idea.",
    )
    validate_parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Allow scaffold files that still declare status: draft.",
    )
    validate_parser.set_defaults(func=validate_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
