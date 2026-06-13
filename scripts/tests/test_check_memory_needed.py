import importlib.util
import sys
import unittest
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "check-memory-needed.py"
    spec = importlib.util.spec_from_file_location("check_memory_needed", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckMemoryNeededTests(unittest.TestCase):
    def test_does_not_require_memory_for_regular_plan_or_spec(self):
        checker = load_module()

        for path in (
            "docs/superpowers/plans/example.md",
            "docs/superpowers/specs/example.md",
        ):
            with self.subTest(path=path):
                self.assertFalse(checker.needs_memory_update([path], []))

    def test_requires_memory_for_agent_and_pipeline_rules(self):
        checker = load_module()

        for path in (
            "AGENTS.md",
            "CONTRIBUTING.md",
            "docs/knowledge-pipeline/README.md",
            ".agents/skills/source-command-ingest/SKILL.md",
        ):
            with self.subTest(path=path):
                self.assertTrue(checker.needs_memory_update([path], []))

    def test_protocol_change_is_itself_a_memory_update(self):
        checker = load_module()

        self.assertFalse(
            checker.needs_memory_update(
                ["docs/agent-memory/protocol.md"],
                ["docs/agent-memory/protocol.md"],
            )
        )

    def test_allows_operating_rule_change_with_memory(self):
        checker = load_module()

        self.assertFalse(
            checker.needs_memory_update(
                ["AGENTS.md"],
                ["docs/agent-memory/decisions/operating-rules.md"],
            )
        )

    def test_ignores_regular_code_changes(self):
        checker = load_module()

        self.assertFalse(checker.needs_memory_update(["apps/backend/app/main.py"], []))


if __name__ == "__main__":
    unittest.main()
