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

### Creating Annotations

Annotations are child items of the **PDF attachment** (not the parent bibliographic item).

**Find the PDF attachment key first:**
```bash
curl -s "https://api.zotero.org/users/${ZOTERO_LIBRARY_ID}/items/<PARENT_KEY>/children?format=json" \
  -H "Zotero-API-Key: ${ZOTERO_API_KEY}" \
  | jq '.[] | select(.data.contentType == "application/pdf") | {key: .key, filename: .data.filename}'
```

**Create annotations (POST up to 50 per request):**
```bash
curl -s -X POST "https://api.zotero.org/users/${ZOTERO_LIBRARY_ID}/items" \
  -H "Zotero-API-Key: ${ZOTERO_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '[{
    "itemType": "annotation",
    "parentItem": "PDF_ATTACHMENT_KEY",
    "annotationType": "note",
    "annotationComment": "Your comment here",
    "annotationColor": "#5fb236",
    "annotationPageLabel": "4",
    "annotationSortIndex": "00003|000000|00000",
    "annotationPosition": "{\"pageIndex\": 3, \"rects\": [[450, 750, 472, 772]]}",
    "tags": [{"tag": "reading-guide"}]
  }]'
```

**Critical: `annotationSortIndex` is REQUIRED (NOT NULL constraint).**
Format: `PPPPP|TTTTTT|OOOOO` (pageIndex zero-padded 5 digits | text char offset 6 digits | y-offset 5 digits).

**Annotation types:** `note` (sticky note), `highlight` (text highlight), `text` (inline text annotation)

**Colors for reading guides:**
- Green (`#5fb236`) = MUST READ
- Yellow (`#ffd400`) = SKIM/SKIP
- Red (`#ff6666`) = most critical

**Delete annotations:**
```bash
curl -s -X DELETE "https://api.zotero.org/users/${ZOTERO_LIBRARY_ID}/items?itemKey=KEY1,KEY2" \
  -H "Zotero-API-Key: ${ZOTERO_API_KEY}" \
  -H "If-Unmodified-Since-Version: VERSION"
```
Get the version from the `last-modified-version` response header of a GET request.

### Gotchas
- `parentItem` must be the PDF attachment key, NOT the parent bibliographic item key
- PDFs with `linkMode: imported_file` may not be downloadable via API (local-only storage)
- File uploads require storage quota (Peter's is currently full)
- Annotations are metadata-only and always sync regardless of file storage quota
