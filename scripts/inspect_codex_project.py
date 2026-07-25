#!/usr/bin/env python3
"""Inspect Codex instruction and capability discovery without exposing secrets."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    tomllib = None


def nonempty(path: Path) -> bool:
    try:
        return path.is_file() and bool(path.read_text(encoding="utf-8-sig").strip())
    except (OSError, UnicodeError):
        return False


def load_toml(path: Path) -> dict[str, Any]:
    if tomllib is None or not path.is_file():
        return {}
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def git_root(cwd: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return Path(result.stdout.strip()).resolve()


def path_chain(root: Path, cwd: Path) -> list[Path]:
    try:
        relative = cwd.relative_to(root)
    except ValueError:
        return [cwd]
    chain = [root]
    current = root
    for part in relative.parts:
        current = current / part
        chain.append(current)
    return chain


def pick_instruction(directory: Path, fallbacks: list[str]) -> Path | None:
    for name in ["AGENTS.override.md", "AGENTS.md", *fallbacks]:
        candidate = directory / name
        if nonempty(candidate):
            return candidate
    return None


def skill_count(root: Path) -> int:
    if not root.is_dir():
        return 0
    return sum(1 for path in root.rglob("SKILL.md") if path.is_file())


def toml_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    try:
        return sorted(path for path in root.glob("*.toml") if path.is_file())
    except OSError:
        return []


def direct_child_repos(cwd: Path) -> list[Path]:
    repos: list[Path] = []
    try:
        for child in cwd.iterdir():
            if child.is_dir() and (child / ".git").exists():
                repos.append(child)
    except OSError:
        pass
    return sorted(repos)


def inspect(cwd: Path) -> dict[str, Any]:
    cwd = cwd.resolve()
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex")).resolve()
    user_config_path = codex_home / "config.toml"
    user_config = load_toml(user_config_path)

    configured_markers = user_config.get("project_root_markers")
    project = git_root(cwd)
    project_root = project or cwd
    shape = "git-repository" if project else "non-git-workspace"
    child_repos = direct_child_repos(cwd) if not project else []
    if child_repos:
        shape = "wrapper-workspace"

    fallbacks = user_config.get("project_doc_fallback_filenames") or []
    if not isinstance(fallbacks, list):
        fallbacks = []
    fallbacks = [str(item) for item in fallbacks]
    budget = user_config.get("project_doc_max_bytes", 32768)
    if not isinstance(budget, int) or budget <= 0:
        budget = 32768

    global_override = codex_home / "AGENTS.override.md"
    global_default = codex_home / "AGENTS.md"
    global_instruction = (
        global_override if nonempty(global_override) else global_default if nonempty(global_default) else None
    )

    chain = path_chain(project_root, cwd)
    project_instructions = [path for directory in chain if (path := pick_instruction(directory, fallbacks))]
    project_bytes = sum(path.stat().st_size for path in project_instructions)
    global_bytes = global_instruction.stat().st_size if global_instruction else 0

    project_configs = [directory / ".codex" / "config.toml" for directory in chain]
    project_configs = [path for path in project_configs if path.is_file()]
    project_hooks = [directory / ".codex" / "hooks.json" for directory in chain]
    project_hooks = [path for path in project_hooks if path.is_file()]
    project_rules = [directory / ".codex" / "rules" for directory in chain]
    project_rules = [path for path in project_rules if path.is_dir()]
    project_agents: list[Path] = []
    for directory in chain:
        project_agents.extend(toml_files(directory / ".codex" / "agents"))

    user_mcp = sorted((user_config.get("mcp_servers") or {}).keys())
    user_agents_configured = isinstance(user_config.get("agents"), dict)
    features = user_config.get("features") or {}
    memories_enabled = bool(features.get("memories", False))
    user_hook_sources = [
        path
        for path in [codex_home / "hooks.json", codex_home / "config.toml"]
        if path.is_file()
    ]
    user_agents = toml_files(codex_home / "agents")

    skill_roots: dict[str, int] = {
        "user_shared": skill_count(home / ".agents" / "skills"),
        "user_codex": skill_count(codex_home / "skills"),
    }
    for directory in chain:
        count = skill_count(directory / ".agents" / "skills")
        if count:
            skill_roots[str(directory / ".agents" / "skills")] = count

    warnings: list[str] = []
    failures: list[str] = []
    if not global_instruction:
        warnings.append("No non-empty global AGENTS.md was found in CODEX_HOME.")
    elif global_bytes > 16384:
        warnings.append(
            f"Global AGENTS.md is {global_bytes} bytes; broad guidance is injected into every project."
        )
    if not project_instructions:
        warnings.append("No project AGENTS.md chain is discoverable from the intended CWD.")
    if project_bytes > budget:
        failures.append(
            f"Project instruction chain is {project_bytes} bytes and exceeds the {budget}-byte budget."
        )
    elif project_bytes > int(budget * 0.8):
        warnings.append(
            f"Project instruction chain uses more than 80% of its {budget}-byte budget."
        )

    if project:
        parent = project_root.parent
        missed = [parent / "AGENTS.override.md", parent / "AGENTS.md"]
        missed = [path for path in missed if nonempty(path)]
        if missed:
            warnings.append(
                "CWD is inside a Git root, so parent instruction files are outside discovery: "
                + ", ".join(str(path) for path in missed)
            )
    if (project_root / "CLAUDE.md").is_file() and not any(
        path.parent == project_root for path in project_instructions
    ):
        warnings.append("CLAUDE.md exists at project root but Codex has no root AGENTS.md entrypoint.")

    report: dict[str, Any] = {
        "cwd": str(cwd),
        "shape": shape,
        "project_root": str(project_root),
        "git_root": str(project) if project else None,
        "direct_child_repositories": [str(path) for path in child_repos],
        "configured_project_root_markers": configured_markers,
        "global_instruction": str(global_instruction) if global_instruction else None,
        "global_instruction_bytes": global_bytes,
        "project_instruction_chain": [str(path) for path in project_instructions],
        "project_instruction_bytes": project_bytes,
        "project_instruction_budget": budget,
        "global_mcp_names": user_mcp,
        "skill_counts": skill_roots,
        "user_hook_sources": [str(path) for path in user_hook_sources],
        "project_config_files": [str(path) for path in project_configs],
        "project_hook_files": [str(path) for path in project_hooks],
        "project_rule_directories": [str(path) for path in project_rules],
        "user_custom_agents": [path.stem for path in user_agents],
        "project_custom_agents": [path.stem for path in project_agents],
        "user_agents_section_configured": user_agents_configured,
        "native_memories_enabled": memories_enabled,
        "native_memory_directory_exists": (codex_home / "memories").is_dir(),
        "warnings": warnings,
        "failures": failures,
    }
    return report


def print_text(report: dict[str, Any]) -> None:
    print(f"CWD: {report['cwd']}")
    print(f"Shape: {report['shape']}")
    print(f"Project root: {report['project_root']}")
    print(f"Git root: {report['git_root'] or '<none>'}")
    if report["direct_child_repositories"]:
        print("Child Git repos: " + ", ".join(report["direct_child_repositories"]))
    print(
        "Global instruction: "
        + (report["global_instruction"] or "<none>")
        + f" ({report['global_instruction_bytes']} bytes)"
    )
    print("Project instruction chain:")
    if report["project_instruction_chain"]:
        for path in report["project_instruction_chain"]:
            print(f"  - {path}")
    else:
        print("  <none>")
    print(
        f"Project instruction budget: {report['project_instruction_bytes']} / "
        f"{report['project_instruction_budget']} bytes"
    )
    print("Global MCP names: " + (", ".join(report["global_mcp_names"]) or "<none>"))
    print(
        "Skills: "
        + ", ".join(f"{name}={count}" for name, count in report["skill_counts"].items())
    )
    print(
        "Custom agents: "
        f"user_section={report['user_agents_section_configured']}, "
        f"user={', '.join(report['user_custom_agents']) or '<none>'}, "
        f"project={', '.join(report['project_custom_agents']) or '<none>'}"
    )
    print(
        "Native memories: "
        f"enabled={report['native_memories_enabled']}, "
        f"directory={report['native_memory_directory_exists']}"
    )
    print(f"User hook sources: {len(report['user_hook_sources'])}")
    print(
        f"Project config/hooks/rules: {len(report['project_config_files'])}/"
        f"{len(report['project_hook_files'])}/{len(report['project_rule_directories'])}"
    )
    for message in report["warnings"]:
        print(f"WARN: {message}")
    for message in report["failures"]:
        print(f"FAIL: {message}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = inspect(args.cwd)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    if report["failures"] or (args.strict and report["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
