# Global Instructions
- Prefer concise explanations
- Use uv for Python package management instead of pip
- Never add Co-Authored-By or any AI attribution to git commits or PRs
- When the user asks "is there a way to..." or "could you theoretically...", **answer the question first** — don't start implementing. Only write code when explicitly asked to.
- Start with the simplest approach. Do NOT over-engineer. If asked for tests, make them minimal. Avoid unnecessary abstractions or dependencies.
- Always check your environment before running platform-specific commands. Do NOT assume container vs host. Use `uname`, `hostname`, or check for Docker markers first.

# Zotero
- MCP tools: `zotero_search_items`, `zotero_item_metadata`, `zotero_item_fulltext`
- For annotations use `/zotero-annotations <query>` (MCP doesn't expose them)
