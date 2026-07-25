# Contributing

**English** · [Русский](CONTRIBUTING.ru.md)

Issues and pull requests are welcome.

Keep changes focused on reliable Codex workspace organization. New rules should have one clear owner and should not duplicate mutable state across several files.

Before opening a pull request, run:

```bash
python -m unittest discover -s tests -v
python scripts/inspect_codex_project.py --cwd .
```

Do not include credentials, personal paths, client data, session logs, or private workspace notes in fixtures and examples.
