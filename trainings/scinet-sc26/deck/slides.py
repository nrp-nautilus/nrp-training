"""Every slide of the SCinet deck, defined once; build_html.py and build_deck.py render it.

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


def add(*a, **kw):
    SLIDES.append(Slide(*a, **kw))


def section(title, notes):
    add(title, kind="section", notes=notes)


def sub(x, y, w, h, inner, cls="", style="", attrs=""):
    """A positioned child inside a Raw element (inches relative to the Raw's top-left)."""
    return f'<div class="sb {cls}" {attrs} style="{pos(x, y, w, h)}{style}">{inner}</div>'


def short_gpu(p):
    for a in ["H100", "H200", "A100", "A6000", "A10", "L40", "V100"]:
        if a in p:
            return a
    return p


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

add("Agenda", [
    Bullets(X0, TOP + 0.15, 7.6, 4.6, [
        "What NRP is, in five minutes",
        "How it's built: the network, sites, storage, ingress",
        "How we run it: GitLab and Argo CD, CI in VMs, NetBox, monitoring, perfSONAR, security, sharing GPUs",
        "AI: the LLM service, from the gateway to the GPUs, and an ops bot built on it",
        "Using it yourself",
        "Live demo, then questions"], size=22, gap=12, cls="stagger"),
    Text(8.6, TOP + 0.25, 4.13, 3.0, [
        T("About 33 minutes of slides,", size=18, color=MUTED),
        T("a 12-minute demo,", size=18, color=MUTED, before=4),
        T("then questions.", size=18, color=MUTED, before=4),
        T("Ask anything along the way.", size=18, color=BODY, before=20, bold=True)]),
    Text(X0, 5.85, 12.1, 0.4, T("Slides and the demo notebook:", size=18)),
    Link(X0, 6.25, 12.1, 0.4, "https://training.nrp-nautilus.io/scinet-sc26", size=18),
], notes="""
[0:01] The plan: a few minutes on what NRP is, for anyone new to it. Then the part I think you'll care about most: how it's built and how we run it. Then the AI service, which is the most interesting system we run right now. Then how you'd use it, a short demo, and questions. Interrupt any time.
""")

# ═════════════════════════════════════════════════════════════════════════════════════
# WHAT NRP IS
# ═════════════════════════════════════════════════════════════════════════════════════
section("What NRP Is", "[0:02] Quick context first.")


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
        svg += (f'<g transform="translate({p["x"]:.1f},{p["y"]:.1f})"><g class="pin k-{p["kind"]}" '
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
        ("Today:", 0, 1), (f"{NODES} nodes at {SITES} sites", 1, 1),
        (f"{GPUS:,} GPUs in {GPU_MODELS} models; {CORES:,} CPU cores", 1, 1),
        (f"{PB:.0f} PB of raw Ceph storage", 1, 1),
        ("Free for non-commercial research and education", 0, 2),
        ("One team runs it from the OS up; campuses keep priority on what they contribute", 0, 2)], size=19),
    Link(6.55, TOP + 0.05, 6.18, 0.3, "https://dash.nrp-nautilus.io", size=14, align="r"),
    Raw(6.55, TOP + 0.45, 6.18, 4.1, usmap_html(GEO), draw=map_draw),
    Text(6.55, TOP + 4.6, 6.18, 0.5, [T(f"Sites from the NRP dashboard, {SNAP}", size=12, color=MUTED, align="r"),
                                      T(offmap_note(GEO), size=12, color=MUTED, align="r")], step=1),
    Text(X0, 6.74, 7.0, 0.2, T(f"Nodes, GPUs, cores and storage: cluster snapshot, {SNAP}", size=10, color=MUTED)),
], steps=2, cls="whatnrp", builds=True, notes=f"""
[0:02] NRP is one Kubernetes cluster, called Nautilus, for research and education. Three sites operate it: SDSC at UC San Diego, Nebraska, and MGHPCC in Massachusetts, and NSF funds it.

[click] The hardware comes from more than seventy institutions, and it sits on research and education networks. Every pin is a real site, from the dashboard's own data: {SITES} sites, {NODES} nodes, {GPUS:,} GPUs in {GPU_MODELS} models, about {CORES // 1000}k cores and {PB:.0f} petabytes of raw Ceph. A few more sites are off this map, in Hawaii, Guam, Korea, Brazil and Europe.

[click] It's free for non-commercial research and education. The model is a potluck: a campus contributes nodes and keeps priority on them, idle capacity is shared, and one team operates the whole stack, so a campus with hardware but no Kubernetes team can still take part.
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
         (CORES, "CPU cores", 0, ""), (PB, f"raw Ceph in {len(S['ceph'])} clusters", 1, " PB"),
         (S["namespaces"], "namespaces: labs, courses, services", 0, "")]
st_els = []
for i, (v, lab, dec, suf) in enumerate(stats):
    cx, cy = X0 + (i % 3) * 4.1, TOP + 0.3 + (i // 3) * 2.2
    st_els += [Frame(cx, cy, 3.85, 1.95, fill=CARD, line=None, radius=0.06),
               Stat(cx + 0.3, cy + 0.25, 3.4, 1.6, v, lab, dec=dec, suffix=suf, big=58, label_size=17)]
st_els.append(Text(X0, 6.25, W, 0.3, T(f"Cluster snapshot, {SNAP} (Kubernetes {S['k8s']}). Sites: the NRP "
                                       f"dashboard.", size=12, color=MUTED)))
add("NRP in Numbers", st_els, cls="numbers", notes=f"""
[0:04] The same thing in numbers, from a snapshot I took this week: {NODES} nodes, {SITES} sites, {GPUS:,} GPUs in {GPU_MODELS} different models, which tells you it's built from what campuses buy, not from one procurement. About {CORES // 1000} thousand cores, {PB:.0f} petabytes of raw Ceph across {len(S['ceph'])} clusters, and {S['namespaces']:,} namespaces: every lab, course and service gets its own.
""")

# ═════════════════════════════════════════════════════════════════════════════════════
# HOW IT'S BUILT
# ═════════════════════════════════════════════════════════════════════════════════════
section("How It's Built", "[0:06] How it's built, starting with the part you care about: the network.")

net = [Bullets(X0, TOP + 0.15, 5.25, 5.2, [
    "Nodes sit in campus **Science DMZs**, outside campus firewalls, at 10–100 Gb/s",
    "**Jumbo frames:** MTU 9000 between all nodes",
    "Regional and national R&E networks carry the traffic",
    f"{S['i2_nodes']} nodes sit in {S['i2_sites']} Internet2 locations",
    f"**Calico** builds the pod network: a VXLAN overlay, IPv4 and IPv6 ({S['calico_ipv6_nodes']} nodes dual-stack)"],
    size=18)]
cx = [6.15, 8.37, 10.59]
for i, c in enumerate(["Campus A", "Campus B", "Campus C"]):
    x = cx[i]
    net += [Frame(x, TOP + 0.1, 2.08, 2.75, label=c, line="C9D4E3", label_size=13),
            Box(x + 0.15, TOP + 0.55, 1.78, 0.72, "Campus LAN", "firewall, IDS", state="dim", head_size=13,
                sub_size=11),
            Box(x + 0.15, TOP + 1.85, 1.78, 0.82, "NRP node", "Science DMZ", state="orange", head_size=14,
                sub_size=11.5),
            Arrow(x + 1.04, TOP + 2.67, x + 1.04, TOP + 3.45, head=False, width=2.5, color=NAVY)]
net += [Box(6.15, TOP + 3.45, 6.52, 0.62, "R&E networks", "regional networks, Internet2, international links",
            state="active", head_size=15, sub_size=12),
        Arrow(cx[0] + 1.93, TOP + 2.26, cx[1] + 0.15, TOP + 2.26, dashed=True, color=ORANGE, width=2.5, head=False,
              step=1),
        Arrow(cx[1] + 1.93, TOP + 2.26, cx[2] + 0.15, TOP + 2.26, dashed=True, color=ORANGE, width=2.5, head=False,
              step=1),
        Text(6.15, TOP + 4.25, 6.52, 0.9, [T("Dashed: the Calico VXLAN overlay. Pods on any node reach pods on any "
                                             "other node directly.", size=14, color=MUTED, align="c")], step=1),
        Raw(6.15, TOP + 1.85, 6.52, 0.82, '<span class="pkt"></span>', only=[2], pptx=False)]
add("The Network Underneath", net, steps=2, cls="netunder", notes=f"""
[0:06] The network is the foundation, and it's the PRP heritage. Nodes go in the campus Science DMZ, outside the campus firewall and IDS, at 10 to 100 gig, with jumbo frames end to end. The regional networks and Internet2 carry the traffic; Internet2 itself hosts {S['i2_nodes']} of our nodes in {S['i2_sites']} locations.

[click] On top of that, Calico builds the pod network as a VXLAN overlay, dual-stack on {S['calico_ipv6_nodes']} nodes, so a pod at one campus talks to a pod at another directly.

[click] A pod in campus A sends to a pod in campus C as if they were on the same network. That's what makes one cluster across a hundred sites behave like one cluster.
""")

ports = [["From the internet", "Why"], ["22/tcp", "SSH, for NRP operators"],
         ["443/tcp", "HTTPS; opened on every node by cluster policy"],
         ["ICMP", "ping, and path MTU discovery for jumbo frames"],
         ["8443/tcp", "object reads over HTTPS and XRootD (data caches)"],
         ["8444/tcp", "Pelican tokens, director health checks, metrics"],
         ["50000–51000/tcp", "GridFTP data channels"]]
add("Policy Lives in the Cluster", [
    Bullets(X0, TOP + 0.15, 5.6, 5.2, [
        "Nodes are open to the world; **Calico GlobalNetworkPolicy** filters at the host, before NAT",
        "Hosts in a central network set reach each other with no filtering",
        "Campuses keep no per-node firewall rules; local iptables and firewalld stay off",
        "Why: the node population changes every week, faster than any campus change process"], size=18),
    Table(6.55, TOP + 0.2, 6.18, 3.6, ports, [1.9, 4.28], size=14, mono=(0,), row_h=0.55, cls="rows"),
    Text(6.55, TOP + 4.15, 6.18, 0.8, T("The last three only on nodes that run a data cache, an origin or a Globus "
                                        "endpoint.", size=13, color=MUTED)),
    Link(X0, 6.3, 9.0, 0.3, "https://nrp.ai/documentation/admindocs/participating/network/", size=13),
], notes="""
[0:07] How we filter, which is usually the first question from network people. Nodes are open to the world, and Calico global network policy filters at the host, before NAT. Every host in a central network set can reach every other with no filtering; everything else is filtered by policy that lives in the cluster. Campuses don't maintain per-node firewall rules, and we ask them to turn off local iptables and firewalld because they fight with the cluster policy.

The reason is churn: nodes come and go every week, and no campus change process keeps up with that. From the internet: SSH for operators, 443, ICMP for path MTU discovery, which jumbo frames need, and data-cache and GridFTP ports only on the nodes that run those services.
""")

regions = [(k if k != "none" else "no region label", v) for k, v in S["regions"].items()]


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


add("One Cluster, Many Sites", [
    Bullets(X0, TOP + 0.15, 5.3, 5.2, [
        f"One control plane; Kubernetes {S['k8s'].lstrip('v').rsplit('.', 1)[0]}",
        f"Topology labels on every node: region, zone ({S['zones']} zones), site",
        "Workloads ask for locality: spread over zones, or stay near their data",
        f"Mostly x86-64; {S['arch'].get('arm64', 0)} ARM64 nodes",
        "Operated from SDSC, Nebraska–Lincoln and MGHPCC"], size=18),
    Text(6.3, TOP + 0.1, 6.43, 0.4, T("Nodes by region", size=17, bold=True, color=NAVY)),
    Raw(6.3, TOP + 0.6, 6.43, 4.0, hbars_html(regions, max(v for _, v in regions)),
        draw=hbars_draw(6.3, TOP + 0.6, 6.43, regions, max(v for _, v in regions), row_h=0.48)),
    Text(6.3, TOP + 4.7, 6.43, 0.3, T(f"topology.kubernetes.io/region, {SNAP}", size=12, color=MUTED, font=MONO)),
], cls="sites", notes=f"""
[0:09] It's one cluster with one control plane, running Kubernetes {S['k8s'].lstrip('v').rsplit('.', 1)[0]}. Every node carries topology labels, region, zone and site, so workloads can spread across zones for resilience or stay near their data. Most of the nodes are on the West Coast, which is the PRP history, then the central and eastern regions, plus a handful in the Pacific, Europe and Latin America.
""")

ceph = S["ceph"]
crow = [(c["name"], c["total"] / 1e15) for c in ceph]
cused = [c["used"] / 1e15 for c in ceph]
add("Storage", [
    Bullets(X0, TOP + 0.15, 5.6, 5.2, [
        f"**Rook** runs {len(ceph)} **Ceph** clusters, one per region or large site: {PB:.1f} PB raw",
        "CephFS for shared files, RBD for block, S3 for objects",
        "**Linstor** (DRBD) for fast replicated block storage",
        "**CVMFS** for software; local NVMe for scratch",
        "Pick the pool near your compute"], size=18),
    Text(6.55, TOP + 0.1, 6.18, 0.4, T("Ceph clusters: raw capacity, and used", size=17, bold=True, color=NAVY)),
    Raw(6.55, TOP + 0.6, 6.18, 4.2, hbars_html(crow, max(v for _, v in crow), label_w=230, color="#C9D9EA",
                                               fmt=lambda v: f"{v:.2f} PB", used=cused),
        draw=hbars_draw(6.55, TOP + 0.6, 6.18, crow, max(v for _, v in crow), label_w=1.6, row_h=0.44,
                        fmt=lambda v: f"{v:.2f} PB", used=cused)),
    Text(6.55, TOP + 4.75, 6.18, 0.3, T(f"From the CephCluster resources, {SNAP}", size=12, color=MUTED)),
], cls="storage", notes=f"""
[0:10] Storage. Rook runs {len(ceph)} Ceph clusters, one per region or large site, about {PB:.0f} petabytes raw in total; the big one is the original West Coast pool. Users get CephFS for shared files, RBD block volumes and S3. Linstor, which is DRBD underneath, gives fast replicated block storage for things that need it. CVMFS for software distribution, and local NVMe for scratch. The rule for users: pick the pool near your compute, because the cluster spans a continent.
""")

hw = [("NVIDIA GPUs", f"{GPUS:,} in {GPU_MODELS} models, GTX 1080 Ti to H200"), ("AMD GPUs", "ROCm device plugin"),
      ("Qualcomm Cloud AI 100", "inference cards, requested like a GPU"), ("Xilinx Alveo FPGAs", "Vivado and Vitis"),
      ("ESnet SmartNIC", "FPGA network cards, P4 pipelines"), ("ARM64 nodes", "they need multi-arch images")]
rt = [("Containers", "runc, plus the NVIDIA runtime"), ("Kata VMs", "a lightweight VM per pod"),
      ("Sysbox", "system containers: Docker inside a pod"), ("KubeVirt", "full VMs: Ubuntu, Windows, Talos"),
      ("Multus and SR-IOV", "extra NICs in a pod, for network research"),
      ("Confidential VMs", "Kata with AMD SNP or Intel TDX, GPUs included")]
he = [Text(X0, TOP + 0.05, 6.0, 0.4, T("Accelerators", size=19, bold=True, color=NAVY)),
      Text(6.83, TOP + 0.05, 5.9, 0.4, T("Runtimes and networking", size=19, bold=True, color=NAVY))]
for i, (h, b) in enumerate(hw):
    he.append(Box(X0 + (i % 2) * 3.0, TOP + 0.55 + (i // 2) * 1.2, 2.85, 1.05, h, b, head_size=16, sub_size=12.5,
                  cls="rise", style=f"transition-delay:{0.1 + i * 0.12:.2f}s"))
for i, (h, b) in enumerate(rt):
    he.append(Box(6.83 + (i % 2) * 2.98, TOP + 0.55 + (i // 2) * 1.2, 2.85, 1.05, h, b, head_size=16, sub_size=12.5,
                  state="white", cls="rise", style=f"transition-delay:{0.8 + i * 0.12:.2f}s"))
he.append(Text(X0, 5.75, W, 0.5, T(f"Runtime classes on the cluster: {len(S['runtimeclasses'])}, most of them Kata "
                                   f"variants (QEMU, Cloud Hypervisor, Firecracker, Dragonball).",
                                   size=14, color=MUTED)))
add("More Than GPUs", he, optional=True, notes=f"""
[0:11] It isn't only GPUs. There are AMD GPUs, Qualcomm inference cards, Xilinx FPGAs and ESnet's FPGA SmartNICs, and a few ARM nodes. On the runtime side: ordinary containers; Kata, which gives each pod its own lightweight VM, and which comes back in a few slides; Sysbox for Docker-in-a-pod; KubeVirt for full VMs including Windows; Multus with SR-IOV to give a pod extra NICs for network research; and confidential VMs, Kata with SNP or TDX. There are {len(S['runtimeclasses'])} runtime classes defined, most of them Kata variants.
""")

ing = [Box(X0, TOP + 0.3, 1.55, 0.95, "Client", "anywhere", head_size=16),
       Box(2.75, TOP + 0.3, 2.1, 0.95, "Upstream router", "learns the VIPs by BGP", head_size=15, sub_size=12),
       Box(5.4, TOP + 0.3, 2.45, 0.95, "Ingress", f"Envoy Gateway; HAProxy on {S['haproxy_ingress_nodes']} nodes",
           head_size=15, sub_size=12),
       Box(8.4, TOP + 0.3, 1.75, 0.95, "Service", "in your namespace", head_size=15, sub_size=12),
       Box(10.7, TOP + 0.3, 2.03, 0.95, "Your pods", "on any node", head_size=15, sub_size=12),
       Box(2.75, TOP + 1.95, 2.1, 0.85, "MetalLB", "announces service VIPs, IPv4 and IPv6", state="white",
           head_size=15, sub_size=11.5),
       Arrow(3.8, TOP + 1.95, 3.8, TOP + 1.27, dashed=True, hl=[1]),
       Arrow(X0 + 1.55, TOP + 0.78, 2.75, TOP + 0.78, hl=[2]),
       Arrow(4.85, TOP + 0.78, 5.4, TOP + 0.78, hl=[2]),
       Arrow(7.85, TOP + 0.78, 8.4, TOP + 0.78, hl=[3]),
       Arrow(10.15, TOP + 0.78, 10.7, TOP + 0.78, hl=[3]),
       Box(5.4, TOP + 1.95, 2.45, 0.85, "cert-manager", "TLS certificates for every host name", state="white",
           head_size=15, sub_size=11.5),
       Arrow(6.62, TOP + 1.95, 6.62, TOP + 1.27, dashed=True),
       Bullets(X0, TOP + 3.25, W, 2.1, [
           f"{S['ingresses']:,} Ingress objects on HAProxy, and {S['httproutes']} Gateway API routes on Envoy Gateway, "
           "which newer services use",
           "Users expose a web service with an Ingress or an HTTPRoute in their own namespace; DNS and TLS come "
           "with it",
           "Load-balancer VIPs for non-HTTP services, by request"], size=17, gap=8)]
ing[1].hl, ing[2].hl, ing[3].hl, ing[4].hl, ing[5].hl = [1, 2], [2], [3], [3], [1]
add("Getting Traffic In", ing, steps=3, cls="ingress", notes=f"""
[0:12] How traffic gets in. MetalLB speakers announce service VIPs to the upstream router over BGP, for IPv4 and IPv6. [click] A client's request reaches an ingress: HAProxy runs on {S['haproxy_ingress_nodes']} nodes, and Envoy Gateway, with the newer Gateway API, is taking over newer services. Remember Envoy Gateway; it comes back in the AI part. [click] From there to the Service and the pods, wherever they run.

There are about a thousand Ingress objects today and a few dozen Gateway API routes. For users it's self-service: you create an Ingress or an HTTPRoute in your namespace and cert-manager gets you a certificate.
""")

# ═════════════════════════════════════════════════════════════════════════════════════
# HOW WE RUN IT
# ═════════════════════════════════════════════════════════════════════════════════════
section("How We Run It", "[0:13] Now the operations side: how a small team runs this.")

go = [Box(X0, TOP + 0.3, 2.3, 1.0, "An admin", "git push", head_size=16, mono_sub=True, hl=[1]),
      Box(3.55, TOP + 0.3, 2.3, 1.0, "GitLab", "the repo: manifests, Helm values", head_size=16, sub_size=12, hl=[1]),
      Box(6.5, TOP + 0.3, 2.3, 1.0, "Argo CD", "compares git with the cluster", head_size=16, sub_size=12,
          hl=[1, 3]),
      Box(9.45, TOP + 0.3, 3.28, 1.0, "The cluster", "what's actually running", head_size=16, sub_size=12, hl=[1, 3]),
      Arrow(2.9, TOP + 0.8, 3.55, TOP + 0.8, hl=[1]), Arrow(5.85, TOP + 0.8, 6.5, TOP + 0.8, hl=[1]),
      Arrow(8.8, TOP + 0.8, 9.45, TOP + 0.8, hl=[1, 3]),
      Box(9.45, TOP + 1.85, 3.28, 0.85, "kubectl edit", "a manual change: drift", state="red", head_size=15,
          sub_size=12, mono_sub=False, step=2, cls="drift"),
      Arrow(11.09, TOP + 1.85, 11.09, TOP + 1.32, color=RED, step=2),
      Text(6.5, TOP + 1.85, 2.85, 0.9, [T("self-heal: put back what git says", size=15, bold=True, color=BLUE,
                                          align="c")], anchor="m", step=3),
      Bullets(X0, TOP + 3.1, W, 2.2, [
          f"Self-hosted **GitLab** {S['gitlab_version'].split('-')[0]}: code, issues, a container registry, CI",
          f"**Argo CD** syncs {len(S['argo_apps'])} applications, GitLab itself among them",
          "**Self-heal:** a manual change is reverted to what's in git; history and review come free",
          "Not everything is in Argo yet: some services are still applied by hand from their repos (`kubectl diff`, "
          "`kubectl apply`, then push)"], size=17, gap=8)]
add("Git Is the Source of Truth", go, steps=3, cls="gitops", builds=True, notes=f"""
[0:13] The operating principle is that git is the source of truth. [click] An admin pushes a change to our self-hosted GitLab; Argo CD sees the repo change, compares it with what's running, and syncs the cluster. Argo manages {len(S['argo_apps'])} applications today, including GitLab itself.

[click] Now somebody runs kubectl edit at two in the morning. That's drift. [click] With self-heal on, Argo puts back what git says. You get review, history and rollback for free. (The full list of what Argo runs is in the backup slides.)

Honest caveat: not everything is in Argo. Some services still live in a repo but get applied by hand: kubectl diff, kubectl apply, push.
""")


RUNNER = '''[[runners]]
  [runners.kubernetes]
    namespace = "gitlab-ci-kata"
    runtime_class_name = "kata"
    privileged = false
    image = "alpine:3.22"
    cpu_limit = "4"
    cpu_limit_overwrite_max_allowed = "12"
    memory_limit = "8Gi"
    memory_limit_overwrite_max_allowed = "50Gi"'''
ci = [Box(X0, TOP + 0.2, 1.9, 0.9, "GitLab", "a pipeline starts", head_size=15, sub_size=12),
      Arrow(2.5, TOP + 0.65, 2.95, TOP + 0.65),
      Box(2.95, TOP + 0.2, 2.25, 0.9, "Runner", "Kubernetes executor", head_size=15, sub_size=12),
      Arrow(4.08, TOP + 1.1, 4.08, TOP + 1.55),
      Frame(X0, TOP + 1.55, 5.95, 2.45, label="namespace gitlab-ci-kata", line="B9C7D8", label_size=13)]
for i in range(3):
    x = X0 + 0.2 + i * 1.88
    ci += [Frame(x, TOP + 2.05, 1.72, 1.75, label="Kata VM", line=ORANGE, dashed=True, label_color=ORANGE,
                 label_size=12, step=1, style=f"transition-delay:{i * 0.35:.2f}s"),
           Box(x + 0.15, TOP + 2.5, 1.42, 1.1, "CI job", ["build an image", "run tests", "deploy"][i],
               state="white", head_size=14, sub_size=11.5, step=1, style=f"transition-delay:{i * 0.35 + 0.15:.2f}s")]
ci += [Code(6.83, TOP + 0.2, 5.9, 3.8, RUNNER, size=12.5, title="Runner config (from the cluster)"),
       Bullets(X0, TOP + 4.25, W, 1.2, [
           "The shared runners start each CI job as a pod in its own lightweight VM: a privileged build can't "
           "reach the node",
           f"{len(S['gitlab_runners'])} runners; images go to **gitlab-registry.nrp-nautilus.io** and are pulled "
           "from inside the cluster"], size=17, gap=6)]
add("CI in a VM per Job", ci, steps=1, cls="kata", notes=f"""
[0:15] CI is where shared clusters get nervous, because people want to run Docker builds, and a privileged container on a shared node is a problem. Our answer: the shared GitLab runners use the Kubernetes executor, and each job starts as a pod with the Kata runtime class, the VM-per-pod runtime from the hardware slide. [click] So each CI job gets its own lightweight VM. (There's also a dedicated build server for jobs that need a real Docker daemon.) A build can be privileged inside its VM without touching the node.

On the right is the actual runner config: the namespace, the Kata runtime class, the default image, and limits users can raise up to 12 CPUs and 50 gigs. Images go to our registry and get pulled from inside the cluster, which is much faster than Docker Hub.
""")

KANIKO = '''image: ghcr.io/osscontainertools/kaniko:debug

build-and-push-job:
  stage: build
  variables:
    GODEBUG: "http2client=0"
  script:
    - echo "{\\"auths\\":{\\"$CI_REGISTRY\\":{\\"username\\":
        \\"$CI_REGISTRY_USER\\",\\"password\\":\\"$CI_REGISTRY_PASSWORD\\"}}}"
        > /kaniko/.docker/config.json
    - /kaniko/executor --cache=true --push-retry=10
        --context $CI_PROJECT_DIR
        --dockerfile $CI_PROJECT_DIR/Dockerfile
        --destination $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA'''
add("Build and Deploy Your Own", [
    Code(X0, TOP + 0.1, 7.1, 4.7, KANIKO, size=12, title=".gitlab-ci.yml (from the NRP docs)", typed=True),
    Bullets(8.0, TOP + 0.15, 4.73, 4.9, [
        "Any NRP user can create projects at **gitlab.nrp-nautilus.io**",
        "Kaniko builds an image with no Docker daemon",
        "The registry is in the cluster: pulls are fast",
        "The GitLab agent for Kubernetes deploys to your namespace",
        "Build multi-arch images for the ARM64 nodes"], size=17, gap=8, cls="stagger"),
    Link(X0, 6.3, 9.0, 0.3, "https://nrp.ai/documentation/userdocs/development/gitlab/", size=13),
], optional=True, notes="""
[0:16] And the same thing from the user side. Anyone with an NRP login can use the GitLab. This is the pipeline from our docs: Kaniko builds the image without a Docker daemon and pushes it to the project's registry, tagged with the commit. The GitLab agent for Kubernetes can then deploy it into your namespace, so you can do GitOps for your own services the same way we do for ours.
""")

nb = [Bullets(X0, TOP + 0.15, 5.0, 5.2, [
    "**NetBox 4**, deployed by Argo CD from the NetBox Labs Helm chart",
    f"**netbox-agent** on every node ({S['netbox_agents']} pods): privileged, host network",
    "**lldpd** learns the switch and port each NIC is cabled to",
    "The site comes from the node's `netbox.io/site` label",
    "Alongside: Diode for ingest, and a Nornir pod for automation"], size=17, gap=8),
    Box(5.95, TOP + 0.25, 2.3, 1.55, "Switch", "at the site", state="white", head_size=17, sub_size=13),
    Box(5.95, TOP + 2.75, 2.3, 1.55, "NRP node", "netbox-agent + lldpd", state="orange", head_size=17, sub_size=12.5),
    Arrow(7.1, TOP + 2.75, 7.1, TOP + 1.8, head=False, width=3, color=NAVY),
    Text(7.25, TOP + 2.05, 1.4, 0.5, T("LLDP", size=14, bold=True, color=ORANGE), step=1),
    Raw(7.0, TOP + 1.8, 0.2, 0.95, '<span class="lldp"></span>', only=[1], pptx=False),
    Arrow(8.25, TOP + 3.52, 8.85, TOP + 3.52, step=2, hl=[2]),
    Frame(8.85, TOP + 0.25, 3.88, 4.75, label="NetBox: what the agent records", fill="F7F9FC", line="B9C7D8",
          label_size=14, step=2)]
rec = [("Device", "node name, role Server, site"), ("Interfaces", "names, MACs, IPs"),
       ("Cable", "NIC to the switch port, from LLDP"), ("Inventory", "CPUs, memory, disks, GPUs"),
       ("Updated", "once a day, plus up to an hour of jitter")]
for i, (h, b) in enumerate(rec):
    nb.append(Text(9.05, TOP + 0.75 + i * 0.83, 3.55, 0.8, [T(h, size=15, bold=True, color=NAVY),
                                                            T(b, size=13.5, color=BODY, before=1)], step=2,
                   style=f"transition-delay:{0.2 + i * 0.25:.2f}s"))
add("NetBox Knows Every Node", nb, steps=2, cls="netbox", notes=f"""
[0:16] NetBox. Your colleague mentioned you use it too. Ours is NetBox 4, deployed by Argo from the NetBox Labs chart. The interesting part is how it stays true. Every node runs netbox-agent as a privileged pod on the host network; that's {S['netbox_agents']} pods.

[click] The agent runs lldpd, so it hears the switch's LLDP announcements and learns which switch and port each NIC is plugged into.

[click] Then it writes what it found into NetBox: the device and its site, the interfaces with MACs and IPs, the cable to the switch port, and the inventory: CPUs, memory, disks and GPUs. It does this once a day with up to an hour of random delay, so five hundred nodes never hit NetBox at the same moment. The site comes from a node label, so the cluster and NetBox agree on where a node is.
""")

AGENT_YAML = '''netbox:
  url: https://netbox-4.nrp-nautilus.io
network:
  ignore_interfaces: (dummy.*|docker.*|tunl*|cali*|vxlan.*|lo|ibp.*|.*ifb.*)
  ignore_ips: (127\\.0\\..*)
  lldp: true
  nic_id: name
  primary_mac: permanent
virtual:
  cluster_name: nautilus
datacenter_location:
  driver: cmd:kubectl get node ${NODE_NAME} -o jsonpath=
    '{.metadata.labels.netbox\\.io/site}' | tr '[:upper:]' '[:lower:]'
inventory: true'''
AGENT_LOOP = '''lldpd           # start listening for LLDP
# at least 30 s so LLDP has found its neighbours
pause $(random_between 30 "$INITIAL_DELAY_MAX")
while true; do
  netbox_agent -c "$RUNTIME_CONFIG" --update-all -d &&
  netbox_agent -c "$RUNTIME_CONFIG" --update-inventory -d
  # a day, plus up to an hour of jitter
  pause $((RUN_INTERVAL + $(random_between 0 "$RUN_JITTER")))
done'''
add("The Agent, Up Close", [
    Code(X0, TOP + 0.1, 6.65, 4.6, AGENT_YAML, size=11, title="netbox_agent.yaml (token left out)", lang="yaml"),
    Code(7.4, TOP + 0.1, 5.33, 4.6, AGENT_LOOP, size=11, title="The run loop (from the startup script)"),
    Text(X0, TOP + 4.85, W, 0.6, T("Interfaces the overlay creates (cali*, vxlan*, tunl*) are ignored, so NetBox "
                                   "holds the physical network only.", size=16, color=BODY)),
], optional=True, notes="""
[0:17] The agent config, from the cluster, minus the token. Two details worth stealing. It ignores the interfaces Calico and VXLAN create, so NetBox only holds physical interfaces. And the site is a command: it asks Kubernetes for the node's site label. The loop: start lldpd, wait at least thirty seconds so LLDP has found its neighbours, then run once a day with jitter.
""")

mon = [Text(X0, TOP + 0.05, 2.9, 0.4, T("Sources", size=17, bold=True, color=NAVY))]
srcs = [("node-exporter", f"on all {S['node_exporter']} nodes"), ("kube-state-metrics", "objects and their state"),
        ("DCGM", "GPU use, memory, power"), ("Apps", "Ceph, the ingress, every service")]
for i, (h, b) in enumerate(srcs):
    mon.append(Box(X0, TOP + 0.5 + i * 1.0, 2.9, 0.85, h, b, head_size=14.5, sub_size=11.5, state="white"))
mon += [Box(4.15, TOP + 1.2, 2.3, 1.6, "Prometheus", "2 replicas, run by the Prometheus operator", head_size=16,
            sub_size=12, step=1, hl=[1]),
        Box(7.0, TOP + 1.2, 2.3, 1.6, "Thanos", f"querier ({S['thanos_querier']} replicas), store, compactor",
            head_size=16, sub_size=12, step=1, hl=[1]),
        Arrow(3.5, TOP + 2.0, 4.15, TOP + 2.0, step=1, hl=[1]), Arrow(6.45, TOP + 2.0, 7.0, TOP + 2.0, step=1, hl=[1]),
        Arrow(9.3, TOP + 2.0, 9.85, TOP + 2.0, step=2, hl=[2]),
        Text(9.85, TOP + 0.05, 2.88, 0.4, T("Consumers", size=17, bold=True, color=NAVY), step=2)]
cons = [("Grafana", "dashboards"), ("Alertmanager", "3 replicas; routes the alerts"),
        ("Public dashboards", "nrp.ai/viz")]
for i, (h, b) in enumerate(cons):
    mon.append(Box(9.85, TOP + 0.75 + i * 1.15, 2.88, 0.9, h, b, head_size=14.5, sub_size=11.5, state="white",
                   step=2))
mon.append(Text(X0, TOP + 4.6, W, 0.7, T("Logs: Elastic collects syslog from every node, SSH logins included.",
                                         size=17, color=BODY)))
add("Watching the Cluster", mon, steps=2, cls="monitor", notes=f"""
[0:18] Monitoring is standard Prometheus, at scale. Sources: node-exporter on all {S['node_exporter']} nodes, kube-state-metrics, DCGM for the GPUs, and the apps themselves, vLLM, Ceph, the ingress. [click] Prometheus, run by the operator, and Thanos in front of it: {S['thanos_querier']} querier replicas plus store and compactor for long-term history. [click] On top: Grafana, Alertmanager and the public dashboards on nrp.ai. Logs go to Elastic, including every SSH login, which matters for security.
""")

ZONES = S["a2a_zones"]
NZ = len(ZONES)
RING_LABELS = {"ucsd-sdsc": "UCSD", "amsterdam": "Amsterdam", "guam": "Guam", "korea": "Korea", "singapore": "Singapore",
               "brazil": "Brazil", "czech": "Czechia", "hawaii": "Hawaii", "unl": "Nebraska", "mghpcc": "MGHPCC",
               "pacificwave": "Pacific Wave", "nysernet": "NYSERNet"}


def ring(cx, cy, r):
    return [(cx + r * math.cos(2 * math.pi * i / NZ - math.pi / 2), cy + r * math.sin(2 * math.pi * i / NZ - math.pi / 2))
            for i in range(NZ)]


def mesh_png():
    out = FIG / "mesh.png"
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    pts = ring(0, 0, 1)
    fig = plt.figure(figsize=(5.4, 5.4), dpi=220)
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
    ax.set_xlim(-1.05, 1.05); ax.set_ylim(1.05, -1.05); ax.axis("off")
    segs = [(pts[i], pts[j]) for i in range(NZ) for j in range(i + 1, NZ)]
    ax.add_collection(LineCollection(segs, colors="#00629B", linewidths=0.25, alpha=0.18))
    hub = ZONES.index("ucsd-sdsc") if "ucsd-sdsc" in ZONES else 0
    ax.add_collection(LineCollection([(pts[hub], pts[j]) for j in range(NZ) if j != hub], colors="#EB6834",
                                     linewidths=0.6, alpha=0.8))
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=9, color="#182B49", zorder=3)
    for i, z in enumerate(ZONES):
        if z in RING_LABELS:
            x, y = pts[i]
            ax.text(x * 1.13, y * 1.13, RING_LABELS[z], fontsize=7.5, ha="center", va="center", color="#182B49",
                    family="DejaVu Sans", fontweight="bold")
    fig.savefig(out, transparent=False, facecolor="white")
    plt.close(fig)
    return out


def mesh_html(size):
    c, r = size / 2, size / 2 - 70
    pts = ring(c, c, r)
    allp = "".join(f"M{pts[i][0]:.1f},{pts[i][1]:.1f}L{pts[j][0]:.1f},{pts[j][1]:.1f}"
                   for i in range(NZ) for j in range(i + 1, NZ))
    hub = ZONES.index("ucsd-sdsc") if "ucsd-sdsc" in ZONES else 0
    spokes = "".join(f'<line x1="{pts[hub][0]:.1f}" y1="{pts[hub][1]:.1f}" x2="{p[0]:.1f}" y2="{p[1]:.1f}" '
                     f'pathLength="1" style="--d:{0.2 + j * 0.012:.3f}s"/>' for j, p in enumerate(pts) if j != hub)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" style="--d:{i * 0.01:.2f}s"/>' for i, (x, y) in enumerate(pts))
    labs = ""
    for i, z in enumerate(ZONES):
        if z in RING_LABELS:
            x, y = pts[i]
            lx, ly = c + (x - c) * 1.17, c + (y - c) * 1.13
            labs += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="central">{RING_LABELS[z]}</text>'
    return (f'<svg class="mesh" viewBox="0 0 {size} {size}" width="{size}" height="{size}"><path class="all" d="{allp}"/>'
            f'<g class="spokes">{spokes}</g><g class="dots">{dots}</g><g class="labs">{labs}</g></svg>')


add("Measuring the Network", [
    Bullets(X0, TOP + 0.15, 6.1, 5.2, [
        f"A **perfSONAR testpoint** on every node ({S['perfsonar_testpoints']} pods, from a DaemonSet)",
        f"**MaDDash** all-to-all between one node per site: {NZ} sites, with the `nautilus.io/a2a-latency` label",
        "Mesh config, iperf3 servers and traceroute run as services in the cluster",
        "When a user says the cluster is slow, we can see whether it's the path",
        "perfsonar.nrp-nautilus.io"], size=18, gap=9),
    Raw(7.05, TOP - 0.05, 5.6, 5.6, mesh_html(800),
        draw=lambda s, k: s.image(mesh_png(), 7.05, TOP - 0.05, 5.6, 5.4)),
    Text(7.05, TOP + 5.25, 5.6, 0.3, T(f"{NZ} sites in the mesh, {SNAP}; orange: one site's tests to every other",
                                       size=12, color=MUTED, align="c"), step=1),
], steps=2, cls="perfsonar", notes=f"""
[0:19] And the network gets measured, which I suspect is the slide you'll have opinions about. A perfSONAR testpoint runs on every node from a DaemonSet, {S['perfsonar_testpoints']} of them. One node per site carries a label that puts it in the all-to-all mesh in MaDDash: {NZ} sites today. [click] Each site tests to every other one; here's one site's share. [click] And here's the whole mesh. The mesh config, iperf3 servers and traceroute run as services in the cluster. It's how we answer "the cluster is slow" with "it's this path".
""")

sec_cols = [("Identity", ["Authentik", "CILogon: federated campus login", "Groups drive namespace access"]),
            ("Detect", ["Falco: runtime alerts, e.g. crypto miners in user pods", "Falco Talon: automated response",
                        "Wazuh; Elastic syslog, SSH logins included"]),
            ("Prevent", ["Gatekeeper admission policies", "Kata VMs for CI and untrusted builds",
                         "Central Calico policy", "CVE mitigations rolled out by Argo CD"]),
            ("Audit", ["IPMI scanner: alerts if a BMC is reachable from outside",
                       "JupyterHub scanner: no anonymous hubs"])]
se = []
for i, (h, items) in enumerate(sec_cols):
    x = X0 + i * 3.07
    se += [Frame(x, TOP + 0.15, 2.9, 4.8, fill=CARD, line=None, radius=0.05, cls="rise",
                 style=f"transition-delay:{i * 0.2:.1f}s"),
           Text(x + 0.2, TOP + 0.3, 2.5, 0.5, T(h, size=21, bold=True, color=NAVY), cls="rise",
                style=f"transition-delay:{i * 0.2:.1f}s"),
           Bullets(x + 0.2, TOP + 0.9, 2.55, 4.0, items, size=17, gap=10, cls="rise",
                   style=f"transition-delay:{i * 0.2 + 0.1:.1f}s")]
add("Security", se, notes="""
[0:20] Security, in four parts. Identity: Authentik, with CILogon for federated campus logins, and groups drive who can use which namespace. Detection: Falco watches runtime behavior, and the classic catch is a crypto miner in a user pod; Falco Talon can respond automatically; Wazuh, and Elastic with every SSH login. Prevention: Gatekeeper admission policies, Kata VMs for CI, the central Calico policy, and CVE mitigations rolled out through Argo. And audits: a scanner that alerts if anyone's IPMI is reachable from outside, and one that checks every JupyterHub on the cluster requires an institutional login.
""")

care = [["Tool", "What it does"], ["kured", "Rolling reboots after kernel updates, a few nodes at a time"],
        ["self-node-remediation", "Fences and recovers nodes that stop responding"],
        ["node-label-monitor", "Watches node labels the scheduler depends on"],
        ["GPU operator, power management", "Drivers, and GPU power tracking"],
        ["Nagios NRPE", "Host checks"],
        ["Upgrade runbooks", "Kubernetes, Calico, Rook, GitLab, JupyterHub, Prometheus ... in the admin docs"]]
add("Routine Care", [
    Table(X0, TOP + 0.15, W, 4.2, care, [3.4, 8.7], size=16, row_h=0.6, mono=(0,), cls="rows"),
    Link(X0, 6.0, 9.0, 0.3, "https://nrp.ai/documentation/admindocs/upgrades/intro/", size=13),
], optional=True, notes="""
[0:21] The routine care that keeps five hundred nodes current: kured reboots nodes a few at a time after kernel updates; self-node-remediation recovers nodes that stop responding; a monitor watches the labels the scheduler depends on. And there's a written runbook for every upgrade, Kubernetes, Calico, Rook, GitLab, in the admin docs.
""")

fs = [Bullets(X0, TOP + 0.15, 5.4, 5.2, [
    "Contributors keep priority on their nodes: reservation taints, and Kueue with NRP's own controllers",
    "Priority classes: **owner**, **nice** (−10), **opportunistic** (preempted first)",
    "Idle GPUs go to opportunistic work, such as Open Science Grid jobs for IceCube and LIGO",
    "Opportunistic work must tolerate being preempted: checkpoint, or just restart"], size=17, gap=9),
    Frame(6.3, TOP + 0.15, 6.43, 3.4, label="A contributed GPU node · 8 GPUs", line="B9C7D8", label_size=14)]
slots = ["own", "own", "idle", "idle", "idle", "idle", "idle", "idle"]
fs.append(Raw(6.5, TOP + 0.75, 6.03, 2.6, "".join(
    f'<div class="gs g{i} {k}"><span class="o">owner</span><span class="i">idle</span><span class="p">opportunistic</span>'
    f'<span class="x">owner</span></div>' for i, k in enumerate(slots)),
    draw=lambda s, k: [(s.rect(6.5 + i * 0.75, TOP + 0.75, 0.66, 2.4, fill=NAVY if i < 2 or i in (2, 3) else "E9B55C",
                               radius=0.12),
                        s.text(6.5 + i * 0.75, TOP + 0.75, 0.66, 2.4,
                               P("owner" if i < 4 else "opport.", size=10, bold=True, color=WHITE if i < 4 else NAVY,
                                 align="c"), anchor="m")) for i in range(8)]))
cap = {0: "The owner's jobs use two GPUs; six sit idle.",
       1: "Opportunistic work fills the idle GPUs, for example OSG glideins.",
       2: "The owner submits more work: the scheduler preempts opportunistic pods to make room."}
for k, t in cap.items():
    fs.append(Text(6.3, TOP + 3.75, 6.43, 1.0, T(t, size=16, color=BODY), only=[k]))
add("Sharing GPUs Fairly", fs, steps=2, cls="fairshare", notes="""
[0:22] How sharing works, because it's the economic model. A contributed node belongs to its owner first, enforced with reservation taints and Kueue, which we've extended with our own controllers. Here the owner is using two of eight GPUs. [click] Opportunistic work fills the rest, for example Open Science Grid glideins running jobs for experiments like IceCube and LIGO. [click] When the owner needs more, the scheduler preempts the opportunistic pods. Opportunistic work has to tolerate that: it checkpoints, or it just starts again somewhere else.
""")

JOIN = [("Rack and cable", "power, cooling, a Science DMZ port, jumbo frames"),
        ("Hand over access", "IPMI, or root SSH from NRP's management address"),
        ("NRP installs", "Ubuntu 24.04, drivers and storage; joins Nautilus"),
        ("Labels and policy", "region, zone, site, GPU model; the central Calico policy"),
        ("It reports in", "to NetBox, Prometheus and the perfSONAR mesh")]
jn = []
bw, gap = 2.2, 0.28
for i, (h, b) in enumerate(JOIN):
    x = X0 + i * (bw + gap)
    jn.append(Box(x, TOP + 0.2, bw, 1.45, f"{i + 1}. {h}", b, head_size=15, sub_size=12.5, step=i,
                  hl=[i], state="normal"))
    if i:
        jn.append(Arrow(x - gap + 0.02, TOP + 0.92, x - 0.02, TOP + 0.92, step=i))
jn += [Text(X0, TOP + 2.05, 5.9, 0.4, T("The site", size=19, bold=True, color=NAVY)),
       Bullets(X0, TOP + 2.5, 5.9, 2.2, ["Keeps an on-site contact for hands-on work",
                                         "Sends maintenance notices; forwards warranty tickets"], size=17, gap=6),
       Text(6.83, TOP + 2.05, 5.9, 0.4, T("NRP", size=19, bold=True, color=NAVY)),
       Bullets(6.83, TOP + 2.5, 5.9, 2.2, ["Patching, packages and host hardening",
                                           "24/7 monitoring and alerting; incident handling from the OS up"],
               size=17, gap=6),
       Text(X0, TOP + 4.0, W, 0.9, T("Then it's schedulable, yours first: owner priority for your users, idle time "
                                     "for everyone else.", size=22, bold=True, color=BLUE), step=4),
       Link(X0, TOP + 4.85, W, 0.3, "https://nrp.ai/documentation/admindocs/participating/new-contributor-guide/",
            size=13)]
add("How a Node Joins", jn, steps=4, notes="""
[0:08] You've now seen all the pieces, so here's what happens when a campus contributes a node; this is also how your institution would join. The site racks and cables it into the Science DMZ, with jumbo frames. [click] It gives us access, IPMI or root SSH from our management address. [click] We install Ubuntu, the drivers and storage, and join it to the cluster. [click] It gets its topology labels and falls under the central Calico policy. [click] And it reports in: the NetBox agent records it and its switch port, node-exporter feeds Prometheus, and its perfSONAR testpoint joins the mesh.

The split of work: the site keeps someone who can touch the box; we do everything from the OS up. And then it's schedulable, with owner priority, exactly the sharing model from the previous slide.
""")

# ═════════════════════════════════════════════════════════════════════════════════════
# AI
# ═════════════════════════════════════════════════════════════════════════════════════
section("AI on NRP", "[0:23] The AI service: the most interesting system we run right now.")

# GPUs per model, from the snapshot
per_model = {}
for p in S["llm_placement"]:
    m = model_name(p["workload"])
    g = next(s for s in S["llm_servers"] if s["name"] == p["workload"])
    d = per_model.setdefault(m, {})
    d[short_gpu(p["gpu"])] = d.get(short_gpu(p["gpu"]), 0) + sum(g["gpu"].values())
ORDER = ["deepseek-v4-flash", "glm-5", "kimi", "minimax", "qwen3", "qwen3-small", "gpt-oss", "gemma", "gemma-small",
         "gemma-small-e4b", "qwen3-embedding"]
mrows = [["Model name", "Serving on"]] + [[m, ", ".join(f"{v} × {k}" for k, v in sorted(per_model[m].items(),
                                                                                       key=lambda kv: -kv[1]))]
                                          for m in ORDER if m in per_model]
add("The LLM Service", [
    Bullets(X0, TOP + 0.15, 5.5, 5.2, [
        "One OpenAI-compatible endpoint, **ellm.nrp-nautilus.io/v1**; an Anthropic-compatible one too",
        f"{len(MODEL_NAMES)} model names on that one endpoint",
        f"{S['llm_gpus']} GPUs serve them, from A10s to H200s, at {len({p['site'] for p in S['llm_placement']})} sites",
        f"About {TOKENS_A_DAY} tokens a day (September 2026)",
        "Free for research and education, with a token from nrp.ai/llmtoken"], size=17, gap=8),
    Table(6.45, TOP + 0.1, 6.28, 4.95, mrows, [2.5, 3.78], size=13, mono=(0,), row_h=0.41, cls="rows"),
    Text(6.45, TOP + 5.1, 6.28, 0.3, T(f"Model-server pods by GPU, {SNAP}. The catalog changes.", size=12, color=MUTED)),
], notes=f"""
[0:23] The LLM service. One OpenAI-compatible endpoint, plus an Anthropic-compatible one so tools like Claude Code work against it. {len(MODEL_NAMES)} model names behind it, for open-weight models like DeepSeek, GLM, Kimi, Qwen and Gemma. {S['llm_gpus']} GPUs serve them, and it's used heavily: about seven billion tokens a day in September. It's free for research and education with a token.

On the right is what's serving each model right now: DeepSeek on H100s, GLM on H200s and H100s, Kimi and MiniMax on eight A100s each, and the small models on A10s and A6000s. Let me show you where those GPUs are.
""")

LLM = llm_sites(GEO, S)


def llm_map_html():
    w, h = GEO["width"], GEO["height"]
    land = "".join("M" + "L".join(f"{x:g},{y:g}" for x, y in pts) + "Z" for pts in GEO["paths"])
    r = PIN_STYLE["llm"][1]
    svg = (f'<svg class="usmap llm" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}"><path class="land" '
           f'd="{land}"/><defs><path id="pin-llm" d="{pin_path(r)}"/></defs>')
    for i, p in enumerate(LLM):
        svg += (f'<g transform="translate({p["x"]:.1f},{p["y"]:.1f})"><g class="pin k-llm" style="--d:{0.2 + i * 0.25:.2f}s">'
                f'<use href="#pin-llm"/><circle cy="{-1.6 * r:.1f}" r="{0.62 * r:.1f}"/><text y="{-1.6 * r:.1f}" '
                f'text-anchor="middle" dominant-baseline="central">{p["n"]}</text></g></g>')
    return svg + "</svg>"


lrows = [["#", "Site", "Models", "GPUs"]] + [[str(p["n"]), " + ".join(
    s.replace("University of California, San Diego", "UC San Diego").replace("San Diego State University", "SDSU")
    .replace("California State University, Sacramento", "Sacramento State")
    .replace("California State Polytechnic University, Humboldt", "Cal Poly Humboldt")
    .replace("University of Nebraska, Lincoln", "Nebraska–Lincoln").replace("University of New Mexico", "UNM")
    for s in p["sites"]), ", ".join(p["models"]), p["gpu_text"]] for p in LLM]
add("Where the Models Run", [
    Raw(X0, TOP + 0.3, 5.9, 3.95, llm_map_html(),
        draw=lambda s, k: s.image(FIG / "llm_map.png", X0, TOP + 0.3, 5.9, 3.95, align="l", valign="t")),
    Table(6.7, TOP + 0.1, 6.03, 5.0, lrows, [0.35, 1.9, 2.3, 1.5], size=11.5, row_h=0.5, cls="rows", bold_first=False),
    Text(X0, TOP + 4.45, 5.9, 0.9, T("Every pin is a set of model servers in the same cluster, behind the same "
                                     "endpoint. Fresno State and Internet2 Ann Arbor are placed by city.", size=13,
                                     color=MUTED)),
], cls="llmsites", notes="""
[0:24] Here's where the model servers are running this week: the San Diego campuses, Nebraska, Sacramento State, Chico State, Fresno State, Humboldt, New Mexico, and an Internet2 node in Ann Arbor. That's the point of the whole design: GPUs that campuses contributed, wherever they are, serving one endpoint. A request from Chicago can be answered by a GPU in Fresno or Ann Arbor, and the user never knows.
""")

# The request path, step by step
RP_Y, RP_H = TOP + 0.3, 1.0
rp = [Box(X0, RP_Y, 1.55, RP_H, "Client", "OpenAI API", head_size=16, sub_size=12, hl=[1, 4]),
      Box(2.6, RP_Y, 2.35, RP_H, "Envoy AI Gateway", "ellm.nrp-nautilus.io", head_size=15, sub_size=12, hl=[1, 2, 4]),
      Box(5.5, RP_Y, 2.25, RP_H, "AIGatewayRoute", "x-ai-eg-model: qwen3", head_size=15, sub_size=12, mono_sub=True,
          hl=[2]),
      Box(8.3, RP_Y, 2.05, RP_H, "InferencePool", "with an endpoint picker", head_size=15, sub_size=12, hl=[3]),
      Arrow(2.15, RP_Y + 0.5, 2.6, RP_Y + 0.5, hl=[1]), Arrow(4.95, RP_Y + 0.5, 5.5, RP_Y + 0.5, hl=[2]),
      Arrow(7.75, RP_Y + 0.5, 8.3, RP_Y + 0.5, hl=[3]),
      Box(2.6, RP_Y + 1.75, 2.35, 0.95, "llm-auth", "ext_authz over gRPC; fail closed", state="white", head_size=15,
          sub_size=12, hl=[1]),
      Arrow(3.77, RP_Y + 1.0, 3.77, RP_Y + 1.75, hl=[1]),
      Box(5.5, RP_Y + 1.75, 2.25, 0.95, "Rate limiter", "output tokens per token and model", state="white",
          head_size=15, sub_size=12, hl=[4]),
      Arrow(4.95, RP_Y + 0.9, 5.5, RP_Y + 2.2, hl=[4], step=4)]
pods = [("vLLM pod a", "queue 6 · KV cache 88%"), ("vLLM pod b", "queue 0 · KV cache 31%"),
        ("vLLM pod c", "queue 2 · KV cache 64%")]
for i, (h, b) in enumerate(pods):
    rp.append(Box(10.9, RP_Y - 0.25 + i * 0.85, 1.83, 0.72, h, b, state="white", head_size=13, sub_size=10.5,
                  hl=[3] if i == 1 else None))
    rp.append(Arrow(10.35, RP_Y + 0.5, 10.9, RP_Y + 0.11 + i * 0.85, hl=[3] if i == 1 else None,
                    color=MUTED if i == 1 else "C9D4E3"))
rp.append(Text(10.9, RP_Y + 2.33, 1.83, 0.4, T("example values", size=11, color=MUTED, align="c")))
CAPS = {0: ("One request, five stops", "The gateway is the Envoy Gateway from the ingress slide, plus its AI "
            "extension, Envoy AI Gateway. A client asks for `qwen3`."),
        1: ("1. Who are you?", "The gateway sends the bearer token to an external auth service over gRPC. If auth "
            "can't answer, the request fails: fail closed."),
        2: ("2. Which model?", "The gateway reads `model` from the JSON body into the `x-ai-eg-model` header, and an "
            "AIGatewayRoute rule matches it to a backend: here an InferencePool."),
        3: ("3. Which pod?", "The endpoint picker scores the pool's vLLM pods by queue depth, KV-cache use and "
            "prefix-cache hits, and picks one."),
        4: ("4. The answer, and the bill", "vLLM answers. The gateway reads the token counts from the response; the "
            "rate limiter charges output tokens to this token and model.")}
for k, (h, b) in CAPS.items():
    rp.append(Text(X0, TOP + 3.45, W, 1.6, [T(h, size=22, bold=True, color=NAVY), T(b, size=19, color=BODY, before=6)],
                   only=[k]))
rp.append(Raw(0, 0, 13.333, 7.5, '<span class="pkt rp"></span>', pptx=False))
add("A Request, Step by Step", rp, steps=4, cls="reqpath", builds=True, notes="""
[0:25] One request through the gateway. Remember Envoy Gateway from the ingress slide: the LLM gateway is the same thing plus its AI extension, Envoy AI Gateway. A client asks for qwen3 with the standard OpenAI API.

[click] First, who are you. Envoy calls an external auth service over gRPC with the bearer token, and it fails closed: if auth can't answer, nobody gets through.

[click] Second, which model. The gateway parses the JSON body, lifts the model name into a header, x-ai-eg-model, and an AIGatewayRoute rule matches that header to a backend. Here the backend is an InferencePool, from the Gateway API inference extension.

[click] Third, which pod. The pool has an endpoint picker that scores the vLLM pods on queue depth, KV-cache use, and whether a pod already has this prompt's prefix cached, which matters a lot for chat and agents. The numbers here are illustrative; the logic is real.

[click] Fourth, the bill. vLLM answers, the gateway reads the token counts from the response, and the rate limiter charges the output tokens against this user's token and this model.
""")

BTP = '''apiVersion: gateway.envoyproxy.io/v1alpha1
kind: BackendTrafficPolicy
metadata: {name: envoy-ai-gateway-nrp, namespace: nrp-llm}
spec:
  rateLimit:
    type: Global
    global:
      rules:
      - clientSelectors:
        - headers:
          - {name: authorization, type: Distinct}
          - {name: x-ai-eg-model, type: Distinct}
        limit: {requests: 48000, unit: Minute}
        cost:
          request: {from: Number, number: 1}
          response:
            from: Metadata
            metadata: {namespace: io.envoy.ai_gateway,
                       key: llm_output_token}
  retry:
    numRetries: 2
    retryOn: {httpStatusCodes: [500, 502, 503, 504]}
  healthCheck:
    active: {type: HTTP, http: {path: /health}, interval: 10s,
             unhealthyThreshold: 3}
    passive: {consecutive5XxErrors: 2, baseEjectionTime: 30s,
              maxEjectionPercent: 50}'''
HDRS = '''$ curl -si https://ellm.nrp-nautilus.io/v1/chat/completions \\
    -H "Authorization: Bearer $OPENAI_API_KEY" \\
    -d '{"model": "qwen3", ...}' | grep -i ratelimit
x-ratelimit-limit: 48000, 48000;w=60
x-ratelimit-remaining: 47999
x-ratelimit-reset: 9'''
add("Gateway Policies", [
    Code(X0, TOP, 6.45, 5.3, BTP, size=10, lang="yaml",
         lines_hl={**{i: [1] for i in range(5, 20)}, **{i: [2] for i in range(20, 23)},
                   **{i: [3] for i in range(23, 28)}}),
    Text(7.25, TOP + 0.05, 5.48, 2.3, [
        T("**Rate limit:** 48,000 output tokens a minute, per token and model", size=16, step=1),
        T("**Retries:** twice, on 5xx", size=16, before=10, step=2),
        T("**Health:** probe /health every 10 s; eject a pod after two 5xx", size=16, before=10, step=3)]),
    Text(7.25, TOP + 2.55, 5.48, 0.35, T("What a client sees (demo, 10 Nov)", size=14, bold=True, color=NAVY)),
    Code(7.25, TOP + 2.95, 5.48, 2.35, HDRS, size=10.5),
], steps=3, cls="policies", notes="""
[0:26] The policy behind that, straight from the cluster. [click] The rate limit is global, keyed on the authorization header and the model, and the cost is the number of output tokens in the response: 48,000 a minute per token and model. Clients see it in standard rate-limit headers, as in the curl on the right. [click] Retries, twice, on 500-series errors. [click] Active health checks on /health every ten seconds, and passive outlier detection: two 5xx in a row and the pod is ejected for thirty seconds, never more than half the pool.
""")


def chain_of(task):
    r = next(r for r in S["llm_routes"] if task in r["models"])
    out = []
    for b in sorted(r["backends"], key=lambda b: b["priority"]):
        n = b["name"].replace("envoy-ai-gateway-nrp-", "").replace("envoy-ai-gateway-sdsc-", "").replace("-direct", "")
        n = {"massedcompute-gemma4": "gemma-small-e4b"}.get(n, n)
        out.append(n)
    return out


trows = [["Ask for", "Tried in this order"]] + [[t, " → ".join(chain_of(t))] for t in TASKS
                                                if any(t in r["models"] for r in S["llm_routes"])]
tm = [Table(X0, TOP + 0.1, 7.15, 5.0, trows, [1.55, 5.6], size=12.5, mono=(0, 1), row_h=0.5, cls="rows")]
coding = chain_of("coding")
tm.append(Box(8.2, TOP + 0.1, 4.53, 0.75, "model: coding", None, state="active", head_size=16))
for i, n in enumerate(coding):
    y = TOP + 1.25 + i * 0.95
    tm.append(Box(8.75, y, 3.98, 0.72, n, f"priority {i}", state="white", head_size=15, sub_size=11.5,
                  hl=[1] if i == 0 else [2] if i == 1 else None, mono_sub=True))
    tm.append(Arrow(8.45, TOP + 0.85, 8.45, y + 0.36, head=False, color="C9D4E3"))
    tm.append(Arrow(8.45, y + 0.36, 8.75, y + 0.36, hl=[1] if i == 0 else [2] if i == 1 else None))
tm.append(Raw(8.75, TOP + 1.25, 3.98, 0.72, '<div class="eject">unhealthy: ejected</div>', only=[2], pptx=False))
tm.append(Text(8.2, TOP + 5.1, 4.53, 0.4, T("GitLab Duo Self-Hosted uses `service`.", size=13, color=MUTED)))
add("Ask for a Task, Not a Model", tm, steps=2, cls="tasks", notes=f"""
[0:27] One thing I like about this setup: you can ask for a task instead of a model. The model name coding is not a model. It's a priority list: {', then '.join(coding)}. [click] Normally the first one answers. [click] If it's down or ejected by the health checks, the gateway falls through to the next. Users and tools get a stable name while the catalog rotates underneath. Our own GitLab's AI features use one of these, service.
""")

STS = """apiVersion: apps/v1
kind: StatefulSet
metadata: {name: qwen38-flash-next-a100, namespace: nrp-llm}
spec:
  replicas: 2
  template:
    metadata:
      labels: {component: llm, service-group: qwen-vllm-inference}
    spec:
      priorityClassName: owner          # tolerates the reservation taint
      containers:
      - image: vllm/vllm-openai:v0.33.0
        args: ["vllm serve Qwen/Qwen3.8-Flash-Next-FP8 --port 5000
                --tensor-parallel-size 4 --enable-expert-parallel
                --enable-prefix-caching --max-model-len 1000000
                --kv-cache-dtype bfloat16 --otlp-traces-endpoint ..."]
        resources:
          limits: {cpu: "36", memory: 440Gi, nvidia.com/a100: 4}
        readinessProbe: {httpGet: {path: /health, port: 5000}}
      affinity:   # GPU memory > 80 GB, Ampere or newer
  volumeClaimTemplates:
  - metadata: {name: qwen38-flash-cache}
    spec: {storageClassName: linstor-igrok,
           resources: {requests: {storage: 256Gi}}}"""
sts_hl = {8: [1], 10: [1], 12: [2], 13: [2], 14: [2], 15: [2], 16: [2], 19: [3], 21: [4], 22: [4], 23: [4],
          24: [4]}
add("Serving with vLLM", [
    Code(X0, TOP + 0.05, 7.6, 5.3, STS, size=11, lang="yaml", lines_hl=sts_hl,
         title="qwen3, from the cluster (shortened)"),
    Text(8.45, TOP + 0.1, 4.28, 5.2, [
        T("**Labels** put the pod in the `qwen3` pool; priority **owner**", size=16, step=1),
        T("**vLLM**: tensor parallel 4, expert parallel, prefix caching, traces to OpenTelemetry", size=16,
          before=12, step=2),
        T("**Health**: probes on `/health`; vLLM and DCGM metrics go to the same Prometheus and Thanos, and drive the "
          "LLM status page", size=16, before=12, step=3),
        T("**Weights** on a Linstor volume, so a restart doesn't download them again", size=16, before=12, step=4),
        T(f"{len([x for x in S['llm_servers'] if not x['name'].endswith('-worker')])} servers like this. Their config is "
          "in GitLab (`prp/llm-proxy`), applied by hand, not yet by Argo CD", size=15, color=MUTED, before=20)]),
], steps=4, cls="vllm", notes="""
[0:28] What one of those model servers looks like, from the cluster, shortened. It's a StatefulSet. [click] Its labels put it in the qwen3 pool from the request slide, and it runs at owner priority, from the sharing slide. [click] vLLM with tensor parallelism across four A100s, expert parallelism, prefix caching, and traces to an OpenTelemetry collector. [click] Health probes on /health, and the metrics go into the same Prometheus and Thanos as everything else; they drive the public LLM status page. [click] And the weights sit on a Linstor volume, the replicated block storage from earlier, so a restart doesn't re-download them.

This is one of the services I mentioned that isn't in Argo yet: the config lives in GitLab and gets applied by hand.
""")

qs = [Bullets(X0, TOP + 0.15, 5.4, 5.2, [
    "Extra replicas run at **opportunistic** priority on idle GPUs and join the same pool",
    "`qwen3-small`: 4 × A6000 at Chico State as owner, plus two H200 replicas at Fresno State as opportunistic",
    "`glm-5` and `gemma` borrow H100s and A100s at low priority too",
    "Preempted when the owner needs the GPU; the endpoint picker routes around the gap"], size=17, gap=9),
    Box(6.4, TOP + 0.2, 6.33, 0.85, "InferencePool qwen3-small", "selects pods by label: service-group=qwen3-small",
        state="active", head_size=16, sub_size=12)]
reps = [("CSU Chico", "4 × A6000 · owner", "normal"), ("Fresno State", "1 × H200 · opportunistic", "gold"),
        ("Fresno State", "1 × H200 · opportunistic", "gold")]
for i, (h, b, st) in enumerate(reps):
    x = 6.4 + i * 2.15
    qs.append(Box(x, TOP + 1.75, 2.03, 1.1, h, b, state=st, head_size=15, sub_size=11.5,
                  cls=f"rep r{i}"))
    qs.append(Arrow(9.56, TOP + 1.05, x + 1.0, TOP + 1.75, cls=f"rep r{i}"))
qs.append(Raw(6.4 + 2 * 2.15, TOP + 1.75, 2.03, 1.1, '<div class="eject gone">preempted</div>', only=[1],
              pptx=False))
qs.append(Text(6.4, TOP + 3.15, 6.33, 1.5, T("Step 1: the H200's owner needs it back. One replica is preempted; the "
                                             "pool keeps answering from the other two.", size=16, color=BODY),
               step=1))
add("Borrowing Idle GPUs", qs, steps=1, cls="scavenge", notes="""
[0:29] This is my favorite trick, and it's the opportunistic priority from the sharing slide applied to inference. A model's pool selects pods by label, so we can add replicas anywhere. qwen3-small runs on four A6000s at Chico State as an owner workload, and we add two replicas on H200s at Fresno State at opportunistic priority, so they only use those GPUs when they're idle. [click] When Fresno needs its GPU, the scheduler preempts a replica, the endpoint picker stops sending it traffic, and the service keeps answering. Idle GPUs anywhere in the country become inference capacity, with no effect on their owners.
""")

tn = [Frame(X0, TOP + 0.15, 4.4, 3.0, label="Node A · 4 × H100", line="B9C7D8", label_size=14),
      Frame(5.25, TOP + 0.15, 4.4, 3.0, label="Node B · 4 × H100", line="B9C7D8", label_size=14)]
for n, x0 in enumerate([X0, 5.25]):
    tn.append(Box(x0 + 0.2, TOP + 0.65, 4.0, 0.7, "head pod: serves the API" if n == 0 else "worker pod",
                  "pipeline stage 1" if n == 0 else "pipeline stage 2", state="active" if n == 0 else "normal",
                  head_size=14, sub_size=11.5))
    for g in range(4):
        tn.append(Box(x0 + 0.2 + g * 1.0, TOP + 1.6, 0.92, 0.9, f"GPU {g}", "TP rank", state="white", head_size=12,
                      sub_size=10))
    tn.append(Text(x0 + 0.2, TOP + 2.6, 4.0, 0.4, T("tensor parallel 4, inside the node (NVLink)", size=12,
                                                    color=MUTED, align="c")))
tn.append(Arrow(5.0, TOP + 1.0, 5.45, TOP + 1.0, color=ORANGE, width=3))
tn.append(Text(4.6, TOP + 3.2, 5.0, 0.4, T("pipeline parallel 2, across nodes (NCCL over the network)", size=13,
                                           color=ORANGE, align="c")))
tn.append(Bullets(9.95, TOP + 0.15, 2.78, 5.2, [
    "DeepSeek V4.1 Flash, two copies",
    "Head and worker StatefulSets",
    "A custom supervisor restarts both together (LeaderWorkerSet isn't installed)",
    "Headless Service; NetworkPolicy limits traffic to the group",
    "NCCL settings pinned, e.g. `NCCL_SOCKET_IFNAME=eth0`"], size=14, gap=6))
tn.append(Text(X0, TOP + 3.75, 9.05, 1.4, T("Expert parallelism spreads the model's experts across the GPUs. Both "
                                            "copies run on SDSC's Expanse H100 nodes.", size=15, color=BODY)))
add("One Model, Two Nodes", tn, optional=True, notes="""
[0:30] The biggest model doesn't fit on one node, so DeepSeek runs across two four-H100 nodes: tensor parallel inside each node, pipeline parallel across the pair, expert parallel on top. Kubernetes has LeaderWorkerSet for this, but it isn't installed on Nautilus, so the team wrote a small supervisor that restarts head and worker together. A headless service and a network policy keep the group's NCCL traffic to itself.
""")

ar = [("Open WebUI", "chat in the browser, with a terminals operator"), ("Web search", "SearXNG, for tools and chat"),
      ("Embeddings", "qwen3-embedding; TEI on a GPU"), ("Vector databases", "Milvus (managed) and Qdrant"),
      ("MCP route", "an MCP gateway; an accounting MCP server"), ("Telemetry", "OpenTelemetry collector into ClickHouse"),
      ("Coding agents", "Claude Code, opencode and others, with tested configurations")]
ae = []
for i, (h, b) in enumerate(ar):
    ae.append(Box(X0 + (i % 4) * 3.07 + (1.535 if i >= 4 else 0), TOP + 0.2 + (i // 4) * 1.7, 2.92, 1.45, h, b,
                  head_size=17, sub_size=13,
                  cls="rise", style=f"transition-delay:{0.1 + i * 0.1:.1f}s"))
ae.append(Text(X0, TOP + 3.75, W, 1.0, T("All of it on the same cluster, most of it deployed the same way as everything "
                                         "else: from git.", size=19, color=BODY)))
add("Around the Models", ae, optional=True, notes="""
[0:30] Around the models there's a small ecosystem: Open WebUI for chat, web search, embeddings and two vector databases, an MCP route, telemetry into ClickHouse, and tested configurations for coding agents.
""")

bot = [Box(X0, TOP + 0.3, 2.7, 1.2, "An operator in Slack", "mentions the bot with a question", head_size=15,
           sub_size=12, hl=[1]),
       Box(4.0, TOP + 0.3, 2.9, 1.2, "A model on NRP", "deepseek-v4-flash, through the same gateway", head_size=15,
           sub_size=12, hl=[1, 2, 3]),
       Box(8.2, TOP + 0.3, 4.53, 1.2, "16 read-only tools", "pods, logs, events, nodes · PromQL on Thanos · NRP "
           "docs search · accounting MCP · triage playbooks", head_size=15, sub_size=12, hl=[2]),
       Arrow(3.3, TOP + 0.9, 4.0, TOP + 0.9, hl=[1]),
       Arrow(6.9, TOP + 0.75, 8.2, TOP + 0.75, hl=[2]), Arrow(8.2, TOP + 1.05, 6.9, TOP + 1.05, hl=[2]),
       Text(6.95, TOP + 1.12, 1.25, 0.4, T("a loop", size=12, color=MUTED, align="c"), step=2),
       Box(4.0, TOP + 2.0, 2.9, 1.0, "An answer in the thread", "the finding, the evidence, the tool calls",
           head_size=15, sub_size=12, step=3, hl=[3]),
       Arrow(5.45, TOP + 1.5, 5.45, TOP + 2.0, step=3, hl=[3]),
       Text(X0, TOP + 3.2, 5.9, 0.4, T("Guardrails", size=19, bold=True, color=NAVY)),
       Bullets(X0, TOP + 3.65, 5.9, 2.0, ["RBAC denies secrets, exec and every write",
                                          "Namespace allowlist; credentials redacted",
                                          "Logs and events treated as untrusted (prompt injection)",
                                          "Budgets on tool calls, iterations and time"], size=15, gap=4),
       Text(6.83, TOP + 3.2, 5.9, 0.4, T("Status", size=19, bold=True, color=NAVY)),
       Bullets(6.83, TOP + 3.65, 5.9, 2.0, ["Phase 1, read-only: built and tested with mocks",
                                            "Phase 2, write actions behind two-human approval: not started",
                                            "Also an MCP server, and an eval harness to compare models"],
               size=15, gap=4)]
add("An LLM on Call: nrp-ops-bot", bot, steps=3, cls="opsbot", notes="""
[0:21] To close the AI part, where it meets the operations part. nrp-ops-bot is an operator's assistant in Slack, built from pieces you've now seen. [click] You mention it with a question, and it calls a model through the same gateway, deepseek-v4-flash. [click] The model works in a loop with sixteen read-only tools: pods, logs, events and nodes from Kubernetes, PromQL against the Thanos from the monitoring slide, a search index of our docs, the accounting server, and per-service triage playbooks. [click] It answers in the thread with the finding, the evidence and the tool calls it made, so you can check its work.

The guardrails matter more than the model: RBAC that denies secrets, exec and every write; redaction; and it treats pod logs and events as untrusted input, because a log line is a great place for a prompt injection. It's honest to say this is early: phase one is built and tested with mocks; write actions with two-human approval haven't started.
""")

# ═════════════════════════════════════════════════════════════════════════════════════
# USE IT
# ═════════════════════════════════════════════════════════════════════════════════════
section("Using It Yourself", "[0:31] You can use all of this. Here's how.")

ways = [("JupyterHub", "notebooks with a GPU, in the browser", "jupyterhub-west.nrp-nautilus.io"),
        ("Coder", "VS Code in the browser, in your namespace", "coder.nrp-nautilus.io"),
        ("kubectl", "jobs, services and storage in a namespace", "nrp.ai/config"),
        ("GitLab", "repos, CI in Kata VMs, a registry", "gitlab.nrp-nautilus.io"),
        ("LLM API", "OpenAI- and Anthropic-compatible", "ellm.nrp-nautilus.io/v1"),
        ("Open WebUI", "chat with every model", "nrp-openwebui.nrp-nautilus.io")]
we = []
for i, (h, b, u) in enumerate(ways):
    x, y = X0 + (i % 3) * 4.1, TOP + 0.2 + (i // 3) * 2.2
    we += [Box(x, y, 3.9, 1.95, h, b, head_size=22, sub_size=15, cls="rise", style=f"transition-delay:{i * 0.12:.2f}s"),
           Text(x, y + 1.35, 3.9, 0.4, T(u, size=13, color=BLUE, font=MONO, align="c"), cls="rise",
                style=f"transition-delay:{i * 0.12:.2f}s")]
we.append(Text(X0, 5.85, W, 0.5, T("Who uses them today: research groups, each in a namespace; courses, each with "
                                    "its own JupyterHub; and collaborations through OSG.", size=16, color=MUTED)))
add("Ways In", we, notes="""
[0:31] Six ways in, depending on how much infrastructure you want to touch. JupyterHub and Coder in the browser; kubectl for anything Kubernetes can run; GitLab for code and CI, the same one from earlier; the LLM API, the endpoint from the AI part; and Open WebUI to just chat with the models. Today that's research groups, courses that each get their own hub, and big collaborations through OSG.
""")

add("Getting Access", [
    Text(X0, TOP + 0.15, 6.3, 5.1, [
        T("1.  Log in at **nrp.ai**", size=20),
        T("Log In → CILogon → your institution", size=17, before=3),
        T("2.  Get into a namespace", size=20, before=16),
        T("Request one at **get-started.nrp-nautilus.io**", size=17, before=3),
        T("Or ask an existing namespace admin to add you", size=17, before=3),
        T("3.  Start working", size=20, before=16),
        T("JupyterHub, kubectl, GitLab, or an LLM token from **nrp.ai/llmtoken**", size=17, before=3),
        T("**Who can request a namespace:** faculty, staff, postdocs and research scientists; students through "
          "their PI.", size=16, before=20)], cls="stagger"),
    Link(7.2, TOP + 0.05, 5.53, 0.3, "https://get-started.nrp-nautilus.io", size=14, align="r"),
    Image(7.2, TOP + 0.42, 5.53, 4.8, IMG / "namespace_form.png", border="DDE8F2", align="r", valign="t", cls="pop"),
], notes="""
[0:32] Access is three steps. Log in at nrp.ai through CILogon with your institution. Get into a namespace: if you're faculty, staff, a postdoc or a research scientist you can request one with this form; a person reviews it. Then start working. For the LLMs, you get a token from nrp.ai/llmtoken.
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
[0:32] And the ways to run work, which map onto Kubernetes objects. JupyterHub: pick a GPU, work in a notebook; idle servers stop, an hour after you close the browser on our hub. [click] A bare pod with a shell: deleted after six hours, at most two GPUs. [click] A Deployment for a service that stays up and gets restarted when it crashes; removed after two weeks unless we grant an exception. [click] And Jobs for real work: submit six, four start, two wait in Pending and take the first GPUs that free up, and when they finish the GPUs go back to the pool.
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
[0:33] For completeness, a GPU job. Four parts: where it runs, your namespace; what it runs, an image and a command; what it needs, two CPUs, six gigs, one GPU; and which GPU, by memory and generation rather than by brand. The demo submits exactly this.
""")

add("Where to Start", [
    Text(X0, TOP + 0.1, 5.9, 0.45, T("Use it", size=21, bold=True, color=NAVY)),
    Bullets(X0, TOP + 0.6, 5.9, 4.5, [
        "**The LLM API in your automation:** config review, log triage, a docs assistant; task names keep working "
        "as the catalog changes",
        "**Your tools in a namespace:** web apps, Postgres and ClickHouse from the operators, S3 for data",
        "**GitLab CI** to build and ship them",
        "**GPUs for AI and ML:** a notebook to start, Jobs when it's real"], size=17, gap=10),
    Text(6.83, TOP + 0.1, 5.9, 0.45, T("Connect to it", size=21, bold=True, color=NAVY)),
    Bullets(6.83, TOP + 0.6, 5.9, 4.5, [
        "**Contribute nodes**, the way a node joins: you keep priority, NRP runs them",
        "**InterLink:** a Slurm cluster appears as a virtual node",
        "**Federation** with another Kubernetes cluster",
        "**FABRIC and SENSE** testbeds, with Multus for extra NICs",
        "**perfSONAR:** a testpoint on your node joins the mesh"], size=17, gap=10),
    Link(X0, 6.0, W, 0.3, "https://nrp.ai/documentation/admindocs/participating/new-contributor-guide/", size=13),
], notes="""
[0:34] Where to start, two ways. Use it: the LLM API in your own automation, where the task names save you from chasing model names; your tools in a namespace; GitLab CI to build them; GPUs for ML. Or connect to it: contribute nodes, the way you saw a node join; attach a Slurm cluster through InterLink; federate a Kubernetes cluster; the FABRIC and SENSE testbed integrations; or just put a perfSONAR testpoint in the mesh.
""")

section("Live Demo", """[0:35] About twelve minutes. Notebook: workspace/notebooks/demo.ipynb (Bash kernel) on jh-training.nrp-nautilus.io; the operator view from a laptop terminal with admin kubectl. Run sheet: deck/README.md.

1. The cluster (3 min): kubectl get nodes with -L and -l for regions and GPU models; then, on the laptop, the NetBox agent, perfSONAR and node-exporter DaemonSets, the Argo CD apps, the gateway routes and pools.
2. The LLM gateway (5 min): curl | jq for the model list and one qwen3 answer; curl -si | grep for the rate-limit headers; then the task name coding and which model answered.
3. A GPU job (4 min): set ME, submit, kubectl get pods until Running, logs -f, delete. If it's Pending, describe, then show the warm-up job. If time: Argo CD, Grafana and MaDDash in a browser.""")

add("Acknowledgments", [
    Bullets(X0, TOP + 0.15, W, 5.0, [
        "NRP is supported by NSF awards OAC-1541349, OAC-1826967, OAC-2030508, OAC-1841530, OAC-2005369, "
        "OAC-2112167, CISE-1713149, CISE-2100237 and CISE-2120019",
        "Networks: CENIC, Pacific Wave, Internet2, MREN, GPN, NYSERNet, FLR, NEREN, Sun Corridor, OARnet, SCLR and "
        "the Albuquerque GigaPoP",
        "The NRP operations teams at SDSC, the University of Nebraska–Lincoln and MGHPCC, and the campuses that "
        "host and share their hardware",
        "SCinet, for having us during the NOC move"], size=18, gap=14),
], notes="[0:47] Thanks to NSF, the networks, the operations teams and the campuses, and to SCinet for having me.")

links = [("Today's materials", "training.nrp-nautilus.io/scinet-sc26"), ("Portal and login", "nrp.ai"),
         ("Request a namespace", "get-started.nrp-nautilus.io"), ("LLM endpoint", "ellm.nrp-nautilus.io/v1"),
         ("LLM token", "nrp.ai/llmtoken"), ("perfSONAR", "perfsonar.nrp-nautilus.io"),
         ("Admin guide", "nrp.ai/documentation/admindocs"), ("Support chat and email", "nrp.ai/contact")]
q = "".join(f'<div class="qrow"><span>{lab}</span><a href="https://{u}" target="_blank" rel="noopener">{u}</a></div>'
            for lab, u in links)


def q_draw(s, k):
    for i, (lab, u) in enumerate(links):
        y = 1.70 + i * 0.56
        s.text(X0, y, 3.1, 0.5, P(lab, size=17, color=LIGHT), anchor="m")
        s.text(X0 + 3.15, y, 6.6, 0.5, P(u, size=15, bold=True, color=GOLD, font=MONO), anchor="m")


add("Questions?", [
    Raw(X0, 1.7, 9.5, 4.6, q, draw=q_draw, cls="stagger"),
    Text(X0, 6.25, 12.1, 0.45, T("Daniel Diaz  ·  d4diaz@ucsd.edu", size=19, bold=True, color=WHITE)),
], kind="reverse", notes="[0:48] Questions. All the links are on the slide.")

# ═════════════════════════════════════════════════════════════════════════════════════
# BACKUP
# ═════════════════════════════════════════════════════════════════════════════════════
section("Backup", "Backup slides for questions.")

def src(a):
    r = a["repo"].replace("https://", "").replace(".git", "")
    if a["chart"]:
        return f"Helm chart: {a['chart']}"
    if r.startswith("gitlab.nrp-nautilus.io/"):
        return "NRP GitLab: " + r.split("/", 1)[1]
    if r.startswith("github.com/"):
        return "GitHub: " + r.split("/", 1)[1]
    return r


def pol(a):
    return ("auto, self-heal" if a["self_heal"] else "auto") if a["auto"] else "manual"


rows_a = sorted(APPS, key=lambda a: a["name"])
half = (len(rows_a) + 1) // 2
t1 = [["Application", "Source", "Sync"]] + [[a["name"], src(a), pol(a)] for a in rows_a[:half]]
t2 = [["Application", "Source", "Sync"]] + [[a["name"], src(a), pol(a)] for a in rows_a[half:]]
add("What Argo CD Runs", [
    Table(X0, TOP, 5.98, 4.7, t1, [2.15, 2.85, 1.1], size=11, row_h=0.42, mono=(0,), cls="rows"),
    Table(6.75, TOP, 5.98, 4.7, t2, [2.15, 2.85, 1.1], size=11, row_h=0.42, mono=(0,), cls="rows"),
    Text(X0, 6.42, W, 0.3, T(f"Argo CD applications on the cluster, {SNAP}; Argo's own example app left out.",
                             size=12, color=MUTED)),
], notes="""
[0:14] For the curious, the actual list. Security tooling, Falco and Wazuh and a CVE mitigation repo; Grafana; NetBox and its agent; Kueue; the onboarding site; Open WebUI; GitLab. Most sync automatically with self-heal; a few are manual on purpose.
""")


gw = [Box(X0, TOP + 0.1, 2.5, 0.75, "EnvoyProxy", "proxy deployment settings", state="white", head_size=14, sub_size=11),
      Box(3.55, TOP + 0.1, 2.5, 0.75, "GatewayClass", "envoy-ai-gateway-nrp", state="white", head_size=14,
          sub_size=11, mono_sub=True),
      Box(6.5, TOP + 0.1, 2.5, 0.75, "Gateway", "envoy-ai-gateway-nrp", state="active", head_size=14, sub_size=11,
          mono_sub=True),
      Arrow(3.1, TOP + 0.47, 3.55, TOP + 0.47), Arrow(6.05, TOP + 0.47, 6.5, TOP + 0.47),
      Box(6.5, TOP + 1.35, 2.5, 0.75, "AIGatewayRoute", "match x-ai-eg-model", head_size=14, sub_size=11),
      Arrow(7.75, TOP + 0.85, 7.75, TOP + 1.35),
      Box(3.55, TOP + 2.65, 2.5, 0.85, "InferencePool", "+ endpoint picker (EPP)", head_size=14, sub_size=11),
      Box(9.45, TOP + 2.65, 3.28, 0.85, "AIServiceBackend → Backend", "one endpoint, schema OpenAI", head_size=14,
          sub_size=11),
      Arrow(7.2, TOP + 2.1, 4.8, TOP + 2.65), Arrow(8.3, TOP + 2.1, 11.09, TOP + 2.65),
      Box(3.55, TOP + 3.95, 2.5, 0.75, "vLLM pods", "selected by label", state="white", head_size=14, sub_size=11),
      Arrow(4.8, TOP + 3.5, 4.8, TOP + 3.95),
      Box(9.45, TOP + 3.95, 3.28, 0.75, "BackendSecurityPolicy", "API key to the backend", state="white", head_size=14,
          sub_size=11),
      Arrow(11.09, TOP + 3.95, 11.09, TOP + 3.5, dashed=True),
      Box(9.45, TOP + 0.1, 3.28, 0.75, "SecurityPolicy", "ext auth: llm-auth (gRPC)", state="white", head_size=14,
          sub_size=11),
      Box(9.45, TOP + 1.35, 3.28, 0.75, "BackendTrafficPolicy", "rate limit, retries, health", state="white",
          head_size=14, sub_size=11),
      Arrow(9.45, TOP + 0.47, 9.0, TOP + 0.47, dashed=True), Arrow(9.45, TOP + 1.72, 9.0, TOP + 1.72, dashed=True),
      Text(X0, TOP + 1.3, 2.9, 2.5, [T(f"{len(S['llm_routes'])} route rules", size=16, bold=True, color=NAVY),
                                     T(f"{len(S['inference_pools'])} InferencePools", size=16, bold=True, color=NAVY,
                                       before=6),
                                     T("Up to 16 rules per AIGatewayRoute, so routes are split across objects",
                                       size=14, before=10)]),
      Text(X0, 6.2, W, 0.4, T("From the NRP admin guide, Managing AI Models; object names from the cluster.", size=12,
                              color=MUTED))]
add("Envoy AI Gateway Objects", gw, notes="Backup: how the gateway objects fit together.")

add("Using GPUs Fairly", [
    Text(X0, TOP + 0.1, 5.9, 0.45, T("Do", size=21, bold=True, color=NAVY)),
    Bullets(X0, TOP + 0.6, 5.9, 4.6, ["Run batch work as a **Job** that exits",
                                      "Request what you'll use; keep limits within 20% of requests",
                                      "Keep data on a persistent volume or in S3", "Run a sweep as many one-GPU jobs",
                                      "Borrow idle A100/H100s with `priorityClassName: opportunistic`, and checkpoint"],
            size=18),
    Text(6.83, TOP + 0.1, 5.9, 0.45, T("Don't", size=21, bold=True, color=NAVY)),
    Bullets(6.83, TOP + 0.6, 5.9, 4.6, ["Leave a notebook holding a GPU overnight",
                                        "Put `sleep` in a Job to keep a GPU (bannable)",
                                        "Ask for 4 GPUs \"just in case\": use must stay above 40%",
                                        "Keep results on the pod's own disk; it vanishes with the pod"], size=18),
    Link(X0, 6.3, 9.0, 0.3, "https://nrp.ai/documentation/userdocs/start/policies/", size=14),
], notes="Backup: the cluster policy, short version.")


# ═════════════════════════════════════════════════════════════════════════════════════
# TIMING: the "[h:mm]" that starts each speaker note, computed from these durations (seconds),
# so reordering or cutting slides keeps the times right. Backup slides get none.
# ═════════════════════════════════════════════════════════════════════════════════════
SECONDS = {"Inside the National Research Platform": 60, "Agenda": 45, "What is NRP?": 90, "From PRP to NRP": 50,
           "NRP in Numbers": 40, "The Network Underneath": 75, "Policy Lives in the Cluster": 60,
           "One Cluster, Many Sites": 45, "Storage": 50, "More Than GPUs": 50, "Getting Traffic In": 60,
           "Git Is the Source of Truth": 70, "CI in a VM per Job": 60, "Build and Deploy Your Own": 40,
           "NetBox Knows Every Node": 75, "The Agent, Up Close": 40, "Watching the Cluster": 50,
           "Measuring the Network": 60, "Security": 60, "Routine Care": 30, "Sharing GPUs Fairly": 60,
           "How a Node Joins": 60, "The LLM Service": 50, "Where the Models Run": 40, "A Request, Step by Step": 100,
           "Gateway Policies": 60, "Ask for a Task, Not a Model": 50, "Serving with vLLM": 60,
           "Borrowing Idle GPUs": 50, "One Model, Two Nodes": 45, "Around the Models": 30,
           "An LLM on Call: nrp-ops-bot": 75, "Ways In": 40, "Getting Access": 45, "Ways to Run Work": 70,
           "A GPU Job": 40, "Where to Start": 50, "Live Demo": 720, "Acknowledgments": 20}


def retime(slides, default=55, section=10):
    import re
    t, backup = 0, False
    for sd in slides:
        backup = backup or sd.title == "Backup"
        tag = re.compile(r"^\[\d+:\d\d\]\s*")
        if backup:
            sd.notes = tag.sub("", sd.notes)
            continue
        if sd.notes:
            sd.notes = f"[{t // 3600}:{t // 60 % 60:02d}] " + tag.sub("", sd.notes)
        t += SECONDS.get(sd.title, section if sd.kind == "section" else default)
    return t


TOTAL = retime(SLIDES)
