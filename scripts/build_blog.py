#!/usr/bin/env python3
"""
Render blog/*.md into static pages under site/blog/.

    python scripts/build_blog.py                 # publish
    python scripts/build_blog.py --drafts        # include drafts, for preview
    python scripts/build_blog.py --clean         # remove generated output first

Rendering happens here, at build time, rather than in the visitor's browser. A
blog exists to be indexed, and a page whose text only appears after JavaScript
runs indexes badly. The output is plain HTML on the same nginx that serves the
rest of the site: no runtime dependency, no client-side markdown library, and
the posts stay authored as Markdown.

Everything under site/blog/ is generated and git-ignored. The sources are the
Markdown files in blog/, and this script is the only thing that writes the
output directory.

Each post carries YAML front matter:

    ---
    title: What a run actually leaves behind
    date: 2026-09-10
    description: One sentence for the index page, the meta tag and the feed.
    author: MayaTrail
    tags: [detection-engineering, aws]
    draft: true
    ---

`title` and `date` are required; everything else is optional. `draft: true`
keeps a post out of the build unless --drafts is passed, so an unfinished piece
can sit in the repository without shipping.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

try:
    import markdown
    import yaml
except ImportError:  # pragma: no cover - the message is the whole point
    sys.exit(
        "The blog build needs Python-Markdown and PyYAML:\n"
        "    pip install -r requirements-blog.txt"
    )

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SOURCE_DIR = _REPO_ROOT / "blog"
_OUTPUT_DIR = _REPO_ROOT / "site" / "blog"
_SITE_URL = "https://mayatrail.tech"

_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Markdown extensions worth having for a security blog: fenced code with
# highlighting, tables for coverage grids, footnotes for citations, and
# attr_list so a post can mark up an element without dropping to raw HTML.
_EXTENSIONS = [
    "extra",          # tables, fenced_code, footnotes, attr_list, def_list, abbr
    "codehilite",
    "sane_lists",
    "smarty",
    "toc",
]
_EXTENSION_CONFIGS = {
    "codehilite": {"css_class": "highlight", "guess_lang": False},
    "toc": {"permalink": False},
    "smarty": {"smart_dashes": True, "smart_quotes": True},
}


@dataclass
class Post:
    """One rendered post."""

    slug: str
    title: str
    published: date
    description: str
    author: str
    tags: list[str]
    draft: bool
    body_html: str
    reading_minutes: int

    @property
    def url(self) -> str:
        return f"/blog/{self.slug}/"

    @property
    def iso_date(self) -> str:
        return self.published.isoformat()

    @property
    def display_date(self) -> str:
        # Cross-platform: %-d is glibc-only and %#d is Windows-only, so the day
        # is formatted by hand rather than by strftime.
        return f"{self.published.day} {self.published.strftime('%B %Y')}"


def _parse_front_matter(text: str, path: Path) -> tuple[dict, str]:
    """Split a post into its metadata and its Markdown body."""
    match = _FRONT_MATTER.match(text)
    if not match:
        raise ValueError(f"{path.name}: no YAML front matter (a --- block at the top)")
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"{path.name}: front matter is not valid YAML: {exc}") from exc
    if not isinstance(meta, dict):
        raise ValueError(f"{path.name}: front matter must be a mapping")
    return meta, text[match.end():]


def _as_date(value: object, path: Path) -> date:
    """Accept a YAML date or an ISO string, and say so clearly when neither."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError(f"{path.name}: date {value!r} is not ISO (YYYY-MM-DD)") from exc
    raise ValueError(f"{path.name}: front matter needs a date")


def _reading_minutes(markdown_body: str) -> int:
    """Rough reading time. Deliberately coarse: it is a hint, not a promise."""
    words = len(re.findall(r"\b\w+\b", markdown_body))
    return max(1, round(words / 220))


def load_post(path: Path) -> Post:
    """Parse and render one Markdown file."""
    meta, body = _parse_front_matter(path.read_text(encoding="utf-8"), path)

    title = str(meta.get("title", "")).strip()
    if not title:
        raise ValueError(f"{path.name}: front matter needs a title")

    renderer = markdown.Markdown(
        extensions=_EXTENSIONS, extension_configs=_EXTENSION_CONFIGS, output_format="html"
    )
    body_html = renderer.convert(body)

    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]

    return Post(
        slug=str(meta.get("slug") or path.stem).strip(),
        title=title,
        published=_as_date(meta.get("date"), path),
        description=str(meta.get("description", "")).strip(),
        author=str(meta.get("author", "MayaTrail")).strip(),
        tags=[str(tag) for tag in tags],
        draft=bool(meta.get("draft", False)),
        body_html=body_html,
        reading_minutes=_reading_minutes(body),
    )


# --------------------------------------------------------------------------
# Templates. Kept as functions rather than a template engine: the site has no
# package manager, and three pages do not justify one.
# --------------------------------------------------------------------------

def _nav(depth: int) -> str:
    """Site masthead. `depth` is how many directories deep the page sits."""
    up = "../" * depth
    links = [
        ("index.html", "Platform"),
        ("index.html#services", "Services"),
        ("index.html#pricing", "Pricing"),
    ]
    items = "".join(f'\n      <a href="{up}{href}">{label}</a>' for href, label in links)
    return f"""<nav class="nav">
  <div class="nav-inner">
    <a href="{up}index.html" class="brand" style="margin-right:auto;">
      <svg class="brand-mark" width="24" height="24" viewBox="0 0 120 120" aria-hidden="true"><line x1="60" y1="20" x2="22" y2="90" stroke="#6aa8ff" stroke-opacity=".45" stroke-width="2.6" stroke-linecap="round"/><line x1="60" y1="20" x2="98" y2="90" stroke="#6aa8ff" stroke-opacity=".45" stroke-width="2.6" stroke-linecap="round"/><line x1="22" y1="90" x2="98" y2="90" stroke="#6aa8ff" stroke-opacity=".45" stroke-width="2.6" stroke-linecap="round"/><line x1="60" y1="20" x2="60" y2="64" stroke="#6aa8ff" stroke-opacity=".45" stroke-width="2.6" stroke-linecap="round"/><line x1="22" y1="90" x2="60" y2="64" stroke="#6aa8ff" stroke-opacity=".45" stroke-width="2.6" stroke-linecap="round"/><line x1="98" y1="90" x2="60" y2="64" stroke="#6aa8ff" stroke-opacity=".45" stroke-width="2.6" stroke-linecap="round"/><circle cx="22" cy="90" r="7" fill="#6aa8ff"/><circle cx="98" cy="90" r="7" fill="#6aa8ff"/><circle cx="60" cy="64" r="6" fill="#6aa8ff"/><circle cx="60" cy="20" r="7" fill="#ff4b6e"/></svg>
      <span class="brand-wm"><span class="bm-maya">Maya</span><span class="bm-trail">Trail</span></span>
    </a>
    <div class="nav-links">{items}
      <a href="{up}blog/" class="active">Blog</a>
    </div>
    <a class="nav-gh" href="https://github.com/MayaTrail/step1">GitHub</a>
    <a class="nav-cta" style="white-space:nowrap;" href="mailto:admin@mayatrail.tech?subject=MayaTrail%20access%20request">Request access</a>
  </div>
</nav>"""


def _footer(depth: int) -> str:
    up = "../" * depth
    links = [
        ("index.html", "Platform"), ("index.html#services", "Services"),
        ("index.html#pricing", "Pricing"),
    ]
    items = "".join(f'\n    <a href="{up}{href}">{label}</a>' for href, label in links)
    return f"""<footer>
  <span><b style="color:var(--ink-2)">© 2026 MAYATRAIL TECH</b> · v0.1 <span class="note">use only in isolated test accounts</span></span>
  <div class="links">{items}
    <a href="{up}blog/">Blog</a>
    <a class="gh" href="https://github.com/MayaTrail/step1">GitHub ↗</a>
  </div>
</footer>"""


def _head(title: str, description: str, depth: int, canonical: str, extra: str = "") -> str:
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}" />
<link rel="canonical" href="{html.escape(canonical)}" />
<meta property="og:type" content="article" />
<meta property="og:title" content="{html.escape(title)}" />
<meta property="og:description" content="{html.escape(description)}" />
<meta property="og:url" content="{html.escape(canonical)}" />
<meta name="twitter:card" content="summary_large_image" />
<link rel="alternate" type="application/rss+xml" title="MayaTrail blog" href="{up}blog/feed.xml" />
<link rel="icon" type="image/svg+xml" href="{up}favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap">
<link rel="stylesheet" href="{up}mayatrail-base.css">
<link rel="stylesheet" href="{up}mayatrail-blog.css">
{extra}</head>
<body>"""


def render_index(posts: list[Post]) -> str:
    """The post list at /blog/."""
    if posts:
        entries = "\n".join(
            f"""      <a class="entry" href="{post.slug}/">
        <span class="entry__meta">
          <time datetime="{post.iso_date}">{post.display_date}</time>
          <span class="entry__read">{post.reading_minutes} min read</span>
        </span>
        <span class="entry__body">
          <span class="entry__title">{html.escape(post.title)}</span>
          {f'<span class="entry__desc">{html.escape(post.description)}</span>' if post.description else ''}
        </span>
      </a>"""
            for post in posts
        )
        listing = f'    <div class="entries">\n{entries}\n    </div>'
    else:
        listing = """    <div class="empty">
      <p>No posts yet. Field notes on cloud detection engineering will land here.</p>
      <a class="btn outline" href="../index.html">Back to the platform</a>
    </div>"""

    return f"""{_head(
        "Field notes - MayaTrail",
        "Notes on cloud attack emulation and detection engineering from the MayaTrail team.",
        depth=1,
        canonical=f"{_SITE_URL}/blog/",
    )}
{_nav(1)}

<main>
  <section class="s blog-head">
    <h1 class="h-1">Field notes.</h1>
    <p class="lede">What we learn running documented cloud campaigns against real AWS accounts, and what the detections do about it.</p>
    <a class="more" href="feed.xml">Subscribe by RSS <span class="arrow">→</span></a>
  </section>

  <section class="s blog-list">
{listing}
  </section>

{_footer(1)}
</main>
</body>
</html>
"""


def render_post(post: Post, newer: Post | None, older: Post | None) -> str:
    """One post at /blog/<slug>/."""
    tags = ""
    if post.tags:
        pills = "".join(f'<span class="pill">{html.escape(tag)}</span>' for tag in post.tags)
        tags = f'\n      <div class="post__tags">{pills}</div>'

    around = []
    if older:
        around.append(
            f'<a class="around__link" href="../{older.slug}/">'
            f'<span class="around__dir">Older</span>'
            f'<span class="around__title">{html.escape(older.title)}</span></a>'
        )
    if newer:
        around.append(
            f'<a class="around__link around__link--next" href="../{newer.slug}/">'
            f'<span class="around__dir">Newer</span>'
            f'<span class="around__title">{html.escape(newer.title)}</span></a>'
        )
    around_html = (
        f'\n  <nav class="around" aria-label="More posts">\n    {"".join(around)}\n  </nav>'
        if around
        else ""
    )

    # Structured data so a post shows as an article rather than a generic page.
    schema = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BlogPosting",
"headline":{_json(post.title)},"datePublished":"{post.iso_date}",
"description":{_json(post.description)},
"author":{{"@type":"Organization","name":{_json(post.author)}}},
"publisher":{{"@type":"Organization","name":"MayaTrail"}},
"mainEntityOfPage":"{_SITE_URL}{post.url}"}}
</script>
"""

    return f"""{_head(
        f"{post.title} - MayaTrail",
        post.description or post.title,
        depth=2,
        canonical=f"{_SITE_URL}{post.url}",
        extra=schema,
    )}
{_nav(2)}

<main>
  <article class="s post">
    <header class="post__head">
      <a class="post__back" href="../">Field notes</a>
      <h1 class="h-1">{html.escape(post.title)}</h1>
      <div class="post__meta">
        <time datetime="{post.iso_date}">{post.display_date}</time>
        <span>{html.escape(post.author)}</span>
        <span>{post.reading_minutes} min read</span>
      </div>{tags}
    </header>

    <div class="prose">
{post.body_html}
    </div>

    <div class="post__cta">
      <h2 class="h-2">See this in your own AWS.</h2>
      <p>MayaTrail runs a documented cloud campaign inside your account and shows which of your detections fired.</p>
      <a class="btn" href="mailto:admin@mayatrail.tech?subject=MayaTrail%20access%20request">Request access <span class="arrow">→</span></a>
    </div>
  </article>{around_html}

{_footer(2)}
</main>
</body>
</html>
"""


def _json(value: str) -> str:
    """Minimal JSON string escaping for the ld+json block."""
    import json

    return json.dumps(value or "")


def render_feed(posts: list[Post]) -> str:
    """RSS 2.0. A technical audience still reads feeds."""
    items = "\n".join(
        f"""    <item>
      <title>{html.escape(post.title)}</title>
      <link>{_SITE_URL}{post.url}</link>
      <guid isPermaLink="true">{_SITE_URL}{post.url}</guid>
      <pubDate>{format_datetime(datetime.combine(post.published, datetime.min.time(), timezone.utc))}</pubDate>
      <description>{html.escape(post.description or post.title)}</description>
    </item>"""
        for post in posts
    )
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>MayaTrail - Field notes</title>
    <link>{_SITE_URL}/blog/</link>
    <description>Notes on cloud attack emulation and detection engineering.</description>
    <language>en</language>
{items}
  </channel>
</rss>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render blog/*.md into site/blog/.")
    parser.add_argument("--drafts", action="store_true", help="include posts marked draft")
    parser.add_argument("--clean", action="store_true", help="delete site/blog/ first")
    args = parser.parse_args()

    if args.clean and _OUTPUT_DIR.exists():
        shutil.rmtree(_OUTPUT_DIR)

    sources = sorted(_SOURCE_DIR.glob("*.md")) if _SOURCE_DIR.exists() else []
    posts: list[Post] = []
    drafts_held = 0

    for path in sources:
        try:
            post = load_post(path)
        except ValueError as exc:
            print(f"FAIL  {exc}", file=sys.stderr)
            return 1
        if post.draft and not args.drafts:
            drafts_held += 1
            print(f"draft {path.name} (held back; --drafts to preview)")
            continue
        posts.append(post)

    slugs = [post.slug for post in posts]
    duplicates = {slug for slug in slugs if slugs.count(slug) > 1}
    if duplicates:
        print(f"FAIL  duplicate slug(s): {', '.join(sorted(duplicates))}", file=sys.stderr)
        return 1

    # Newest first everywhere: the index, the feed and the prev/next links.
    posts.sort(key=lambda post: (post.published, post.slug), reverse=True)

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (_OUTPUT_DIR / "index.html").write_text(render_index(posts), encoding="utf-8")
    (_OUTPUT_DIR / "feed.xml").write_text(render_feed(posts), encoding="utf-8")

    for position, post in enumerate(posts):
        newer = posts[position - 1] if position > 0 else None
        older = posts[position + 1] if position + 1 < len(posts) else None
        directory = _OUTPUT_DIR / post.slug
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(render_post(post, newer, older), encoding="utf-8")
        print(f"ok    /blog/{post.slug}/  {post.title}")

    held = f", {drafts_held} draft(s) held back" if drafts_held else ""
    print(f"\nBuilt {len(posts)} post(s) into site/blog/{held}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
