---
title: First Steps
teaching: 25
exercises: 15
questions:
  - How do I add a new lesson?
  - How do I control the order and timing?
objectives:
  - Create a new lesson from scratch.
  - Set teaching and exercise minutes.
keypoints:
  - Add a Markdown file to lessons/ and list its name in config.yml.
  - Teaching + exercise minutes feed the schedule on the home page.
---

## Adding a lesson

1. Create a file like `lessons/03-my-topic.md`.
2. Give it frontmatter (`title`, `teaching`, `exercises`, ...).
3. Add `03-my-topic` to the `lessons:` list in `config.yml`.
4. Re-run `python3 build.py`.

That's the whole loop.

::: challenge Try it
Add a third lesson called "Wrap-up" with 10 minutes of teaching and no
exercises. Rebuild and confirm it appears in the schedule with the right time.

::: solution
Create `lessons/03-wrap-up.md` with `teaching: 10` and `exercises: 0` in the
frontmatter, add `03-wrap-up` to `config.yml`, then run `python3 build.py`.
:::
:::

## Where things live

- `lessons/` — your lesson content (Markdown).
- `config.yml` — lesson title and lesson order.
- `build.py` — the generator (no dependencies).
- `site/` — the generated website (open `site/index.html`).
