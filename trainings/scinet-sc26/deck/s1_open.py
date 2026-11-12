"""Opening and 'What NRP Is': title, agenda, what is NRP, history, numbers.

Part of the SCinet deck: slides.py imports the section files in order. Shared constants and
helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
"""
from common import *  # noqa: F401,F403

# ═════════════════════════════════════════════════════════════════════════════════════
# OPENING
# ═════════════════════════════════════════════════════════════════════════════════════
TITLE = ["Inside the National", "Research Platform"]
TAGLINE = "How we build it, how we run it, and how you can use it"
SPEAKER = "**Daniel Diaz**  ·  San Diego Supercomputer Center, UC San Diego"
EVENT = "SCinet  ·  SC26  ·  Chicago  ·  November 2026"

add("Inside the National Research Platform", kind="title", notes="""
[0:00] Thanks for having me in the middle of the NOC move. I'm Daniel Diaz, from the San Diego Supercomputer Center. I'm one of the people who run the National Research Platform, and I also use it for my own machine-learning research.

You build a production network in a few weeks and then move it across a convention center. We run a Kubernetes cluster spread over more than a hundred sites, mostly on research and education networks. So today is less about what a notebook is, and more about how it's built and run: the network underneath, GitOps, CI, NetBox, monitoring, and the AI service on top. Then how you can use it, and a short live demo.
""")

# The agenda's nautilus (the cluster's name): a logarithmic-spiral shell that draws itself, then grows its
# chambers one by one. Geometry in pixels on a w x h box; the PowerPoint gets the same drawing as a PNG.
NAUT_B = math.log(3.0) / (2 * math.pi)          # a real nautilus widens about 3x per turn
NAUT_T0, NAUT_T1 = 0.35 * math.pi, 4.45 * math.pi  # the spiral's start and end angle


def naut_geom(w, h):
    sc = 0.95 * min(w, h) / (2.0 * math.exp(NAUT_B * NAUT_T1))
    cx, cy = w * 0.47, h * 0.5

    def pt(th):
        r = sc * math.exp(NAUT_B * th)
        return cx + r * math.cos(th), cy - r * math.sin(th)

    n = 260
    spiral = [pt(NAUT_T0 + (NAUT_T1 - NAUT_T0) * i / n) for i in range(n + 1)]
    spiral.append(pt(NAUT_T1 - 2 * math.pi))                      # the aperture: back to the whorl below
    inner = [pt(NAUT_T1 - 2 * math.pi + 2 * math.pi * i / 120) for i in range(121)]   # the outer turn: the silhouette
    septa = []
    th = NAUT_T0 + 2 * math.pi + 0.3
    while th < NAUT_T1 - 0.6:
        (x1, y1), (x2, y2) = pt(th), pt(th - 2 * math.pi)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        tx, ty = -math.sin(th), -math.cos(th)                 # tangent, toward smaller angles: bulge back
        d = math.hypot(x2 - x1, y2 - y1) * 0.32
        septa.append(((x1, y1), (mx + tx * d, my + ty * d), (x2, y2)))
        th += 0.3
    return spiral, inner, septa


def naut_svg(w, h):
    spiral, inner, septa = naut_geom(w, h)
    f = lambda pts: "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)          # noqa: E731
    body = f(inner) + "Z"                                                          # the silhouette, filled
    sep = "".join(f'<path class="sep" style="--d:{1.4 + i * 0.11:.2f}s" d="M{a[0]:.1f},{a[1]:.1f} Q{b[0]:.1f},'
                  f'{b[1]:.1f} {c[0]:.1f},{c[1]:.1f}"/>' for i, (a, b, c) in enumerate(septa))
    css = """<style>
.naut svg { overflow: visible; }
.naut .body { fill: url(#nautfill); opacity: 0; transition: opacity 1.2s ease 1.2s; }
.naut .shell { fill: none; stroke: var(--navy); stroke-width: 5; stroke-linecap: round; stroke-dasharray: 1;
  stroke-dashoffset: 1; transition: stroke-dashoffset 2.2s cubic-bezier(.4,0,.2,1) .2s; }
.naut .sep { fill: none; stroke: var(--blue); stroke-width: 3; opacity: 0; transition: opacity .35s ease var(--d); }
.slide.active .naut .body { opacity: 1; } .slide.active .naut .shell { stroke-dashoffset: 0; }
.slide.active .naut .sep { opacity: .85; }
.slide.active .naut svg { animation: nautbob 7s ease-in-out 4s infinite; transform-origin: 47% 50%; }
@keyframes nautbob { 0%, 100% { transform: rotate(0deg); } 50% { transform: rotate(-4deg) translateY(-6px); } }
</style>"""
    return (css + f'<svg width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}"><defs>'
            '<linearGradient id="nautfill" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FDEBE3"/>'
            '<stop offset="1" stop-color="#DDE8F2"/></linearGradient></defs>'
            f'<path class="body" d="{body}"/>{sep}<path class="shell" pathLength="1" d="{f(spiral)}"/></svg>')


def naut_png(w_in, h_in):
    out = FIG / "nautilus.png"
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    w, h = w_in * 100, h_in * 100
    spiral, inner, septa = naut_geom(w, h)
    fig = plt.figure(figsize=(w_in, h_in), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.axis("off")
    ax.add_patch(Polygon(inner, closed=True, facecolor="#F3EDE9", edgecolor="none"))
    for a, b, c in septa:
        ts = [i / 20 for i in range(21)]
        ax.plot([(1 - s) ** 2 * a[0] + 2 * (1 - s) * s * b[0] + s * s * c[0] for s in ts],
                [(1 - s) ** 2 * a[1] + 2 * (1 - s) * s * b[1] + s * s * c[1] for s in ts], color="#00629B", lw=1.6)
    ax.plot([x for x, _ in spiral], [y for _, y in spiral], color="#182B49", lw=2.6, solid_capstyle="round")
    fig.savefig(out, transparent=True)
    plt.close(fig)
    return out


NW, NH = 3.9, 3.7
NAUTILUS = [Raw(8.75, TOP + 0.1, NW, NH, naut_svg(NW * PX, NH * PX), cls="naut",
                draw=lambda s, k: s.image(naut_png(NW, NH), 8.75, TOP + 0.1, NW, NH)),
            Text(8.75, TOP + 3.9, NW, 0.35, T("Nautilus: the name of NRP's cluster", size=14, color=MUTED,
                                               align="c"))]

add("Agenda", [
    Bullets(X0, TOP + 0.15, 7.6, 4.6, [
        "What is NRP?",
        "How it's built: the network, storage, hardware, ingress",
        "How we run it: deploying services, CI in VMs, NetBox, monitoring, perfSONAR, security, sharing GPUs",
        "AI: the LLM service, from the gateway to the GPUs, and an ops bot built on it",
        "Using it yourself",
        "Live demo, then questions"], size=22, gap=12, cls="stagger"),
    *NAUTILUS,
    Text(X0, 5.85, 12.1, 0.4, T("Slides and the demo notebook:", size=18)),
    Link(X0, 6.25, 12.1, 0.4, "https://training.nrp-nautilus.io/scinet-sc26", size=18),
], notes="""
[0:01] The plan: a few minutes on what NRP is, for anyone new to it. Then the part I think you'll care about most: how it's built and how we run it. Then the AI service, which is the most interesting system we run right now. Then how you'd use it, a short demo, and questions. Interrupt any time.
""")

# ═════════════════════════════════════════════════════════════════════════════════════
# WHAT NRP IS
# ═════════════════════════════════════════════════════════════════════════════════════
section("What NRP Is", "[0:02] Quick context first.")


def is_i2(site):
    """Internet2 hosts nodes in its own locations; the dashboard names those sites "Internet2 ..."."""
    return site.get("name", "").replace(" ", "").lower().startswith("internet2")


I2_CSS = """<style>
.whatnrp .usmap .pin.i2 use { transition: fill .5s; }
.whatnrp:not([data-cur="0"]) .usmap .pin.i2 use { fill: var(--orange); transition-delay: 2.4s; }
.whatnrp:not([data-cur="0"]) .usmap .pin.i2 { animation: i2pulse .9s ease 2.4s 1; }
@keyframes i2pulse { 0%, 100% { transform: none; } 45% { transform: scale(1.7); } }
.whatnrp .i2key { color: var(--orange); font-weight: 700; }
</style>"""


def usmap_html(geo, kinds=("ops", "other")):
    w, h = geo["width"], geo["height"]
    land = "".join("M" + "L".join(f"{x:g},{y:g}" for x, y in pts) + "Z" for pts in geo["paths"])
    svg = (f'<svg class="usmap" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}">'
           f'<path class="land" d="{land}"/><defs>'
           + "".join(f'<path id="pin-{k}" d="{pin_path(r)}"/>' for k, (_, r) in PIN_STYLE.items()) + "</defs>")
    ops = [p for p in geo["pins"] if p["kind"] == "ops"]
    for p in sorted(geo["pins"], key=lambda p: p["kind"] == "ops"):
        if p["kind"] not in kinds:
            continue
        r = PIN_STYLE[p["kind"]][1]
        d = 0.35 + 0.3 * ops.index(p) if p in ops else 0.05 + 1.6 * p["x"] / w
        i2 = " i2" if is_i2(p) else ""
        svg += (f'<g transform="translate({p["x"]:.1f},{p["y"]:.1f})"><g class="pin k-{p["kind"]}{i2}" '
                f'style="--d:{d:.2f}s"><use href="#pin-{p["kind"]}"/><circle cy="{-1.6 * r:.1f}" '
                f'r="{0.38 * r:.1f}"/></g></g>')
    for p in ops:
        dx, dy, anchor = LABEL_AT[p["label"]]
        svg += (f'<text class="pl" style="--d:{0.6 + 0.3 * ops.index(p):.2f}s" x="{p["x"] + dx:.1f}" '
                f'y="{p["y"] + dy:.1f}" text-anchor="{anchor}" dominant-baseline="central">{escape(p["label"])}</text>')
    return svg + "</svg>"


def map_draw(s, k):
    s.image(FIG / f"map_{min(k, 1)}.png", 6.55, TOP + 0.45, 6.18, 4.1, align="r", valign="t")


add("What is NRP?", [
    Bullets(X0, TOP + 0.15, 5.7, 5.2, [
        ("One national **Kubernetes** cluster, **Nautilus**, for research and education", 0, 0),
        ("Operated by SDSC (UC San Diego), Nebraska–Lincoln and MGHPCC; funded by NSF", 0, 0),
        ("Hardware from 70+ institutions, on research and education networks", 0, 1),
        (f"Internet2 hosts {S['i2_nodes']} nodes in {S['i2_sites']} of its own locations (orange)", 1, 1),
        ("Today:", 0, 1), (f"{NODES} nodes at {SITES} sites", 1, 1),
        (f"{GPUS:,} GPUs in {GPU_MODELS} models; {CORES:,} CPUs", 1, 1),
        (f"{PB:.0f} PB of raw Ceph storage", 1, 1),
        ("Free for non-commercial research and education", 0, 2),
        ("One team runs it from the OS up; campuses keep priority on what they contribute", 0, 2)], size=18, gap=7),
    Link(6.55, TOP + 0.05, 6.18, 0.3, "https://dash.nrp-nautilus.io", size=14, align="r"),
    Raw(6.55, TOP + 0.45, 6.18, 4.1, I2_CSS + usmap_html(GEO), draw=map_draw),
    Text(6.55, TOP + 4.6, 6.18, 0.5, [T(f"Sites from the NRP dashboard, {SNAP}", size=12, color=MUTED, align="r"),
                                      T(offmap_note(GEO), size=12, color=MUTED, align="r")], step=1),
    Text(X0, 6.74, 7.0, 0.2, T(f"Nodes, GPUs, CPUs (hardware threads) and storage: cluster snapshot, {SNAP}", size=10, color=MUTED)),
], steps=2, cls="whatnrp", builds=True, notes=f"""
[0:02] NRP is one Kubernetes cluster, called Nautilus, for research and education. Three sites operate it: SDSC at UC San Diego, Nebraska, and MGHPCC in Massachusetts, and NSF funds it.

[click] The hardware comes from more than seventy institutions, and it sits on research and education networks. The orange pins are Internet2's own locations: Internet2 hosts {S['i2_nodes']} of our nodes in {S['i2_sites']} of its sites, so the backbone itself is part of the cluster. Every pin is a real site, from the dashboard's own data: {SITES} sites, {NODES} nodes, {GPUS:,} GPUs in {GPU_MODELS} models, about {CORES // 1000} thousand CPUs and {PB:.0f} petabytes of raw Ceph. A few more sites are off this map, in Hawaii, Guam, Korea, Brazil and Europe.

[click] It's free for non-commercial research and education. The model is a potluck: a campus contributes nodes and keeps priority on them, idle capacity is shared, and one team operates the whole stack, so a campus with hardware but no Kubernetes team can still take part.
""")

# Containers and Kubernetes (from the UCLA deck): layers stack into an image, the cluster appears,
# and a container lifts off the image and lands on a GPU node
K8S_CSS = """<style>
.k8sintro .layer.on { transform: none; }
.k8sintro .kcl { width: 100%; height: 100%; border: 2px solid #B9C7D8; border-radius: 10px; padding: 18px 28px; }
.k8sintro .kcl .knode { background: #fff; border: 2px solid #C9D4E3; border-radius: 10px; height: 144px; margin-top: 28px;
  padding: 22px; display: flex; flex-direction: column; justify-content: center; }
.k8sintro .kcl .knode b { font-size: 28px; color: var(--navy); } .k8sintro .kcl .knode span { font-size: 24px; }
.k8sintro .chip { width: 100%; height: 100%; background: #FDEBE3; color: var(--navy); border: 4px solid var(--orange);
  border-radius: 14px; font: 700 22px/1 var(--f-body); display: flex; align-items: center; justify-content: center;
  text-align: center; padding: 6px; box-shadow: 0 6px 18px rgba(0,0,0,.2); }
.k8sintro .imgbox { width: 100%; height: 100%; overflow: visible; }
.k8sintro .imgbox rect { fill: none; stroke: var(--orange); stroke-width: 5; stroke-dasharray: 1; stroke-dashoffset: 1;
  transition: stroke-dashoffset 1s ease .1s; }
.k8sintro [data-s].on .imgbox rect { stroke-dashoffset: 0; }
.k8sintro .karr { position: absolute; left: 0; right: 0; top: 50%; height: 4px; margin-top: -2px; background: var(--muted); }
.k8sintro .karr::after { content: ""; position: absolute; right: -2px; top: -9px; border: 11px solid transparent;
  border-left: 16px solid var(--muted); border-right: 0; }
.k8sintro .mover { transition: left 1.1s cubic-bezier(.5,0,.2,1), top 1.1s cubic-bezier(.5,0,.2,1),
  width 1.1s cubic-bezier(.5,0,.2,1), height 1.1s cubic-bezier(.5,0,.2,1), opacity .3s, transform .3s; }
.k8sintro[data-cur="4"] .mover { left: 1625px !important; top: 539px !important; width: 151px !important;
  height: 86px !important; }
</style>"""
LAYERS = [("app.py", "your code"), ("PyTorch, NumPy", None), ("CUDA libraries", None), ("Linux userland", None)]
KNODES = [("Node", "64 CPU cores"), ("Node", "8 × A10 GPUs"), ("Node", "4 × A100 GPUs")]
k8s = [Bullets(X0, TOP + 0.15, 5.3, 5.2, [
    ("**Container image:** an app and everything it needs, built once from a Dockerfile; runs the same anywhere",
     0, None),
    ("**Kubernetes** runs containers across many machines: you declare what you want (an image, CPUs, memory, "
     "a GPU), the **scheduler** picks a **node** that has it, and controllers keep it that way", 0, 3),
    ("A running container is a **pod**. Pods, Jobs, Deployments and Services live in a **namespace**: one per "
     "lab, course or service", 0, 4),
    (f"NRP is one Kubernetes cluster: {NODES} nodes", 0, 4)], size=18, gap=10),
    Raw(0, 0, 0.1, 0.1, K8S_CSS, pptx=False)]
for i, (h, sub_) in enumerate(reversed(LAYERS)):                  # bottom layer first
    k = len(LAYERS) - 1 - i
    k8s.append(Box(6.25, TOP + 0.75 + k * 0.68, 2.55, 0.6, h, sub_, state="active" if k == 0 else "normal",
                   head_size=15, sub_size=11.5, step=1, cls="layer", style=f"transition-delay:{i * 0.18:.2f}s"))
k8s += [Text(6.15, TOP + 0.2, 2.75, 0.4, T("Container image", size=17, bold=True, color=ORANGE, align="c"), step=2),
        Raw(6.15, TOP + 0.63, 2.75, 2.86, '<svg class="imgbox" viewBox="0 0 396 412"><rect x="3" y="3" width="390" '
            'height="406" rx="16" pathLength="1"/></svg>', step=2,
            draw=lambda s, k: s.rect(6.15, TOP + 0.63, 2.75, 2.86, fill=None, radius=0.06, line=ORANGE)),
        Text(6.15, TOP + 3.58, 2.75, 0.5, T("built once, from a Dockerfile", size=14, color=BODY, align="c"), step=2),
        Raw(8.98, TOP + 1.95, 0.45, 0.2, '<div class="karr"></div>', step=3,
            draw=lambda s, k: s.line(8.98, TOP + 2.05, 9.43, TOP + 2.05, color=MUTED, width=2.5, arrow=True))]
kcl = '<div class="kcl"><p class="dh l" style="font-size:30px">Kubernetes cluster</p>' + "".join(
    f'<div class="knode"><b>{h}</b><span>{b}</span></div>' for h, b in KNODES) + "</div>"


def kcl_draw(s, k):
    Frame(9.55, TOP + 0.15, 3.18, 4.35, label="Kubernetes cluster", line="B9C7D8").pptx(s, k)
    for i, (h, b) in enumerate(KNODES):
        Box(9.72, TOP + 0.62 + i * 1.19, 2.84, 1.0, h, b, state="white", head_size=14, sub_size=12).pptx(s, k)
    Box(11.35, TOP + 1.98, 1.05, 0.66, "your container", None, state="orange", head_size=10).pptx(s, k)


k8s += [Raw(9.55, TOP + 0.15, 3.18, 4.35, kcl, step=3, draw=kcl_draw),
        Text(9.55, TOP + 4.55, 3.18, 0.5, T("the scheduler picks a node with a free GPU", size=13, color=MUTED,
                                            align="c"), step=3),
        Raw(6.15, TOP + 0.63, 2.75, 2.86, '<div class="chip">your container</div>', step=4, cls="mover",
            pptx=False)]
add("Containers and Kubernetes", k8s, steps=4, cls="k8sintro", secs=60, notes="""
A quick word on what "one Kubernetes cluster" means, since everything after this builds on it. [click] A container image packs an application with everything it needs, the libraries, CUDA, a Linux userland. [click] It's built once from a Dockerfile and runs the same on a laptop or on any node.

[click] Kubernetes runs containers across many machines. You declare what you want, an image, CPUs, memory, a GPU; the scheduler finds a node that has it, and controllers keep the declared state true: if a pod dies, it's replaced.

[click] A running container is a pod. Pods, Jobs, Deployments and Services all live in a namespace, and on NRP every lab, course and service gets its own; more on that when we get to access. NRP is one Kubernetes cluster of all those nodes.
""")

MILESTONES = [("2015", "Pacific Research Platform", "Data transfer nodes (FIONAs) in campus Science DMZs, on CENIC and "
               "Pacific Wave", "OAC-1541349"),
              ("2018", "Toward a National Research Platform", "The same model, beyond the West Coast",
               "OAC-1826967"),
              ("2021", "National Research Platform", "An NSF Category II resource: GPUs, storage and services for "
               "research and education", "OAC-2112167"),
              ("2026", "Today", f"One Kubernetes cluster, Nautilus: {NODES} nodes at {SITES} sites, and AI models "
               "as a service", "")]
tl = [Arrow(X0, TOP + 1.25, X1, TOP + 1.25, color="B9C7D8", width=3, head=True)]
for i, (yr, head, body, award) in enumerate(MILESTONES):
    x = X0 + i * 3.05
    tl += [Frame(x + 0.02, TOP + 1.13, 0.24, 0.24, fill=BLUE if i < 3 else ORANGE, line=None, radius=0.5, step=i),
           Text(x, TOP + 0.2, 2.9, 0.8, T(yr, size=44, font=TEKO, color=BLUE if i < 3 else ORANGE, line=0.8), step=i),
           Text(x, TOP + 1.6, 2.85, 3.0, [T(head, size=18, bold=True, color=NAVY, line=1.0),
                                          T(body, size=15, color=BODY, before=6),
                                          T(award, size=12, color=MUTED, before=8)], step=i)]
tl.append(Text(X0, 6.2, W, 0.4, T("Under each milestone: its NSF award.", size=13, color=MUTED), step=3))
add("From PRP to NRP", tl, steps=3, optional=True, notes="""
[0:03] Where it came from, because it explains why it's built on the network the way it is. It started in 2015 as the Pacific Research Platform: put data transfer nodes, called FIONAs, in campus Science DMZs, connected by CENIC and Pacific Wave, and make disk-to-disk transfers between campuses actually fast.

[click] In 2018 the same idea went national.

[click] In 2021 NSF funded NRP as a Category II resource, which is when GPUs, storage and services became the point, not just data movement.

[click] And today it's one Kubernetes cluster, Nautilus, the one you saw on the map, plus AI models served as a service.
""")

stats = [(NODES, "nodes", 0, ""), (SITES, "sites on the dashboard", 0, ""), (GPUS, f"GPUs in {GPU_MODELS} models", 0, ""),
         (CORES, "CPUs (hardware threads)", 0, ""), (PB, f"raw Ceph in {len(S['ceph'])} clusters", 1, " PB"),
         (S["namespaces"], "namespaces: labs, courses, services", 0, "")]
st_els = []
for i, (v, lab, dec, suf) in enumerate(stats):
    cx, cy = X0 + (i % 3) * 4.1, TOP + 0.3 + (i // 3) * 2.2
    st_els += [Frame(cx, cy, 3.85, 1.95, fill=CARD, line=None, radius=0.06),
               Stat(cx + 0.3, cy + 0.25, 3.4, 1.6, v, lab, dec=dec, suffix=suf, big=58, label_size=17)]
st_els.append(Text(X0, 6.25, W, 0.3, T(f"Cluster snapshot, {SNAP} (Kubernetes {S['k8s']}). Sites: the NRP "
                                       f"dashboard.", size=12, color=MUTED)))
add("NRP in Numbers", st_els, cls="numbers", notes=f"""
[0:04] The same thing in numbers, from a snapshot I took this week: {NODES} nodes, {SITES} sites, {GPUS:,} GPUs in {GPU_MODELS} different models, which tells you it's built from what campuses buy, not from one procurement. About {CORES // 1000} thousand CPUs, {PB:.0f} petabytes of raw Ceph across {len(S['ceph'])} clusters, and {S['namespaces']:,} namespaces: every lab, course and service gets its own.
""")
