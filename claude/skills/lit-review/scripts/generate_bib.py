# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Generate references.bib from deduplicated paper metadata.

Citekeys follow firstauthorYEARkeyword (lowercase), e.g. cloud2024gradient.
arXiv papers -> @misc with eprint; papers with a DOI/venue -> @article;
LW/AF posts -> @misc with howpublished.

Usage:
    uv run generate_bib.py --papers deduplicated.json --output references.bib
"""

import argparse
import json
import re
import sys
from pathlib import Path

STOPWORDS = {
    "a", "an", "the", "on", "of", "for", "and", "in", "to", "with", "via",
    "from", "at", "by", "is", "are", "do", "does", "can", "how", "what", "why",
    "towards", "toward",
}


def author_names(paper: dict) -> list[str]:
    """Normalize authors to a list of name strings across source formats."""
    authors = paper.get("authors") or []
    names = []
    for a in authors:
        if isinstance(a, dict):
            name = a.get("name", "")
        else:
            name = str(a)
        if name:
            names.append(name)
    if not names and paper.get("author"):  # LW/AF posts
        names = [str(paper["author"])]
    return names


def first_author_surname(names: list[str]) -> str:
    if not names:
        return "anon"
    surname = names[0].split()[-1] if names[0].split() else "anon"
    return re.sub(r"[^a-z]", "", surname.lower()) or "anon"


def title_keyword(title: str) -> str:
    for word in re.findall(r"[A-Za-z]+", title.lower()):
        if word not in STOPWORDS and len(word) > 2:
            return word
    return "untitled"


def bib_escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "").replace("}", "").replace("%", r"\%").replace("&", r"\&")


def make_entry(paper: dict, citekey: str) -> str:
    title = bib_escape(paper.get("title", "Untitled"))
    names = author_names(paper)
    year = paper.get("year") or (paper.get("published") or "")[:4] or "n.d."
    url = paper.get("url") or paper.get("arxiv_id") or ""
    fields = [f"  title = {{{title}}}"]
    if names:
        fields.append("  author = {" + " and ".join(bib_escape(n) for n in names) + "}")
    fields.append(f"  year = {{{year}}}")

    source = paper.get("source", "")
    arxiv_id = paper.get("arxiv_id") or ""
    # arxiv_id may be a full entry URL (arxiv lib) or a bare id (S2)
    bare_arxiv = ""
    if arxiv_id:
        bare_arxiv = re.sub(r".*arxiv\.org/abs/", "", arxiv_id).strip("/")
        bare_arxiv = re.sub(r"v\d+$", "", bare_arxiv)

    if source in ("lesswrong", "alignment_forum", "lesswrong_af"):
        entry_type = "misc"
        platform = "Alignment Forum" if "alignmentforum" in (url or "") else "LessWrong"
        fields.append(f"  howpublished = {{{platform}}}")
    elif bare_arxiv:
        entry_type = "misc"
        fields.append(f"  eprint = {{{bare_arxiv}}}")
        fields.append("  archiveprefix = {arXiv}")
    elif paper.get("doi"):
        entry_type = "article"
        fields.append(f"  doi = {{{paper['doi']}}}")
    else:
        entry_type = "misc"

    if url:
        fields.append(f"  url = {{{url}}}")

    return f"@{entry_type}{{{citekey},\n" + ",\n".join(fields) + "\n}\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--papers", type=Path, required=True, help="deduplicated.json")
    parser.add_argument("--output", type=Path, required=True, help="references.bib path")
    args = parser.parse_args()

    with open(args.papers) as f:
        papers = json.load(f)

    used: dict[str, int] = {}
    entries = []
    for paper in papers:
        if not paper.get("title"):
            continue
        names = author_names(paper)
        year = paper.get("year") or (paper.get("published") or "")[:4] or "nd"
        base = f"{first_author_surname(names)}{year}{title_keyword(paper.get('title', ''))}"
        # Disambiguate collisions with a, b, c...
        n = used.get(base, 0)
        used[base] = n + 1
        citekey = base if n == 0 else f"{base}{chr(ord('a') + n)}"
        entries.append(make_entry(paper, citekey))

    args.output.write_text("\n".join(entries), encoding="utf-8")
    print(f"Wrote {len(entries)} entries to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
