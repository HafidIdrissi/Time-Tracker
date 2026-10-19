import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISSUE_LINK = re.compile(r"https://github\.com/HafidIdrissi/Time-Tracker/issues/\d+")
SEARCH_LINK = re.compile(r"https://github\.com/HafidIdrissi/Time-Tracker/issues\?q=[^)\s]+")


def section(text, heading):
    start = text.index(heading)
    end = text.find("\n#", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


class TestContributorDocs(unittest.TestCase):
    def test_first_contribution_table_uses_available_task_searches(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        table = section(readme, "### Choose your first contribution")

        self.assertIsNone(ISSUE_LINK.search(table))
        rows = [line for line in table.splitlines() if line.startswith("| ") and "---" not in line][1:]
        self.assertGreaterEqual(len(rows), 5)
        for row in rows:
            links = SEARCH_LINK.findall(row)
            self.assertTrue(links, row)
            for link in links:
                self.assertIn("is%3Aopen", link)
                self.assertIn("no%3Aassignee", link)

    def test_docs_warn_that_availability_can_change(self):
        readme = section(
            (ROOT / "README.md").read_text(encoding="utf-8"),
            "### Choose your first contribution",
        )
        contributing = section(
            (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8"),
            "## Find and claim an issue",
        )
        for text in (readme, contributing):
            self.assertIn("availability can change", text.lower())
            self.assertIn("linked pull requests", text)


if __name__ == "__main__":
    unittest.main()
