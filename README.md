# Bare-bones lesson generator

A minimal, Carpentries-style lesson builder. Write lessons in Markdown, run one
Python script, get a navigable static website. **No Python dependencies** —
pure Python standard library (3.8+). No pip, Node, or pandoc.

## Hosting many trainings (NRP)

This repo hosts several trainings at once, each in its own folder under
`trainings/`, with a shared landing page:

```
trainings/<name>/config.yml      # title, subtitle, date, length, lessons
trainings/<name>/lessons/*.md     # the lesson pages
trainings/<name>/images/          # optional assets
trainings/<name>/slides/*.md      # optional in-page slide decks
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
  `images/` / `slides/` structure with starter files.
- **Take a training off** — delete its folder, or set `published: false` in its
  `config.yml`.
- **Order on the landing page** — trainings without `date:` appear first.
  Dated trainings use `date: YYYY-MM-DD` and appear newest-first. `length:`
  renders as a badge on the card.
- **Link post-training resources** — set `materials_branch: materials/<name>` in
  `config.yml`; the training home page links to that GitHub branch.
- **Publish runnable materials** — the GitHub Actions materials workflow updates
  `materials/<name>` automatically when changes under `trainings/` land on
  `main`. The materials branch root contains the contents of `trainings/<name>/`,
  including `workspace/`, `lessons/`, `images/`, and `slides/`.

The current trainings are **`rcsi`** (1 hour) and **`cra-rel`** (2 hours). Their
in-page **"Launch in JupyterHub"** buttons are nbgitpuller links that target
`https://jh-training.nrp-nautilus.io` (the materials site is hosted separately
on `training.nrp-nautilus.io`).

## Publishing materials branches

Materials branches are what nbgitpuller pulls into JupyterHub. The
`.github/workflows/materials.yml` workflow publishes them automatically from
the committed training directory on `main`.

For `trainings/rcsi/`, this creates or updates `materials/rcsi` with this shape:

```text
config.yml
lessons/
workspace/
images/
slides/
```

The JupyterHub links should clone the materials branch into `targetpath=<name>`
and open `urlpath=lab/tree/<name>/workspace`. Notebook links should include the
workspace path, for example:

```text
urlpath=lab/tree/rcsi/workspace/2_inference.ipynb
```

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

Use the type after the opening `:::`. Add text after the type to override the
default title:

```markdown
::: important Check this first
Make sure your kubeconfig points at the right cluster before running commands.
:::

::: danger Do not run this on a shared namespace
This command deletes resources.
:::
```

Built-in types:

| Type | Default title | Styling |
|---|---|---|
| `objectives` | Objectives | Blue |
| `questions` | Questions | Blue |
| `challenge` | Challenge | Orange |
| `solution` | Solution | Teal |
| `important` | Important | Yellow with warning icon |
| `danger` | Danger | Red with warning icon |
| `callout` | Note | Gray |
| `keypoints` | Key Points | Purple |
| `discussion` | Discussion | Gray |
| `prereq` | Prerequisites | Gray |

Any other word renders as a generic callout with that word as the title.

## In-page slides

Use a `slides` block when part of a lesson is easier to present as a compact
deck. Separate slides with a top-level `---` line:

````markdown
::: slides Optional deck title
# First slide

- One point
- Another point

---

# Second slide

```bash
kubectl get pods
```
:::
````

Slides render inline with previous/next controls, keyboard navigation when the
deck is focused, and a fullscreen button. Use `ArrowLeft`/`ArrowRight`,
`PageUp`/`PageDown`, `Home`, and `End` while presenting.

You can also keep a deck in a separate Markdown file or PDF and include it from
a lesson. Include paths are relative to the training directory:

````markdown
::: slides Demo deck
@include slides/demo.md
:::
````

The included file uses the same slide separator:

```markdown
# First slide

---

# Second slide
```

PDF (experimental) decks render one PDF page at a time with previous/next controls and the
same fullscreen button:

```markdown
::: slides Demo PDF
@include slides/demo.pdf
:::
```

PDF decks render one page at a time from cached PNGs under
`slides/_rendered/`. When Poppler's `pdftoppm` command is available,
`python3 build_site.py` creates or refreshes that cache automatically. Commit
the generated `_rendered/` files with the PDF so cluster builds can reuse them
without installing Poppler. On macOS, install Poppler with `brew install
poppler`.

## Adding / reordering lessons

1. Add a file to `lessons/`, e.g. `03-wrap-up.md`.
2. List its name (without `.md`) in the `lessons:` block of `config.yml`.
3. Rebuild. Files not listed in `config.yml` are appended alphabetically.

## Supported Markdown

Headings, paragraphs, **bold**/*italic*, `inline code`, fenced code blocks,
ordered/unordered lists, blockquotes, horizontal rules, links, images, callouts,
and in-page slide decks.

Fenced code blocks can include a language label. `bash`, `python`, `cpp` /
`c++`, and `yaml` / `yml` get built-in syntax highlighting and a visible header:

````markdown
```bash
kubectl get pods -n default
```
````

It's a deliberate subset — enough to author lessons without a heavy toolchain.
If you outgrow it, the lessons are plain Markdown and port cleanly to MkDocs,
the Carpentries Workbench, or any other tool.
