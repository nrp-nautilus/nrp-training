"""'What a Course Can Use': CPUs and GPUs, how GPUs are shared, storage, ways to run work, fair use.

Part of the NAIRR Classroom webinar deck: slides.py imports the section files in order. Shared constants
and helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
"""
from common import *  # noqa: F401,F403

RESV_NODES, RESV_GROUPS = 119, 23          # nodes with a nautilus.io/reservation taint, and groups, 11 Nov 2026
OPP_PODS, OPP_OSG = 232, 208               # running pods at opportunistic priority, and those in osg-opportunistic

section("Resources for Your Course", "The hardware, and the rules for sharing it.")

# ── What a Course Can Use ───────────────────────────────────────────────────────────────────────────────
SHORT = {"NVIDIA-A10": "A10", "NVIDIA-GeForce-RTX-3090": "RTX 3090", "NVIDIA-GeForce-RTX-2080-Ti": "RTX 2080 Ti",
         "NVIDIA-A100-SXM4-80GB": "A100 80 GB", "NVIDIA-A100-80GB-PCIe-MIG-1g.10gb": "A100 slice (10 GB)",
         "NVIDIA-L4": "L4", "NVIDIA-GeForce-GTX-1080-Ti": "GTX 1080 Ti", "Tesla-V100-SXM2-32GB": "V100 32 GB",
         "NVIDIA-L40": "L40", "NVIDIA-RTX-A6000": "RTX A6000"}
gpu_rows = [(SHORT.get(f["product"], f["product"]), f["gpus"]) for f in S["fleet"][:10]]
gmax = max(v for _, v in gpu_rows)


def gpu_html():
    h = ""
    for i, (lab, v) in enumerate(gpu_rows):
        h += (f'<div class="hb"><span class="hn" style="width:250px">{escape(lab)}</span><span class="ht">'
              f'<i class="t" style="--w:{v / gmax * 100:.1f}%;background:var(--blue);transition-delay:{i * 0.07:.2f}s">'
              f'</i><em>{v}</em></span></div>')
    return f'<style>.cuse .hb {{ height: 50px; }}</style><div class="hbars">{h}</div>'


def gpu_draw(s, k):
    for i, (lab, v) in enumerate(gpu_rows):
        y = TOP + 0.65 + i * 0.35
        s.text(6.55, y, 1.7, 0.35, P(lab, size=12, color=BODY, align="r"), anchor="m")
        bw = 3.3 * v / gmax
        s.rect(8.35, y + 0.06, max(bw, 0.02), 0.23, fill=BLUE, radius=0.1)
        s.text(8.42 + bw, y, 0.8, 0.35, P(str(v), size=12, color=MUTED), anchor="m")


use = [("CPUs", f"about {CORES // 1000} thousand; most coursework needs nothing else"),
       ("GPUs", f"{GPUS:,} in {GPU_MODELS} models, from classroom cards to A100s"),
       ("Storage", "a home folder per student, shared course data, S3"),
       ("AI models", "hosted open-weight LLMs behind an OpenAI-style API")]
cu = [Text(6.55, TOP + 0.1, 6.18, 0.45, T("GPUs on NRP, the ten most common models", size=17, bold=True, color=NAVY)),
      Raw(6.55, TOP + 0.6, 6.18, 3.6, gpu_html(), cls="cuse", draw=gpu_draw),
      Text(6.55, TOP + 4.25, 6.18, 0.6, T(f"Cluster snapshot, {SNAP}. Live view: nrp.ai/viz/resources", size=12,
                                          color=MUTED))]
for i, (h, b) in enumerate(use):
    cu.append(Box(X0, TOP + 0.15 + i * 1.22, 5.6, 1.05, h, b, head_size=19, sub_size=14, align="l", state="white",
                  cls="rise", style=f"transition-delay:{0.1 + i * 0.15:.2f}s"))
cu.append(Text(X0, TOP + 5.05, 12.1, 0.4, T("Ask for the kind of hardware the work needs, not the biggest card: "
                                            "most of a semester runs on CPUs.", size=16, color=BODY)))
add("What a Course Can Use", cu, secs=60, notes=f"""
What can a course use? CPUs first: about {CORES // 1000} thousand of them, and most coursework, pandas, scikit-learn, an intro to data science, never needs anything else. Then GPUs: {GPUS:,} of them in {GPU_MODELS} models. On the right are the most common: lots of A10s and RTX 3090s, which are great for teaching, and A100s when a unit really needs one. Storage: every student gets a home folder, and the course can share data. And hosted AI models, which students can call from a notebook. The rule of thumb: ask for the kind of hardware the work needs, not the biggest card.
""")


# ── Choosing GPUs for a course: memory decides what fits ────────────────────────────────────────────────
GPUMEM = [("A100 slice", 10, "NVIDIA-A100-80GB-PCIe-MIG-1g.10gb"), ("RTX 2080 Ti", 11, "NVIDIA-GeForce-RTX-2080-Ti"),
          ("A10", 24, "NVIDIA-A10"), ("RTX 3090", 24, "NVIDIA-GeForce-RTX-3090"), ("L4", 24, "NVIDIA-L4"),
          ("V100", 32, "Tesla-V100-SXM2-32GB"), ("L40", 48, "NVIDIA-L40"), ("RTX A6000", 48, "NVIDIA-RTX-A6000"),
          ("A100", 80, "NVIDIA-A100-SXM4-80GB")]
COUNT = {f["product"]: f["gpus"] for f in S["fleet"]}
WORK = [("Intro data science: pandas, scikit-learn", "CPUs only: 2 CPUs, 8 GB", "white"),
        ("Deep-learning labs: CNNs, small transformers", "one GPU with 10–24 GB", "gold"),
        ("Bigger models: fine-tuning, long training runs", "48–80 GB, fewer students at once", "orange"),
        ("Using LLMs, not training them", "no GPU: NRP's hosted models", "green")]
gc = []
for i, (h, b, st) in enumerate(WORK):
    gc.append(Box(X0, TOP + 0.15 + i * 1.12, 5.7, 0.95, h, b, state=st, head_size=16, sub_size=13.5, align="l",
                  step=i, hl=None))
gm = max(m for _, m, _ in GPUMEM)
bars = ""
for i, (n, m, key) in enumerate(GPUMEM):
    band = "b1" if m <= 24 else "b2"
    bars += (f'<div class="hb {band}"><span class="hn" style="width:190px">{escape(n)}</span><span class="ht">'
             f'<i class="t" style="--w:{m / gm * 100:.1f}%;transition-delay:{i * 0.06:.2f}s"></i>'
             f'<em>{m} GB · {COUNT.get(key, 0)} on NRP</em></span></div>')
gstyle = ('<style>.gpuchoice .hb { height: 48px; } .gpuchoice .hb .t { background: #C9D9EA; } '
          '.gpuchoice[data-cur="1"] .hb.b1 .t, .gpuchoice[data-cur="2"] .hb.b2 .t { background: var(--blue); } '
          '.gpuchoice[data-cur="1"] .hb.b1 .hn, .gpuchoice[data-cur="2"] .hb.b2 .hn { font-weight: 700; '
          'color: var(--navy); }</style>')


def gmem_draw(s, k):
    for i, (n, m, key) in enumerate(GPUMEM):
        y = TOP + 0.65 + i * 0.4
        lit = (k == 1 and m <= 24) or (k == 2 and m > 24)
        s.text(6.6, y, 1.4, 0.4, P(n, size=12, color=BODY, align="r", bold=lit), anchor="m")
        s.rect(8.1, y + 0.08, max(2.6 * m / gm, 0.02), 0.24, fill=BLUE if lit else "C9D9EA", radius=0.1)
        s.text(8.18 + 2.6 * m / gm, y, 2.0, 0.4, P(f"{m} GB · {COUNT.get(key, 0)} on NRP", size=11, color=MUTED),
               anchor="m")


gc += [Text(6.6, TOP + 0.1, 6.13, 0.45, T("GPU memory decides what fits", size=17, bold=True, color=NAVY)),
       Raw(6.6, TOP + 0.6, 6.13, 3.7, gstyle + f'<div class="hbars">{bars}</div>', draw=gmem_draw),
       Text(X0, TOP + 4.75, W, 0.7, T("Ask by memory and generation (say, more than 20 GB, Ampere or newer) rather "
                                      "than by name: more GPUs qualify, and students wait less.", size=16,
                                      color=BODY), step=2)]
add("Choosing GPUs for a Course", gc, steps=3, cls="gpuchoice", builds=True, secs=80, notes=f"""
Which GPU does a course need? Usually none. Intro data science, pandas, scikit-learn: CPUs only, two CPUs and eight gigs per student.

[click] Deep-learning labs, CNNs and small transformers: one GPU with 10 to 24 gigabytes of memory. That's the biggest group on NRP: A10s, RTX 3090s, L4s, and slices of an A100 with 10 gigabytes each, which let many students share one big card.

[click] Bigger models, fine-tuning or long training runs: 48 to 80 gigabytes, the L40s, A6000s and A100s, for fewer students at once. And a tip: ask by memory and generation, not by a specific name, so more GPUs qualify and students wait less.

[click] And if the course uses LLMs rather than training them, you don't need a GPU at all: the hosted models do that work, which I'll come back to.
""")


# ── Sharing GPUs: a reserved node (taint + toleration), then a shared node (opportunistic + preemption) ──
FA = (6.3, TOP + 0.1, 5.25, 2.05)          # reserved node frame
FB = (6.3, TOP + 2.4, 5.25, 2.05)          # shared node frame
SLOT_W, SLOT_H = 1.15, 1.25
CHIP = (11.7, 1.03)                        # x and width of the pods arriving from the right


def slot_x(f, j):
    return f[0] + 0.15 + j * (SLOT_W + 0.1)


def fair_html():
    ox, oy = FA[0], FA[1]

    def p(x, y, w, h):
        return f"left:{(x - ox) * PX:.0f}px;top:{(y - oy) * PX:.0f}px;width:{w * PX:.0f}px;height:{h * PX:.0f}px;"

    dxa = (slot_x(FA, 3) - CHIP[0]) * PX
    dxb = (slot_x(FB, 1) - CHIP[0]) * PX
    css = f"""<style>
.fairshare .fs {{ position:absolute; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; font:700 24px/1.1 var(--f-body); transition: background .5s, color .5s; }}
.fairshare .fs small {{ display:block; font-weight:400; font-size:18px; margin-top:4px; }}
.fairshare .fs .p {{ font-size:20px; }}
.fairshare .own {{ background:var(--navy); color:#fff; }}
.fairshare .res {{ background:repeating-linear-gradient(45deg,#E4E8EE 0 10px,#F1F3F6 10px 20px); color:#6B7480; }}
.fairshare .idle {{ background:#DDE1E6; color:#6B7480; }}
.fairshare .fs span {{ display:none; }}
.fairshare .idle .i {{ display:block; }}
.fairshare:not([data-cur="0"]) .idle {{ background:#F6D58C; color:var(--navy); }}
.fairshare:not([data-cur="0"]) .idle .i {{ display:none; }} .fairshare:not([data-cur="0"]) .idle .p {{ display:block; }}
.fairshare[data-cur="2"] .idle.g1 {{ background:var(--navy); color:#fff; animation: fs-pre 1.6s ease; }}
.fairshare[data-cur="2"] .idle.g1 .p {{ display:none; }} .fairshare[data-cur="2"] .idle.g1 .x {{ display:block; }}
@keyframes fs-pre {{ 0%, 55% {{ background:#F6D58C; color:var(--navy); }} 62%, 82% {{ background:var(--red); color:#fff; }} 100% {{ background:var(--navy); color:#fff; }} }}
.fairshare .chip {{ position:absolute; border-radius:12px; background:#fff; border:3px solid var(--navy); color:var(--navy); font:700 21px/1.15 var(--f-body); display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; z-index:4; }}
.fairshare .chip small {{ font-weight:400; font-size:17px; }}
.fairshare .ca .no {{ position:absolute; right:-10px; top:-14px; width:38px; height:38px; border-radius:50%; background:var(--red); color:#fff; font:700 26px/38px var(--f-body); opacity:0; }}
.fairshare.active .ca {{ animation: fs-try 2.6s ease .5s both; }}
.fairshare.active .ca .no {{ animation: fs-no .3s ease 2.2s forwards; }}
@keyframes fs-try {{ 0% {{ transform:none; }} 40%, 52% {{ transform:translateX({dxa:.0f}px); border-color:var(--navy); }} 58% {{ transform:translateX({dxa:.0f}px); border-color:var(--red); background:#F6D6D3; }} 85%, 100% {{ transform:none; border-color:var(--red); background:#F6D6D3; }} }}
@keyframes fs-no {{ to {{ opacity:1; }} }}
.fairshare .cb {{ opacity:0; background:var(--navy); color:#fff; border-color:var(--navy); }}
.fairshare[data-cur="2"] .cb {{ animation: fs-in 1.6s ease .2s both; }}
@keyframes fs-in {{ 0% {{ opacity:1; transform:none; }} 55% {{ opacity:1; transform:translateX({dxb:.0f}px); }} 70%, 100% {{ opacity:0; transform:translateX({dxb:.0f}px); }} }}
</style>"""
    h = css
    for f, lab, kinds in [(FA, "Reserved node · taint <code>nautilus.io/reservation=lab-a</code>",
                           ["own", "own", "res", "res"]),
                          (FB, "Shared node: no taint", ["own", "idle", "idle", "idle"])]:
        h += (f'<div class="fs-fr" style="position:absolute;{p(*f)}border:3px solid #B9C7D8;border-radius:12px;">'
              f'<span style="position:absolute;left:18px;top:8px;font:700 26px var(--f-body);color:var(--navy)">{lab}'
              f'</span></div>')
        for j, kd in enumerate(kinds):
            inner = {"own": ("lab-a pod" if f is FA else "a user's job") + "<small>GPU in use</small>",
                     "res": "idle<small>reserved</small>",
                     "idle": ('<span class="i">idle</span><span class="p">opportunistic<small>OSG job</small></span>'
                              '<span class="x">new job<small>took this GPU</small></span>')}[kd]
            h += f'<div class="fs {kd} g{j}" style="{p(slot_x(f, j), f[1] + 0.6, SLOT_W, SLOT_H)}">{inner}</div>'
    h += (f'<div class="chip ca" style="{p(CHIP[0], FA[1] + 0.6, CHIP[1], SLOT_H)}">lab-b pod<small>no toleration</small>'
          f'<span class="no">✕</span></div>')
    h += f'<div class="chip cb" style="{p(CHIP[0], FB[1] + 0.6, CHIP[1], SLOT_H)}">new job<small>normal priority</small></div>'
    return h


def fair_draw(s, k):
    for f, lab in [(FA, "Reserved node · taint nautilus.io/reservation=lab-a"), (FB, "Shared node: no taint")]:
        s.rect(*f, fill=None, line="B9C7D8", radius=0.06)
        s.text(f[0] + 0.15, f[1] + 0.06, f[2] - 0.3, 0.4, P(lab, size=13, bold=True, color=NAVY))
    for j, kd in enumerate(["own", "own", "res", "res"]):
        fill, col, t = {"own": (NAVY, WHITE, "lab-a pod"), "res": ("ECEFF3", "6B7480", "idle, reserved")}[kd]
        s.rect(slot_x(FA, j), FA[1] + 0.6, SLOT_W, SLOT_H, fill=fill, radius=0.1)
        s.text(slot_x(FA, j), FA[1] + 0.6, SLOT_W, SLOT_H, P(t, size=11, bold=True, color=col, align="c"), anchor="m")
    s.rect(CHIP[0], FA[1] + 0.6, CHIP[1], SLOT_H, fill="F6D6D3", line="B3261E", radius=0.1)
    s.text(CHIP[0], FA[1] + 0.6, CHIP[1], SLOT_H, P("lab-b pod ✕ no toleration", size=10.5, bold=True, color=NAVY,
                                                    align="c"), anchor="m")
    for j in range(4):
        if j == 0 or (k == 2 and j == 1):
            fill, col, t = NAVY, WHITE, "a user's job" if j == 0 else "new job (took this GPU)"
        elif k == 0:
            fill, col, t = "DDE1E6", "6B7480", "idle"
        else:
            fill, col, t = "F6D58C", NAVY, "opportunistic (OSG)"
        s.rect(slot_x(FB, j), FB[1] + 0.6, SLOT_W, SLOT_H, fill=fill, radius=0.1)
        s.text(slot_x(FB, j), FB[1] + 0.6, SLOT_W, SLOT_H, P(t, size=11, bold=True, color=col, align="c"), anchor="m")


fs = [Bullets(X0, TOP + 0.15, 5.4, 5.2, [
    ("**Reserved nodes:** on request, admins taint a contributor's nodes; only pods that **tolerate** the taint, the "
     "owner's, run there", 0, 0),
    (f"Today: {RESV_NODES} nodes reserved for {RESV_GROUPS} groups", 1, 0),
    ("**Shared nodes:** idle GPUs go to **opportunistic** pods, the lowest priority class, e.g. OSG jobs for "
     "IceCube and LIGO", 0, 1),
    (f"{OPP_PODS} opportunistic pods running, {OPP_OSG} of them from OSG", 1, 1),
    ("When anyone needs that GPU, the opportunistic pod is **preempted**: it must checkpoint, or just restart", 0, 2)],
    size=17, gap=10),
    Raw(FA[0], FA[1], 6.43, FB[1] + FB[3] - FA[1], fair_html(), draw=fair_draw)]
cap = {0: "A pod without the toleration can't land on the reserved node, even on an idle GPU.",
       1: "On a shared node, opportunistic pods fill the idle GPUs.",
       2: "A normal pod arrives: the scheduler preempts an opportunistic pod to make room."}
for k, t in cap.items():
    fs.append(Text(FA[0], FB[1] + FB[3] + 0.2, 6.43, 0.7, T(t, size=16, color=BODY), only=[k]))
add("Sharing GPUs Fairly", fs, steps=2, cls="fairshare", builds=True, secs=80, notes=f"""
Why a GPU is sometimes busy, and how a class can count on one. Two kinds of nodes. A contributor can ask for their nodes to be reserved: we put a reservation taint on them, and only pods that tolerate that taint, which are the owner's, can land there. Here a pod from another lab tries an idle GPU on a reserved node and is turned away. Today {RESV_NODES} nodes carry a reservation, for {RESV_GROUPS} groups.

[click] Everything else is shared. On a shared node, idle GPUs go to opportunistic work: that's a priority class, the lowest one. Most of it is Open Science Grid glideins running jobs for experiments like IceCube and LIGO: {OPP_PODS} opportunistic pods right now, {OPP_OSG} of them from OSG.

[click] When anyone with a normal job needs that GPU, the scheduler preempts the opportunistic pod. So opportunistic work has to tolerate that: it checkpoints, or it just starts again somewhere else.
""")


# ── Regions and Storage (was "One Cluster, Many Sites" + "Storage") ───────────────────────────────────────
ceph = S["ceph"]
crow = [(c["name"], c["total"] / 1e15) for c in ceph]
cused = [c["used"] / 1e15 for c in ceph]


def hbars_html(rows, maxv, label_w=260, color="var(--blue)", fmt=lambda v: f"{v:,}", used=None):
    h = ""
    for i, (lab, v) in enumerate(rows):
        u = ""
        if used is not None:
            u = (f'<i class="u" style="--w:{used[i] / maxv * 100:.1f}%;transition-delay:{0.3 + i * 0.06:.2f}s"></i>')
        h += (f'<div class="hb"><span class="hn" style="width:{label_w}px">{escape(lab)}</span><span class="ht">'
              f'<i class="t" style="--w:{v / maxv * 100:.1f}%;background:{color};transition-delay:{i * 0.06:.2f}s">'
              f'</i>{u}<em>{fmt(v)}</em></span></div>')
    return f'<div class="hbars">{h}</div>'


def hbars_draw(x, y, w, rows, maxv, label_w=1.8, row_h=0.42, color=BLUE, fmt=lambda v: f"{v:,}", used=None,
               size=13):
    def draw(s, k):
        for i, (lab, v) in enumerate(rows):
            yy = y + i * row_h
            s.text(x, yy, label_w - 0.1, row_h, P(lab, size=size, color=BODY, align="r"), anchor="m")
            bw_ = (w - label_w - 1.3) * v / maxv
            s.rect(x + label_w, yy + 0.07, max(bw_, 0.02), row_h - 0.14,
                   fill="C9D9EA" if used is not None else color, radius=0.1)
            if used is not None:
                s.rect(x + label_w, yy + 0.07, max((w - label_w - 1.3) * used[i] / maxv, 0.02), row_h - 0.14,
                       fill=color, radius=0.1)
            s.text(x + label_w + bw_ + 0.08, yy, 1.3, row_h, P(fmt(v), size=size, color=MUTED), anchor="m")
    return draw


add("Regions and Storage", [
    Bullets(X0, TOP + 0.15, 5.6, 5.2, [
        f"Every node is labeled with its **region**, **zone** ({S['zones']} zones) and **site**; workloads spread "
        "out or stay near their data",
        f"**Rook** runs {len(ceph)} **Ceph** clusters, one per region or large site: {PB:.1f} PB raw",
        "CephFS for shared files, RBD for block, S3 for objects",
        "**Linstor** (DRBD) for fast replicated block storage; **CVMFS** for software; local NVMe for scratch",
        "Pick the storage in the region where you compute"], size=18),
    Text(6.55, TOP + 0.1, 6.18, 0.4, T("Ceph clusters: raw capacity, and used", size=17, bold=True, color=NAVY)),
    Raw(6.55, TOP + 0.6, 6.18, 4.2, hbars_html(crow, max(v for _, v in crow), label_w=230, color="#C9D9EA",
                                               fmt=lambda v: f"{v:.2f} PB", used=cused),
        draw=hbars_draw(6.55, TOP + 0.6, 6.18, crow, max(v for _, v in crow), label_w=1.6, row_h=0.44,
                        fmt=lambda v: f"{v:.2f} PB", used=cused)),
    Text(6.55, TOP + 4.75, 6.18, 0.3, T(f"From the CephCluster resources, {SNAP}", size=12, color=MUTED)),
], cls="storage", secs=60, notes=f"""
One cluster, but it spans a continent, so every node carries topology labels: region, zone and site. Workloads can spread across zones for resilience, or stay near their data.

Storage follows the regions. Rook runs {len(ceph)} Ceph clusters, one per region or large site, about {PB:.0f} petabytes raw in total; the big one is the original West Coast pool. Users get CephFS for shared files, RBD block volumes and S3. Linstor, which is DRBD underneath, gives fast replicated block storage for things that need it. CVMFS for software distribution, and local NVMe for scratch. The rule for users: pick the storage in the region where you compute.
""")


# Ways to run work: ported from the UCLA deck (JupyterHub, a pod, a Deployment, then a sweep of Jobs)
def runways():
    h = ""

    def at(x, y, w, hh, inner, cls="", step=None, only=None, style=""):
        a = f' data-s="{step}"' if step is not None else ""
        a += f' data-only="{only}"' if only is not None else ""
        return f'<div class="sb {cls}"{a} style="{pos(x, y, w, hh)}{style}">{inner}</div>'

    def ul(items, size):
        return (f'<ul class="bl" style="font-size:{size * 2}px;--gap:16px">'
                + "".join(f'<li class="l0">{md(t)}</li>' for t in items) + "</ul>")

    for i, (head, items) in enumerate(RUN_WAYS):
        y = TOP + 0.1 + i * 1.65
        h += at(X0, y, 5.55, 1.6, f'<p class="dh l" style="font-size:38px">{escape(head)}</p>'
                f'<div style="margin-top:14px">{ul(items, 15.5)}</div>', f"lw b{i}", step=i or None)
    h += at(6.55, TOP + 0.1, 6.18, 0.45, '<p class="dh l" style="font-size:38px">Batch: a Job</p>', step=3)
    h += at(6.55, TOP + 0.52, 6.18, 0.75, ul(RUN_JOB, 15.5), step=3)
    h += at(6.55, TOP + 1.3, 6.18, 0.52, f'<div class="code one" style="font-size:24px"><pre>{escape(RUN_CMD)}</pre></div>',
            step=3)
    UNIT, T0 = 0.55, 1.5
    LX, TW, LH, LG = 115, 775, 58, 11
    g = '<span class="plab">Pending</span>'
    for i, (job, gpu, t0, t1) in enumerate(SWEEP):
        g += (f'<span class="pc" style="left:{LX + i * 129}px;--a:{0.5 + i * 0.08:.2f}s;--b:{T0 + t0 * UNIT:.2f}s">'
              f'{job}</span>')
    for k in range(4):
        g += f'<span class="glab" style="top:{70 + k * (LH + LG)}px">GPU {k + 1}</span>'
        g += f'<span class="trk" style="top:{70 + k * (LH + LG)}px"></span>'
    for job, gpu, t0, t1 in SWEEP:
        bw_ = (t1 - t0) / SWEEP_T * TW - 6
        st = f"left:{LX + t0 / SWEEP_T * TW + 3:.0f}px;top:{70 + gpu * (LH + LG) + 4}px;"
        tm_ = f"--t0:{T0 + t0 * UNIT:.2f}s;--t1:{T0 + t1 * UNIT:.2f}s;--du:{(t1 - t0) * UNIT:.2f}s"
        g += (f'<span class="gb" style="{st}--w:{bw_:.0f}px;{tm_}"></span>'
              f'<span class="gl" style="{st}--w:{bw_:.0f}px;{tm_}">{job}</span>')
    g += f'<span class="nowl" style="--t0:{T0:.2f}s;--du:{SWEEP_T * UNIT:.2f}s"></span>'
    g += (f'<span class="tax" style="top:{70 + 4 * (LH + LG) - 4}px"></span><span class="tlab" style="top:'
          f'{70 + 4 * (LH + LG)}px">time</span>')
    h += at(6.55, TOP + 1.95, 6.18, 2.95, f'<div class="gantt">{g}</div>', step=3)
    h += at(6.55, TOP + 4.85, 6.18, 0.55, f'<p class="cap" style="font-size:27px">{escape(RUN_CAPTION)}</p>', step=3)
    LCT = 3.6

    def lifecycle(k, lane, segs, marks):
        hh = f'<span class="lcl">{lane}</span><span class="trk" style="top:40px"></span>'
        for t0, t1, kind, text in segs:
            w = (t1 - t0) * TW - 4
            hh += (f'<span class="sg {kind}" style="left:{LX + t0 * TW + 2:.0f}px;--w:{w:.0f}px;--t0:{0.5 + t0 * LCT:.2f}s;'
                   f'--du:{(t1 - t0) * LCT:.2f}s">{escape(text)}</span>')
        for p_, text, kind, place, align in marks:
            x = LX + p_ * TW
            tx = {"start": f"left:{x - 2:.0f}px", "center": f"left:{x - 300:.0f}px;width:600px;text-align:center",
                  "end": f"right:{890 - x - 2:.0f}px;text-align:right"}[align]
            hh += (f'<span class="mk {kind}" style="left:{x - 1.5:.0f}px;--t:{0.5 + p_ * LCT:.2f}s"></span>'
                   f'<span class="mt {kind}" style="{tx};top:{0 if place == "above" else 110}px;--t:{0.5 + p_ * LCT:.2f}s">'
                   f'{escape(text)}</span>')
        return at(6.55, TOP + 3.35, 6.18, 1.9, f'<div class="lc lc{k}">{hh}</div>', only=str(k))

    from elements import uri
    h += at(6.55, TOP + 0.05, 2.95, 0.4, '<p class="dh l" style="font-size:26px">1. Pick a GPU</p>', only="0")
    h += at(6.55, TOP + 0.45, 2.95, 2.65, f'<img class="im framed" src="{uri(IMG / "jhub_spawner.png")}" alt="">',
            only="0")
    h += at(9.6, TOP + 0.05, 3.13, 0.4, '<p class="dh l" style="font-size:26px">2. Your notebook runs on it</p>',
            only="0")
    h += at(9.6, TOP + 0.45, 3.13, 2.65, f'<img class="im framed" src="{uri(IMG / "jupyterlab_gpu.png")}" alt="">',
            only="0")
    h += lifecycle(0, "GPU", [(0, .55, "run", "you work in notebooks"), (.55, .8, "idle", "idle")],
                   [(.55, "you close the browser", "neutral", "above", "center"),
                    (.8, "1 h later: server stops, GPU back to the pool", "ok", "below", "end")])
    pod_term = ["$ kubectl apply -f pod.yaml", "pod/dev-pod created", "$ kubectl exec -it dev-pod -- bash",
                "root@dev-pod:/# nvidia-smi -L", "GPU 0: NVIDIA A10 (UUID: GPU-…)", "root@dev-pod:/# python test.py"]
    h += at(6.55, TOP + 0.3, 6.18, 2.3, '<div class="code kterm podterm" style="font-size:25px"><pre>'
            + "".join(f'<span class="ln{" cmd" if l.startswith(("$ ", "root@")) else ""}" style="--i:{i}">{escape(l)}'
                      f'</span>' for i, l in enumerate(pod_term)) + "</pre></div>", only="1")
    h += lifecycle(1, "GPU", [(0, .8, "run", "dev-pod: a shell, tests, debugging")],
                   [(.8, "6 h: the pod is deleted", "bad", "below", "end")])
    dep = ('<div class="depbox"><p class="dh l" style="font-size:28px">Deployment <code>web-app</code> · 2 replicas</p>'
           '<div class="dpods"><div class="dpod"><code>web-app-5d59d-x2kqp</code><b>Running</b></div>'
           '<div class="dpod swapper"><span class="p1"><code>web-app-5d59d-m4q9d</code><b>Running</b></span>'
           '<span class="p2"><code>web-app-5d59d-m4q9d</code><b>crashed</b></span>'
           '<span class="p3"><code>web-app-5d59d-c8w3n</code><b>Running</b></span></div></div>'
           '<p class="cap" style="font-size:26px;margin-top:18px">Kubernetes keeps two copies running; when one '
           'crashes, it starts a replacement</p></div>')
    h += at(6.55, TOP + 0.3, 6.18, 2.45, dep, only="2")
    h += lifecycle(2, "Node", [(0, .42, "run", "web-app"), (.45, .92, "run", "web-app (replacement)")],
                   [(.435, "crash: restarted for you", "bad", "above", "center"),
                    (.92, "2 weeks: removed, unless admins grant an exception", "neutral", "below", "end")])
    return h


def runways_draw(s, k):
    from deckkit import CODE_BG
    for i, (head, items) in enumerate(RUN_WAYS):
        y = TOP + 0.1 + i * 1.65
        s.text(X0, y, 5.55, 0.45, P(head, size=19, bold=True, color=NAVY))
        s.text(X0, y + 0.42, 5.55, 1.15, [P(t, size=15.5, color=BODY, bullet=True, accent=NAVY, before=4 if j else 0)
                                           for j, t in enumerate(items)])
    s.text(6.55, TOP + 0.1, 6.18, 0.45, P("Batch: a Job", size=19, bold=True, color=NAVY))
    s.text(6.55, TOP + 0.52, 6.18, 0.8, [P(t, size=15.5, color=BODY, bullet=True, accent=NAVY, before=4 if j else 0)
                                          for j, t in enumerate(RUN_JOB)])
    s.code(6.55, TOP + 1.3, 6.18, 0.62, RUN_CMD, size=12)
    GX, GW, LY, LHH, LGG = 7.35, 5.38, TOP + 2.45, 0.4, 0.08
    for g in range(4):
        y = LY + g * (LHH + LGG)
        s.text(6.55, y, 0.75, LHH, P(f"GPU {g + 1}", size=12, bold=True, color=NAVY), anchor="m")
        s.rect(GX, y, GW, LHH, fill="F3F4F6", radius=0.12)
    for job, g, t0, t1 in SWEEP:
        y = LY + g * (LHH + LGG)
        x, w = GX + t0 / SWEEP_T * GW, (t1 - t0) / SWEEP_T * GW
        s.rect(x + 0.02, y + 0.03, w - 0.04, LHH - 0.06, fill="8FB0CF", radius=0.18)
        s.text(x, y, w, LHH, P(job, size=11, bold=True, color=NAVY, align="c", font=MONO), anchor="m")
    ay = LY + 4 * (LHH + LGG) - 0.02
    s.line(GX, ay, GX + GW, ay, color=MUTED, width=1.25)
    s.text(6.55, ay + 0.32, 6.18, 0.6, P(RUN_CAPTION, size=13.5, color=MUTED, line=1.0))


add("Ways to Run Work", [Raw(0, 0, 13.333, 7.5, runways(), draw=runways_draw)], steps=3, cls="runways", notes="""
And the ways to run work, which map onto Kubernetes objects. JupyterHub: pick a GPU, work in a notebook; idle servers stop, an hour after you close the browser on our hub. [click] A bare pod with a shell: deleted after six hours, at most two GPUs. [click] A Deployment for a service that stays up and gets restarted when it crashes; removed after two weeks unless we grant an exception. [click] And Jobs for real work: submit six, four start, two wait in Pending and take the first GPUs that free up, and when they finish the GPUs go back to the pool.
""")

YAML = """apiVersion: batch/v1
kind: Job
metadata: {name: gpu-train-daniel, namespace: my-lab}     # (1)
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: train
        image: pytorch/pytorch:2.9.0-cuda13.0-cudnn9-runtime  # (2)
        command: ["python", "train.py"]
        resources:                                       # (3)
          requests: {cpu: "2", memory: 6Gi, nvidia.com/gpu: 1}
          limits:   {cpu: "2", memory: 6Gi, nvidia.com/gpu: 1}
      affinity:                                          # (4)
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - {key: nvidia.com/gpu.memory, operator: Gt, values: ["20000"]}
              - {key: nvidia.com/gpu.compute.major, operator: Gt, values: ["7"]}"""
groups = {3: 1, 10: 2, 11: 2, 12: 3, 13: 3, 14: 3, 15: 4, 16: 4, 17: 4, 18: 4, 19: 4, 20: 4, 21: 4}
calls = [("Where:", "your namespace"), ("What:", "a container image, and the command to run"),
         ("Resources:", "2 CPUs, 6 GB of memory, one GPU"),
         ("Which GPU:", "more than 20 GB, Ampere or newer; or name exact models")]
add("A GPU Job", [
    Code(X0, TOP + 0.1, 8.25, 5.2, YAML, size=12, lang="yaml", lines_hl={k: [v] for k, v in groups.items()}),
    *[Text(9.1, TOP + 0.2 + i * 1.25, 3.63, 1.2, T(f"({i + 1}) **{h}** {b}", size=17), hl=[i + 1], cls="co")
      for i, (h, b) in enumerate(calls)],
], steps=4, cls="gpujob", optional=True, notes="""
When a project outgrows the notebook, a GPU job. Four parts: where it runs, your namespace; what it runs, an image and a command; what it needs, two CPUs, six gigs, one GPU; and which GPU, by memory and generation rather than by brand. That's what a student's final project might submit when a notebook isn't enough.
""")


add("Using GPUs Fairly", [
    Text(X0, TOP + 0.1, 5.9, 0.45, T("Do", size=21, bold=True, color=NAVY)),
    Bullets(X0, TOP + 0.6, 5.9, 4.6, ["Give GPUs only to the menu options that need them",
                                      "Let idle servers stop: keep the culling on",
                                      "Request what students will use; keep limits close to requests",
                                      "Keep data in home folders or the shared volume, not inside the image"],
            size=18),
    Text(6.83, TOP + 0.1, 5.9, 0.45, T("Don't", size=21, bold=True, color=NAVY)),
    Bullets(6.83, TOP + 0.6, 5.9, 4.6, ["Leave servers holding GPUs overnight",
                                        "Give every student 4 GPUs “just in case”: use must stay above 40%",
                                        "Put results on the server's own disk: it vanishes with the server"],
            size=18),
    Link(X0, 6.3, 9.0, 0.3, "https://nrp.ai/documentation/userdocs/start/policies/", size=14),
], secs=50, notes="""
The cluster policy, short version, for a class. Give GPUs only to the menu options that need them, keep the culling on, request what students will use, and keep data in home folders or the shared volume. Don't leave servers holding GPUs overnight or hand every student four GPUs just in case: GPU use has to stay above 40 percent, and the culling takes care of most of this for you.
""")
