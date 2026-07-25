# Minimal parent → subagents example

**English** · [Русский](README.ru.md)

Copy only the pieces your project needs:

```text
project/
├── AGENTS.md
└── .codex/
    ├── config.toml
    └── agents/
        ├── explorer.toml
        └── reviewer.toml
```

The parent agent remains responsible for scope, decisions, authorization, integration, and the final result. The custom agents handle bounded read-only work and return evidence.

The role files intentionally omit `model` and `model_reasoning_effort`, so they inherit the configured defaults or the parent settings. Pin those values only when the role has a stable reason to differ.

Project-scoped `.codex` configuration and agents load only for a trusted project. Review these files before trusting the repository.
