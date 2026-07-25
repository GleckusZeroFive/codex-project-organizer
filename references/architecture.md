# Codex project organization reference

## Ownership matrix

| Information or behavior | Canonical surface | Notes |
|---|---|---|
| One-off task constraint | Current prompt/thread | Do not persist automatically. |
| Personal behavior across projects | `~/.codex/AGENTS.md` | Keep short; broad text is injected everywhere. |
| Stable repo convention | Root or nested `AGENTS.md` | Put it at the narrowest directory that owns it. |
| Current phase, blockers, NEXT, authorization | One project LIVE STATE file/section | Snapshot, not append-only log. |
| Architecture/contract/scope/decisions | Existing project docs | Link from the entrypoint; one owner per fact type. |
| Repeatable multi-step workflow | User or repo skill | User: cross-project. Repo: truly project-specific. |
| Narrow delegated role | `~/.codex/agents/*.toml` or `.codex/agents/*.toml` | Personal or project-scoped custom agent. |
| Delegation policy | Applicable `AGENTS.md` or skill | State when parallel work is worth its coordination cost. |
| Live external data/action | MCP or connector | Register globally unless the capability is genuinely project-only. |
| Mechanical lifecycle enforcement | Hook, CI, linter, pre-commit | A prose rule is not enforcement. |
| Shell approval/deny policy | `.rules` | Rules are for commands outside the sandbox, not coding style. |
| Learned recall from old sessions | Native Codex memories | Helpful and generated; never the only mandatory source. |
| Incident history/evidence | Log/archive/artifacts | Promote a validated lesson into its canonical rule owner. |

## Discovery facts

- Codex reads one global file: `$CODEX_HOME/AGENTS.override.md` when non-empty, otherwise `$CODEX_HOME/AGENTS.md`.
- For project guidance it walks from the detected project root to CWD, choosing at most one file per directory: `AGENTS.override.md`, then `AGENTS.md`, then configured fallback names.
- Closer project files appear later and override broader guidance.
- The default project-document budget is 32 KiB. Keep global guidance especially small because it affects every project.
- If CWD is inside a Git repo, the Git root normally stops discovery. An `AGENTS.md` immediately above that repo is not automatically included.
- Project `.codex/config.toml`, hooks, rules, and project custom agents require project trust. User-level configuration remains independent of project trust.
- User skills belong in `~/.agents/skills`; repo skills belong in `.agents/skills`. Skills use progressive disclosure.
- Personal custom agents belong in `~/.codex/agents/`; project custom agents belong in `.codex/agents/`.
- Subagents inherit parent settings when custom agent files omit them. Parent runtime sandbox and approval overrides are reapplied to spawned children.
- Codex app, CLI, and IDE on the same host share user `config.toml` and MCP setup.

Official references:

- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/build-skills
- https://learn.chatgpt.com/docs/config-file/config-advanced
- https://learn.chatgpt.com/docs/hooks
- https://learn.chatgpt.com/docs/customization/memories

## Project shapes

### Normal repository

Launch from the repo root. Keep required repo conventions and commands in root `AGENTS.md`. Add nested files only when a subtree has different commands or constraints.

### Private wrapper around a client repository

```text
private-workspace/
├── AGENTS.md
├── PROJECT.md or CLAUDE.md
├── notes/
├── artifacts/
└── repo/                 # the only Git repository
```

Launch Codex from `private-workspace/`, not `repo/`. Otherwise Git-root discovery will miss the wrapper `AGENTS.md`. Never commit wrapper files to `repo/`.

### Cross-agent project

Choose one vendor-neutral or already-established project canon for mutable state. Keep `AGENTS.md`, `CLAUDE.md`, and other vendor entrypoints short and explicit about how to reach it. Critical safety rules still stay in every automatically loaded entrypoint that must enforce them.

### Parent with specialized subagents

```text
project/
├── AGENTS.md
└── .codex/
    ├── config.toml
    └── agents/
        ├── explorer.toml
        └── reviewer.toml
```

The parent owns requirements, authorization, decisions, and the final answer. Children receive bounded tasks and return compact evidence. Prefer parallel reads; serialize overlapping writes. Keep models inherited unless a stable role-specific requirement justifies pinning one.

### Large monorepo

Root `AGENTS.md` owns universal repo behavior. Service-level files own only the delta. Do not repeat root content in children.

## Native memory boundary

Native memories are off by default and live under `$CODEX_HOME/memories/` when enabled. They are generated asynchronously from eligible chats and may be delayed. Current documentation explicitly says mandatory team guidance belongs in `AGENTS.md` or checked-in docs.

For multi-project work, keep project truth on disk even when native memories are enabled. Memory is a recall layer, not an authorization or status database.

## Anti-patterns

- A huge global `AGENTS.md` containing every project lesson.
- The same mutable status copied into `AGENTS.md`, `CLAUDE.md`, README, memory, and handoff files.
- A local `.codex/config.toml` created merely to duplicate global MCP.
- Broad custom agents that duplicate the parent instead of owning a narrow role.
- Parallel agents making overlapping edits without an explicit coordination boundary.
- “Read every document before every action”; use routing and progressive disclosure.
- Telling the agent to reread an injected global file without giving its physical path.
- Asking the model whether it loaded instructions instead of inspecting session JSONL.
- Storing current authorization or NEXT only in chat history/native memory.
- Putting private client-management workspace files into the client's Git repo.
- Treating a prose instruction as adequate protection for a destructive operation.

## Cold-start acceptance prompt

Use a read-only clean session from the intended CWD:

```text
Without using prior chat history, report the project root and Git boundary, current phase and NEXT, blockers, forbidden external actions, canonical sources, inherited global skills/MCP/hooks, available custom agents, and required verification commands. Cite the local files that prove each project-specific claim. Do not modify anything.
```

The agent must distinguish proved facts from unknowns. A fluent but uncited reconstruction fails.
