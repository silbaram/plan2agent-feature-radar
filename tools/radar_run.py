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


def infer_mode(run_dir: Path) -> str:
    for name in EXISTING_PROJECT_ARTIFACTS:
        if (run_dir / name).is_file():
            return "existing-project"
    return "idea"


def build_index(*, slug: str, title: str, mode: str, artifacts: list[str]) -> str:
    present = set(artifacts)
    lines = [
        f"# 이 run 읽는 법 ({slug})",
        "",
        f"title: {title}",
        f"mode: {mode}",
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


def write_index(run_dir: Path, *, slug: str, title: str, mode: str, overwrite: bool) -> None:
    artifacts = [n for n in MODE_ARTIFACTS[mode] if (run_dir / n).is_file()]
    index_path = run_dir / INDEX_FILE
    if index_path.exists() and not overwrite:
        return
    index_path.write_text(
        build_index(slug=slug, title=title, mode=mode, artifacts=artifacts),
        encoding="utf-8",
    )
    print(f"wrote {index_path}")


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

    write_index(
        run_dir, slug=slug, title=args.title, mode=args.mode, overwrite=args.overwrite
    )
    print(f"run_dir: {run_dir}")
    return 0


def index_run(args: argparse.Namespace) -> int:
    try:
        run_dir = resolve_run(args.source_run)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    mode = args.mode or infer_mode(run_dir)
    title = args.title or run_dir.name
    write_index(run_dir, slug=run_dir.name, title=title, mode=mode, overwrite=True)
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
        help="Artifact set. Default: infer from existing files.",
    )
    index_parser.add_argument("--title", help="Override index title. Default: run dir name.")
    index_parser.set_defaults(func=index_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
