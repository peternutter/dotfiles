---
name: zotero-annotations
description: Fetch and display annotations (highlights, notes, underlines) from a Zotero item. Use when the user asks about their Zotero notes, annotations, highlights, or reading notes.
argument-hint: <search query or item key>
allowed-tools: Bash, Read
---

## Zotero Annotations

Fetch annotations from a Zotero library item.

### Steps

1. **Find the item.** If `$ARGUMENTS` looks like an item key (8 uppercase alphanumeric chars), use it directly. Otherwise, use the `zotero_search_items` MCP tool to search for matching items.

2. **Fetch annotations.** The Zotero MCP does NOT expose annotations — use the REST API directly:
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
    }] | sort_by(.page | tonumber)'
```

3. **Display annotations** grouped by page, with:
   - The annotation type (highlight, underline, note)
   - The highlighted/underlined text (if any)
   - The user's comment (if any)
   - Color context: green (`#5fb236`) = vocabulary/definitions, yellow (`#ffd400`) = thematic highlights/summaries, red (`#ff6666`) = standout passages

4. If no annotations are found, the item may be a top-level parent. Try getting its children first to find the PDF attachment, then fetch annotations from that attachment key.
