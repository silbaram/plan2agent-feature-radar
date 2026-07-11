from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RADAR_RUN = REPO_ROOT / "tools" / "radar_run.py"
RADAR_HANDOFF = REPO_ROOT / "tools" / "radar_handoff.py"
LEGACY_IDEA_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "legacy-idea-run"

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
INDEX_FILE = "_INDEX.md"


def metadata_entries(path: Path) -> list[tuple[int, str, str]]:
    entries: list[tuple[int, str, str]] = []
    metadata_started = False
    title_skipped = False
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
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
        if not separator or not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_-]*", field.strip()
        ):
            break

        metadata_started = True
        entries.append((index, field.strip().lower(), value.strip()))
    return entries


def read_header_values(path: Path, key: str) -> list[str]:
    normalized_key = key.lower()
    return [
        value
        for _, field, value in metadata_entries(path)
        if field == normalized_key
    ]


def read_header_value(path: Path, key: str) -> str | None:
    values = read_header_values(path, key)
    if values:
        return values[0] or None
    return None


def set_header_value(path: Path, key: str, value: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, field, _ in metadata_entries(path):
        if field == key.lower():
            lines[index] = f"{key}: {value}"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    raise AssertionError(f"missing {key!r} header in {path}")


def remove_header(path: Path, key: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, field, _ in metadata_entries(path):
        if field == key.lower():
            del lines[index]
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    raise AssertionError(f"missing {key!r} header in {path}")


def duplicate_header(path: Path, key: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, field, _ in metadata_entries(path):
        if field == key.lower():
            lines.insert(index + 1, lines[index])
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    raise AssertionError(f"missing {key!r} header in {path}")


def complete_artifacts(run_dir: Path, names: list[str]) -> None:
    for name in names:
        set_header_value(run_dir / name, "status", "complete")


def replace_body(path: Path, body_lines: list[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = metadata_entries(path)
    if not entries:
        raise AssertionError(f"missing metadata block in {path}")
    metadata_end = entries[-1][0]
    path.write_text(
        "\n".join([*lines[: metadata_end + 1], "", *body_lines, ""]),
        encoding="utf-8",
    )


def markdown_section_lines(path: Path, heading: str) -> list[str]:
    target = f"## {heading}".lower()
    section: list[str] = []
    in_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.lower() == target:
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if in_section and stripped:
            section.append(stripped)
    return section


def snapshot_tree(root: Path) -> dict[str, tuple[str, bytes | None]]:
    if not root.exists():
        return {}
    snapshot: dict[str, tuple[str, bytes | None]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            snapshot[relative] = ("directory", None)
        elif path.is_file():
            snapshot[relative] = ("file", path.read_bytes())
        else:
            snapshot[relative] = ("other", None)
    return snapshot


class RadarProfileCliTests(unittest.TestCase):
    def run_cli(
        self, script: Path, *args: str, cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def init_run(
        self,
        cwd: Path,
        slug: str,
        *,
        mode: str | None = None,
        profile: str | None = None,
        overwrite: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        args = ["init", "--slug", slug, "--title", f"Title for {slug}"]
        if mode is not None:
            args.extend(["--mode", mode])
        if profile is not None:
            args.extend(["--profile", profile])
        if overwrite:
            args.append("--overwrite")
        result = self.run_cli(RADAR_RUN, *args, cwd=cwd)
        return result, cwd / ".feature-radar" / "runs" / slug

    def copy_legacy_fixture(self, cwd: Path, slug: str = "legacy-idea-run") -> Path:
        run_dir = cwd / slug
        shutil.copytree(LEGACY_IDEA_FIXTURE, run_dir)
        return run_dir

    def assert_profile_headers(
        self, run_dir: Path, names: list[str], expected: str
    ) -> None:
        for name in names:
            with self.subTest(artifact=name):
                self.assertEqual(read_header_value(run_dir / name, "profile"), expected)

    def test_init_defaults_to_general_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(cwd, "general-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_profile_headers(
                run_dir, [*CORE_ARTIFACTS, INDEX_FILE], "general"
            )

    def test_init_tool_gap_uses_the_same_artifact_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(cwd, "tool-gap-run", profile="tool-gap")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                {path.name for path in run_dir.iterdir()},
                {*CORE_ARTIFACTS, INDEX_FILE},
            )
            self.assert_profile_headers(
                run_dir, [*CORE_ARTIFACTS, INDEX_FILE], "tool-gap"
            )

    def test_complete_existing_project_tool_gap_handoff_preserves_axes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(
                cwd,
                "existing-tool-gap",
                mode="existing-project",
                profile="tool-gap",
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            artifacts = [*CORE_ARTIFACTS, *EXISTING_PROJECT_ARTIFACTS]
            expected_files = {*artifacts, INDEX_FILE}
            self.assertEqual({path.name for path in run_dir.iterdir()}, expected_files)
            for name in expected_files:
                with self.subTest(source_artifact=name):
                    self.assertEqual(
                        read_header_value(run_dir / name, "mode"),
                        "existing-project",
                    )
                    self.assertEqual(
                        read_header_value(run_dir / name, "profile"),
                        "tool-gap",
                    )

            complete_artifacts(run_dir, artifacts)
            validation = self.run_cli(
                RADAR_RUN,
                "validate",
                "--source-run",
                str(run_dir),
                "--mode",
                "existing-project",
                cwd=cwd,
            )
            self.assertEqual(
                validation.returncode,
                0,
                validation.stdout + validation.stderr,
            )

            target = cwd / "target"
            handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                cwd=cwd,
            )
            self.assertEqual(handoff.returncode, 0, handoff.stdout + handoff.stderr)

            destination = target / ".feature-radar" / "runs" / run_dir.name
            manifest = destination / "handoff-manifest.md"
            self.assertEqual(read_header_value(manifest, "run_mode"), "existing-project")
            self.assertEqual(read_header_value(manifest, "profile"), "tool-gap")
            self.assertEqual(read_header_value(manifest, "handoff_mode"), "radar-native")
            self.assertEqual(read_header_value(manifest, "mode"), "radar-native")
            self.assertEqual(read_header_value(manifest, "source_complete"), "true")

    def test_profile_example_in_body_is_not_parsed_as_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(
                cwd, "profile-example", profile="tool-gap"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            complete_artifacts(run_dir, CORE_ARTIFACTS)

            bundle = run_dir / "research-bundle.md"
            lines = bundle.read_text(encoding="utf-8").splitlines()
            status_index = next(
                index
                for index, line in enumerate(lines)
                if line.strip().lower() == "status: complete"
            )
            body_example = [
                "",
                "## Profile Syntax Example",
                "",
                "```text",
                "profile: general | tool-gap",
                "```",
                "",
            ]
            bundle.write_text(
                "\n".join([*lines[: status_index + 1], *body_example]),
                encoding="utf-8",
            )
            example_line = bundle.read_text(encoding="utf-8").splitlines().index(
                "profile: general | tool-gap"
            )
            self.assertLess(example_line, 20)

            validation = self.run_cli(
                RADAR_RUN,
                "validate",
                "--source-run",
                str(run_dir),
                cwd=cwd,
            )
            self.assertEqual(
                validation.returncode,
                0,
                validation.stdout + validation.stderr,
            )

            index = run_dir / INDEX_FILE
            index.write_text("stale index\n", encoding="utf-8")
            reindex = self.run_cli(
                RADAR_RUN,
                "index",
                "--source-run",
                str(run_dir),
                cwd=cwd,
            )
            self.assertEqual(reindex.returncode, 0, reindex.stdout + reindex.stderr)
            self.assertEqual(read_header_value(index, "profile"), "tool-gap")

            target = cwd / "target"
            handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                cwd=cwd,
            )
            self.assertEqual(handoff.returncode, 0, handoff.stdout + handoff.stderr)
            destination = target / ".feature-radar" / "runs" / run_dir.name
            manifest = destination / "handoff-manifest.md"
            self.assertEqual(read_header_value(manifest, "profile"), "tool-gap")
            copied_lines = (destination / "research-bundle.md").read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertIn("profile: general | tool-gap", copied_lines)

    def test_body_duplicate_and_invalid_status_cannot_pass_completion_gates(
        self,
    ) -> None:
        def put_complete_status_in_body(run_dir: Path) -> None:
            bundle = run_dir / "research-bundle.md"
            remove_header(bundle, "status")
            replace_body(
                bundle,
                ["```text", "status: complete", "```"],
            )
            self.assertEqual(read_header_values(bundle, "status"), [])
            self.assertIn(
                "status: complete",
                bundle.read_text(encoding="utf-8").splitlines()[:12],
            )

        def duplicate_complete_status(run_dir: Path) -> None:
            duplicate_header(run_dir / "research-bundle.md", "status")

        def make_status_invalid(run_dir: Path) -> None:
            set_header_value(run_dir / "research-bundle.md", "status", "done")

        mutations = {
            "body-only-complete": put_complete_status_in_body,
            "duplicate-complete": duplicate_complete_status,
            "invalid": make_status_invalid,
        }

        for case, mutate in mutations.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                cwd = Path(tmp)
                result, run_dir = self.init_run(
                    cwd, f"bad-status-{case}", profile="tool-gap"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                complete_artifacts(run_dir, CORE_ARTIFACTS)
                mutate(run_dir)

                validation = self.run_cli(
                    RADAR_RUN,
                    "validate",
                    "--source-run",
                    str(run_dir),
                    cwd=cwd,
                )
                self.assertEqual(validation.returncode, 1)
                self.assertIn(
                    "status", (validation.stdout + validation.stderr).lower()
                )

                target = cwd / "target"
                handoff = self.run_cli(
                    RADAR_HANDOFF,
                    "--source-run",
                    str(run_dir),
                    "--target-project",
                    str(target),
                    cwd=cwd,
                )
                self.assertEqual(handoff.returncode, 2)
                self.assertIn("status", (handoff.stdout + handoff.stderr).lower())
                self.assertFalse(target.exists())

                incomplete_handoff = self.run_cli(
                    RADAR_HANDOFF,
                    "--source-run",
                    str(run_dir),
                    "--target-project",
                    str(target),
                    "--allow-incomplete",
                    cwd=cwd,
                )
                self.assertEqual(incomplete_handoff.returncode, 2)
                self.assertIn(
                    "status",
                    (
                        incomplete_handoff.stdout + incomplete_handoff.stderr
                    ).lower(),
                )
                self.assertFalse(target.exists())

    def test_invalid_conflicting_and_mixed_mode_headers_are_rejected(self) -> None:
        def make_invalid(run_dir: Path) -> None:
            for name in CORE_ARTIFACTS:
                set_header_value(run_dir / name, "mode", "invalid")

        def make_conflicting(run_dir: Path) -> None:
            set_header_value(
                run_dir / "source-candidates.md", "mode", "existing-project"
            )

        def make_mixed(run_dir: Path) -> None:
            remove_header(run_dir / "source-candidates.md", "mode")

        mutations = {
            "invalid": make_invalid,
            "conflicting": make_conflicting,
            "mixed-present-and-missing": make_mixed,
        }

        for case, mutate in mutations.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                cwd = Path(tmp)
                result, run_dir = self.init_run(
                    cwd, f"bad-mode-{case}", profile="tool-gap"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                complete_artifacts(run_dir, CORE_ARTIFACTS)
                mutate(run_dir)

                validation = self.run_cli(
                    RADAR_RUN,
                    "validate",
                    "--source-run",
                    str(run_dir),
                    "--mode",
                    "idea",
                    cwd=cwd,
                )
                self.assertEqual(validation.returncode, 1)
                self.assertIn("mode", (validation.stdout + validation.stderr).lower())

                target = cwd / "target"
                handoff = self.run_cli(
                    RADAR_HANDOFF,
                    "--source-run",
                    str(run_dir),
                    "--target-project",
                    str(target),
                    cwd=cwd,
                )
                self.assertEqual(handoff.returncode, 2)
                self.assertIn("mode", (handoff.stdout + handoff.stderr).lower())
                self.assertFalse(target.exists())

    def test_overwrite_rejects_a_mode_transition_and_preserves_the_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(
                cwd,
                "mode-transition",
                mode="existing-project",
                profile="tool-gap",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            before = {
                path.name: path.read_bytes()
                for path in run_dir.iterdir()
                if path.is_file()
            }

            transitioned, transitioned_dir = self.init_run(
                cwd,
                "mode-transition",
                mode="idea",
                profile="general",
                overwrite=True,
            )
            self.assertEqual(transitioned.returncode, 3)
            self.assertIn("mode", (transitioned.stdout + transitioned.stderr).lower())
            self.assertEqual(transitioned_dir, run_dir)
            after = {
                path.name: path.read_bytes()
                for path in run_dir.iterdir()
                if path.is_file()
            }
            self.assertEqual(after, before)

    def test_index_infers_profile_and_rejects_an_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(cwd, "index-profile", profile="tool-gap")
            self.assertEqual(result.returncode, 0, result.stderr)

            index = run_dir / INDEX_FILE
            index.write_text("stale index\n", encoding="utf-8")
            inferred = self.run_cli(
                RADAR_RUN,
                "index",
                "--source-run",
                str(run_dir),
                cwd=cwd,
            )
            self.assertEqual(inferred.returncode, 0, inferred.stdout + inferred.stderr)
            self.assertEqual(read_header_value(index, "profile"), "tool-gap")

            before = index.read_text(encoding="utf-8")
            overridden = self.run_cli(
                RADAR_RUN,
                "index",
                "--source-run",
                str(run_dir),
                "--profile",
                "general",
                cwd=cwd,
            )
            self.assertEqual(overridden.returncode, 2)
            self.assertIn("unrecognized arguments", overridden.stderr)
            self.assertEqual(index.read_text(encoding="utf-8"), before)

    def test_handoff_regenerates_a_stale_index_from_authoritative_headers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(
                cwd, "stale-index", mode="idea", profile="tool-gap"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            complete_artifacts(run_dir, CORE_ARTIFACTS)

            source_index = run_dir / INDEX_FILE
            set_header_value(source_index, "mode", "existing-project")
            set_header_value(source_index, "profile", "general")
            with source_index.open("a", encoding="utf-8") as stream:
                stream.write("\nstale index marker\n")
            self.assertEqual(
                read_header_value(source_index, "mode"), "existing-project"
            )
            self.assertEqual(read_header_value(source_index, "profile"), "general")

            target = cwd / "target"
            handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                cwd=cwd,
            )
            self.assertEqual(handoff.returncode, 0, handoff.stdout + handoff.stderr)

            destination = target / ".feature-radar" / "runs" / run_dir.name
            copied_index = destination / INDEX_FILE
            self.assertEqual(read_header_value(copied_index, "mode"), "idea")
            self.assertEqual(read_header_value(copied_index, "profile"), "tool-gap")
            self.assertNotIn(
                "stale index marker", copied_index.read_text(encoding="utf-8")
            )

    def test_allow_incomplete_manifest_separates_required_and_optional_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(
                cwd, "incomplete-run", mode="idea", profile="tool-gap"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            missing_required = "signal-map.md"
            (run_dir / missing_required).unlink()
            self.assertFalse((run_dir / missing_required).exists())
            present_required = [
                artifact
                for artifact in CORE_ARTIFACTS
                if artifact != missing_required
            ]
            for name in present_required:
                with self.subTest(draft_artifact=name):
                    self.assertEqual(
                        read_header_value(run_dir / name, "status"), "draft"
                    )

            target = cwd / "target"
            handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                "--allow-incomplete",
                cwd=cwd,
            )
            self.assertEqual(handoff.returncode, 0, handoff.stdout + handoff.stderr)

            manifest = (
                target
                / ".feature-radar"
                / "runs"
                / run_dir.name
                / "handoff-manifest.md"
            )
            self.assertEqual(read_header_value(manifest, "source_complete"), "false")
            missing_required_lines = markdown_section_lines(
                manifest, "Missing Required Files"
            )
            missing_optional_lines = markdown_section_lines(
                manifest, "Missing Optional Files"
            )
            caveat_lines = markdown_section_lines(manifest, "Caveats")
            self.assertEqual(missing_required_lines, [f"- {missing_required}"])
            self.assertEqual(missing_optional_lines, ["- p2a-context.json"])
            self.assertIn("incomplete", " ".join(caveat_lines).lower())

    def test_incomplete_overwrite_removes_stale_required_and_optional_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(
                cwd, "stale-overwrite", mode="idea", profile="tool-gap"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            complete_artifacts(run_dir, CORE_ARTIFACTS)
            optional_name = "p2a-context.json"
            optional_contents = '{"fixture": "stale-overwrite"}\n'
            (run_dir / optional_name).write_text(optional_contents, encoding="utf-8")

            target = cwd / "target"
            first_handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                cwd=cwd,
            )
            self.assertEqual(
                first_handoff.returncode,
                0,
                first_handoff.stdout + first_handoff.stderr,
            )
            destination = target / ".feature-radar" / "runs" / run_dir.name
            missing_required = "signal-map.md"
            stale_required = destination / missing_required
            stale_optional = destination / optional_name
            self.assertTrue(stale_required.is_file())
            self.assertEqual(stale_optional.read_text(encoding="utf-8"), optional_contents)

            (run_dir / missing_required).unlink()
            (run_dir / optional_name).unlink()
            before_no_overwrite = snapshot_tree(destination)
            refused = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                "--allow-incomplete",
                cwd=cwd,
            )
            self.assertEqual(refused.returncode, 3)
            self.assertEqual(snapshot_tree(destination), before_no_overwrite)

            overwritten = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                "--allow-incomplete",
                "--overwrite",
                cwd=cwd,
            )
            self.assertEqual(
                overwritten.returncode,
                0,
                overwritten.stdout + overwritten.stderr,
            )
            self.assertFalse(stale_required.exists())
            self.assertFalse(stale_optional.exists())

            manifest = destination / "handoff-manifest.md"
            self.assertEqual(read_header_value(manifest, "source_complete"), "false")
            self.assertEqual(
                markdown_section_lines(manifest, "Missing Required Files"),
                [f"- {missing_required}"],
            )
            self.assertEqual(
                markdown_section_lines(manifest, "Missing Optional Files"),
                [f"- {optional_name}"],
            )

    def test_both_handoff_writes_destination_specific_manifest_axes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(
                cwd, "both-handoff", mode="idea", profile="tool-gap"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            complete_artifacts(run_dir, CORE_ARTIFACTS)
            target = cwd / "both-target"

            handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                "--mode",
                "both",
                cwd=cwd,
            )
            self.assertEqual(handoff.returncode, 0, handoff.stdout + handoff.stderr)

            destinations = {
                "radar-native": target
                / ".feature-radar"
                / "runs"
                / run_dir.name,
                "p2a-preflight": target
                / ".plan2agent"
                / "artifacts"
                / "both-target"
                / "preflight-research",
            }
            for handoff_mode, destination in destinations.items():
                with self.subTest(handoff_mode=handoff_mode):
                    manifest = destination / "handoff-manifest.md"
                    self.assertTrue(manifest.is_file())
                    self.assertEqual(read_header_value(manifest, "run_mode"), "idea")
                    self.assertEqual(
                        read_header_value(manifest, "profile"), "tool-gap"
                    )
                    self.assertEqual(
                        read_header_value(manifest, "handoff_mode"), handoff_mode
                    )
                    self.assertEqual(read_header_value(manifest, "mode"), handoff_mode)
                    self.assertEqual(
                        read_header_value(manifest, "source_complete"), "true"
                    )
                    copied_index = destination / INDEX_FILE
                    self.assertEqual(read_header_value(copied_index, "mode"), "idea")
                    self.assertEqual(
                        read_header_value(copied_index, "profile"), "tool-gap"
                    )
                    for name in CORE_ARTIFACTS:
                        with self.subTest(
                            handoff_mode=handoff_mode, transferred_artifact=name
                        ):
                            copied_artifact = destination / name
                            self.assertTrue(copied_artifact.is_file())
                            self.assertEqual(
                                copied_artifact.read_bytes(),
                                (run_dir / name).read_bytes(),
                            )

    def test_index_defaults_frozen_legacy_run_to_general(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            run_dir = self.copy_legacy_fixture(cwd)
            self.assertIsNone(read_header_value(run_dir / INDEX_FILE, "profile"))

            result = self.run_cli(
                RADAR_RUN,
                "index",
                "--source-run",
                str(run_dir),
                cwd=cwd,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(read_header_value(run_dir / INDEX_FILE, "profile"), "general")

    def test_frozen_legacy_run_without_profiles_validates_and_handoffs_as_general(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            run_dir = self.copy_legacy_fixture(cwd)
            for name in [*CORE_ARTIFACTS, INDEX_FILE]:
                with self.subTest(legacy_artifact=name):
                    self.assertIsNone(read_header_value(run_dir / name, "profile"))

            validation = self.run_cli(
                RADAR_RUN,
                "validate",
                "--source-run",
                str(run_dir),
                cwd=cwd,
            )
            self.assertEqual(
                validation.returncode,
                0,
                validation.stdout + validation.stderr,
            )

            target = cwd / "target"
            handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                cwd=cwd,
            )
            self.assertEqual(handoff.returncode, 0, handoff.stdout + handoff.stderr)
            manifest = (
                target
                / ".feature-radar"
                / "runs"
                / run_dir.name
                / "handoff-manifest.md"
            )
            self.assertEqual(read_header_value(manifest, "run_mode"), "idea")
            self.assertEqual(read_header_value(manifest, "profile"), "general")
            self.assertEqual(read_header_value(manifest, "handoff_mode"), "radar-native")
            self.assertEqual(read_header_value(manifest, "mode"), "radar-native")
            self.assertEqual(read_header_value(manifest, "source_complete"), "true")

    def test_invalid_profile_is_rejected_by_init_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(cwd, "invalid-run", profile="invalid")

            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid choice", result.stderr)
            self.assertFalse(run_dir.exists())

    def test_invalid_conflicting_and_mixed_profile_headers_are_rejected(self) -> None:
        def make_invalid(run_dir: Path) -> None:
            for name in CORE_ARTIFACTS:
                set_header_value(run_dir / name, "profile", "invalid")

        def make_conflicting(run_dir: Path) -> None:
            set_header_value(
                run_dir / "source-candidates.md", "profile", "general"
            )

        def make_mixed(run_dir: Path) -> None:
            remove_header(run_dir / "source-candidates.md", "profile")

        def make_duplicate(run_dir: Path) -> None:
            duplicate_header(run_dir / "research-bundle.md", "profile")

        mutations = {
            "invalid": make_invalid,
            "conflicting": make_conflicting,
            "mixed-present-and-missing": make_mixed,
            "duplicate": make_duplicate,
        }

        for case, mutate in mutations.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                cwd = Path(tmp)
                result, run_dir = self.init_run(
                    cwd, f"bad-{case}", profile="tool-gap"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                complete_artifacts(run_dir, CORE_ARTIFACTS)
                mutate(run_dir)

                validation = self.run_cli(
                    RADAR_RUN,
                    "validate",
                    "--source-run",
                    str(run_dir),
                    cwd=cwd,
                )
                self.assertEqual(validation.returncode, 1)
                self.assertIn(
                    "profile", (validation.stdout + validation.stderr).lower()
                )

                index = run_dir / INDEX_FILE
                index_before = index.read_text(encoding="utf-8")
                reindex = self.run_cli(
                    RADAR_RUN,
                    "index",
                    "--source-run",
                    str(run_dir),
                    cwd=cwd,
                )
                self.assertEqual(reindex.returncode, 2)
                self.assertIn("profile", (reindex.stdout + reindex.stderr).lower())
                self.assertEqual(index.read_text(encoding="utf-8"), index_before)

                target = cwd / "target"
                handoff = self.run_cli(
                    RADAR_HANDOFF,
                    "--source-run",
                    str(run_dir),
                    "--target-project",
                    str(target),
                    "--allow-incomplete",
                    cwd=cwd,
                )
                self.assertEqual(handoff.returncode, 2)
                self.assertIn("profile", (handoff.stdout + handoff.stderr).lower())
                self.assertFalse(target.exists())

    def test_self_handoff_with_overwrite_is_rejected_before_source_mutation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(
                cwd, "self-handoff", mode="idea", profile="tool-gap"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            complete_artifacts(run_dir, CORE_ARTIFACTS)
            index = run_dir / INDEX_FILE
            with index.open("a", encoding="utf-8") as stream:
                stream.write("\nself-handoff preservation marker\n")
            before = snapshot_tree(run_dir)

            handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(cwd),
                "--overwrite",
                cwd=cwd,
            )
            combined_output = (handoff.stdout + handoff.stderr).lower()
            self.assertEqual(handoff.returncode, 3)
            self.assertIn("destination preflight failed", combined_output)
            self.assertIn("source", combined_output)
            self.assertIn("destination", combined_output)
            self.assertNotIn("traceback", combined_output)
            self.assertEqual(snapshot_tree(run_dir), before)

    def test_both_overwrite_rejects_directory_artifact_without_partial_writes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            result, run_dir = self.init_run(
                cwd, "atomic-both", mode="idea", profile="tool-gap"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            complete_artifacts(run_dir, CORE_ARTIFACTS)
            target = cwd / "atomic-target"
            radar_destination = (
                target / ".feature-radar" / "runs" / run_dir.name
            )
            p2a_destination = (
                target
                / ".plan2agent"
                / "artifacts"
                / "atomic-target"
                / "preflight-research"
            )

            radar_destination.mkdir(parents=True)
            (radar_destination / INDEX_FILE).write_text(
                "radar index sentinel\n", encoding="utf-8"
            )
            (radar_destination / "handoff-manifest.md").write_text(
                "radar manifest sentinel\n", encoding="utf-8"
            )
            blocked_artifact = p2a_destination / "signal-map.md"
            blocked_artifact.mkdir(parents=True)
            (blocked_artifact / "directory sentinel.txt").write_text(
                "do not change\n", encoding="utf-8"
            )
            radar_before = snapshot_tree(radar_destination)
            p2a_before = snapshot_tree(p2a_destination)

            handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                "--mode",
                "both",
                "--overwrite",
                cwd=cwd,
            )
            combined_output = (handoff.stdout + handoff.stderr).lower()
            self.assertEqual(handoff.returncode, 3)
            self.assertIn("destination preflight failed", combined_output)
            self.assertIn("non-file destination artifact", combined_output)
            self.assertNotIn("traceback", combined_output)
            self.assertEqual(snapshot_tree(radar_destination), radar_before)
            self.assertEqual(snapshot_tree(p2a_destination), p2a_before)

    def test_init_and_handoff_keep_no_overwrite_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            first, run_dir = self.init_run(cwd, "no-overwrite", profile="tool-gap")
            self.assertEqual(first.returncode, 0, first.stderr)
            source_plan = run_dir / "research-plan.md"
            source_sentinel = "source sentinel: do not replace\n"
            source_contents = source_plan.read_text(encoding="utf-8") + source_sentinel
            source_plan.write_text(source_contents, encoding="utf-8")

            second, _ = self.init_run(cwd, "no-overwrite", profile="general")
            self.assertEqual(second.returncode, 3)
            self.assertEqual(source_plan.read_text(encoding="utf-8"), source_contents)

            target = cwd / "target"
            first_handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                "--allow-incomplete",
                cwd=cwd,
            )
            self.assertEqual(
                first_handoff.returncode,
                0,
                first_handoff.stdout + first_handoff.stderr,
            )
            destination = target / ".feature-radar" / "runs" / run_dir.name
            copied_plan = destination / "research-plan.md"
            manifest = destination / "handoff-manifest.md"
            destination_sentinel = "destination sentinel: do not replace\n"
            manifest_sentinel = "manifest sentinel: do not replace\n"
            copied_plan.write_text(destination_sentinel, encoding="utf-8")
            manifest.write_text(manifest_sentinel, encoding="utf-8")

            second_handoff = self.run_cli(
                RADAR_HANDOFF,
                "--source-run",
                str(run_dir),
                "--target-project",
                str(target),
                "--allow-incomplete",
                cwd=cwd,
            )
            self.assertEqual(second_handoff.returncode, 3)
            self.assertEqual(
                copied_plan.read_text(encoding="utf-8"), destination_sentinel
            )
            self.assertEqual(manifest.read_text(encoding="utf-8"), manifest_sentinel)


if __name__ == "__main__":
    unittest.main()
