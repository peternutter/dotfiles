#!/usr/bin/env bash
# Refresh the local Modal docs + pricing for this skill.
#   - docs (llms-full.txt) + section map: fully automatic.
#   - pricing.json: NOT auto-overwritten (page is HTML, fragile to parse). We curl
#     the pricing page, print the $/hr lines, and diff against pricing.json so a
#     human/agent can reconcile the numbers by hand.
# Run from anywhere: bash ~/.claude/skills/modal/refresh.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REF="$HERE/references"

echo "== docs =="
curl -fsSL https://modal.com/llms-full.txt -o "$REF/modal-docs-full.txt"
curl -fsSL https://modal.com/llms.txt       -o "$REF/modal-docs-index.txt"
# Modal's docs contain example credentials (a fake Docker PAT) that trip GitHub push
# protection. Redact the patterns so the refreshed docs stay committable.
sed -i -E 's/dckr_pat_[A-Za-z0-9_-]+/dckr_pat_EXAMPLE_TOKEN_REDACTED/g' "$REF/modal-docs-full.txt"
grep -nE '^# |^## ' "$REF/modal-docs-full.txt" > "$REF/section-map.txt"
echo "  modal-docs-full.txt: $(wc -l < "$REF/modal-docs-full.txt") lines"
echo "  section-map.txt:     $(wc -l < "$REF/section-map.txt") sections"
echo "  -> if section line ranges shifted a lot, update the table in SKILL.md."

echo "== pricing (manual reconcile) =="
echo "  current pricing.json (as_of $(python3 -c "import json,sys;print(json.load(open('$REF/pricing.json'))['_meta']['as_of'])")):"
python3 -c "import json;d=json.load(open('$REF/pricing.json'))['gpu_per_hour'];[print(f'    {k}: \${v}/hr') for k,v in d.items()]"
echo "  live lines from https://modal.com/pricing (grep for prices -- eyeball + edit pricing.json):"
curl -fsSL https://modal.com/pricing 2>/dev/null \
  | grep -oE '\$[0-9]+\.[0-9]+(/(sec|hr|hour))?' | sort -u | sed 's/^/    /' || echo "    (fetch failed; open the page manually)"
echo "  -> edit references/pricing.json and bump _meta.as_of if anything changed."
echo "done."
