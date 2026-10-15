# mayatrail-web

The official website for **MayaTrail**, cloud attack emulation for detection engineers.

**Live at [mayatrail.tech](https://mayatrail.tech)**

## About

This repository contains the source code for the MayaTrail website: a static
site of plain HTML and CSS, served by nginx in Docker and deployed on AWS. The
site code lives in [`site/`](site/).

Four surfaces, and no more:

| Page | What it is for |
|---|---|
| `site/index.html` | The platform. Hero, the four steps of a run, and what a run can conclude. |
| `site/services.html` | The engagements, from a workshop to a full red team. |
| `site/pricing.html` | The assessment, the annual plans, and how billing works. |
| `site/blog/` | Field notes, generated from `blog/*.md`. |

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

## House style

Two rules worth stating because they are easy to break by habit:

- **No em dashes.** Use a comma, a colon, or a second sentence.
- **No unsourced figures.** Every number on the site has to trace to something
  in the product repository. A verdict matrix that is an example says so on the
  page.

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
