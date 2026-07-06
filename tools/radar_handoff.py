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
    "_INDEX.md",
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

RUN_TYPE_ARTIFACTS = {
    "idea": CORE_ARTIFACTS,
    "existing-project": CORE_ARTIFACTS + EXISTING_PROJECT_ARTIFACTS,
}

RUN_TYPE_VALUES = set(RUN_TYPE_ARTIFACTS)


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


def has_draft_status(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return any(line.strip().lower() == "status: draft" for line in text.splitlines()[:12])


def read_header_value(path: Path, key: str) -> str | None:
    key_prefix = f"{key.lower()}:"
    for line in path.read_text(encoding="utf-8").splitlines()[:20]:
        stripped = line.strip()
        if stripped.lower().startswith(key_prefix):
            value = stripped.split(":", 1)[1].strip()
            return value or None
    return None


def has_complete_status(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return any(line.strip().lower() == "status: complete" for line in text.splitlines()[:12])


def is_empty_file(path: Path) -> bool:
    return not path.read_text(encoding="utf-8").strip()


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


def infer_run_type(source_run: Path, explicit_run_type: str | None) -> tuple[str, str]:
    if explicit_run_type:
        return explicit_run_type, "explicit"

    candidates = ["research-plan.md"] + [
        name for name in COPY_SET if name != "research-plan.md"
    ]
    for name in candidates:
        path = source_run / name
        if not path.is_file():
            continue
        mode = read_header_value(path, "mode")
        if mode in RUN_TYPE_VALUES:
            return mode, f"header:{name}"

    return "idea", "fallback"


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
    parser.add_argument(
        "--run-type",
        choices=["idea", "existing-project"],
        help="Expected source run artifact set for complete validation. Defaults to source run mode header, then idea.",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Deprecated compatibility flag. Complete validation is now the default.",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Allow copying an incomplete or draft source run.",
    )
    args = parser.parse_args(argv)
    if args.require_complete and args.allow_incomplete:
        print(
            "error: --require-complete and --allow-incomplete cannot be used together",
            file=sys.stderr,
        )
        return 2

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
    run_type, run_type_source = infer_run_type(source_run, args.run_type)

    existing_sources = [name for name in COPY_SET if (source_run / name).is_file()]
    missing_optional = [name for name in COPY_SET if name not in existing_sources]
    required_sources = RUN_TYPE_ARTIFACTS[run_type]
    missing_required = [
        name for name in required_sources if not (source_run / name).is_file()
    ]
    empty_required = [
        name
        for name in required_sources
        if (source_run / name).is_file() and is_empty_file(source_run / name)
    ]
    draft_required = [
        name
        for name in required_sources
        if (source_run / name).is_file() and has_draft_status(source_run / name)
    ]
    incomplete_required = [
        name
        for name in required_sources
        if (source_run / name).is_file() and not has_complete_status(source_run / name)
    ]

    if not existing_sources:
        print(
            f"error: no expected Feature Radar artifacts found in {source_run}",
            file=sys.stderr,
        )
        return 2
    require_complete = not args.allow_incomplete
    if require_complete and (missing_required or empty_required or incomplete_required):
        print(
            f"error: source run is incomplete for run type {run_type}",
            file=sys.stderr,
        )
        print(f"run type source: {run_type_source}", file=sys.stderr)
        if missing_required:
            print("missing files:", file=sys.stderr)
            for name in missing_required:
                print(f"- {name}", file=sys.stderr)
        if empty_required:
            print("empty files:", file=sys.stderr)
            for name in empty_required:
                print(f"- {name}", file=sys.stderr)
        if draft_required:
            print("draft files:", file=sys.stderr)
            for name in draft_required:
                print(f"- {name}", file=sys.stderr)
        missing_complete = [
            name
            for name in incomplete_required
            if name not in draft_required
        ]
        if missing_complete:
            print("missing complete status:", file=sys.stderr)
            for name in missing_complete:
                print(f"- {name}", file=sys.stderr)
        print(
            "hint: create or complete the run first, set status: complete, then rerun handoff; use --allow-incomplete only for intentional draft export",
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
        print(f"  run type: {run_type} ({run_type_source})")
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
