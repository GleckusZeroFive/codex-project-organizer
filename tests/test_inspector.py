from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "inspect_codex_project.py"


class InspectorTests(unittest.TestCase):
    def run_inspector(self, cwd: Path, codex_home: Path) -> tuple[int, dict]:
        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--cwd", str(cwd), "--json"],
            text=True,
            encoding="utf-8",
            capture_output=True,
            env=env,
            check=False,
        )
        return result.returncode, json.loads(result.stdout)

    def init_repo(self, path: Path) -> None:
        subprocess.run(
            ["git", "init", "--quiet", str(path)],
            check=True,
            capture_output=True,
        )

    def test_detects_instruction_chain_and_custom_agents(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex-home"
            repo = root / "repo"
            nested = repo / "src"
            (codex_home / "agents").mkdir(parents=True)
            (repo / ".codex" / "agents").mkdir(parents=True)
            nested.mkdir(parents=True)
            self.init_repo(repo)
            (codex_home / "AGENTS.md").write_text("global", encoding="utf-8")
            (codex_home / "agents" / "personal.toml").write_text("name='personal'", encoding="utf-8")
            (repo / "AGENTS.md").write_text("root", encoding="utf-8")
            (nested / "AGENTS.md").write_text("nested", encoding="utf-8")
            (repo / ".codex" / "agents" / "reviewer.toml").write_text(
                "name='reviewer'", encoding="utf-8"
            )

            code, report = self.run_inspector(nested, codex_home)

            self.assertEqual(code, 0)
            self.assertEqual(report["shape"], "git-repository")
            self.assertEqual(len(report["project_instruction_chain"]), 2)
            self.assertEqual(report["user_custom_agents"], ["personal"])
            self.assertEqual(report["project_custom_agents"], ["reviewer"])

    def test_detects_wrapper_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex-home"
            wrapper = root / "wrapper"
            child = wrapper / "client-repo"
            codex_home.mkdir()
            wrapper.mkdir()
            child.mkdir()
            self.init_repo(child)
            (codex_home / "AGENTS.md").write_text("global", encoding="utf-8")
            (wrapper / "AGENTS.md").write_text("private wrapper", encoding="utf-8")

            code, report = self.run_inspector(wrapper, codex_home)

            self.assertEqual(code, 0)
            self.assertEqual(report["shape"], "wrapper-workspace")
            self.assertEqual(report["direct_child_repositories"], [str(child.resolve())])


if __name__ == "__main__":
    unittest.main()
