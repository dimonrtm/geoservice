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
    def test_warns_when_plan_changes_without_memory(self):
        checker = load_module()

        result = checker.needs_memory_update(["docs/superpowers/plans/example.md"], [])

        self.assertTrue(result)

    def test_allows_plan_changes_with_memory(self):
        checker = load_module()

        result = checker.needs_memory_update(
            ["docs/superpowers/plans/example.md"],
            ["docs/agent-memory/patterns/example.md"],
        )

        self.assertFalse(result)

    def test_ignores_regular_code_changes(self):
        checker = load_module()

        result = checker.needs_memory_update(["apps/backend/app/main.py"], [])

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
