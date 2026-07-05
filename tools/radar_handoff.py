#!/usr/bin/env python3
"""Copy a Feature Radar run into a target project.

This helper is intentionally small and dependency-free. It is a packaging
utility, not a research runner or P2A gate generator.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path


COPY_SET = [
    "research-plan.md",
    "source-candidates.md",
    "research-bundle.md",
    "signal-map.md",
    "collection-report.md",
    "local-project-scan.md",
    "capability-gap-analysis.md",
    "next-iteration-recommendations.md",
    "p2a-context.json",
]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def resolve_source_run(source_run: str) -> Path:
    direct = Path(source_run).expanduser()
    if direct.exists():
        return direct.resolve()

    by_slug = Path(".feature-radar") / "runs" / source_run
    if by_slug.exists():
        return by_slug.resolve()

    raise FileNotFoundError(
        f"source run not found: {source_run} "
        f"(also checked {by_slug.as_posix()})"
    )


def build_destinations(
    target_project: Path,
    project_slug: str,
    mode: str,
    project_id: str,
) -> list[tuple[str, Path]]:
    destinations: list[tuple[str, Path]] = []
    if mode in {"radar-native", "both"}:
        destinations.append(
            (
                "radar-native",
                target_project / ".feature-radar" / "runs" / project_slug,
            )
        )
    if mode in {"p2a-preflight", "both"}:
        destinations.append(
            (
                "p2a-preflight",
                target_project
                / ".plan2agent"
                / "artifacts"
                / project_id
                / "preflight-research",
            )
        )
    return destinations


def manifest_text(
    *,
    source_run: Path,
    project_slug: str,
    target_project: Path,
    mode: str,
    p2a_project_id: str,
    overwrite_policy: str,
    copied_files: list[str],
    missing_optional_files: list[str],
    caveats: list[str],
) -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    copied = "\n".join(f"- {name}" for name in copied_files) or "- none"
    missing = "\n".join(f"- {name}" for name in missing_optional_files) or "- none"
    caveat_text = "\n".join(f"- {item}" for item in caveats) or "- none"

    return f"""# Feature Radar Handoff Manifest

source_run: {source_run}
project_slug: {project_slug}
target_project: {target_project}
mode: {mode}
p2a_project_id: {p2a_project_id}
created_at: {now}
overwrite_policy: {overwrite_policy}

## Copied Files

{copied}

## Missing Optional Files

{missing}

## Caveats

{caveat_text}
"""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Copy a Feature Radar run into a target project."
    )
    parser.add_argument(
        "--source-run",
        required=True,
        help="Source run path or slug under .feature-radar/runs/",
    )
    parser.add_argument(
        "--target-project",
        required=True,
        help="Target project directory.",
    )
    parser.add_argument(
        "--mode",
        choices=["radar-native", "p2a-preflight", "both"],
        default="radar-native",
        help="Destination mode. Default: radar-native.",
    )
    parser.add_argument(
        "--project-id",
        help="P2A project id. Defaults to target directory name in kebab-case.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing existing destination files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without writing files.",
    )
    args = parser.parse_args(argv)

    try:
        source_run = resolve_source_run(args.source_run)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    project_slug = source_run.name
    target_project = Path(args.target_project).expanduser().resolve()
    project_id = args.project_id or slugify(target_project.name)
    destinations = build_destinations(
        target_project=target_project,
        project_slug=project_slug,
        mode=args.mode,
        project_id=project_id,
    )

    existing_sources = [name for name in COPY_SET if (source_run / name).is_file()]
    missing_optional = [name for name in COPY_SET if name not in existing_sources]

    if not existing_sources:
        print(
            f"error: no expected Feature Radar artifacts found in {source_run}",
            file=sys.stderr,
        )
        return 2

    conflicts: list[Path] = []
    for _, destination in destinations:
        for name in existing_sources:
            if (destination / name).exists():
                conflicts.append(destination / name)
        if (destination / "handoff-manifest.md").exists():
            conflicts.append(destination / "handoff-manifest.md")

    if conflicts and not args.overwrite:
        print("error: destination files already exist; rerun with --overwrite to replace")
        for path in conflicts:
            print(f"- {path}")
        return 3

    overwrite_policy = "overwrite" if args.overwrite else "no-overwrite"
    caveats = [
        "Research conclusions were copied without rewriting.",
        "p2a-context.json is copied only when present in the source run.",
    ]

    for mode, destination in destinations:
        print(f"{mode}: {destination}")
        for name in existing_sources:
            print(f"  copy {source_run / name} -> {destination / name}")

        if args.dry_run:
            print(f"  write manifest -> {destination / 'handoff-manifest.md'}")
            continue

        destination.mkdir(parents=True, exist_ok=True)
        for name in existing_sources:
            shutil.copy2(source_run / name, destination / name)

        manifest = manifest_text(
            source_run=source_run,
            project_slug=project_slug,
            target_project=target_project,
            mode=mode,
            p2a_project_id=project_id,
            overwrite_policy=overwrite_policy,
            copied_files=existing_sources,
            missing_optional_files=missing_optional,
            caveats=caveats,
        )
        (destination / "handoff-manifest.md").write_text(manifest, encoding="utf-8")
        print(f"  wrote {destination / 'handoff-manifest.md'}")

    if missing_optional:
        print("missing optional files:")
        for name in missing_optional:
            print(f"- {name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
