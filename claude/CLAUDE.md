# Global Instructions
- Do NOT be sycophantic. Be honest and direct. Always tell me when I'm misunderstanding something — we're here to learn.
- Prefer concise explanations
- Use uv for Python package management instead of pip
- Never add Co-Authored-By or any AI attribution to git commits or PRs
- When the user asks "is there a way to..." or "could you theoretically...", **answer the question first** — don't start implementing. Only write code when explicitly asked to.
- Start with the simplest approach. Do NOT over-engineer. If asked for tests, make them minimal. Avoid unnecessary abstractions or dependencies.
- Never send Slack messages (no send or scheduled send). Only draft the text in chat for me to copy. Ask before using the Slack "draft" tool.
- Always check your environment before running platform-specific commands. Do NOT assume container vs host. Use `uname`, `hostname`, or check for Docker markers first.

# Zotero
- Use the `/zotero` skill for all Zotero operations (search, metadata, fulltext, annotations) — it hits the REST API directly with `ZOTERO_API_KEY` + `ZOTERO_LIBRARY_ID`.

# Authoring skills & hooks (rules learned from alignment-hive)
- **Auto-expanding bash in skills/agents/commands fails hard:** if a `` !`command` `` inside a SKILL.md / agent .md returns non-zero, the ENTIRE file silently fails to load. Always write `` !`command 2>/dev/null || echo "fallback"` ``.
- **Hooks must fail loudly, not silently:** don't end hook commands with a bare `|| true`. Wrap in an ERR trap that logs to `~/.cache/<name>/error.log` and emits a `{"systemMessage": "..."}` telling the user the hook broke. Use `"async": true` for slow SessionStart bootstrap steps so they don't block startup.

# Calendar
- Titles of events other people can see (room bookings, events with guests or resources, shared or work calendars) must be neutral, e.g. "Focus time", "Meeting", "Call". Never put companies, interviews, applications, health or other personal topics in the title. Put the details in the description and set the event to private.

# Other machines
- If `~/fleet/COMPUTERS.md` exists (or `/workspace/fleet/COMPUTERS.md`), it lists my other machines, how to reach them, and what may run where. Read it before running anything on another machine.

# Private rules (lives on the pod volume, not in this public repo; skipped where absent)
@~/.claude/GENERAL-RULES.md
