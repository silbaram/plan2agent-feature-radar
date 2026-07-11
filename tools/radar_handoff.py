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

try:
    from radar_run import build_index
except ModuleNotFoundError:  # Support importing this file as tools.radar_handoff.
    from .radar_run import build_index


INDEX_FILE = "_INDEX.md"
MANIFEST_FILE = "handoff-manifest.md"

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

RESEARCH_ARTIFACTS = CORE_ARTIFACTS + EXISTING_PROJECT_ARTIFACTS
OPTIONAL_COPY_SET = ["p2a-context.json"]
COPY_SET = [INDEX_FILE] + RESEARCH_ARTIFACTS + OPTIONAL_COPY_SET

RUN_TYPE_ARTIFACTS = {
    "idea": CORE_ARTIFACTS,
    "existing-project": CORE_ARTIFACTS + EXISTING_PROJECT_ARTIFACTS,
}

RUN_TYPE_VALUES = set(RUN_TYPE_ARTIFACTS)
PROFILE_VALUES = ("general", "tool-gap")
STATUS_VALUES = ("draft", "complete")


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


def read_header_value(path: Path, key: str) -> str | None:
    values = read_header_values(path, key)
    if not values:
        return None
    return values[0] or None


def read_header_values(path: Path, key: str) -> list[str]:
    values: list[str] = []
    metadata_started = False
    title_skipped = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not metadata_started:
            if not stripped:
                continue
            if not title_skipped and re.match(r"^#(?:\s|$)", stripped):
                title_skipped = True
                continue
        elif not stripped or stripped.startswith("#"):
            break

        field, separator, value = stripped.partition(":")
        if not separator or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", field.strip()):
            break

        metadata_started = True
        if field.strip().lower() == key.lower():
            values.append(value.strip())
    return values


def read_status(path: Path) -> tuple[str | None, str | None]:
    values = read_header_values(path, "status")
    if len(values) != 1:
        rendered = ", ".join(repr(value) for value in values) or "none"
        return None, f"expected one status header, found {len(values)} ({rendered})"

    status = values[0].lower()
    if status not in STATUS_VALUES:
        allowed = ", ".join(STATUS_VALUES)
        return None, f"invalid status {values[0]!r}; expected one of: {allowed}"
    return status, None


def has_draft_status(path: Path) -> bool:
    status, error = read_status(path)
    return error is None and status == "draft"


def has_complete_status(path: Path) -> bool:
    status, error = read_status(path)
    return error is None and status == "complete"


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
    valid_headers: list[tuple[str, str]] = []
    present_headers: list[str] = []
    missing_headers: list[str] = []
    invalid_headers: list[str] = []
    present_artifacts: list[str] = []

    for name in RESEARCH_ARTIFACTS:
        path = source_run / name
        if not path.is_file():
            continue
        present_artifacts.append(name)
        values = read_header_values(path, "mode")
        if not values:
            missing_headers.append(name)
            continue

        present_headers.append(name)
        if len(values) != 1:
            rendered = ", ".join(repr(value) for value in values)
            invalid_headers.append(
                f"{name}: expected one mode header, found {len(values)} ({rendered})"
            )
            continue

        mode = values[0]
        if mode not in RUN_TYPE_VALUES:
            allowed = ", ".join(sorted(RUN_TYPE_VALUES))
            invalid_headers.append(
                f"{name}: invalid mode {mode!r}; expected one of: {allowed}"
            )
            continue
        valid_headers.append((name, mode))

    problems = list(invalid_headers)
    if present_headers and missing_headers:
        problems.append(
            "mode header is present in some research artifacts but missing from: "
            f"{', '.join(missing_headers)}"
        )

    modes = {mode for _, mode in valid_headers}
    if len(modes) > 1:
        declarations = ", ".join(
            f"{name}={mode}" for name, mode in valid_headers
        )
        problems.append(f"conflicting mode headers: {declarations}")

    if problems:
        raise ValueError("mode integrity error:\n- " + "\n- ".join(problems))

    if present_headers:
        run_type = valid_headers[0][1]
        run_type_source = "headers:" + ",".join(name for name, _ in valid_headers)
    else:
        run_type = (
            "existing-project"
            if any(name in present_artifacts for name in EXISTING_PROJECT_ARTIFACTS)
            else "idea"
        )
        run_type_source = "legacy:structure"

    unexpected = [
        name
        for name in EXISTING_PROJECT_ARTIFACTS
        if run_type == "idea" and name in present_artifacts
    ]
    if unexpected:
        raise ValueError(
            "mode integrity error:\n- idea run contains existing-project artifacts: "
            + ", ".join(unexpected)
        )

    if explicit_run_type and explicit_run_type != run_type:
        raise ValueError(
            "mode integrity error:\n- explicit run type "
            f"{explicit_run_type!r} conflicts with source run mode {run_type!r}"
        )
    if explicit_run_type:
        return run_type, f"explicit-confirmed:{run_type_source}"

    return run_type, run_type_source


def infer_profile(
    source_run: Path, run_type: str | None = None
) -> tuple[str, str]:
    if run_type is None:
        run_type, _ = infer_run_type(source_run, None)
    expected = RESEARCH_ARTIFACTS
    valid_headers: list[tuple[str, str]] = []
    missing_headers: list[str] = []
    invalid_headers: list[str] = []
    present_headers: list[str] = []

    for name in expected:
        path = source_run / name
        if not path.is_file():
            continue
        values = read_header_values(path, "profile")
        if not values:
            missing_headers.append(name)
            continue

        present_headers.append(name)
        if len(values) != 1:
            rendered = ", ".join(repr(value) for value in values)
            invalid_headers.append(
                f"{name}: expected one profile header, found {len(values)} ({rendered})"
            )
            continue

        profile = values[0]
        if profile not in PROFILE_VALUES:
            allowed = ", ".join(PROFILE_VALUES)
            invalid_headers.append(
                f"{name}: invalid profile {profile!r}; expected one of: {allowed}"
            )
            continue
        valid_headers.append((name, profile))

    problems: list[str] = []
    problems.extend(invalid_headers)
    if present_headers and missing_headers:
        problems.append(
            "profile header is present in some existing expected artifacts but missing "
            f"from: {', '.join(missing_headers)}"
        )

    profiles = {profile for _, profile in valid_headers}
    if len(profiles) > 1:
        declarations = ", ".join(
            f"{name}={profile}" for name, profile in valid_headers
        )
        problems.append(f"conflicting profile headers: {declarations}")

    if problems:
        raise ValueError("profile integrity error:\n- " + "\n- ".join(problems))
    if not present_headers:
        return "general", "legacy:no-profile"
    profile = valid_headers[0][1]
    sources = ",".join(name for name, _ in valid_headers)
    return profile, f"headers:{sources}"


def manifest_text(
    *,
    source_run: Path,
    project_slug: str,
    target_project: Path,
    mode: str,
    p2a_project_id: str,
    overwrite_policy: str,
    copied_files: list[str],
    missing_required_files: list[str],
    missing_optional_files: list[str],
    caveats: list[str],
    profile: str = "general",
    run_mode: str = "idea",
    source_complete: bool = True,
) -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    copied = "\n".join(f"- {name}" for name in copied_files) or "- none"
    missing_required = (
        "\n".join(f"- {name}" for name in missing_required_files) or "- none"
    )
    missing_optional = (
        "\n".join(f"- {name}" for name in missing_optional_files) or "- none"
    )
    caveat_text = "\n".join(f"- {item}" for item in caveats) or "- none"

    # Keep `mode` as the compatibility alias used by existing manifest readers.
    return f"""# Feature Radar Handoff Manifest

source_run: {source_run}
project_slug: {project_slug}
target_project: {target_project}
mode: {mode}
run_mode: {run_mode}
profile: {profile}
handoff_mode: {mode}
p2a_project_id: {p2a_project_id}
created_at: {now}
overwrite_policy: {overwrite_policy}
source_complete: {str(source_complete).lower()}

## Copied Files

{copied}

## Missing Required Files

{missing_required}

## Missing Optional Files

{missing_optional}

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
        help="Assert the expected source run type. Defaults to coherent artifact mode headers, then legacy structural inference.",
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
    try:
        run_type, run_type_source = infer_run_type(source_run, args.run_type)
        profile, profile_source = infer_profile(source_run, run_type)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    required_sources = RUN_TYPE_ARTIFACTS[run_type]
    present_required = [
        name for name in required_sources if (source_run / name).is_file()
    ]
    missing_required = [
        name for name in required_sources if not (source_run / name).is_file()
    ]
    present_optional = [
        name for name in OPTIONAL_COPY_SET if (source_run / name).is_file()
    ]
    missing_optional = [
        name for name in OPTIONAL_COPY_SET if not (source_run / name).is_file()
    ]
    copy_sources = present_required + present_optional
    transferred_files = [INDEX_FILE] + copy_sources
    empty_required = [
        name
        for name in required_sources
        if (source_run / name).is_file() and is_empty_file(source_run / name)
    ]
    statuses = {
        name: read_status(source_run / name)
        for name in present_required
    }
    status_errors = [
        f"{name}: {error}"
        for name, (_, error) in statuses.items()
        if error is not None
    ]
    draft_required = [
        name
        for name, (status, error) in statuses.items()
        if error is None and status == "draft"
    ]
    incomplete_required = [
        name
        for name, (status, error) in statuses.items()
        if error is not None or status != "complete"
    ]

    if not present_required:
        print(
            f"error: no expected Feature Radar artifacts found in {source_run}",
            file=sys.stderr,
        )
        return 2
    if status_errors:
        print("error: invalid authoritative status metadata", file=sys.stderr)
        for error in status_errors:
            print(f"- {error}", file=sys.stderr)
        print(
            "hint: each present research artifact must declare exactly one status: draft or status: complete",
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

    source_complete = not (
        missing_required or empty_required or incomplete_required
    )
    title_path = source_run / "research-plan.md"
    title = (
        read_header_value(title_path, "title")
        if title_path.is_file()
        else None
    ) or project_slug
    index_text = build_index(
        slug=project_slug,
        title=title,
        mode=run_type,
        profile=profile,
        artifacts=present_required,
    )

    managed_names = [*COPY_SET, MANIFEST_FILE]
    output_names = {*transferred_files, MANIFEST_FILE}
    destination_existing: dict[Path, list[Path]] = {}
    preflight_errors: list[str] = []
    for _, destination in destinations:
        if destination.resolve() == source_run.resolve():
            preflight_errors.append(
                f"destination is the source run itself: {destination}"
            )

        ancestor = destination
        while not ancestor.exists() and not ancestor.is_symlink():
            ancestor = ancestor.parent
        if not ancestor.is_dir():
            preflight_errors.append(
                f"destination parent is not a directory: {ancestor}"
            )

        existing_paths: list[Path] = []
        for name in managed_names:
            path = destination / name
            if not path.exists() and not path.is_symlink():
                continue
            existing_paths.append(path)
            if args.overwrite and not path.is_file() and not path.is_symlink():
                preflight_errors.append(
                    f"cannot overwrite non-file destination artifact: {path}"
                )
        destination_existing[destination] = existing_paths

    if preflight_errors:
        print("error: destination preflight failed", file=sys.stderr)
        for error in preflight_errors:
            print(f"- {error}", file=sys.stderr)
        return 3

    conflicts = [
        path
        for existing_paths in destination_existing.values()
        for path in existing_paths
    ]

    if conflicts and not args.overwrite:
        print("error: destination files already exist; rerun with --overwrite to replace")
        for path in conflicts:
            print(f"- {path}")
        return 3

    overwrite_policy = "overwrite" if args.overwrite else "no-overwrite"
    caveats = [
        "Research conclusions were copied without rewriting.",
        "p2a-context.json is copied only when present in the source run.",
        "_INDEX.md was regenerated from authoritative research artifact metadata.",
    ]
    if args.overwrite:
        caveats.append(
            "Managed destination artifacts were synchronized under explicit --overwrite."
        )
    if not source_complete:
        caveats.append("Source run was exported with --allow-incomplete.")
        if missing_required:
            caveats.append(
                "Missing required files: " + ", ".join(missing_required)
            )
        if empty_required:
            caveats.append("Empty required files: " + ", ".join(empty_required))
        if incomplete_required:
            caveats.append(
                "Required files without status: complete: "
                + ", ".join(incomplete_required)
            )

    for mode, destination in destinations:
        print(f"{mode}: {destination}")
        print(f"  run type: {run_type} ({run_type_source})")
        print(f"  profile: {profile} ({profile_source})")
        if args.overwrite:
            for path in destination_existing[destination]:
                action = "replace" if path.name in output_names else "remove stale"
                print(f"  {action} {path}")
        print(f"  generate {destination / INDEX_FILE}")
        for name in copy_sources:
            print(f"  copy {source_run / name} -> {destination / name}")

        if args.dry_run:
            print(f"  write manifest -> {destination / MANIFEST_FILE}")
            continue

        destination.mkdir(parents=True, exist_ok=True)
        if args.overwrite:
            for path in destination_existing[destination]:
                if path.exists() or path.is_symlink():
                    path.unlink()
        (destination / INDEX_FILE).write_text(index_text, encoding="utf-8")
        for name in copy_sources:
            shutil.copy2(source_run / name, destination / name)

        manifest = manifest_text(
            source_run=source_run,
            project_slug=project_slug,
            target_project=target_project,
            mode=mode,
            run_mode=run_type,
            profile=profile,
            p2a_project_id=project_id,
            overwrite_policy=overwrite_policy,
            source_complete=source_complete,
            copied_files=transferred_files,
            missing_required_files=missing_required,
            missing_optional_files=missing_optional,
            caveats=caveats,
        )
        (destination / MANIFEST_FILE).write_text(manifest, encoding="utf-8")
        print(f"  wrote {destination / MANIFEST_FILE}")

    if missing_optional:
        print("missing optional files:")
        for name in missing_optional:
            print(f"- {name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
