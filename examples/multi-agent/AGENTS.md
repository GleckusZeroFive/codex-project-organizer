# Agent guidance

- The parent agent owns requirements, authorization, decisions, and the final answer.
- Delegate independent read-heavy work when parallelism materially improves speed or quality.
- Use `explorer` to map code paths and collect file-backed evidence.
- Use `reviewer` after a proposed change to identify correctness, security, and regression risks.
- Wait for requested subagents before finalizing the result.
- Do not let parallel agents edit overlapping files.
- Run the repository's relevant tests before declaring completion.
