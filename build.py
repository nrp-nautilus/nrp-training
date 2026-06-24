#!/usr/bin/env python3
"""
Usage:
    python3 build.py            # build site/ from lessons/ and config.yml
    python3 build.py --serve    # build, then serve starting at http://localhost:8000

Authoring model
---------------
Each lesson page is a Markdown file in lessons/. The top of the file holds
YAML-ish frontmatter between '---' fences:

    ---
    title: Getting Started
    teaching: 20        # minutes of teaching
    exercises: 10       # minutes of exercises
    questions:
      - How do I do the thing?
    objectives:
      - Do the thing.
    keypoints:
      - The thing is done like so.
    ---

The body is Markdown. In addition to common Markdown, you can use callout
blocks delimited by colons:

    ::: challenge Reverse a string
    Write a function that reverses a string.

    ::: solution
    Use slicing: `s[::-1]`.
    :::
    :::

Supported callout types: objectives, challenge, solution, callout, keypoints,
discussion, prereq. Unknown types render as a generic callout.
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSON_DIR = ROOT / "lessons"
LEGACY_LESSON_DIR = ROOT / "episodes"
SITE_DIR = ROOT / "site"
CONFIG = ROOT / "config.yml"

# Optional link back to a multi-lesson landing page (set by build_site.py).
SITE_HOME_LINK = None

CALLOUT_LABELS = {
    "objectives": "Objectives",
    "questions": "Questions",
    "challenge": "Challenge",
    "solution": "Solution",
    "callout": "Note",
    "keypoints": "Key Points",
    "discussion": "Discussion",
    "prereq": "Prerequisites",
}


# --------------------------------------------------------------------------
# Tiny YAML subset parser (enough for our frontmatter / config)
# --------------------------------------------------------------------------
def parse_yaml(text):
    """Parse a small YAML subset: scalars and simple block lists.

    Supports:
        key: value
        key:
          - item
          - item
    Values are returned as strings; lists as lists of strings.
    """
    data = {}
    current_key = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if re.match(r"^\s*-\s+", line):
            if current_key is None:
                continue
            item = re.sub(r"^\s*-\s+", "", line).strip()
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(_unquote(item))
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value == "":
                data[key] = []          # may become a list as items arrive
                current_key = key
            else:
                data[key] = _unquote(value)
                current_key = key
    return data


def _unquote(s):
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def split_frontmatter(text):
    if text.startswith("---"):
        parts = text.split("\n", 1)[1].split("\n---", 1)
        if len(parts) == 2:
            return parse_yaml(parts[0]), parts[1].lstrip("\n")
    return {}, text


# --------------------------------------------------------------------------
# Markdown -> HTML (small subset, block-based)
# --------------------------------------------------------------------------
def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def inline(text):
    """Inline formatting. `text` must already be HTML-escaped."""
    # images: ![alt](src)
    text = re.sub(r"!\[(.*?)\]\((.*?)\)",
                  r'<img src="\2" alt="\1">', text)
    # links: [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)",
                  r'<a href="\2">\1</a>', text)
    # inline code: `code`  (protect contents from other rules)
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    # bold then italic
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    # restore code
    text = re.sub(r"\x00(\d+)\x00",
                  lambda m: f"<code>{codes[int(m.group(1))]}</code>", text)
    return text


def render_blocks(lines):
    """Render a list of Markdown lines (no callouts) into HTML."""
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # blank line
        if not line.strip():
            i += 1
            continue

        # fenced code block
        m = re.match(r"^```\s*([\w+-]*)\s*$", line)
        if m:
            lang = m.group(1)
            i += 1
            code = []
            while i < n and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # closing fence
            cls = f' class="language-{lang}"' if lang else ""
            body = html.escape("\n".join(code))
            out.append(f"<pre><code{cls}>{body}</code></pre>")
            continue

        # raw HTML block: a line starting with an HTML tag passes through
        # verbatim (un-escaped) until a blank line. Lets authors use
        # <details>, <img align=...>, <br>, etc. Blank lines inside let
        # interleaved Markdown (e.g. an image in a <details>) still render.
        if re.match(r"^\s*</?[a-zA-Z][\w-]*", line):
            raw = []
            while i < n and lines[i].strip():
                raw.append(lines[i])
                i += 1
            out.append("\n".join(raw))
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            content = inline(html.escape(m.group(2).strip()))
            sid = slugify(m.group(2))
            out.append(f'<h{level} id="{sid}">{content}</h{level}>')
            i += 1
            continue

        # horizontal rule
        if re.match(r"^(---|\*\*\*|___)\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # blockquote
        if line.startswith(">"):
            quote = []
            while i < n and lines[i].startswith(">"):
                quote.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + render_blocks(quote) + "</blockquote>")
            continue

        # lists (ordered / unordered)
        if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            items = []
            while i < n and re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]):
                item = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", lines[i])
                items.append(inline(html.escape(item)))
                i += 1
            tag = "ol" if ordered else "ul"
            lis = "".join(f"<li>{it}</li>" for it in items)
            out.append(f"<{tag}>{lis}</{tag}>")
            continue

        # GFM pipe table: a header row followed by a |---|---| separator
        if "|" in line and i + 1 < n and re.match(
                r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$",
                lines[i + 1]):
            def _cells(row):
                row = row.strip()
                if row.startswith("|"):
                    row = row[1:]
                if row.endswith("|"):
                    row = row[:-1]
                return [c.strip() for c in row.split("|")]
            headers = _cells(line)
            i += 2  # consume header + separator
            rows = []
            while i < n and lines[i].strip() and "|" in lines[i]:
                rows.append(_cells(lines[i]))
                i += 1
            thead = "".join(f"<th>{inline(html.escape(h))}</th>" for h in headers)
            trows = []
            for r in rows:
                tds = "".join(f"<td>{inline(html.escape(c))}</td>" for c in r)
                trows.append(f"<tr>{tds}</tr>")
            out.append('<table class="md-table"><thead><tr>' + thead +
                       "</tr></thead><tbody>" + "".join(trows) +
                       "</tbody></table>")
            continue

        # paragraph: gather until blank line / block start (incl. a line that
        # begins an HTML block, so raw HTML isn't swallowed and escaped).
        para = []
        while i < n and lines[i].strip() and not re.match(
            r"^(#{1,6}\s|```|>|\s*([-*+]|\d+\.)\s|(---|\*\*\*|___)\s*$|\s*</?[a-zA-Z])",
            lines[i],
        ):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>" + inline(html.escape(" ".join(para))) + "</p>")

    return "\n".join(out)


def render_markdown(text):
    """Render Markdown including ::: callout ::: blocks (one level of nesting)."""
    lines = text.splitlines()
    out = []
    i = 0
    n = len(lines)
    buffer = []

    def flush():
        if buffer:
            out.append(render_blocks(buffer))
            buffer.clear()

    while i < n:
        m = re.match(r"^:::+\s+(\w+)\s*(.*)$", lines[i])
        if m:
            flush()
            ctype = m.group(1).lower()
            title = m.group(2).strip()
            # collect until matching closing ::: (track nesting depth)
            depth = 1
            inner = []
            i += 1
            while i < n and depth > 0:
                if re.match(r"^:::+\s+\w+", lines[i]):
                    depth += 1
                    inner.append(lines[i])
                elif re.match(r"^:::+\s*$", lines[i]):
                    depth -= 1
                    if depth > 0:
                        inner.append(lines[i])
                else:
                    inner.append(lines[i])
                i += 1
            label = title or CALLOUT_LABELS.get(ctype, ctype.title())
            body = render_markdown("\n".join(inner))
            out.append(
                f'<div class="callout callout-{html.escape(ctype)}">'
                f'<div class="callout-title">{html.escape(label)}</div>'
                f'<div class="callout-body">{body}</div></div>'
            )
            continue
        buffer.append(lines[i])
        i += 1
    flush()
    return "\n".join(out)


def boxed_list(ctype, label, items):
    if not items:
        return ""
    lis = "".join(f"<li>{inline(html.escape(x))}</li>" for x in items)
    return (
        f'<div class="callout callout-{ctype}">'
        f'<div class="callout-title">{label}</div>'
        f'<div class="callout-body"><ul>{lis}</ul></div></div>'
    )


# --------------------------------------------------------------------------
# Page templates
# --------------------------------------------------------------------------
def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def page(title, lesson_title, body, nav_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} &mdash; {html.escape(lesson_title)}</title>
<link rel="icon" href="nrp-tiny.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="https://nrp.ai"><img class="brand-logo" src="nrp-logo.webp" alt="National Research Platform" width="163" height="30"></a>
  <a class="site-title" href="index.html">{html.escape(lesson_title)}</a>
  <button class="nav-toggle" type="button" data-nav-toggle aria-controls="lesson-nav" aria-expanded="true">Hide nav</button>
</header>
<nav id="lesson-nav" class="lesson-nav" aria-label="Lesson navigation">
  <div class="lesson-nav-inner">{nav_html}</div>
</nav>
<main class="content">{body}</main>
<footer class="site-footer">
  Built with a bare-bones lesson generator.
</footer>
{NAV_SCRIPT}
</body>
</html>
"""


def build_nav(lesson_title, lessons, active=None):
    items = []
    if SITE_HOME_LINK:
        items.append(
            f'<a class="nav-all" href="{SITE_HOME_LINK}">&larr; All trainings</a>')
    items.append('<a class="nav-home" href="index.html">Home</a>')

    lesson_links = []
    for lesson in lessons:
        active_attr = ' aria-current="page"' if lesson["slug"] == active else ""
        class_attr = ' class="active"' if lesson["slug"] == active else ""
        lesson_links.append(
            f'<a{class_attr} href="{lesson["slug"]}.html"{active_attr}>'
            f'{html.escape(lesson["title"])}</a>'
        )
    items.append(
        '<details class="lesson-menu"><summary>Lessons</summary>'
        '<div class="lesson-menu-list">'
        + "\n".join(lesson_links)
        + "</div></details>"
    )
    return "\n".join(items)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------
def source_lesson_dir():
    if LESSON_DIR.exists():
        return LESSON_DIR
    if LEGACY_LESSON_DIR.exists():
        return LEGACY_LESSON_DIR
    return LESSON_DIR


def configured_lessons(config):
    return config.get("lessons", config.get("episodes"))


def load_lessons(config):
    lesson_dir = source_lesson_dir()
    files = {p.stem: p for p in lesson_dir.glob("*.md")}
    ordered = [s for s in as_list(configured_lessons(config)) if s in files]
    ordered += sorted(s for s in files if s not in ordered)

    lessons = []
    for slug in ordered:
        fm, body = split_frontmatter(files[slug].read_text(encoding="utf-8"))
        lessons.append({
            "slug": slug,
            "path": files[slug],
            "title": fm.get("title", slug),
            "teaching": int(fm.get("teaching", 0) or 0),
            "exercises": int(fm.get("exercises", 0) or 0),
            "questions": as_list(fm.get("questions")),
            "objectives": as_list(fm.get("objectives")),
            "keypoints": as_list(fm.get("keypoints")),
            "body": body,
        })
    return lessons


def render_lesson(lesson, lesson_title, lessons, index):
    nav = build_nav(lesson_title, lessons, active=lesson["slug"])

    top = boxed_list("objectives", "Questions", lesson["questions"])
    top += boxed_list("objectives", "Objectives", lesson["objectives"])

    content = render_markdown(lesson["body"])

    bottom = boxed_list("keypoints", "Key Points", lesson["keypoints"])

    # prev / next
    prev_lesson = lessons[index - 1] if index > 0 else None
    next_lesson = lessons[index + 1] if index < len(lessons) - 1 else None
    prev_html = (
        f'<a class="prev" href="{prev_lesson["slug"]}.html">&larr; {html.escape(prev_lesson["title"])}</a>'
        if prev_lesson else "<span></span>"
    )
    next_html = (
        f'<a class="next" href="{next_lesson["slug"]}.html">{html.escape(next_lesson["title"])} &rarr;</a>'
        if next_lesson else "<span></span>"
    )

    mins = lesson["teaching"] + lesson["exercises"]
    meta = (
        f'<p class="lesson-meta">Teaching: {lesson["teaching"]} min '
        f'&middot; Exercises: {lesson["exercises"]} min '
        f'&middot; Total: {mins} min</p>'
    )

    body = (
        f'<h1>{html.escape(lesson["title"])}</h1>{meta}{top}{content}{bottom}'
        f'<div class="pager">{prev_html}{next_html}</div>'
    )
    return page(lesson["title"], lesson_title, body, nav)


def render_index(config, lessons):
    lesson_title = config.get("title", "Lesson")
    subtitle = config.get("subtitle", "")
    nav = build_nav(lesson_title, lessons)

    rows = []
    cumulative = 0
    for lesson in lessons:
        mins = lesson["teaching"] + lesson["exercises"]
        start = f"{cumulative // 60:02d}:{cumulative % 60:02d}"
        cumulative += mins
        rows.append(
            f"<tr><td>{start}</td>"
            f'<td><a href="{lesson["slug"]}.html">{html.escape(lesson["title"])}</a></td>'
            f"<td>{mins} min</td></tr>"
        )
    finish = f"{cumulative // 60:02d}:{cumulative % 60:02d}"

    schedule = (
        '<table class="schedule"><thead><tr><th>Start</th><th>Lesson</th>'
        "<th>Duration</th></tr></thead><tbody>"
        + "".join(rows)
        + f'<tr class="finish"><td>{finish}</td><td>Finish</td><td></td></tr>'
        + "</tbody></table>"
    )

    body = (
        f"<h1>{html.escape(lesson_title)}</h1>"
        f'<p class="subtitle">{html.escape(subtitle)}</p>'
        f"<h2>Schedule</h2>{schedule}"
        '<p class="hint">Times are cumulative and assume a prompt start. '
        "Edit durations in each lesson's frontmatter.</p>"
    )
    return page("Home", lesson_title, body, nav)


def build():
    config = parse_yaml(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
    lesson_title = config.get("title", "Lesson")

    lesson_dir = source_lesson_dir()
    if not lesson_dir.exists():
        sys.exit(f"No lessons/ directory found at {LESSON_DIR}")

    lessons = load_lessons(config)
    if not lessons:
        sys.exit(f"No lessons found in {lesson_dir}/*.md")

    SITE_DIR.mkdir(exist_ok=True)
    (SITE_DIR / "style.css").write_text(STYLE, encoding="utf-8")
    (SITE_DIR / "index.html").write_text(
        render_index(config, lessons), encoding="utf-8")

    for idx, lesson in enumerate(lessons):
        (SITE_DIR / f"{lesson['slug']}.html").write_text(
            render_lesson(lesson, lesson_title, lessons, idx), encoding="utf-8")

    print(f"Built {len(lessons)} lesson(s) + index into {SITE_DIR}/")
    for lesson in lessons:
        print(f"  - {lesson['slug']}.html  ({lesson['title']})")


def serve(port=8000):
    from functools import partial
    import errno
    import http.server
    import socketserver

    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE_DIR))
    for candidate in range(port, port + 100):
        try:
            httpd = ReusableTCPServer(("", candidate), handler)
        except OSError as exc:
            if exc.errno == errno.EADDRINUSE:
                continue
            raise
        with httpd:
            print(f"Serving {SITE_DIR} at http://localhost:{candidate}  (Ctrl-C to stop)")
            httpd.serve_forever()
        return
    raise OSError(f"No available port found in range {port}-{port + 99}")


NAV_SCRIPT = """\
<script>
(() => {
  const storageKey = "nrpLessonNavHidden";
  const nav = document.getElementById("lesson-nav");
  const toggle = document.querySelector("[data-nav-toggle]");
  if (!nav || !toggle) return;

  function setHidden(hidden) {
    document.body.classList.toggle("nav-hidden", hidden);
    toggle.setAttribute("aria-expanded", String(!hidden));
    toggle.textContent = hidden ? "Show nav" : "Hide nav";
    try {
      window.localStorage.setItem(storageKey, hidden ? "1" : "0");
    } catch (error) {
      // Private browsing modes may block localStorage.
    }
  }

  let hidden = false;
  try {
    hidden = window.localStorage.getItem(storageKey) === "1";
  } catch (error) {
    hidden = false;
  }

  setHidden(hidden);
  toggle.addEventListener("click", () => {
    setHidden(!document.body.classList.contains("nav-hidden"));
  });
})();
</script>
"""


STYLE = """\
/* NRP theme: matches gitlab.nrp-nautilus.io/prp/nrp-site (AstroWind, Inter,
   primary #0161ef / secondary #0154cf / accent #6d28d9, navy #030620). */
:root {
  --fg: #101010; --muted: rgba(16,16,16,.66); --bg: #ffffff; --panel: #f6f8fa;
  --border: #e5e9f0; --accent: #0161ef; --accent-2: #0154cf; --accent-weak: #e7f0ff;
  --obj: #0161ef; --challenge: #b45309; --solution: #0f766e;
  --keypoints: #6d28d9; --note: #475569; --navy: #030620;
  --max: 820px;
}
* { box-sizing: border-box; }
body { margin: 0; color: var(--fg); background: var(--bg);
  font: 16px/1.7 "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased; }
h1, h2, h3, h4 { font-weight: 700; letter-spacing: -.012em; color: var(--navy); }
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-2); text-decoration: underline; }
::selection { background: lavender; }
.site-header { display: flex; align-items: center; gap: 16px; background: #fff;
  padding: 11px 28px; border-bottom: 1px solid var(--border);
  box-shadow: 0 1px 12px rgb(140 152 164 / 10%); position: sticky; top: 0; z-index: 20; }
.brand { display: flex; align-items: center; line-height: 0; }
.brand-logo { height: 30px; width: auto; display: block; }
.site-title { color: var(--fg); font-weight: 700; font-size: 1.0rem;
  padding-left: 16px; border-left: 1px solid var(--border); min-width: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.site-title:hover { text-decoration: none; color: var(--accent); }
.nav-toggle { margin-left: auto; flex: 0 0 auto; border: 1px solid var(--border);
  border-radius: 6px; background: #fff; color: var(--fg); cursor: pointer;
  font: inherit; font-size: .85rem; font-weight: 600; line-height: 1.2; padding: 7px 10px; }
.nav-toggle:hover { border-color: var(--accent); color: var(--accent); }
.lesson-nav { background: #fff; border-bottom: 1px solid var(--border); position: relative; z-index: 10; }
.lesson-nav-inner { display: flex; align-items: center; gap: 8px; max-width: 1180px; margin: 0 auto;
  padding: 10px 24px; }
.lesson-nav a,
.lesson-menu summary { flex: 0 0 auto; border: 1px solid transparent; border-radius: 6px;
  color: var(--fg); font-size: .92rem; line-height: 1.25; padding: 6px 10px;
  white-space: nowrap; }
.lesson-nav a:hover,
.lesson-menu summary:hover { background: var(--panel); color: var(--accent); text-decoration: none; }
.lesson-nav .nav-all { color: var(--muted); }
.lesson-nav .nav-home { font-weight: 600; }
.lesson-menu { position: relative; }
.lesson-menu summary { display: flex; align-items: center; cursor: pointer; font-weight: 600;
  list-style: none; user-select: none; }
.lesson-menu summary::-webkit-details-marker { display: none; }
.lesson-menu summary::after { content: ""; border-left: 4px solid transparent;
  border-right: 4px solid transparent; border-top: 5px solid currentColor; margin-left: 8px; }
.lesson-menu[open] summary { background: var(--panel); color: var(--accent); }
.lesson-menu-list { position: absolute; left: 0; top: calc(100% + 8px); z-index: 30;
  min-width: 240px; max-width: min(420px, calc(100vw - 48px)); background: #fff;
  border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 12px 28px rgb(3 6 32 / 14%);
  padding: 6px; }
.lesson-menu-list a { display: block; white-space: normal; }
.lesson-menu-list a + a { margin-top: 2px; }
.lesson-menu-list .active { background: var(--accent-weak); border-color: rgb(1 97 239 / 24%);
  color: var(--accent); font-weight: 700; }
.nav-hidden .lesson-nav { display: none; }
.content { max-width: var(--max); margin: 0 auto; min-width: 0; padding: 32px 24px 28px; }
.content h1 { margin-top: 0; line-height: 1.2; }
.subtitle { color: var(--muted); font-size: 1.1rem; margin-top: -8px; }
.lesson-meta { color: var(--muted); font-size: .9rem; margin-top: -6px; }
pre { background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px; overflow: auto; }
code { background: var(--panel); padding: .1em .35em; border-radius: 4px;
  font-size: .9em; font-family: "SF Mono", Menlo, Consolas, monospace; }
pre code { background: none; padding: 0; }
blockquote { margin: 1em 0; padding: .2em 1em; border-left: 4px solid var(--accent-weak); color: var(--muted); }
img { max-width: 100%; }
.callout { border: 1px solid var(--border); border-left-width: 5px; border-radius: 10px;
  margin: 1.2em 0; background: var(--bg); overflow: hidden; }
.callout-title { font-weight: 700; padding: 8px 16px; background: var(--panel); }
.callout-body { padding: 4px 16px; }
.callout-body > :first-child { margin-top: .4em; }
/* Launch buttons: bold markdown links inside callouts render as NRP pill buttons. */
.callout-body strong a { display: inline-block; background: var(--accent); color: #fff;
  font-weight: 600; padding: 9px 18px; border-radius: 999px; text-decoration: none;
  box-shadow: 0 1px 6px rgb(1 97 239 / 30%); transition: background .15s ease, transform .1s ease; }
.callout-body strong a:hover { background: var(--accent-2); color: #fff; text-decoration: none;
  transform: translateY(-1px); }
.callout-objectives { border-left-color: var(--obj); }
.callout-objectives > .callout-title { background: var(--accent-weak); }
.callout-challenge { border-left-color: var(--challenge); }
.callout-solution { border-left-color: var(--solution); }
.callout-keypoints { border-left-color: var(--keypoints); }
.callout-callout, .callout-discussion, .callout-prereq { border-left-color: var(--note); }
.schedule, .md-table { border-collapse: collapse; width: 100%; margin: 1em 0; }
.schedule th, .schedule td,
.md-table th, .md-table td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; vertical-align: top; }
.schedule thead, .md-table thead { background: var(--panel); }
.schedule tr.finish { font-weight: 600; background: var(--panel); }
.hint { color: var(--muted); font-size: .9rem; }
.pager { display: flex; justify-content: space-between; margin-top: 36px;
  padding-top: 16px; border-top: 1px solid var(--border); }
.site-footer { color: var(--muted); text-align: center; padding: 24px; font-size: .85rem; }
@media (max-width: 760px) {
  .site-header { padding: 10px 16px; gap: 10px; }
  .brand-logo { max-width: 38vw; }
  .site-title { font-size: .92rem; padding-left: 10px; }
  .nav-toggle { padding: 6px 8px; }
  .lesson-nav-inner { padding: 8px 16px; }
  .lesson-menu-list { left: auto; right: 0; max-width: calc(100vw - 32px); }
  .content { padding: 24px 18px 28px; }
}
"""


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        serve()
