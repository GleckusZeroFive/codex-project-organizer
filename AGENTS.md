# Repository guidance

- Keep this repository portable across Windows, macOS, and Linux.
- Keep `SKILL.md` focused on the reusable workflow; put deeper rationale in `references/`.
- Do not add personal paths, credentials, client data, session logs, or private workspace notes.
- Preserve read-only defaults in the inspector and examples.
- Run `python -m unittest discover -s tests -v` after changing Python code.
- Run `python scripts/inspect_codex_project.py --cwd .` before publishing changes.
