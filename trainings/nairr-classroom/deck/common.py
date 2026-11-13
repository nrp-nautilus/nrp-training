"""Shared constants and helpers for the webinar deck's section files (s1_open.py ... s6_backup.py).

Numbers come from data/snapshot.json (snapshot.py, read-only queries against the cluster) and the
site list in data/nrp_sites.json (the NRP dashboard's API). Slides marked optional=True are the
first to cut if the talk runs long; deck/README.md lists them.
"""
import json
import math
from datetime import date
from html import escape
from pathlib import Path

from deckkit import BLUE, BODY, CARD, GOLD, LIGHT, MONO, MUTED, NAVY, ORANGE, SANS, TEKO, WHITE, P
from elements import (AMBER, GREEN, PX, RED, Arrow, Box, Bullets, Code, Frame, Image, Link, Raw, Slide, Stat, T,
                      Table, Text, md, pos)
from make_map import LABEL_AT, LABEL_PX, PIN_STYLE, geometry, llm_sites, model_name, offmap_note, pin_path
from sweep import RUN_CAPTION, RUN_CMD, RUN_JOB, RUN_WAYS, SWEEP, SWEEP_T

HERE = Path(__file__).resolve().parent
IMG = HERE / "assets" / "images"
FIG = HERE / "figures"
S = json.loads((HERE / "data" / "snapshot.json").read_text())
SNAP = f"{date.fromisoformat(S['date']):%-d %b %Y}"

TOP, X0, X1, W = 1.45, 0.6, 12.73, 12.13
NODES, GPUS, GPU_MODELS, CORES = S["nodes"], S["gpus"], S["gpu_models"], S["cores"]
PB = sum(c["total"] for c in S["ceph"]) / 1e15
GEO = geometry(890)
SITES = GEO["n_sites"]
APPS = [a for a in S["argo_apps"] if a["name"] != "guestbook"]          # guestbook is Argo's own example
MODEL_NAMES = sorted({m for r in S["llm_routes"] for m in r["models"]})
TASKS = ["agents", "coding", "general", "reasoning", "vision", "long-context", "kubernetes", "cuda", "service"]
TOKENS_A_DAY = "7.1 billion"          # September 2026 average, from the HPC-CI webinar (as in the UCLA deck)

SLIDES = []


SECONDS = {}          # slide title -> seconds, for the "[h:mm]" timing tags (see slides.py)


def add(*a, secs=None, **kw):
    SLIDES.append(Slide(*a, **kw))
    if secs is not None:
        SECONDS[SLIDES[-1].title] = secs


def section(title, notes, secs=None):
    add(title, kind="section", notes=notes, secs=secs)


def sub(x, y, w, h, inner, cls="", style="", attrs=""):
    """A positioned child inside a Raw element (inches relative to the Raw's top-left)."""
    return f'<div class="sb {cls}" {attrs} style="{pos(x, y, w, h)}{style}">{inner}</div>'


def short_gpu(p):
    for a in ["H100", "H200", "A100", "A6000", "A10", "L40", "V100"]:
        if a in p:
            return a
    return p


# ── shared animation helpers (HTML only; the PowerPoint shows the final state without them) ──────────
_UID = [0]


def packet(slide_cls, stops, size=28, speed=7.0, color="var(--gold)", loop=False, z=6):
    """A dot that travels a path at each build step, then waits at the path's last point.

    stops: {step: [(x, y), ...]} in inches on the slide. At a step with a path the dot runs along it
    (first point to last) at `speed` inches a second; at steps without one it's hidden. loop=True
    replays the path forever (with a short pause), for continuous traffic.
    Returns a full-slide Raw element; add it to the slide's element list.
    """
    _UID[0] += 1
    k_id = f"pk{_UID[0]}"
    css = (f".{k_id} {{ position:absolute; width:{size}px; height:{size}px; margin:-{size / 2:.0f}px 0 0 -{size / 2:.0f}px; "
           f"border-radius:50%; background:{color}; border:4px solid var(--navy); box-shadow:0 3px 10px rgba(0,0,0,.25); "
           f"opacity:0; z-index:{z}; }}\n")
    for k, pts in stops.items():
        d = [0.0]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            d.append(d[-1] + math.hypot(x2 - x1, y2 - y1))
        total = d[-1] or 1
        dur = max(total / speed, 0.01)
        frames = "".join(f"{(dd / total) * (88 if loop else 100):.1f}% {{ left:{x * PX:.0f}px; top:{y * PX:.0f}px; }} "
                         for dd, (x, y) in zip(d, pts))
        if loop:
            frames += f"100% {{ left:{pts[-1][0] * PX:.0f}px; top:{pts[-1][1] * PX:.0f}px; }}"
        css += f"@keyframes {k_id}_{k} {{ {frames} }}\n"
        anim = (f"{k_id}_{k} {dur / (0.88 if loop else 1):.2f}s linear .25s infinite" if loop
                else f"{k_id}_{k} {dur:.2f}s cubic-bezier(.45,0,.3,1) .25s both")
        css += (f".{slide_cls}[data-cur=\"{k}\"] .{k_id} {{ opacity:1; left:{pts[-1][0] * PX:.0f}px; "
                f"top:{pts[-1][1] * PX:.0f}px; animation:{anim}; }}\n")
    return Raw(0, 0, 13.333, 7.5, f'<style>{css}</style><span class="{k_id}"></span>', pptx=False,
               style="pointer-events:none;z-index:6;")


def flow(paths, n=3, dur=1.8, r=8, color="#EB6834", step=None, only=None):
    """Dots that stream along each path forever (continuous traffic), as an SVG over the whole slide.

    paths: [[(x, y), ...], ...] in inches. Show it from a step (step=k) or at some steps (only=[...]).
    """
    svg = '<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;left:0;top:0;overflow:visible">'
    for pts in paths:
        d = "M" + " L".join(f"{x * PX:.0f},{y * PX:.0f}" for x, y in pts)
        for i in range(n):
            svg += (f'<circle r="{r}" fill="{color}" stroke="#fff" stroke-width="2.5"><animateMotion path="{d}" '
                    f'dur="{dur}s" begin="{-i * dur / n:.2f}s" repeatCount="indefinite"/></circle>')
    return Raw(0, 0, 13.333, 7.5, svg + "</svg>", pptx=False, step=step, only=only,
               style="pointer-events:none;z-index:5;")
