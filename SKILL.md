---
name: organize-codex-project
description: "Audit and organize a local software workspace for reliable Codex use: AGENTS.md discovery, instruction ownership, project live state, global versus project skills/MCP/hooks, Git boundaries, custom parent/subagent roles, cross-agent handoff, and cold-start or compaction recovery. Use when initializing a project for Codex, cleaning up scattered agent rules or memory, diagnosing lost global instructions/skills/MCP, adding or repairing AGENTS.md, configuring subagents, or preparing a repo/workspace for repeatable work across sessions."
---

# Organize a Codex Project

Make the smallest structure that lets a fresh Codex session recover the right rules, capabilities, state, and next action without contaminating the client repository or duplicating global policy.

## 1. Inspect before changing

Resolve this skill directory, then run:

```powershell
python <skill-dir>\scripts\inspect_codex_project.py --cwd <workspace>
```

Use `--json` when another script will consume the result. Run from the exact directory the user intends to open in Codex; CWD affects instruction discovery.

Also inspect the dirty worktree, existing `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, `.codex/`, `.agents/skills/`, project docs, and any wrapper workspace around the Git repo. Never print config values or credentials.

Do not write until the boundary is clear:

- A normal repo usually owns its root `AGENTS.md`.
- A private wrapper workspace containing a client repo keeps private state outside that repo. Launch Codex from the wrapper; do not copy internal files into the client repo.
- A monorepo may need nested `AGENTS.md` only where rules actually differ.
- An existing cross-agent canon must be preserved; add thin entrypoints instead of competing copies.

Preserve unrelated user changes. Do not edit global config, enable memories, register MCP, add hooks, or configure subagents unless the request authorizes that scope.

## 2. Classify every item by owner

Read [references/architecture.md](references/architecture.md) before designing or changing the structure. Use its ownership matrix and project-shape patterns.

Separate at least:

- global personal behavior;
- stable project conventions and verification commands;
- mutable project state, blockers, authorization, and NEXT;
- reusable workflows;
- custom subagent roles and orchestration policy;
- external capabilities;
- mechanical enforcement;
- shell permission policy;
- generated recall and historical evidence.

One fact gets one canonical owner. Other entrypoints may route to it but must not restate changing facts.

## 3. Design the minimum viable agent layer

Prefer this order:

1. Keep global personal defaults in `~/.codex/AGENTS.md` and global reusable workflows in user skills.
2. Put short, always-required project guidance in the applicable `AGENTS.md`.
3. Put mutable status in one explicit LIVE STATE file or section. Include updated time, phase, completed work, blockers, NEXT, Git state, and forbidden external actions.
4. Route deep stable detail to existing architecture, runbook, contract, scope, audit, or decision files.
5. Use a skill for a repeatable procedure, custom agents for narrow delegated roles, MCP for live external systems, hooks/CI for enforceable behavior, and `.rules` only for command approval policy.
6. Treat native Codex memories as generated recall, never as the sole source of mandatory rules or current project state.

Keep critical safety and verification rules directly in the auto-loaded `AGENTS.md`; a bare link is not enough for a rule that must never be missed. Keep detailed procedures out of broad global scope.

Do not create local copies of global skills or MCP configuration to fix a visibility problem. Diagnose scope, trust, CWD, and actual injection first.

For parent/subagent workflows, delegate only independent, bounded work. Prefer read-heavy roles such as exploration, documentation research, test analysis, or review. Give each custom agent a clear job, output contract, and the narrowest useful sandbox. Avoid concurrent edits to overlapping files.

## 4. Implement safely

Use the repository's existing conventions and files where possible. When new files are justified:

- keep `AGENTS.md` concise and project-specific;
- use nested `AGENTS.md` only for a genuine subtree override;
- use a vendor-neutral project canon when several agents must share state;
- make `CLAUDE.md` or other vendor files thin adapters unless one is already the established canon;
- keep private client-management notes outside a client Git repo;
- place reusable personal custom agents in `~/.codex/agents/` and project roles in `.codex/agents/`;
- keep project custom agents model-agnostic unless a pinned model is an intentional project requirement;
- add a deterministic context check only when the project is complex enough to drift.

Avoid mass migration in one edit. For a scattered mature environment, first produce a source-to-owner map, then move one domain at a time with checks after each batch.

## 5. Validate actual behavior

Run the inspector again and resolve all high-confidence failures. Then verify:

1. **Instruction injection:** inspect the newest `~/.codex/sessions/.../*.jsonl` for the injected `AGENTS.md` blocks and CWD. Do not rely only on asking the model which file it loaded; injected text may not include its source path.
2. **Cold start:** start a clean read-only session from the intended CWD and ask it to report project root, Git boundary, phase, NEXT, blockers, forbidden actions, canonical sources, global capability inheritance, custom agents, and verification commands.
3. **Compaction recovery:** ensure mutable state is recoverable from disk after `compact`; use a `PostCompact` or `SessionStart` hook only when deterministic re-anchoring is necessary and trusted.
4. **Capability visibility:** compare configured global MCP/skills/custom agents with what the session actually exposes. Fix registration/trust rather than cloning config locally.
5. **Delegation:** ask the parent to delegate one read-only bounded task to the intended custom agent, inspect the returned evidence, and confirm the parent integrates it instead of merely repeating it.
6. **Publication boundary:** confirm private workspace files are not tracked by the client repo.

If a fresh agent guesses, reads the wrong scope, or needs the old chat to continue, the organization is not complete.

## 6. Report the result

Return a compact handoff:

- detected project shape and intended launch CWD;
- canonical owner for each fact type;
- files created or changed;
- global capabilities and custom agents verified;
- warnings or unresolved conflicts;
- cold-start/doctor result;
- one next action.

Do not claim that Codex “will remember” unless injection or memory behavior was verified from artifacts.
