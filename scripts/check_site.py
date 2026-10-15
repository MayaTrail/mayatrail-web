#!/usr/bin/env python3
"""
Static checks over the built site, run before anything is shared or merged.

    python scripts/check_site.py                       # check site/
    python scripts/check_site.py site extra.html       # and a loose page

Exit code 0 means clean. Everything here is a rule the site has actually
broken at least once, which is why each one is cheap to run and worth running
every time:

  * em dashes, which the house style does not use
  * copy that was deliberately removed and must not creep back
  * exactly one h1 per page, and no duplicate element ids
  * every relative link and in-page anchor resolves
  * no third-party script tags, because the site ships none
  * no grey fills, no box-shadow: the surfaces are square and transparent
  * no class used in the markup that no stylesheet declares, which is how
    dead CSS and renamed classes get caught

The class check has two deliberate exemptions: .entry__body and .sw__panels
are layout wrappers with no styles of their own.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# Copy that was removed on purpose. If one of these comes back, something was
# reverted or pasted in from an older draft.
RETIRED_COPY = (
    "v0.1",
    "isolated test accounts",
    "rounded up",
    "two weeks",
)
UNSTYLED_BY_DESIGN = ("entry__body", "sw__panels")
GREY_FILLS = ("var(--bg-1)", "var(--bg-2)", "var(--bg-3)")

_failures = 0


def fail(message: str) -> None:
    global _failures
    _failures += 1
    print(f"FAIL  {message}")


class Scan(HTMLParser):
    """One pass over a page, collecting everything the checks need."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.duplicate_ids: list[str] = []
        self.h1_count = 0
        self.classes: set[str] = set()
        self.links: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k: (v or "") for k, v in attrs}
        if tag == "h1":
            self.h1_count += 1
        if attr.get("id"):
            if attr["id"] in self.ids:
                self.duplicate_ids.append(attr["id"])
            self.ids.add(attr["id"])
        self.classes.update(attr.get("class", "").split())
        if tag in ("a", "link") and attr.get("href"):
            self.links.append(attr["href"])
        if tag == "img" and attr.get("src"):
            self.links.append(attr["src"])
        if tag == "script" and attr.get("src"):
            self.scripts.append(attr["src"])


def check_links(page: Path, scan: Scan, own_text: str) -> None:
    """Every relative href resolves, and every #anchor exists in its target."""
    for href in scan.links:
        if href.startswith(("http://", "https://", "mailto:", "data:", "tel:")):
            continue
        target, _, anchor = href.partition("#")
        if target:
            destination = (page.parent / target).resolve()
            if destination.is_dir():
                destination = destination / "index.html"
            if not destination.exists():
                fail(f"{page.name}: broken link {href}")
                continue
            document = destination.read_text(encoding="utf-8")
        else:
            document = own_text
        if anchor and f'id="{anchor}"' not in document:
            fail(f"{page.name}: anchor not found {href}")


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path("site")
    extras = [Path(a) for a in argv[2:]]
    pages = sorted(root.rglob("*.html")) + extras
    stylesheets = sorted(root.rglob("*.css"))
    if not pages:
        print(f"nothing to check under {root}")
        return 1

    used_classes: set[str] = set()
    for page in pages:
        text = page.read_text(encoding="utf-8")
        label = page.name if page in extras else page.relative_to(root).as_posix()

        if "—" in text:
            fail(f"{label}: em dash")
        for phrase in RETIRED_COPY:
            if phrase in text:
                fail(f"{label}: retired copy {phrase!r}")
        if "box-shadow" in text:
            fail(f"{label}: box-shadow")
        for fill in GREY_FILLS:
            if fill in text:
                fail(f"{label}: grey fill {fill}")

        scan = Scan()
        scan.feed(text)
        used_classes |= scan.classes
        if scan.h1_count != 1:
            fail(f"{label}: {scan.h1_count} h1 elements, expected 1")
        if scan.duplicate_ids:
            fail(f"{label}: duplicate ids {scan.duplicate_ids}")
        if scan.scripts:
            fail(f"{label}: third-party script {scan.scripts}")
        check_links(page, scan, text)

    # A class is "declared" if any stylesheet or inline <style> mentions it.
    declared = set(
        re.findall(
            r"\.([a-zA-Z][\w-]*)",
            "".join(f.read_text(encoding="utf-8") for f in stylesheets)
            + "".join(p.read_text(encoding="utf-8") for p in pages),
        )
    )
    for name in sorted(used_classes - declared):
        if name not in UNSTYLED_BY_DESIGN:
            fail(f"class used but never styled: .{name}")

    print(f"\nchecked {len(pages)} page(s), {len(stylesheets)} stylesheet(s)")
    print("CLEAN" if not _failures else f"{_failures} problem(s)")
    return 1 if _failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
