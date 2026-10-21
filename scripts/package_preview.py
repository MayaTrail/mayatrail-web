#!/usr/bin/env python3
"""
Build the two things the site gets shared as before it is deployed anywhere.

    python scripts/build_blog.py --drafts      # first, if drafts should show
    python scripts/package_preview.py ../out   # writes both artefacts there

  <out>/mayatrail-website-preview-<date>.zip
      The whole of site/ plus share/READ-ME-FIRST.txt at the root. Unzip,
      open index.html. The blog is in it, so the posts are readable.

  <out>/mayatrail-site-<date>.html
      The home page as one file: the stylesheet inlined and the favicon
      embedded, so it survives being attached to an email on its own. The
      field-notes rows lose their links there, because a post is its own
      document and is not in the file. Google Fonts is the only thing it
      still fetches; without a network the type falls back to system faces.

Nothing here writes into site/. The source of truth is the repository, and
these are disposable copies of it.
"""

from __future__ import annotations

import base64
import re
import shutil
import sys
import zipfile
from datetime import date
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SITE = _REPO_ROOT / "site"
_README = _REPO_ROOT / "share" / "READ-ME-FIRST.txt"


def build_zip(out_dir: Path, stamp: str) -> Path:
    """site/ plus the read-me, zipped with the site at the root."""
    staging = out_dir / f"_staging-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(_SITE, staging)
    if _README.exists():
        shutil.copy2(_README, staging / "READ-ME-FIRST.txt")

    archive = out_dir / f"mayatrail-website-preview-{stamp}.zip"
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(staging).as_posix())
    shutil.rmtree(staging)
    return archive


def build_single_file(out_dir: Path, stamp: str) -> Path:
    """The home page, standing on its own."""
    page = (_SITE / "index.html").read_text(encoding="utf-8")
    css = (_SITE / "mayatrail-base.css").read_text(encoding="utf-8")
    icon = base64.b64encode((_SITE / "favicon.svg").read_bytes()).decode("ascii")

    page = page.replace(
        '<link rel="stylesheet" href="mayatrail-base.css">',
        "<style>\n/* mayatrail-base.css, inlined so this file stands alone */\n"
        + css
        + "</style>",
    )
    page = page.replace(
        '<link rel="icon" type="image/svg+xml" href="favicon.svg">',
        f'<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{icon}">',
    )
    page = page.replace(
        "<title>MayaTrail - Cloud attack emulation</title>",
        "<title>MayaTrail - Cloud attack emulation (preview)</title>",
    )

    # The posts are separate documents and are not here, so nothing in this
    # file pretends to link to them.
    page = re.sub(r'<a class="nrow" href="blog/[^"]*">', '<span class="nrow">', page)
    page = page.replace(
        '<span class="nrow__go">Read &rarr;</span>\n      </a>', "</span>"
    )
    page = re.sub(
        r'    <div class="notes__after">.*?</div>\n',
        '    <p class="sw__hint">Posts open in the full build; this single file'
        " holds the home page only.</p>\n",
        page,
        flags=re.DOTALL,
    )
    page = page.replace('<a href="blog/feed.xml">', "<span>")

    header = (
        "<!--\n"
        "  MayaTrail home page, single-file preview.\n"
        "  Stylesheet inlined, favicon embedded, nothing fetched from disk.\n"
        "  The blog posts are separate documents; use the zip to read them.\n"
        "-->\n"
    )
    single = out_dir / f"mayatrail-site-{stamp}.html"
    single.write_text(header + page, encoding="utf-8")

    leftovers = sorted(
        set(
            re.findall(
                r'(?:src|href)="(?!https?:|mailto:|#|data:)([^"]+)"', header + page
            )
        )
    )
    if leftovers:
        print(f"warn   single file still references {leftovers}", file=sys.stderr)
    return single


def main(argv: list[str]) -> int:
    out_dir = Path(argv[1]) if len(argv) > 1 else _REPO_ROOT.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()

    for artefact in (build_zip(out_dir, stamp), build_single_file(out_dir, stamp)):
        print(f"ok     {artefact}  {artefact.stat().st_size / 1024:.1f} KB")
    print("\nRun scripts/check_site.py over site/ before sending either one.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
