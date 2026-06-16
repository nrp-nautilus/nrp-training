# Bare-bones lesson generator

A minimal, Carpentries-style lesson builder. Write episodes in Markdown, run one
Python script, get a navigable static website. **No dependencies** — pure Python
standard library (3.8+). No pip, Node, or pandoc.

## Quick start

```bash
python3 build.py            # build the site into site/
python3 build.py --serve    # build, then serve at http://localhost:8000
```

Then open `site/index.html` (or the served URL).

## How it works

| Path         | Purpose                                              |
|--------------|------------------------------------------------------|
| `config.yml` | Lesson title, subtitle, and episode order.           |
| `episodes/`  | One Markdown file per episode. This is what you edit. |
| `build.py`   | The generator. Reads episodes, writes `site/`.       |
| `site/`      | Generated output (safe to delete; rebuilt each time). |

## Writing an episode

Each episode starts with frontmatter, then Markdown:

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

## Adding / reordering episodes

1. Add a file to `episodes/`, e.g. `03-wrap-up.md`.
2. List its name (without `.md`) in the `episodes:` block of `config.yml`.
3. Rebuild. Files not listed in `config.yml` are appended alphabetically.

## Supported Markdown

Headings, paragraphs, **bold**/*italic*, `inline code`, fenced code blocks,
ordered/unordered lists, blockquotes, horizontal rules, links, and images.
It's a deliberate subset — enough to author lessons without a heavy toolchain.
If you outgrow it, the episodes are plain Markdown and port cleanly to MkDocs,
the Carpentries Workbench, or any other tool.
