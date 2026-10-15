#!/usr/bin/env python3
"""Render the IR playbook Markdown embedded in site/playbook.html to static HTML.

The page used to ship the Markdown as an inert <script type="text/plain"> block
and compile it in the visitor's browser with marked.js pulled from jsdelivr.
That made the page blank without JavaScript, blank to crawlers, and dependent on
a third-party CDN in the critical path.

This renders the same source with Python-Markdown at build time, exactly as the
blog is built, and writes the result into the #md-body container. The Markdown
block stays in the page as the source of truth, so the step is idempotent: run
it twice and you get the same output.

Usage:
    python scripts/build_playbook.py            # render site/playbook.html
    python scripts/build_playbook.py --check    # non-zero exit if out of date
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "site" / "playbook.html"

SOURCE_RE = re.compile(
    r'(<script type="text/plain" id="md-source">)(.*?)(</script>)', re.S
)
BODY_RE = re.compile(r'(<div class="md" id="md-body">)(.*?)(</div>)', re.S)

# Heading text fragment -> the anchor id the sidebar TOC links to. The browser
# script used to derive these after render; doing it here keeps the anchors
# present in the served HTML.
ANCHORS = [
    ("classification", "classification"),
    ("preparation", "preparation"),
    ("identification", "identification"),
    ("containment", "containment"),
    ("eradication", "eradication"),
    ("recovery", "recovery"),
    ("lessons", "lessons"),
    ("appendix", "appendix"),
]


def render(md_source: str) -> str:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        output_format="html5",
    )
    out = md.convert(md_source)

    # Give the h1/h2 headings the ids the TOC points at.
    def anchor(m: re.Match) -> str:
        tag, attrs, text = m.group(1), m.group(2), m.group(3)
        if "id=" in attrs:
            return m.group(0)
        flat = re.sub(r"[^a-z]+", "-", html.unescape(text).lower())
        for key, slug in ANCHORS:
            if key in flat:
                return "<%s%s id=\"%s\">%s</%s>" % (tag, attrs, slug, text, tag)
        return m.group(0)

    return re.sub(r"<(h[12])([^>]*)>(.*?)</\1>", anchor, out, flags=re.S)


def build(check_only: bool = False) -> int:
    page = PAGE.read_text(encoding="utf-8")

    src_match = SOURCE_RE.search(page)
    if not src_match:
        print("error: no #md-source block in %s" % PAGE, file=sys.stderr)
        return 1
    body_match = BODY_RE.search(page)
    if not body_match:
        print("error: no #md-body container in %s" % PAGE, file=sys.stderr)
        return 1

    md_source = html.unescape(src_match.group(2))
    rendered = "\n" + render(md_source) + "\n"

    if body_match.group(2) == rendered:
        print("playbook.html already up to date")
        return 0
    if check_only:
        print("error: playbook.html is stale - run scripts/build_playbook.py",
              file=sys.stderr)
        return 1

    page = page[:body_match.start(2)] + rendered + page[body_match.end(2):]
    PAGE.write_text(page, encoding="utf-8", newline="")
    print("rendered %d chars of Markdown into playbook.html" % len(md_source))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero if the rendered HTML is stale")
    args = parser.parse_args()
    return build(check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
