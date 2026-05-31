import importlib.util
import sys
import unittest
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "lint-wiki.py"
    spec = importlib.util.spec_from_file_location("lint_wiki", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LintWikiTests(unittest.TestCase):
    def setUp(self):
        self.tmp_parent = Path.cwd() / ".tmp-tests"
        self.tmp_parent.mkdir(exist_ok=True)
        self.root = self.tmp_parent / self._testMethodName
        self.root.mkdir(exist_ok=True)

    def tearDown(self):
        # The Codex Windows sandbox can create files but block Python cleanup ACL changes.
        # Test scratch directories are ignored by Git and left for external cleanup.
        pass

    def write(self, relative_path, text):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_reports_missing_frontmatter(self):
        self.write("Vision_wiki/concepts/no-frontmatter.md", "# No Frontmatter\n")

        lint_wiki = load_module()
        issues = lint_wiki.lint(self.root)

        self.assertIssue(
            issues, "missing_frontmatter", "Vision_wiki/concepts/no-frontmatter.md"
        )

    def test_reports_broken_wikilink(self):
        self.write(
            "Vision_wiki/concepts/source.md",
            "---\ntitle: Source\ntype: concept\nstatus: active\ncreated: 2026-05-30\nupdated: 2026-05-30\nsource: RAW_inputs/example.md\ntags: []\n---\n\n[[Missing/Node]]\n",
        )

        lint_wiki = load_module()
        issues = lint_wiki.lint(self.root)

        self.assertIssue(issues, "broken_wikilink", "Vision_wiki/concepts/source.md")

    def test_reports_required_source_for_non_index_wiki_nodes(self):
        self.write(
            "Code_wiki/архитектура/service.md",
            "---\ntitle: Service\ntype: service\nstatus: active\ncreated: 2026-05-30\nupdated: 2026-05-30\nsource: null\ntags: []\n---\n\n# Service\n\nОписание.\n",
        )

        lint_wiki = load_module()
        issues = lint_wiki.lint(self.root)

        self.assertIssue(issues, "missing_source", "Code_wiki/архитектура/service.md")

    def test_valid_index_and_template_are_clean(self):
        self.write(
            "Code_wiki/index.md",
            "---\ntitle: Code Wiki\ntype: index\nstatus: active\ncreated: 2026-05-30\nupdated: 2026-05-30\nsource: null\ntags: []\n---\n\n# Code Wiki\n\n[[Code_wiki/_templates/_info]]\n",
        )
        self.write(
            "Code_wiki/_templates/_info.md",
            "---\ntitle: Templates\ntype: index\nstatus: active\ncreated: 2026-05-30\nupdated: 2026-05-30\nsource: null\ntags: []\n---\n\n# Templates\n",
        )

        lint_wiki = load_module()
        issues = lint_wiki.lint(self.root)

        self.assertEqual([], issues)

    def test_knowledge_pipeline_runbook_allows_null_source(self):
        self.write(
            "docs/knowledge-pipeline/README.md",
            "---\ntitle: Pipeline\ntype: runbook\nstatus: active\ncreated: 2026-05-30\nupdated: 2026-05-30\nsource: null\ntags: []\n---\n\n# Pipeline\n\nМетодический runbook.\n",
        )

        lint_wiki = load_module()
        issues = lint_wiki.lint(self.root)

        self.assertEqual([], issues)

    def assertIssue(self, issues, code, relative_path):
        found = [
            issue
            for issue in issues
            if issue.code == code and issue.path.as_posix() == relative_path
        ]
        self.assertTrue(
            found, f"Missing issue {code} for {relative_path}. Got: {issues}"
        )


if __name__ == "__main__":
    unittest.main()
