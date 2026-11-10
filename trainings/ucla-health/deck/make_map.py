"""The NRP site map for "What is NRP?": real site locations on a plain map of the US states.

    python3 deck/make_map.py --refresh   # re-download the site list from dash.nrp-nautilus.io/api/nodes
    python3 deck/make_map.py             # -> figures/map_0.png ... map_2.png (the PowerPoint builds)

Sites and coordinates come from the NRP dashboard's own API (the data behind the map at
dash.nrp-nautilus.io), saved in data/nrp_sites.json. State outlines are the US Census
boundaries packaged as us-atlas (data/us-states-10m.json). Sites outside the contiguous US
(Hawaii, Guam, Korea, Brazil, Europe) are listed, not drawn.

build_html.py imports geometry() from here, so the HTML and PowerPoint maps match.
"""
import json
import math
import sys
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SITES = DATA / "nrp_sites.json"
TOPO = DATA / "us-states-10m.json"
FIG = HERE / "figures"

OPS = {"sdsc": "UC San Diego", "unl": "Nebraska–Lincoln", "100-bigelow": "MGHPCC"}   # who runs NRP
UCLA = "ucla"
NOT_DRAWN = {"Alaska", "Hawaii", "Puerto Rico", "Guam", "American Samoa", "Commonwealth of the Northern Mariana Islands",
             "United States Virgin Islands"}


def refresh():
    with urllib.request.urlopen("https://dash.nrp-nautilus.io/api/nodes", timeout=60) as r:
        raw = json.load(r)
    sites = [dict(name=s["name"], site=s["siteName"], slug=s["slug"], lat=s["latitude"], lon=s["longitude"],
                  nodes=len(s["nodes"]), gpus=sum(int(n.get("gpus") or 0) for n in s["nodes"])) for s in raw]
    SITES.write_text(json.dumps(dict(source="https://dash.nrp-nautilus.io/api/nodes", date=str(date.today()),
                                     sites=sites), indent=1))
    print(f"{SITES}  ({len(sites)} sites)")


# ── Albers equal-area conic, the usual projection for the contiguous US ───────────────
P1, P2, LAT0, LON0 = map(math.radians, (29.5, 45.5, 37.5, -96.0))
N = (math.sin(P1) + math.sin(P2)) / 2
C = math.cos(P1) ** 2 + 2 * N * math.sin(P1)
RHO0 = math.sqrt(C - 2 * N * math.sin(LAT0)) / N


def albers(lon, lat):
    rho = math.sqrt(C - 2 * N * math.sin(math.radians(lat))) / N
    th = N * (math.radians(lon) - LON0)
    return rho * math.sin(th), RHO0 - rho * math.cos(th)          # y points up


def states():
    """Contiguous-US state rings as lists of (lon, lat), decoded from TopoJSON."""
    t = json.loads(TOPO.read_text())
    (sx, sy), (tx, ty) = t["transform"]["scale"], t["transform"]["translate"]
    arcs = []
    for arc in t["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x, y = x + dx, y + dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idx):
        out = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(a if not out else a[1:])
        return out

    rings = []
    for g in t["objects"]["states"]["geometries"]:
        if g["properties"]["name"] in NOT_DRAWN:
            continue
        polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
        for poly in polys:
            rings.extend(ring(r) for r in poly)
    return rings


def geometry(width):
    """Everything both builders need, in pixels with y down, for a map `width` pixels wide."""
    rings = [[albers(*p) for p in r] for r in states()]
    xs = [x for r in rings for x, _ in r]
    ys = [y for r in rings for _, y in r]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    padl, padr, padt, padb = 0.07, 0.03, 0.03, 0.09          # room for the labels at the edges
    k = width / ((x1 - x0) * (1 + padl + padr))
    height = (y1 - y0) * k * (1 + padt + padb)

    def px(x, y):
        return (x - x0) * k + width * padl / (1 + padl + padr), (y1 - y) * k + (y1 - y0) * k * padt

    paths = []
    for r in rings:
        pts, last = [], None
        for p in r:
            q = tuple(round(v, 1) for v in px(*p))
            if q != last:
                pts.append(q)
                last = q
        if len(pts) > 2:
            paths.append(pts)
    sites = json.loads(SITES.read_text())
    on, off, seen = [], [], set()
    for s in sites["sites"]:
        if s["lat"] is None:
            continue
        if not (24 < s["lat"] < 50 and -125 < s["lon"] < -66):
            off.append(s)
            continue
        x, y = px(*albers(s["lon"], s["lat"]))
        key = (round(x), round(y))
        kind = "ops" if s["slug"] in OPS else "ucla" if s["slug"] == UCLA else "other"
        if key in seen and kind == "other":
            continue                                        # same spot as a site already drawn
        seen.add(key)
        on.append(dict(s, x=x, y=y, kind=kind, label=OPS.get(s["slug"]) or ("UCLA" if kind == "ucla" else None)))
    on.sort(key=lambda s: s["x"])                           # pins drop west to east
    return dict(width=width, height=height, paths=paths, pins=on, offmap=off, date=sites["date"],
                n_sites=len(sites["sites"]))


# pin: a teardrop with its tip at (0, 0), pointing down (y down); r is the head radius
def pin_points(r, n=24):
    d = 1.6 * r                                   # tip to the centre of the head
    th = math.acos(r / d)                         # where the sides touch the head
    a0, a1 = th - math.pi / 2, 3 * math.pi / 2 - th     # right side to left side, over the top
    pts = [(0.0, 0.0)]
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append((r * math.cos(a), -d - r * math.sin(a)))
    return pts


def pin_path(r):
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pin_points(r)) + " Z"


PIN_STYLE = {"ops": ("#182B49", 11), "ucla": ("#FFCD00", 11), "other": ("#00629B", 7.5)}
LABEL_PX = 26                                   # label size in map pixels
LABEL_AT = {"UC San Diego": (4, 24, "start"), "Nebraska–Lincoln": (0, 24, "middle"), "MGHPCC": (0, -46, "middle"),
            "UCLA": (-14, -14, "end")}          # dx, dy and text anchor, in map pixels


def offmap_note(g):
    places = ["Hawaii", "Guam", "Korea", "Brazil", "Europe"]
    return f"Not drawn: {len(g['offmap'])} sites in {', '.join(places[:-1])} and {places[-1]}"


def render_png(g, stage, out, scale=3):
    """stage 0: the three operator sites; 1: plus UCLA; 2: every site."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from matplotlib.patheffects import withStroke

    w, h = g["width"], g["height"]
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100 * scale)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    for pts in g["paths"]:
        ax.add_patch(Polygon(pts, closed=True, facecolor="#E6ECF3", edgecolor="white", linewidth=0.9))
    show = {"ops"} if stage == 0 else {"ops", "ucla"} if stage == 1 else {"ops", "ucla", "other"}
    order = sorted((p for p in g["pins"] if p["kind"] in show), key=lambda p: {"other": 0, "ucla": 1, "ops": 2}[p["kind"]])
    for p in order:
        col, r = PIN_STYLE[p["kind"]]
        ax.add_patch(Polygon([(x + p["x"], y + p["y"]) for x, y in pin_points(r)], closed=True, facecolor=col,
                             edgecolor="white" if p["kind"] != "ucla" else "#182B49", linewidth=0.9))
        ax.add_patch(plt.Circle((p["x"], p["y"] - 1.6 * r), r * 0.38, color="white" if p["kind"] != "ucla" else "#182B49"))
    for p in order:
        if p["label"]:
            dx, dy, anchor = LABEL_AT[p["label"]]
            ax.text(p["x"] + dx, p["y"] + dy, p["label"], fontsize=LABEL_PX * 0.72, fontweight="bold", color="#182B49",
                    ha={"start": "left", "end": "right", "middle": "center"}[anchor], va="center", zorder=6,
                    path_effects=[withStroke(linewidth=4, foreground="white")], family="DejaVu Sans")
    fig.savefig(out, dpi=100 * scale, transparent=False, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    if "--refresh" in sys.argv:
        refresh()
    FIG.mkdir(exist_ok=True)
    geo = geometry(890)
    for st in range(3):
        render_png(geo, st, FIG / f"map_{st}.png")
    kinds = {k: sum(p["kind"] == k for p in geo["pins"]) for k in ("ops", "ucla", "other")}
    print(f"{FIG}/map_0..2.png  pins {kinds}, {len(geo['offmap'])} off the map; {offmap_note(geo)}")
