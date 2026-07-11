from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_SKILL = REPO_ROOT / ".agents" / "skills" / "feature-radar-research"
CLAUDE_SKILL = REPO_ROOT / ".claude" / "skills" / "feature-radar-research"
OPENAI_YAML = CODEX_SKILL / "agents" / "openai.yaml"


def quoted_yaml_value(text: str, key: str) -> str:
    match = re.search(rf'^\s+{re.escape(key)}:\s+"([^"]*)"\s*$', text, re.MULTILINE)
    if match is None:
        raise AssertionError(f"missing quoted YAML field: {key}")
    return match.group(1)


class SkillInterfaceTests(unittest.TestCase):
    def test_codex_interface_surfaces_invocation_options(self) -> None:
        text = OPENAI_YAML.read_text(encoding="utf-8")
        short_description = quoted_yaml_value(text, "short_description")
        default_prompt = quoted_yaml_value(text, "default_prompt")

        self.assertTrue(25 <= len(short_description) <= 64)
        self.assertIn("$feature-radar-research", default_prompt)
        self.assertIn("general|tool-gap", default_prompt)
        self.assertIn("idea|existing-project", default_prompt)
        self.assertIn("native-run|chat-only", default_prompt)

        for unsupported_schema_key in ("arguments", "parameters", "choices", "enum"):
            self.assertNotRegex(text, rf"(?m)^\s*{unsupported_schema_key}:")

    def test_codex_and_claude_share_the_invocation_contract(self) -> None:
        required_phrases = (
            "## Invocation Contract",
            "`action`",
            "`research_mode`",
            "`profile`",
            "`output`",
            "`handoff_mode`",
            "Do not ask merely because a field was omitted.",
        )

        for skill_file in (CODEX_SKILL / "SKILL.md", CLAUDE_SKILL / "SKILL.md"):
            text = skill_file.read_text(encoding="utf-8")
            with self.subTest(skill=str(skill_file.relative_to(REPO_ROOT))):
                for phrase in required_phrases:
                    self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
