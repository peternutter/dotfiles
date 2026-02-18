# Global Instructions
- Prefer concise explanations
- Use uv for Python package management instead of pip

# Zotero MCP
The Zotero MCP (`zotero-mcp` via uvx) provides three tools: `zotero_search_items`, `zotero_item_metadata`, and `zotero_item_fulltext`.

**Limitation:** The MCP tools do NOT expose annotations (highlights, notes, underlines). To fetch annotations, query the Zotero REST API directly for child items:
```bash
source ~/.env
curl -s "https://api.zotero.org/users/${ZOTERO_LIBRARY_ID}/items/<ITEM_KEY>/children?format=json" \
  -H "Zotero-API-Key: ${ZOTERO_API_KEY}" \
  | jq '[.[] | select(.data.itemType == "annotation") | {
      page: .data.annotationPageLabel,
      type: .data.annotationType,
      text: .data.annotationText,
      comment: .data.annotationComment,
      color: .data.annotationColor
    }]'
```
Color meanings in Peter's annotations: green (`#5fb236`) = vocabulary/definitions, yellow (`#ffd400`) = thematic highlights/summaries, red (`#ff6666`) = standout passages.
