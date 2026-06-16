---
title: Introduction
teaching: 15
exercises: 5
questions:
  - What is this lesson about?
  - Who is it for?
objectives:
  - Explain the goal of the lesson.
  - Identify the prerequisites.
keypoints:
  - Lessons are plain Markdown files in the episodes/ folder.
  - Frontmatter drives the schedule, objectives, and key points.
---

## Welcome

This is a sample episode. Edit `episodes/01-introduction.md` to make it your
own, or copy it to start a new episode. Everything you see here is generated
from Markdown by `build.py`.

You can write **bold**, *italic*, `inline code`, [links](https://www.google.com),
lists, and code blocks:

```bash
# A fenced code block with a language hint
echo "Hello, learners"
```

## Callouts

Use colon-fenced callouts for the Carpentries-style boxes:

::: prereq Before you begin
You should be comfortable with the command line and have access to a terminal.
:::

::: callout A note
Callouts draw the eye to something worth highlighting.
:::

## A challenge with a solution

::: challenge Reverse a string
Write a one-line Python expression that reverses the string `s`.

::: solution
```python
s[::-1]
```
:::
:::
