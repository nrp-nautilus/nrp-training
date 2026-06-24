#!/usr/bin/env python3
"""Build every training under trainings/ into site/, with a landing page.

Layout
------
    trainings/<name>/config.yml     # title, subtitle, date, length, lessons
    trainings/<name>/lessons/*.md   # the lesson pages
    trainings/<name>/images/        # optional assets
    trainings/<name>/slides/        # optional slide decks and PDFs

Each training builds into site/<name>/ (a self-contained lesson site), and a
landing page at site/index.html links them all.

Add a training   -> drop a new dir under trainings/ and rebuild.
Take one off      -> delete its dir, or set `published: false` in its config.yml.

    python3 build_site.py                   # build everything into site/
    python3 build_site.py --serve           # build, then serve starting on :8000
    python3 build_site.py --serve --watch   # rebuild + auto-refresh on edits
"""
import html
import shutil
import sys
import threading
import time
from datetime import date
from pathlib import Path

import build  # reuse the single-lesson generator

ROOT = Path(__file__).resolve().parent
TRAININGS = ROOT / "trainings"
SITE = ROOT / "site"
ASSETS = ROOT / "assets"            # shared NRP brand assets (logo, favicon)
WATCH_POLL_SECONDS = 0.6
LIVE_RELOAD_FILE = "__reload"

LIVE_RELOAD_SNIPPET = """
<script>
(() => {
  const reloadUrl = "/__reload";
  let seen = null;

  async function checkForReload() {
    try {
      const response = await fetch(`${reloadUrl}?t=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) return;
      const version = await response.text();
      if (seen === null) {
        seen = version;
      } else if (version !== seen) {
        location.reload();
      }
    } catch (error) {
      // The server may briefly miss during a rebuild. Try again on the next tick.
    }
  }

  setInterval(checkForReload, 700);
  checkForReload();
})();
</script>
"""

MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def copy_assets(dst):
    """Copy shared brand assets next to a page's style.css so logo/favicon
    resolve relatively at any URL depth (landing at site/, lessons at site/<name>/)."""
    dst.mkdir(parents=True, exist_ok=True)
    for f in ("nrp-logo.webp", "nrp-tiny.png"):
        src = ASSETS / f
        if src.exists():
            shutil.copy2(src, dst / f)


def parse_training_date(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        print(f"  (ignoring invalid date: {raw}; expected YYYY-MM-DD)")
        return None


def format_training_date(value):
    if value is None:
        return ""
    return f"{MONTHS[value.month - 1]} {value.day}, {value.year}"


def discover():
    items = []
    if not TRAININGS.exists():
        sys.exit(f"No trainings/ directory at {TRAININGS}")
    for d in sorted(TRAININGS.iterdir()):
        cfg_path = d / "config.yml"
        if not d.is_dir() or not cfg_path.exists():
            continue
        cfg = build.parse_yaml(cfg_path.read_text(encoding="utf-8"))
        if str(cfg.get("published", "true")).lower() == "false":
            print(f"  (skipping {d.name}: published: false)")
            continue
        training_date = parse_training_date(cfg.get("date"))
        items.append({
            "name": d.name,
            "dir": d,
            "title": cfg.get("title", d.name),
            "subtitle": cfg.get("subtitle", ""),
            "length": cfg.get("length", ""),
            "date": training_date,
            "date_label": format_training_date(training_date),
        })
    def sort_key(item):
        if item["date"] is None:
            return (0, item["title"])
        return (1, -item["date"].toordinal(), item["title"])

    items.sort(key=sort_key)
    return items


def build_one(item):
    """Point build.py's globals at one training and build it into site/<name>/."""
    out = SITE / item["name"]
    build.ROOT = item["dir"]
    build.LESSON_DIR = item["dir"] / "lessons"
    build.LEGACY_LESSON_DIR = item["dir"] / "episodes"
    build.CONFIG = item["dir"] / "config.yml"
    build.SITE_DIR = out
    build.SITE_HOME_LINK = "../index.html"
    out.mkdir(parents=True, exist_ok=True)
    build.build()
    images = item["dir"] / "images"
    if images.is_dir():
        dst = out / "images"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(images, dst)
    copy_assets(out)


def write_landing(items):
    cards = []
    for it in items:
        badges = []
        if it["date_label"]:
            badges.append(f'<span class="card-date">{html.escape(it["date_label"])}</span>')
        if it["length"]:
            badges.append(f'<span class="card-len">{html.escape(it["length"])}</span>')
        badge = " " + " ".join(badges) if badges else ""
        cards.append(
            f'<a class="card" href="{it["name"]}/index.html">'
            f'<h2>{html.escape(it["title"])}{badge}</h2>'
            f'<p>{html.escape(it["subtitle"])}</p></a>'
        )
    body = (
        '<header class="site-header">'
        '<a class="brand" href="https://nrp.ai">'
        '<img class="brand-logo" src="nrp-logo.webp" alt="National Research Platform" width="163" height="30"></a>'
        '<span class="site-title">Trainings</span>'
        '<div class="header-controls">'
        '<button class="icon-toggle theme-toggle" type="button" data-theme-toggle '
        'aria-label="Toggle dark theme" title="Toggle dark theme" aria-pressed="false">&#9680;</button>'
        '</div></header>'
        '<section class="hero">'
        '<div class="hero-inner">'
        '<h1>NRP Trainings</h1>'
        '<p class="hero-sub">Hands-on training modules for the '
        'National Research Platform &mdash; run real workloads on shared GPUs, '
        'launch each lesson straight into JupyterHub.</p>'
        '</div></section>'
        '<main class="landing">'
        '<div class="cards">' + "".join(cards) + '</div>'
        '</main>'
        '<footer class="site-footer">'
        'National Research Platform &middot; '
        '<a href="https://nrp.ai">nrp.ai</a></footer>'
    )
    doc = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>NRP Trainings</title>\n'
        f'{build.THEME_INIT_SCRIPT}\n'
        '<link rel="icon" href="nrp-tiny.png">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=Inter:wght@400;500;600;700;800&display=swap">\n'
        '<link rel="stylesheet" href="style.css">\n</head>\n'
        f'<body>\n{body}\n{build.PAGE_SCRIPT}\n</body>\n</html>\n'
    )
    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(doc, encoding="utf-8")
    (SITE / "style.css").write_text(build.STYLE + LANDING_CSS, encoding="utf-8")
    copy_assets(SITE)


def inject_live_reload():
    for page in SITE.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        if LIVE_RELOAD_FILE in text:
            continue
        if "</body>" in text:
            text = text.replace("</body>", LIVE_RELOAD_SNIPPET + "\n</body>", 1)
        else:
            text += LIVE_RELOAD_SNIPPET
        page.write_text(text, encoding="utf-8")


def write_reload_version():
    (SITE / LIVE_RELOAD_FILE).write_text(str(time.time_ns()), encoding="utf-8")


def build_all(live_reload=False):
    if SITE.exists():
        shutil.rmtree(SITE)
    items = discover()
    if not items:
        sys.exit("No published trainings found under trainings/")
    for it in items:
        print(f"==> {it['name']}")
        build_one(it)
    write_landing(items)
    if live_reload:
        inject_live_reload()
        write_reload_version()
    print(f"\nLanding page + {len(items)} training(s) -> {SITE}/")
    for it in items:
        print(f"  - {it['name']}/  ({it['title']})")


def source_fingerprint():
    paths = [ROOT / "build.py", ROOT / "build_site.py"]
    for watched_dir in (TRAININGS, ASSETS):
        if watched_dir.exists():
            paths.extend(p for p in watched_dir.rglob("*") if p.is_file())

    stats = []
    for path in paths:
        if not path.exists():
            continue
        stat = path.stat()
        stats.append((str(path.relative_to(ROOT)), stat.st_mtime_ns, stat.st_size))
    return tuple(sorted(stats))


def watch_and_rebuild():
    fingerprint = source_fingerprint()
    watched = "trainings/, assets/, build.py, build_site.py"
    print(f"Watching {watched} for changes")
    while True:
        time.sleep(WATCH_POLL_SECONDS)
        current = source_fingerprint()
        if current == fingerprint:
            continue

        fingerprint = current
        print("\nChange detected; rebuilding...")
        try:
            build_all(live_reload=True)
        except Exception as exc:
            print(f"Build failed: {exc}", file=sys.stderr)
        else:
            fingerprint = source_fingerprint()


LANDING_CSS = """
.hero {
  --hero-start: #0a1230;
  --hero-end: var(--navy);
  --hero-glow: rgb(1 97 239 / 35%);
  --hero-fg: #fff;
  --hero-sub: rgb(229 236 246 / 82%);
  background:
    radial-gradient(1100px 400px at 15% -10%, var(--hero-glow), transparent 60%),
    linear-gradient(160deg, var(--hero-start) 0%, var(--hero-end) 70%);
  color: var(--hero-fg); padding: 64px 24px 72px; }
:root[data-theme="dark"] .hero {
  --hero-start: #1a2330;
  --hero-end: #202a36;
  --hero-glow: rgb(145 194 255 / 9%);
  --hero-fg: #f5f8fb;
  --hero-sub: rgba(238,243,248,.72);
}
:root[data-theme="warm-dark"] .hero {
  --hero-start: #211f1c;
  --hero-end: #25231f;
  --hero-glow: rgb(154 191 255 / 8%);
  --hero-fg: #f7f3ed;
  --hero-sub: rgba(240,238,233,.72);
}
:root[data-theme="presenter"] .hero {
  --hero-start: #eef1ec;
  --hero-end: #f4f5f2;
  --hero-glow: rgb(1 97 239 / 10%);
  --hero-fg: #030620;
  --hero-sub: rgba(20,22,21,.68);
}
.hero-inner { max-width: 980px; margin: 0 auto; }
.hero h1 { color: var(--hero-fg); font-size: 2.6rem; line-height: 1.1; margin: 0 0 14px;
  letter-spacing: -.02em; }
.hero-sub { color: var(--hero-sub); font-size: 1.18rem; max-width: 640px; margin: 0; }
.landing { max-width: 980px; margin: 0 auto; padding: 0 24px; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px; margin-top: -34px; margin-bottom: 40px; }
.card { display: block; border: 1px solid var(--border); border-radius: 16px;
  padding: 22px 24px; background: var(--surface); color: var(--fg);
  box-shadow: 0 6px 20px var(--shadow); transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease; }
.card:hover { text-decoration: none; border-color: var(--accent);
  transform: translateY(-3px); box-shadow: 0 12px 30px rgb(1 97 239 / 16%); }
.card h2 { margin: 0 0 8px; font-size: 1.2rem; line-height: 1.3; color: var(--navy); }
.card p { margin: 0; color: var(--muted); }
.card-len, .card-date { font-size: .72rem; color: var(--accent); font-weight: 700;
  background: var(--accent-weak); border-radius: 999px; padding: 2px 10px;
  vertical-align: middle; white-space: nowrap; }
.card-date { color: var(--fg); background: var(--panel); border: 1px solid var(--border); }
"""


def main():
    unknown = [arg for arg in sys.argv[1:] if arg not in ("--serve", "--watch")]
    if unknown:
        sys.exit(f"Unknown option(s): {', '.join(unknown)}")

    live_reload = "--watch" in sys.argv
    serve = "--serve" in sys.argv or live_reload

    build_all(live_reload=live_reload)
    if live_reload:
        thread = threading.Thread(target=watch_and_rebuild, daemon=True)
        thread.start()
    if serve:
        build.SITE_DIR = SITE
        build.serve()


if __name__ == "__main__":
    main()
