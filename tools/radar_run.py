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

ALL_RESEARCH_ARTIFACTS = CORE_ARTIFACTS + EXISTING_PROJECT_ARTIFACTS
MODE_VALUES = tuple(MODE_ARTIFACTS)
PROFILE_VALUES = ("general", "tool-gap")
STATUS_VALUES = ("draft", "complete")

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


INDEX_FILE = "_INDEX.md"

# filename -> (role, 한줄 설명). dict 순서가 인덱스 내 표시 순서가 된다.
ARTIFACT_ROLES = {
    "collection-report.md": (
        "result",
        "최종 판정(Verdict) + 권장 방향 요약. 바쁘면 이거 하나.",
    ),
    "next-iteration-recommendations.md": (
        "result",
        "우선순위 추천 표(action/비용/리스크/신뢰도/다음 단계). 실제 착수 목록.",
    ),
    "research-bundle.md": ("evidence", "분석 본문(로컬 vs 외부 비교, 해석)."),
    "signal-map.md": ("evidence", "신호 ↔ 출처/함의/신뢰도 매핑."),
    "source-candidates.md": ("evidence", "출처 레지스트리(LOCAL/WEB/GH) + URL + 신뢰도."),
    "local-project-scan.md": ("evidence", "로컬 코드 근거(path:line)."),
    "capability-gap-analysis.md": ("evidence", "현재 구현 vs 외부 신호 already/partial/missing 대조."),
    "research-plan.md": ("scope", "조사 범위 계약(결과 문서 아님)."),
}

CATEGORY_ORDER = [
    ("result", "결과 (여기만 봐도 다음에 뭘 할지 나옴)"),
    ("evidence", "근거 (추천이 왜 그런지 역추적용)"),
    ("scope", "범위 (결과 문서 아님)"),
]


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
    values = read_metadata_values(text, "status")
    return len(values) == 1 and values[0].lower() == "draft"


def has_complete_status(text: str) -> bool:
    values = read_metadata_values(text, "status")
    return len(values) == 1 and values[0].lower() == "complete"


def read_metadata_values(text: str, key: str) -> list[str]:
    values: list[str] = []
    metadata_started = False
    title_skipped = False
    for line in text.splitlines():
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


def read_header_values(path: Path, key: str) -> list[str]:
    return read_metadata_values(path.read_text(encoding="utf-8"), key)


def artifact_template(
    *,
    name: str,
    title: str,
    slug: str,
    mode: str,
    local_project: str | None,
    profile: str = "general",
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
profile: {profile}
local_project: {local_project_line}
created_at: {now}
status: draft

{body_by_name[name]}"""


def infer_mode(run_dir: Path) -> str:
    valid_headers: list[tuple[str, str]] = []
    missing_headers: list[str] = []
    invalid_headers: list[str] = []
    present_headers: list[str] = []

    for name in ALL_RESEARCH_ARTIFACTS:
        path = run_dir / name
        if not path.is_file():
            continue
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
        if mode not in MODE_VALUES:
            allowed = ", ".join(MODE_VALUES)
            invalid_headers.append(
                f"{name}: invalid mode {mode!r}; expected one of: {allowed}"
            )
            continue
        valid_headers.append((name, mode))

    problems: list[str] = []
    problems.extend(invalid_headers)
    if present_headers and missing_headers:
        problems.append(
            "mode header is present in some existing research artifacts but missing "
            f"from: {', '.join(missing_headers)}"
        )

    modes = {mode for _, mode in valid_headers}
    if len(modes) > 1:
        declarations = ", ".join(f"{name}={mode}" for name, mode in valid_headers)
        problems.append(f"conflicting mode headers: {declarations}")

    if not problems and len(modes) == 1 and "idea" in modes:
        supplemental = [
            name for name in EXISTING_PROJECT_ARTIFACTS if (run_dir / name).is_file()
        ]
        if supplemental:
            problems.append(
                "mode 'idea' cannot include existing-project supplemental artifacts: "
                + ", ".join(supplemental)
            )

    if problems:
        raise ValueError("mode integrity error:\n- " + "\n- ".join(problems))
    if not present_headers:
        return (
            "existing-project"
            if any((run_dir / name).is_file() for name in EXISTING_PROJECT_ARTIFACTS)
            else "idea"
        )
    return valid_headers[0][1]


def infer_profile(run_dir: Path, mode: str | None = None) -> str:
    # Profile is run-level metadata; mode remains accepted for API compatibility.
    _ = mode
    expected = ALL_RESEARCH_ARTIFACTS
    valid_headers: list[tuple[str, str]] = []
    missing_headers: list[str] = []
    invalid_headers: list[str] = []
    present_headers: list[str] = []

    for name in expected:
        path = run_dir / name
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
        return "general"
    return valid_headers[0][1]


def build_index(
    *,
    slug: str,
    title: str,
    mode: str,
    artifacts: list[str],
    profile: str = "general",
) -> str:
    present = set(artifacts)
    lines = [
        f"# 이 run 읽는 법 ({slug})",
        "",
        f"title: {title}",
        f"mode: {mode}",
        f"profile: {profile}",
        "",
        "Feature Radar run 산출물 안내. 파일은 결과 / 근거 / 범위 / 원본으로 나뉜다.",
        "파일은 일부러 flat 구조로 둔다 — tools/radar_run.py 와 tools/radar_handoff.py 가",
        "flat 구조를 전제로 동작하므로 하위 폴더로 옮기지 말 것.",
        "",
    ]
    for key, heading in CATEGORY_ORDER:
        rows = [
            (name, desc)
            for name, (role, desc) in ARTIFACT_ROLES.items()
            if role == key and name in present
        ]
        if not rows:
            continue
        lines.append(f"## {heading}")
        for name, desc in rows:
            lines.append(f"- {name} — {desc}")
        lines.append("")
    lines += [
        "## 원본 (중간 자료, 있을 때만)",
        "- _raw-*/ — 서브에이전트 원본 출력.",
        "",
        "## 추적 경로",
        "추천 → research-bundle 주장 → signal-map 신호 → source-candidates URL.",
        "로컬 항목은 → local-project-scan 의 path:line.",
        "",
        "읽는 순서: collection-report → next-iteration-recommendations (결정) → 필요 시 근거 문서로.",
        "",
    ]
    return "\n".join(lines)


def write_index(
    run_dir: Path,
    *,
    slug: str,
    title: str,
    mode: str,
    overwrite: bool,
    profile: str = "general",
) -> None:
    artifacts = [n for n in MODE_ARTIFACTS[mode] if (run_dir / n).is_file()]
    index_path = run_dir / INDEX_FILE
    if index_path.exists() and not overwrite:
        return
    index_path.write_text(
        build_index(
            slug=slug,
            title=title,
            mode=mode,
            profile=profile,
            artifacts=artifacts,
        ),
        encoding="utf-8",
    )
    print(f"wrote {index_path}")


def init_run(args: argparse.Namespace) -> int:
    slug = slugify(args.slug)
    run_dir = Path(".feature-radar") / "runs" / slug
    artifacts = MODE_ARTIFACTS[args.mode]

    if run_dir.exists() and not run_dir.is_dir():
        print(f"error: run path is not a directory: {run_dir}", file=sys.stderr)
        return 3
    index_path = run_dir / INDEX_FILE
    if index_path.exists() and not index_path.is_file():
        print(f"error: index path is not a file: {index_path}", file=sys.stderr)
        return 3

    existing = [
        run_dir / name
        for name in ALL_RESEARCH_ARTIFACTS
        if (run_dir / name).exists()
    ]
    if existing and not args.overwrite:
        print("error: run artifact files already exist; rerun with --overwrite to replace")
        for path in existing:
            print(f"- {path}", file=sys.stderr)
        return 3

    if existing and args.overwrite:
        non_files = [path for path in existing if not path.is_file()]
        if non_files:
            print("error: cannot overwrite non-file run artifacts", file=sys.stderr)
            for path in non_files:
                print(f"- {path}", file=sys.stderr)
            return 3
        try:
            existing_mode = infer_mode(run_dir)
        except ValueError as exc:
            print(
                f"error: cannot safely overwrite an invalid existing run: {exc}",
                file=sys.stderr,
            )
            print("hint: repair the existing run or initialize a new slug", file=sys.stderr)
            return 2
        if existing_mode != args.mode:
            print(
                "error: --overwrite cannot change an existing run mode "
                f"from {existing_mode} to {args.mode}",
                file=sys.stderr,
            )
            print("hint: initialize the new mode with a new slug", file=sys.stderr)
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
                profile=args.profile,
                local_project=args.local_project,
            ),
            encoding="utf-8",
        )
        print(f"wrote {path}")

    write_index(
        run_dir,
        slug=slug,
        title=args.title,
        mode=args.mode,
        profile=args.profile,
        overwrite=True,
    )
    print(f"run_dir: {run_dir}")
    return 0


def index_run(args: argparse.Namespace) -> int:
    try:
        run_dir = resolve_run(args.source_run)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        mode = infer_mode(run_dir)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.mode and args.mode != mode:
        print(
            f"error: requested mode {args.mode} does not match run mode {mode}",
            file=sys.stderr,
        )
        return 2
    try:
        profile = infer_profile(run_dir, mode)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    title = args.title or run_dir.name
    write_index(
        run_dir,
        slug=run_dir.name,
        title=title,
        mode=mode,
        profile=profile,
        overwrite=True,
    )
    return 0


def validate_run(args: argparse.Namespace) -> int:
    try:
        run_dir = resolve_run(args.source_run)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        resolved_mode = infer_mode(run_dir)
        mode_error = None
    except ValueError as exc:
        resolved_mode = None
        mode_error = str(exc)
    if mode_error is None and resolved_mode != args.mode:
        mode_error = (
            "mode integrity error: "
            f"requested mode {args.mode} does not match run mode {resolved_mode}"
        )

    required = MODE_ARTIFACTS[args.mode]
    try:
        profile = infer_profile(run_dir, args.mode)
        profile_error = None
    except ValueError as exc:
        profile = None
        profile_error = str(exc)
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
    draft: list[str] = []
    status_errors: list[str] = []
    for name, text in artifact_texts.items():
        values = read_metadata_values(text, "status")
        if not values:
            status_errors.append(f"{name}: missing status header")
            continue
        if len(values) != 1:
            rendered = ", ".join(repr(value) for value in values)
            status_errors.append(
                f"{name}: expected one status header, found {len(values)} ({rendered})"
            )
            continue
        raw_status = values[0]
        status = raw_status.lower()
        if status not in STATUS_VALUES:
            allowed = ", ".join(STATUS_VALUES)
            status_errors.append(
                f"{name}: invalid status {raw_status!r}; expected one of: {allowed}"
            )
        elif status == "draft":
            draft.append(name)

    if (
        mode_error
        or profile_error
        or missing
        or empty
        or status_errors
        or (draft and not args.allow_draft)
    ):
        print(f"run invalid: {run_dir}")
        if mode_error:
            print(mode_error)
        if profile_error:
            print(profile_error)
        if missing:
            print("missing files:")
            for name in missing:
                print(f"- {name}")
        if empty:
            print("empty files:")
            for name in empty:
                print(f"- {name}")
        if status_errors:
            print("invalid status headers:")
            for error in status_errors:
                print(f"- {error}")
        if draft and not args.allow_draft:
            print("draft files:")
            for name in draft:
                print(f"- {name}")
        if status_errors or (draft and not args.allow_draft):
            print("hint: complete the research content and set status: complete")
        return 1

    print(f"run valid: {run_dir}")
    print(f"profile: {profile}")
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
        "--profile",
        choices=PROFILE_VALUES,
        default="general",
        help="Research profile recorded in artifact headers. Default: general.",
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

    index_parser = subparsers.add_parser(
        "index", help="(Re)generate _INDEX.md for an existing run."
    )
    index_parser.add_argument(
        "--source-run",
        required=True,
        help="Run path or slug under .feature-radar/runs/.",
    )
    index_parser.add_argument(
        "--mode",
        choices=["idea", "existing-project"],
        help=(
            "Assert the source run mode. Default: infer from artifact headers or "
            "legacy structure."
        ),
    )
    index_parser.add_argument("--title", help="Override index title. Default: run dir name.")
    index_parser.set_defaults(func=index_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
