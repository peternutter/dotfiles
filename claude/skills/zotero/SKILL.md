---
name: zotero
description: Query the user's Zotero library via the REST API. Use for searching items, fetching metadata/fulltext/annotations, and creating or deleting annotations.
argument-hint: <query or item key>
allowed-tools: Bash, Read
---

## Zotero

All operations hit the Zotero REST API directly. Credentials come from `~/.env`:

```bash
source ~/.env   # ZOTERO_API_KEY, ZOTERO_LIBRARY_ID
BASE="https://api.zotero.org/users/${ZOTERO_LIBRARY_ID}"
AUTH=(-H "Zotero-API-Key: ${ZOTERO_API_KEY}")
```

An item key is 8 uppercase alphanumeric characters (e.g. `ABCD1234`). If `$ARGUMENTS` matches that pattern, treat it as a key; otherwise search.

### Search items

```bash
curl -s "${BASE}/items?q=QUERY&qmode=everything&limit=20&format=json" "${AUTH[@]}" \
  | jq '[.[] | {key, title: .data.title, creators: [.data.creators[]?.lastName], year: (.data.date // "" | capture("(?<y>[0-9]{4})").y // null), itemType: .data.itemType}]'
```

Useful params: `qmode=titleCreatorYear` (narrower), `itemType=journalArticle`, `tag=foo`, `sort=dateAdded&direction=desc`.

### Fetch item metadata

```bash
curl -s "${BASE}/items/<KEY>?format=json" "${AUTH[@]}" | jq '.data'
```

### Fetch fulltext

Fulltext lives on the **PDF attachment**, not the parent record. Find the attachment first:

```bash
curl -s "${BASE}/items/<PARENT_KEY>/children?format=json" "${AUTH[@]}" \
  | jq '.[] | select(.data.contentType == "application/pdf") | .key'
```

Then:

```bash
curl -s "${BASE}/items/<ATTACHMENT_KEY>/fulltext" "${AUTH[@]}" | jq -r '.content'
```

### Fetch annotations

Annotations are child items of the PDF attachment. From a parent record: get children → find PDF attachment → list its children and filter by `itemType == annotation`.

```bash
curl -s "${BASE}/items/<ATTACHMENT_KEY>/children?format=json" "${AUTH[@]}" \
  | jq '[.[] | select(.data.itemType == "annotation") | {
      page: .data.annotationPageLabel,
      type: .data.annotationType,
      text: .data.annotationText,
      comment: .data.annotationComment,
      color: .data.annotationColor
    }] | sort_by(.page | tonumber)'
```

Display grouped by page with type, highlighted text, comment, and color context:
- Green (`#5fb236`) = vocabulary / definitions / must-read
- Yellow (`#ffd400`) = thematic / summary / skim
- Red (`#ff6666`) = standout / most critical

### Create annotations

Annotations attach to the **PDF attachment**, not the parent bibliographic item. Find the attachment key first (see fulltext section).

```bash
curl -s -X POST "${BASE}/items" "${AUTH[@]}" -H "Content-Type: application/json" \
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

POST up to 50 annotations per request.

**`annotationSortIndex` is required** (NOT NULL). Format: `PPPPP|TTTTTT|OOOOO` — pageIndex (5 digits) | text char offset (6 digits) | y-offset (5 digits).

**Types:** `note` (sticky note), `highlight` (text highlight), `text` (inline text).

### Delete annotations

```bash
curl -sI "${BASE}/items/<KEY>" "${AUTH[@]}" | grep -i last-modified-version   # get version

curl -s -X DELETE "${BASE}/items?itemKey=KEY1,KEY2" "${AUTH[@]}" \
  -H "If-Unmodified-Since-Version: VERSION"
```

### Gotchas

- `parentItem` for annotations must be the **PDF attachment key**, not the parent bibliographic record.
- `imported_file` PDFs may not be downloadable via API (local-only storage).
- File uploads require storage quota — annotations (metadata) always sync regardless.
- Fulltext may be empty on unprocessed PDFs; Zotero extracts it asynchronously.
