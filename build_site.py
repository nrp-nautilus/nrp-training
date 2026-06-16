#!/usr/bin/env python3
"""Build every training under trainings/ into site/, with a landing page.

Layout
------
    trainings/<name>/config.yml     # title, subtitle, length, order, episodes
    trainings/<name>/episodes/*.md  # the lesson pages
    trainings/<name>/images/        # optional assets

Each training builds into site/<name>/ (a self-contained lesson site), and a
landing page at site/index.html links them all.

Add a training   -> drop a new dir under trainings/ and rebuild.
Take one off      -> delete its dir, or set `published: false` in its config.yml.

    python3 build_site.py            # build everything into site/
    python3 build_site.py --serve    # build, then serve on :8000
"""
import html
import shutil
import sys
from pathlib import Path

import build  # reuse the single-lesson generator

ROOT = Path(__file__).resolve().parent
TRAININGS = ROOT / "trainings"
SITE = ROOT / "site"
ASSETS = ROOT / "assets"            # shared NRP brand assets (logo, favicon)


def copy_assets(dst):
    """Copy shared brand assets next to a page's style.css so logo/favicon
    resolve relatively at any URL depth (landing at site/, lessons at site/<name>/)."""
    dst.mkdir(parents=True, exist_ok=True)
    for f in ("nrp-logo.webp", "nrp-tiny.png"):
        src = ASSETS / f
        if src.exists():
            shutil.copy2(src, dst / f)


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
        items.append({
            "name": d.name,
            "dir": d,
            "title": cfg.get("title", d.name),
            "subtitle": cfg.get("subtitle", ""),
            "length": cfg.get("length", ""),
            "order": int(cfg.get("order", 999) or 999),
        })
    items.sort(key=lambda x: (x["order"], x["title"]))
    return items


def build_one(item):
    """Point build.py's globals at one training and build it into site/<name>/."""
    out = SITE / item["name"]
    build.ROOT = item["dir"]
    build.EPISODE_DIR = item["dir"] / "episodes"
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
        badge = (f'<span class="card-len">{html.escape(it["length"])}</span>'
                 if it["length"] else "")
        cards.append(
            f'<a class="card" href="{it["name"]}/index.html">'
            f'<h2>{html.escape(it["title"])} {badge}</h2>'
            f'<p>{html.escape(it["subtitle"])}</p></a>'
        )
    body = (
        '<header class="site-header">'
        '<a class="brand" href="https://nrp.ai">'
        '<img class="brand-logo" src="nrp-logo.webp" alt="National Research Platform" width="163" height="30"></a>'
        '<span class="site-title">Trainings</span></header>'
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
        '<link rel="icon" href="nrp-tiny.png">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=Inter:wght@400;500;600;700;800&display=swap">\n'
        '<link rel="stylesheet" href="style.css">\n</head>\n'
        f'<body>\n{body}\n</body>\n</html>\n'
    )
    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(doc, encoding="utf-8")
    (SITE / "style.css").write_text(build.STYLE + LANDING_CSS, encoding="utf-8")
    copy_assets(SITE)


LANDING_CSS = """
.hero { background:
    radial-gradient(1100px 400px at 15% -10%, rgb(1 97 239 / 35%), transparent 60%),
    linear-gradient(160deg, #0a1230 0%, var(--navy) 70%);
  color: #fff; padding: 64px 24px 72px; }
.hero-inner { max-width: 980px; margin: 0 auto; }
.hero h1 { color: #fff; font-size: 2.6rem; line-height: 1.1; margin: 0 0 14px;
  letter-spacing: -.02em; }
.hero-sub { color: rgb(229 236 246 / 82%); font-size: 1.18rem; max-width: 640px; margin: 0; }
.landing { max-width: 980px; margin: 0 auto; padding: 0 24px; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px; margin-top: -34px; margin-bottom: 40px; }
.card { display: block; border: 1px solid var(--border); border-radius: 16px;
  padding: 22px 24px; background: #fff; color: var(--fg);
  box-shadow: 0 6px 20px rgb(3 6 32 / 8%); transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease; }
.card:hover { text-decoration: none; border-color: var(--accent);
  transform: translateY(-3px); box-shadow: 0 12px 30px rgb(1 97 239 / 16%); }
.card h2 { margin: 0 0 8px; font-size: 1.2rem; line-height: 1.3; color: var(--navy); }
.card p { margin: 0; color: var(--muted); }
.card-len { font-size: .72rem; color: var(--accent); font-weight: 700;
  background: var(--accent-weak); border-radius: 999px; padding: 2px 10px;
  vertical-align: middle; white-space: nowrap; }
"""


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    items = discover()
    if not items:
        sys.exit("No published trainings found under trainings/")
    for it in items:
        print(f"==> {it['name']}")
        build_one(it)
    write_landing(items)
    print(f"\nLanding page + {len(items)} training(s) -> {SITE}/")
    for it in items:
        print(f"  - {it['name']}/  ({it['title']})")
    if "--serve" in sys.argv:
        build.SITE_DIR = SITE
        build.serve()


if __name__ == "__main__":
    main()
