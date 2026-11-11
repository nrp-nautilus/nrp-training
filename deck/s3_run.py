"""'How We Run It': deploying services, GitOps, CI, NetBox, monitoring, perfSONAR, security, sharing, joining.

Part of the SCinet deck: slides.py imports the section files in order. Shared constants and
helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
Live data for the monitoring and perfSONAR slides comes from data/metrics.json (metrics.py).
"""
import time

from common import *  # noqa: F401,F403

_MF = HERE / "data" / "metrics.json"
METRICS = json.loads(_MF.read_text()) if _MF.exists() else {}

# From the cluster on 11 Nov 2026 (kubectl get nodes / pods): reservation taints and opportunistic pods
RESV_NODES, RESV_GROUPS = 119, 23
OPP_PODS, OPP_OSG = 232, 208

# ═════════════════════════════════════════════════════════════════════════════════════
# HOW WE RUN IT
# ═════════════════════════════════════════════════════════════════════════════════════
section("How We Run It", "Now the operations side: how a small team runs this.")

# ── How services get deployed: the overview the next three slides zoom into ──────────────────────
LANE_Y = [TOP + 0.55 + i * 1.3 for i in range(3)]
LH = 1.05
DEPLOY = [("Argo CD", "pulls from git, keeps syncing, puts back drift",
           "**Admins:** platform services, such as Falco, NetBox, Grafana and GitLab itself"),
          ("GitLab CI/CD", "a pipeline builds, tests and deploys through GitLab's Kubernetes integration",
           "**Admins and users:** the most common path: build an image, roll it out to a namespace"),
          ("By hand", "`kubectl apply` or `helm upgrade` from a repo",
           "**Admins:** some services, like the LLM servers. **Users:** most work in their own namespace")]
dp = [Box(X0, LANE_Y[0], 1.95, LANE_Y[2] + LH - LANE_Y[0], "GitLab", "repos: manifests, Helm values, code",
          head_size=18, sub_size=13),
      Box(7.0, LANE_Y[0], 1.85, LANE_Y[2] + LH - LANE_Y[0], "The cluster", "objects in a namespace", state="active",
          head_size=18, sub_size=13),
      Text(9.15, TOP + 0.05, 3.58, 0.4, T("Who uses it, and for what", size=15, bold=True, color=NAVY)),
      Text(3.05, TOP + 0.05, 3.4, 0.4, T("Three ways in", size=15, bold=True, color=NAVY, align="c"))]
for i, (h, b, who) in enumerate(DEPLOY):
    y = LANE_Y[i]
    yc = y + LH / 2
    dp += [Arrow(2.55, yc, 3.05, yc, hl=[i + 1]),
           Box(3.05, y, 3.4, LH, h, b, state="white", head_size=17, sub_size=12.5, hl=[i + 1]),
           Arrow(6.45, yc, 7.0, yc, hl=[i + 1]),
           Text(9.15, y, 3.58, LH, T(who, size=14.5), anchor="m", cls=f"who w{i}")]
    f = flow([[(2.0, yc), (7.6, yc)]], n=4, dur=2.0, r=9, only=[i + 1])
    f.style = "pointer-events:none;z-index:0;"     # under the boxes: the dots pass through them
    dp.insert(0, f)
dp.append(Text(X0, TOP + 4.5, W, 0.5, T("Next: Argo CD up close, then CI. Whichever way it comes, a service ends up as "
                                        "Kubernetes objects in a namespace.", size=16, color=MUTED)))
dp.append(Raw(0, 0, 0.1, 0.1, "<style>" + "".join(
    f'.deploy[data-cur="{k}"] .who:not(.w{k - 1}) {{ opacity:.35; }}\n' for k in (1, 2, 3))
    + ".deploy .who { transition: opacity .4s; }</style>", pptx=False))
add("How Services Get Deployed", dp, steps=3, cls="deploy", builds=True, secs=55, notes=f"""
Before the tools, the big picture: how anything gets onto the cluster. Everything starts in a repo on our GitLab, and there are three ways from there to the cluster.

[click] Argo CD. It pulls from git and keeps the cluster matching it. That's how we run the platform services: Falco, NetBox, Grafana, GitLab itself.

[click] GitLab CI/CD. A pipeline builds and tests an image, then deploys it through GitLab's Kubernetes integration. This is probably the most-used path, by us and by users.

[click] And by hand: kubectl apply or helm upgrade from a repo. Some of our services still work this way, the LLM servers among them, and it's how most users work in their own namespaces.

Whichever path, the result is the same: Kubernetes objects in a namespace. The next slides zoom into Argo CD and then into CI.
""")

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
          "Argo CD is one of the three ways in: other services deploy from GitLab CI, or by hand from their repos"],
          size=17, gap=8)]
add("Git Is the Source of Truth", go, steps=3, cls="gitops", builds=True, secs=60, notes=f"""
The first way in, up close: Argo CD, and the principle behind it, git is the source of truth. [click] An admin pushes a change to our self-hosted GitLab; Argo CD sees the repo change, compares it with what's running, and syncs the cluster. Argo manages {len(S['argo_apps'])} applications today, including GitLab itself.

[click] Now somebody runs kubectl edit at two in the morning. That's drift. [click] With self-heal on, Argo puts back what git says. You get review, history and rollback for free. (The full list of what Argo runs is in the backup slides.)

Argo isn't the only way in, as the last slide showed: plenty of services deploy from GitLab CI, and some are applied by hand from their repos.
""")


RUNNER = '''[[runners]]
  [runners.kubernetes]
    namespace = "gitlab-ci-kata"
    runtime_class_name = "kata"
    privileged = false
    image = "alpine:3.22"
    pull_policy = ["always"]
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
ci += [Code(6.83, TOP + 0.2, 5.9, 3.8, RUNNER, size=12.5, title="The default runner's config (from the cluster)"),
       Bullets(X0, TOP + 4.25, W, 1.2, [
           "The shared runners start each CI job as a pod in its own lightweight VM: even a privileged build can't "
           "reach the node",
           f"{len(S['gitlab_runners'])} runner flavors (backup slide); images go to **gitlab-registry.nrp-nautilus.io** "
           "and are pulled from inside the cluster"], size=17, gap=6)]
add("CI in a VM per Job", ci, steps=1, cls="kata", secs=60, notes="""
The second way in, the CI/CD path, from the inside. CI is where shared clusters get nervous, because people want to run Docker builds, and a privileged container on a shared node is a problem. Our answer: the shared GitLab runners use the Kubernetes executor, and each job starts as a pod with the Kata runtime class, the VM-per-pod runtime from the hardware slide. [click] So each CI job gets its own lightweight VM. Docker builds go to a separate runner that is privileged with Docker-in-Docker, but still inside its own Kata VM, so "privileged" stops at the VM's edge, not the node.

On the right is the default runner's actual config: the namespace, the Kata runtime class, the default image, and limits users can raise up to 12 CPUs and 50 gigs. The pull policy is "always", so one project's job can't start another project's private image from a node's cache. Images go to our registry and get pulled from inside the cluster, which is much faster than Docker Hub. The four runner flavors are in the backup slides.
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
        "Deploy to your namespace through GitLab's Kubernetes integration: the CI/CD path from before",
        "Build multi-arch images for the ARM64 nodes"], size=17, gap=8, cls="stagger"),
    Link(X0, 6.3, 9.0, 0.3, "https://nrp.ai/documentation/userdocs/development/gitlab/", size=13),
], optional=True, secs=40, notes="""
And the same CI/CD path from the user side. Anyone with an NRP login can use the GitLab. This is the pipeline from our docs: Kaniko builds the image without a Docker daemon and pushes it to the project's registry, tagged with the commit. Then GitLab's Kubernetes integration deploys it into your namespace, so you can run your own services the same way we run ours.
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
NetBox. Your colleague mentioned you use it too. Ours is NetBox 4, deployed by Argo from the NetBox Labs chart. The interesting part is how it stays true. Every node runs netbox-agent as a privileged pod on the host network; that's {S['netbox_agents']} pods.

[click] The agent runs lldpd, so it hears the switch's LLDP announcements and learns which switch and port each NIC is plugged into.

[click] Then it writes what it found into NetBox: the device and its site, the interfaces with MACs and IPs, the cable to the switch port, and the inventory: CPUs, memory, disks and GPUs. It does this once a day with up to an hour of random delay, so five hundred nodes never hit NetBox at the same moment. The site comes from a node label, so the cluster and NetBox agree on where a node is. (The agent's config and its run loop are in the backup slides.)
""")

# ── Monitoring: data flows from the sources through Prometheus and Thanos into Grafana panels ─────────
SRC_X, SRC_W, SRC_H = X0, 2.4, 0.8
SRC_Y = [TOP + 0.5 + i * 0.95 for i in range(4)]
PROM = (3.45, TOP + 1.35, 1.95, 1.4)
THAN = (5.85, TOP + 1.35, 2.05, 1.4)
DASH = (8.45, TOP, 4.28, 3.55)
PIPE_Y = PROM[1] + PROM[3] / 2
PANELS = [("cpu", "CPU use", "#73BF69"), ("mem", "Memory use", "#F2CC0C"), ("gpu", "GPU utilization", "#5794F2")]


def _series():
    """{key: [values]} hourly over seven days, from metrics.json; flat illustrative curves without it."""
    th = METRICS.get("thanos") or {}
    if all(th.get(k) for k, _, _ in PANELS):
        return {k: [v for _, v in th[k]] for k, _, _ in PANELS}, True
    base = {"cpu": 40, "mem": 55, "gpu": 50}
    return {k: [base[k] + 6 * math.sin(i / 24 * 2 * math.pi) for i in range(168)] for k, _, _ in PANELS}, False


SERIES, REAL = _series()
if REAL:
    _t0, _t1 = (time.gmtime(METRICS["thanos"][k]) for k in ("start", "end"))
    DASH_NOTE = (f"From Thanos, hourly, {_t0.tm_mday}–{_t1.tm_mday} {time.strftime('%b %Y', _t1)}: CPU and memory "
                 "averaged over nodes, GPU over GPUs")
else:
    DASH_NOTE = "Illustrative curves (run deck/metrics.py for the cluster's own)"


def panels_html():
    w, h = DASH[2] * PX, DASH[3] * PX
    ph, gap, top = 132, 12, 62
    cw, ch = w - 2 * 14 - 2 * 12, ph - 46
    out = (f'<style>.gdash {{ position:absolute; inset:0; background:#181B1F; border-radius:10px; padding:12px 14px; '
           f'font-family:var(--f-body); }} .gdash .gh {{ color:#CCCCDC; font:600 22px var(--f-body); }} '
           f'.gdash .gh span {{ color:#8E8E9E; font-weight:400; font-size:19px; margin-left:10px; }} '
           f'.gdash .gp {{ position:absolute; left:14px; right:14px; height:{ph}px; background:#22252B; '
           f'border:1px solid #2F333B; border-radius:6px; padding:8px 12px; }} '
           f'.gdash .gt {{ color:#CCCCDC; font-size:19px; font-weight:600; }} '
           f'.gdash .gv {{ position:absolute; right:12px; top:4px; font:600 26px var(--f-body); }} '
           f'.gdash svg {{ position:absolute; left:12px; bottom:8px; overflow:visible; }} '
           f'.gdash .ln {{ fill:none; stroke-width:2.5; stroke-dasharray:1; stroke-dashoffset:1; }} '
           f'.gdash .ar {{ opacity:0; }} .gdash .grid line {{ stroke:#2F333B; stroke-width:1; }} '
           f'.monitor[data-cur="2"] .gdash .ln {{ stroke-dashoffset:0; transition:stroke-dashoffset 2.6s linear .5s; }} '
           f'.monitor[data-cur="2"] .gdash .ar {{ opacity:.18; transition:opacity .8s ease 3s; }} '
           f'.monitor .gdash .gv {{ opacity:0; }} .monitor[data-cur="2"] .gdash .gv {{ opacity:1; '
           f'transition:opacity .4s ease 3s; }}</style>'
           f'<div class="gdash"><div class="gh">Grafana<span>cluster overview · last 7 days</span></div>')
    for i, (k, name, col) in enumerate(PANELS):
        vals = SERIES[k]
        n = len(vals)
        pts = [(j / (n - 1) * cw, ch - max(0, min(100, v)) / 100 * ch) for j, v in enumerate(vals)]
        line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        area = f"0,{ch} " + line + f" {cw:.1f},{ch}"
        grid = "".join(f'<line x1="0" x2="{cw:.0f}" y1="{ch * f:.0f}" y2="{ch * f:.0f}"/>' for f in (0, .5, 1))
        out += (f'<div class="gp" style="top:{top + i * (ph + gap)}px"><div class="gt">{name}</div>'
                f'<div class="gv" style="color:{col}">{vals[-1]:.0f}%</div>'
                f'<svg width="{cw:.0f}" height="{ch:.0f}" viewBox="0 0 {cw:.0f} {ch:.0f}"><g class="grid">{grid}</g>'
                f'<polygon class="ar" points="{area}" fill="{col}"/>'
                f'<polyline class="ln" pathLength="1" points="{line}" stroke="{col}"/></svg></div>')
    return out + "</div>"


def panels_png():
    out = FIG / "grafana_panels.png"
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(DASH[2], DASH[3]), dpi=200, facecolor="#181B1F")
    fig.text(0.04, 0.95, "Grafana", color="#CCCCDC", fontsize=11, fontweight="bold", va="top", family="DejaVu Sans")
    fig.text(0.24, 0.95, "cluster overview · last 7 days", color="#8E8E9E", fontsize=9, va="top", family="DejaVu Sans")
    for i, (k, name, col) in enumerate(PANELS):
        ax = fig.add_axes([0.05, 0.62 - i * 0.29, 0.9, 0.2], facecolor="#22252B")
        v = SERIES[k]
        ax.plot(range(len(v)), v, color=col, lw=1.4)
        ax.fill_between(range(len(v)), v, color=col, alpha=0.18)
        ax.set_ylim(0, 100); ax.set_xlim(0, len(v) - 1)
        ax.set_xticks([]); ax.set_yticks([0, 50, 100]); ax.tick_params(colors="#8E8E9E", labelsize=6, length=0)
        ax.grid(axis="y", color="#2F333B", lw=0.6)
        for sp in ax.spines.values():
            sp.set_color("#2F333B")
        fig.text(0.05, 0.62 - i * 0.29 + 0.215, name, color="#CCCCDC", fontsize=8.5, fontweight="bold",
                 family="DejaVu Sans")
        fig.text(0.95, 0.62 - i * 0.29 + 0.215, f"{v[-1]:.0f}%", color=col, fontsize=10, fontweight="bold", ha="right",
                 family="DejaVu Sans")
    fig.savefig(out, facecolor="#181B1F")
    plt.close(fig)
    return out


mon = [Text(SRC_X, TOP + 0.0, SRC_W, 0.4, T("Sources", size=17, bold=True, color=NAVY))]
srcs = [("node-exporter", f"on all {S['node_exporter']} nodes"), ("kube-state-metrics", "objects and their state"),
        ("DCGM", "GPU use, memory, power"), ("Apps", "Ceph, the ingress, every service")]
for i, (h, b) in enumerate(srcs):
    mon.append(Box(SRC_X, SRC_Y[i], SRC_W, SRC_H, h, b, head_size=14.5, sub_size=11.5, state="white"))
    mon.append(Arrow(SRC_X + SRC_W, SRC_Y[i] + SRC_H / 2, PROM[0], PIPE_Y, step=1, color="C9D4E3"))
mon += [Box(*PROM, "Prometheus", "2 replicas, run by the Prometheus operator", head_size=16, sub_size=12, step=1,
            hl=[1]),
        Box(*THAN, "Thanos", f"querier ({S['thanos_querier']} replicas), store, compactor", head_size=16, sub_size=12,
            step=1, hl=[1]),
        Arrow(PROM[0] + PROM[2], PIPE_Y, THAN[0], PIPE_Y, step=1, hl=[1]),
        Arrow(THAN[0] + THAN[2], PIPE_Y, DASH[0], PIPE_Y, step=2, hl=[2]),
        flow([[(SRC_X + SRC_W, SRC_Y[i] + SRC_H / 2), (PROM[0], PIPE_Y)] for i in range(4)]
             + [[(PROM[0] + PROM[2], PIPE_Y), (THAN[0], PIPE_Y)]], n=2, dur=1.4, r=7, only=[1, 2]),
        flow([[(THAN[0] + THAN[2], PIPE_Y), (DASH[0] + 0.1, PIPE_Y)]], n=2, dur=1.0, r=7, only=[2]),
        Raw(*DASH, panels_html(), step=2, draw=lambda s, k: s.image(panels_png(), *DASH)),
        Box(DASH[0], TOP + 3.75, 2.06, 0.75, "Alertmanager", "3 replicas; routes alerts", head_size=14, sub_size=11,
            state="white", step=2),
        Box(DASH[0] + 2.22, TOP + 3.75, 2.06, 0.75, "Public dashboards", "nrp.ai/viz", head_size=14, sub_size=11,
            state="white", step=2),
        Text(DASH[0], TOP + 4.6, DASH[2], 0.3, T(DASH_NOTE, size=11, color=MUTED), step=2),
        Text(X0, TOP + 4.75, 7.6, 0.5, T("Logs: Elastic collects syslog from every node, SSH logins included.", size=16,
                                         color=BODY))]
add("Watching the Cluster", mon, steps=2, cls="monitor", secs=60, notes=f"""
Monitoring is standard Prometheus, at scale. The sources: node-exporter on all {S['node_exporter']} nodes, kube-state-metrics for the Kubernetes objects, DCGM for the GPUs, and the apps themselves: Ceph, the ingress, and the model servers you'll see later.

[click] Prometheus, run by the operator, scrapes them, and Thanos sits in front of it: {S['thanos_querier']} querier replicas, plus store and compactor for long-term history.

[click] On top: Grafana. These three panels are real, the last week straight from Thanos: CPU and memory use averaged over the nodes, and GPU utilization averaged over the GPUs. The CPUs are mostly idle; the GPUs are the busy part. Alertmanager routes the alerts, and the public dashboards on nrp.ai/viz read from the same place. Logs go to Elastic, including every SSH login, which matters for security.
""")

# ── perfSONAR: the all-to-all mesh, then the real MaDDash loss grid ────────────────────────────────
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
    # step 2 must visibly show every pair: the shared CSS keeps the full mesh almost invisible
    style = ('<style>.perfsonar[data-cur="2"] .mesh path.all { opacity:.22; stroke-width:.55; } '
             '.perfsonar[data-cur="2"] .mesh .spokes line { opacity:.5; }</style>')
    return (f'{style}<svg class="mesh" viewBox="0 0 {size} {size}" width="{size}" height="{size}"><path class="all" '
            f'd="{allp}"/><g class="spokes">{spokes}</g><g class="dots">{dots}</g><g class="labs">{labs}</g></svg>')


MD = METRICS.get("maddash")
MD_COLORS = {0: "#4CAF50", 1: "#F2C230", 2: "#D9352B", 3: "#C9CDD3", None: "#FFFFFF"}


def grid_png():
    """The MaDDash all-to-all loss grid as an image: one cell per (source, destination) pair."""
    out = FIG / "maddash_loss.png"
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    rows = MD["rows"]
    n = len(rows)
    z = [[(c if c is not None else 4) for c in r] for r in MD["grid"]]
    cmap = ListedColormap([MD_COLORS[0], MD_COLORS[1], MD_COLORS[2], MD_COLORS[3], "#FFFFFF"])
    fig = plt.figure(figsize=(5.6, 5.3), dpi=220)
    ax = fig.add_axes([0.2, 0.03, 0.78, 0.82])
    ax.imshow(z, cmap=cmap, vmin=-0.5, vmax=4.5, interpolation="nearest", aspect="auto")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("#B9C7D8")
    # region blocks: rows are named "<region> <zone>"
    reg = [r.split(" ")[0] for r in rows]
    starts = [i for i in range(n) if i == 0 or reg[i] != reg[i - 1]]
    for s0 in starts[1:]:
        ax.axhline(s0 - 0.5, color="white", lw=1.2); ax.axvline(s0 - 0.5, color="white", lw=1.2)
    for a, b in zip(starts, starts[1:] + [n]):
        if b - a >= 3:
            ax.text(-1.5, (a + b - 1) / 2, reg[a], ha="right", va="center", fontsize=7.5, color="#182B49",
                    family="DejaVu Sans", fontweight="bold")
    fig.text(0.59, 0.95, "destination →", ha="center", fontsize=8, color="#5C6778", family="DejaVu Sans")
    fig.text(0.02, 0.88, "source ↓", fontsize=8, color="#5C6778", family="DejaVu Sans")
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    return out


ps = [Bullets(X0, TOP + 0.15, 6.1, 5.3, [
    (f"Two **perfSONAR testpoints** on every node ({S['perfsonar_testpoints']} each): one on the host network, "
     "one in the pod network", 0, 0),
    ("A **mesh config** says who tests whom; each testpoint's **pScheduler** runs its share", 0, 0),
    (f"**All-to-all** between one node per site ({NZ} sites): one-way latency and loss nonstop, throughput every "
     "18 h, traceroute every 6 h", 0, 1),
    ("Results go to an **archive**; **MaDDash** draws them as a grid at perfsonar.nrp-nautilus.io", 0, 3),
    ("Host network vs pod network: is a slow path the network, or the overlay?", 0, 3)], size=17, gap=9),
    Raw(7.05, TOP - 0.05, 5.6, 5.6, mesh_html(800), only=[0, 1, 2],
        draw=lambda s, k: s.image(mesh_png(), 7.05, TOP - 0.05, 5.6, 5.4))]
caps = {1: "Orange: one site's tests to every other site",
        2: f"Every site tests every other: {NZ} × {NZ - 1} directed pairs"}
if MD:
    upd = time.gmtime(MD["updated"])
    ps.append(Image(7.05, TOP - 0.05, 5.6, 5.0, grid_png(), only=[3]))
    caps[3] = (f"MaDDash packet-loss grid, {upd.tm_mday} {time.strftime('%b %Y', upd)}: green ≤ 0.001%, yellow "
               "more, red ≥ 0.1%, gray no data yet")
for k, t in caps.items():
    ps.append(Text(7.05, TOP + (4.98 if k == 3 else 5.25), 5.6, 0.5, T(t, size=12, color=MUTED, align="c"), only=[k]))
add("Measuring the Network", ps, steps=3 if MD else 2, cls="perfsonar", builds=True, secs=75, notes=f"""
And the network gets measured, which I suspect is the slide you'll have opinions about. perfSONAR is the R&E community's measurement toolkit. Every node runs two perfSONAR testpoints from DaemonSets, {S['perfsonar_testpoints']} of each: one on the host's own network, and one inside the pod network. A testpoint is the small perfSONAR install: its pScheduler runs tests with other testpoints. What to test comes from a mesh config, a JSON file served from the cluster that lists the members and the tests; each testpoint reads it and schedules its share.

[click] Our all-to-all mesh takes one node per site, {NZ} sites, picked by a node label. Each one measures one-way latency and packet loss to every other all the time, throughput every 18 hours, and traceroute every 6 hours. Here's one site's share.

[click] And here's every pair: {NZ} times {NZ - 1} tests, in both directions.

[click] The results go to an archive, and MaDDash turns them into this grid: source down the side, destination across the top, one square per pair. This is today's real packet-loss grid: green is clean, yellow and red are loss, gray is no data yet. A red column means one site sees loss from everybody, so the problem is near that site; a red row, near the sender. Because there's a testpoint on the host network and one in the pod network, we can tell whether a slow path is the network itself or our overlay. It's how we answer "the cluster is slow" with "it's this path".
""")

sec_cols = [("Identity", ["Authentik", "CILogon: federated campus login", "Groups drive namespace access"],
             "e.g. a new login sees no namespaces until a namespace admin adds it"),
            ("Detect", ["Falco: runtime alerts", "Falco Talon: automated response",
                        "Wazuh; Elastic syslog, SSH logins included"],
             "e.g. a pod runs a crypto miner or calls a mining pool: Falco alerts, Talon kills the pod"),
            ("Prevent", ["Gatekeeper admission policies", "Kata VMs for CI and untrusted builds",
                         "Central Calico policy", "CVE mitigations rolled out by Argo CD"],
             "e.g. a pod that asks to be privileged, or sets CUDA_VISIBLE_DEVICES to reach GPUs it wasn't given, "
             "is rejected"),
            ("Audit", ["IPMI scanner: alerts if a BMC is reachable from outside",
                       "JupyterHub scanner: no anonymous hubs"],
             "e.g. a node's BMC answers from the internet: operators get an alert")]
se = []
for i, (h, items, ex) in enumerate(sec_cols):
    x = X0 + i * 3.07
    se += [Frame(x, TOP + 0.15, 2.9, 4.95, fill=CARD, line=None, radius=0.05, cls="rise",
                 style=f"transition-delay:{i * 0.2:.1f}s"),
           Text(x + 0.2, TOP + 0.3, 2.5, 0.5, T(h, size=21, bold=True, color=NAVY), cls="rise",
                style=f"transition-delay:{i * 0.2:.1f}s"),
           Bullets(x + 0.2, TOP + 0.9, 2.55, 2.5, items, size=16, gap=8, cls="rise",
                   style=f"transition-delay:{i * 0.2 + 0.1:.1f}s"),
           Frame(x + 0.12, TOP + 3.45, 2.66, 1.53, fill="FFF4CC", line="E9B55C", radius=0.06, step=1,
                 style=f"transition-delay:{i * 0.15:.2f}s"),
           Text(x + 0.25, TOP + 3.5, 2.42, 1.45, T(ex, size=14, color=NAVY), anchor="m", step=1,
                style=f"transition-delay:{i * 0.15:.2f}s")]
add("Security", se, steps=1, secs=70, notes="""
Security, in four parts. Identity: Authentik, with CILogon for federated campus logins, and groups drive who can use which namespace. Detection: Falco watches what runs; Falco Talon can respond automatically; plus Wazuh, and Elastic with every SSH login. Prevention: Gatekeeper admission policies, Kata VMs for CI, the central Calico policy, and CVE mitigations rolled out through Argo. And audits: a scanner that alerts if anyone's IPMI is reachable from outside, and one that checks every JupyterHub on the cluster requires an institutional login.

[click] What each one catches, as examples. Identity: logging in gets you nothing until a namespace admin adds you. Detection: our Falco rules look for crypto-miner binaries and connections to mining pools and proxies, and Talon terminates that pod. Prevention: Gatekeeper rejects a privileged pod in a user namespace, or one that sets CUDA_VISIBLE_DEVICES to reach GPUs the scheduler didn't give it. Audit: a BMC that answers from the internet raises an alert.
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
The routine care that keeps five hundred nodes current: kured reboots nodes a few at a time after kernel updates; self-node-remediation recovers nodes that stop responding; a monitor watches the labels the scheduler depends on. And there's a written runbook for every upgrade, Kubernetes, Calico, Rook, GitLab, in the admin docs.
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
add("Sharing GPUs Fairly", fs, steps=2, cls="fairshare", builds=True, secs=70, notes=f"""
How sharing works, because it's the economic model. Two kinds of nodes. A contributor can ask for their nodes to be reserved: we put a reservation taint on them, and only pods that tolerate that taint, which are the owner's, can land there. Here a pod from another lab tries an idle GPU on a reserved node and is turned away. Today {RESV_NODES} nodes carry a reservation, for {RESV_GROUPS} groups.

[click] Everything else is shared. On a shared node, idle GPUs go to opportunistic work: that's a priority class, the lowest one. Most of it is Open Science Grid glideins running jobs for experiments like IceCube and LIGO: {OPP_PODS} opportunistic pods right now, {OPP_OSG} of them from OSG.

[click] When anyone with a normal job needs that GPU, the scheduler preempts the opportunistic pod. So opportunistic work has to tolerate that: it checkpoints, or it just starts again somewhere else.
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
jn += [Text(X0, TOP + 2.05, 5.9, 0.4, T("Host site", size=19, bold=True, color=NAVY)),
       Bullets(X0, TOP + 2.5, 5.9, 2.2, ["Keeps an on-site contact for hands-on work",
                                         "Sends maintenance notices; forwards warranty tickets"], size=17, gap=6),
       Text(6.83, TOP + 2.05, 5.9, 0.4, T("NRP", size=19, bold=True, color=NAVY)),
       Bullets(6.83, TOP + 2.5, 5.9, 2.2, ["Patching, packages and host hardening",
                                           "24/7 monitoring and alerting; incident handling from the OS up"],
               size=17, gap=6),
       Text(X0, TOP + 4.0, W, 0.9, T("Then it's schedulable: shared with everyone, or reserved for your group if you "
                                     "ask, with a taint only your pods tolerate.", size=22, bold=True, color=BLUE),
            step=4),
       Link(X0, TOP + 4.85, W, 0.3, "https://nrp.ai/documentation/admindocs/participating/new-contributor-guide/",
            size=13)]
add("How a Node Joins", jn, steps=4, notes="""
You've now seen all the pieces, so here's what happens when a campus contributes a node; this is also how your institution would join. The host site racks and cables it into the Science DMZ, with jumbo frames. [click] It gives us access, IPMI or root SSH from our management address. [click] We install Ubuntu, the drivers and storage, and join it to the cluster. [click] It gets its topology labels and falls under the central Calico policy. [click] And it reports in: the NetBox agent records it and its switch port, node-exporter feeds Prometheus, and its perfSONAR testpoints join the mesh.

The split of work: the host site keeps someone who can touch the box; we do everything from the OS up. And then it's schedulable, exactly the sharing model from the previous slide: shared with everyone, or, if the owner asks, reserved with a taint that only their pods tolerate.
""")
