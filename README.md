# Bare-bones lesson generator

A minimal, Carpentries-style lesson builder. Write lessons in Markdown, run one
Python script, get a navigable static website. **No dependencies** — pure Python
standard library (3.8+). No pip, Node, or pandoc.

## Hosting many trainings (NRP)

This repo hosts several trainings at once, each in its own folder under
`trainings/`, with a shared landing page:

```
trainings/<name>/config.yml      # title, subtitle, length, order, lessons
trainings/<name>/lessons/*.md     # the lesson pages
trainings/<name>/images/          # optional assets
```

```bash
python3 build_site.py            # build EVERY training into site/, + a landing page
python3 build_site.py --serve    # build all, then serve at http://localhost:8000
python3 build_site.py --serve --watch  # rebuild and auto-refresh the browser on edits
```

`site/index.html` is the landing page (one card per training); each training
builds into `site/<name>/`.

- **Add a training** — create `trainings/<name>/` with a `config.yml` and a
  `lessons/` folder, then rebuild.
- **Scaffold a training** — run `python3 new_training.py <name>` to create the
  expected `config.yml`, `lessons/`, `workspace/`, `workspace/yamls/`, and
  `images/` structure with starter files.
- **Take a training off** — delete its folder, or set `published: false` in its
  `config.yml`.
- **Order on the landing page** — set `order:` (lower = first) in each
  `config.yml`; `length:` renders as a badge on the card.

The current trainings are **`rcsi`** (1 hour) and **`cra-rel`** (2 hours). Their
in-page **"Launch in JupyterHub"** buttons are nbgitpuller links that target
`https://jh-training.nrp-nautilus.io` (the materials site is hosted separately
on `training.nrp-nautilus.io`).

## Quick start (single lesson)

The original single-lesson mode still works from the repo root (`lessons/` +
`config.yml`):

```bash
python3 build.py            # build the site into site/
python3 build.py --serve    # build, then serve at http://localhost:8000
```

Then open `site/index.html` (or the served URL).

## How it works

| Path         | Purpose                                              |
|--------------|------------------------------------------------------|
| `config.yml` | Lesson title, subtitle, and lesson order.            |
| `lessons/`   | One Markdown file per lesson. This is what you edit.  |
| `build.py`   | The generator. Reads lessons, writes `site/`.        |
| `site/`      | Generated output (safe to delete; rebuilt each time). |

## Writing a lesson

Each lesson starts with frontmatter, then Markdown:

```markdown
---
title: Getting Started
teaching: 20
exercises: 10
questions:
  - How do I do the thing?
objectives:
  - Do the thing.
keypoints:
  - The thing is done like so.
---

## A heading

Normal Markdown: **bold**, *italic*, `code`, [links](https://example.com),
lists, and fenced code blocks.
```

`teaching` + `exercises` minutes feed the auto-generated schedule on the home
page. `questions`/`objectives` render as a box at the top of the page;
`keypoints` render as a box at the bottom.

## Callout boxes

Colon-fenced blocks become styled callouts (nestable one level deep):

```markdown
::: challenge Reverse a string
Write a function that reverses a string.

::: solution
Use slicing: `s[::-1]`.
:::
:::
```

Built-in types: `objectives`, `questions`, `challenge`, `solution`, `callout`,
`keypoints`, `discussion`, `prereq`. Any other word renders as a generic
callout with that word as the title.

## Adding / reordering lessons

1. Add a file to `lessons/`, e.g. `03-wrap-up.md`.
2. List its name (without `.md`) in the `lessons:` block of `config.yml`.
3. Rebuild. Files not listed in `config.yml` are appended alphabetically.

## Supported Markdown

Headings, paragraphs, **bold**/*italic*, `inline code`, fenced code blocks,
ordered/unordered lists, blockquotes, horizontal rules, links, and images.
It's a deliberate subset — enough to author lessons without a heavy toolchain.
If you outgrow it, the lessons are plain Markdown and port cleanly to MkDocs,
the Carpentries Workbench, or any other tool.
