# mayatrail-web

The official website for **MayaTrail**, cloud attack emulation for detection engineers.

**Live at [mayatrail.tech](https://mayatrail.tech)**

## About

This repository contains the source code for the MayaTrail website: a static
site of plain HTML and CSS, served by nginx in Docker and deployed on AWS. The
site code lives in [`site/`](site/).

Two documents, and no more:

| Page | What it is for |
|---|---|
| `site/index.html` | One scroll, four surfaces: `#platform`, `#services`, `#pricing`, `#blog`. Scrolling carries you from one into the next and the nav marks itself as each passes under it. |
| `site/blog/` | Field notes, generated from `blog/*.md`. The home page carries the latest few; a whole post is its own document, so it can be linked and indexed on its own. |

`site/services.html` and `site/pricing.html` are redirect stubs. Those URLs were
shared before the rework, so they stay alive and land on the matching surface.
Do not add content to them.

Everything deeper than that lives in the product repository at
[github.com/MayaTrail/step1](https://github.com/MayaTrail/step1): campaign
manifests, the incident-response playbooks, and the per-service ground truth.
The site is deliberately the shallow end. If a page starts wanting a reference
table, the reference belongs in git where it can be reviewed and versioned.

The site ships no third-party JavaScript. The only script on any page is the
inline switcher on the home page, which degrades to a readable first panel when
JavaScript is off.

## The blog

Posts live in [`blog/`](blog/) as Markdown and are rendered to static HTML at
`/blog/` during the Docker build, so the published site stays plain nginx and
the posts stay indexable.

Write a post as `blog/my-post.md` with YAML front matter:

```yaml
---
title: What a run actually leaves behind
date: 2026-09-10
description: One sentence, used on the index, the meta tag and the RSS feed.
tags: [detection-engineering, aws]
draft: true
---
```

`title` and `date` are required. `draft: true` keeps a post out of the build
until you remove it. The filename becomes the URL: `/blog/my-post/`.

Preview locally:

```bash
pip install -r requirements-blog.txt
python scripts/build_blog.py --drafts --clean
python -m http.server 8000 --directory site
```

`site/blog/` is generated output and is git-ignored. The Markdown is the source
of truth, and the builder stage in the Dockerfile regenerates it on every
deploy.

`build_blog.py` also writes the home page's field-notes rows, between the
`<!-- BLOG:ENTRIES -->` markers in `site/index.html`. That part is not
git-ignored, so building with `--drafts` leaves `site/index.html` modified.
The committed state is the published one: whatever a build without `--drafts`
produces.

## Before you share it or merge it

```bash
python scripts/check_site.py                      # static checks over site/
python scripts/package_preview.py ../out          # the two share artefacts
```

`check_site.py` is the gate: em dashes, retired copy, one `h1` per page, no
duplicate ids, every relative link and anchor resolving, no third-party
scripts, no grey fills or shadows, and no class in the markup that no
stylesheet declares. It exits non-zero on the first problem, so it works in a
hook or a CI step. Exemptions are listed at the top of the file, not hidden.

`package_preview.py` writes the zip of the whole site and a single-file copy of
the home page with the stylesheet inlined and the favicon embedded, for when
someone wants one attachment rather than an archive. The read-me that goes in
the zip is [`share/READ-ME-FIRST.txt`](share/READ-ME-FIRST.txt); it names what
is deliberately unfinished, so nobody reviews a gap as a bug.

## House style

Two rules worth stating because they are easy to break by habit:

- **No em dashes.** Use a comma, a colon, or a second sentence.
- **No unsourced figures.** Every number on the site has to trace to something
  in the product repository. A verdict matrix that is an example says so on the
  page. The same goes for product behaviour: the Team plan once promised
  scheduled re-runs "daily, weekly or monthly" when the backend only had a
  one-shot `scheduled_for`, and that is the kind of claim a reader can check.
- **Emulation, not run.** "Emulation" is the product's own noun and one of the
  things that distinguishes it. Run is fine as a verb.

## What was removed

The coverage and research pages, the scenario catalogue, the run walkthrough and
the IR playbook page were taken off the site in the October 2026 rework. They
are kept in [`archive/superseded/`](archive/superseded/) for reference, along
with the React toolchain the run page needed. The product documentation in
`step1` is the replacement for all of it.

## Team Members

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-4-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

Thanks goes to these wonderful people
([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Himan10"><img src="https://avatars.githubusercontent.com/u/33115688?v=4?s=100" width="100px;" alt="Himanshu Bhatnagar"/><br /><sub><b>Himanshu Bhatnagar</b></sub></a><br /><a href="https://github.com/MayaTrail/mayatrail-web/commits/main/?author=Himan10" title="Code">💻</a> <a href="https://github.com/MayaTrail/mayatrail-web/commits/main/?author=Himan10" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/ehayushpathak"><img src="https://avatars.githubusercontent.com/u/29299611?v=4?s=100" width="100px;" alt="Ayush Pathak"/><br /><sub><b>Ayush Pathak</b></sub></a><br /><a href="https://github.com/MayaTrail/mayatrail-web/commits/main/?author=ehayushpathak" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Ephemaral"><img src="https://github.com/Ephemaral.png?size=100" width="100px;" alt="Abhishek Lal"/><br /><sub><b>Abhishek Lal</b></sub></a><br /><a href="https://github.com/MayaTrail/mayatrail-web/commits/main/?author=Ephemaral" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/founderkd"><img src="https://github.com/founderkd.png?size=100" width="100px;" alt="Kunjan Dhoble"/><br /><sub><b>Kunjan Dhoble</b></sub></a><br /><a href="https://github.com/MayaTrail/mayatrail-web/commits/main/?author=founderkd" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the
[all-contributors](https://github.com/all-contributors/all-contributors)
specification. Contributions of any kind welcome!

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file in this repository.
