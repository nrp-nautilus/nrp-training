"""'How It's Built': the network, policy, regions and storage, hardware, ingress.

Part of the SCinet deck: slides.py imports the section files in order. Shared constants and
helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
"""
from common import *  # noqa: F401,F403

# ═════════════════════════════════════════════════════════════════════════════════════
# HOW IT'S BUILT
# ═════════════════════════════════════════════════════════════════════════════════════
section("How It's Built", "[0:06] How it's built, starting with the part you care about: the network.")

# ── The Network Underneath: the pods see one hop on the overlay; the packet really rides the R&E networks ──
net = [Bullets(X0, TOP + 0.15, 5.25, 5.2, [
    "Nodes sit in campus **Science DMZs**, outside campus firewalls, at 10–100 Gb/s",
    "**Jumbo frames:** MTU 9000 between all nodes",
    "Regional networks and Internet2 carry the traffic",
    f"**Calico** builds the pod network: a **VXLAN** overlay, IPv4 and IPv6 ({S['calico_ipv6_nodes']} nodes "
    "dual-stack)",
    ("Pod to pod, the packet is wrapped in UDP between the two nodes' addresses and crosses the real network", 0, 2)],
    size=18)]
cx = [6.15, 8.37, 10.59]
for i, c in enumerate(["Campus A", "Campus B", "Campus C"]):
    x = cx[i]
    net += [Frame(x, TOP + 0.1, 2.08, 2.75, label=c, line="C9D4E3", label_size=13),
            Box(x + 0.15, TOP + 0.55, 1.78, 0.72, "Campus LAN", "firewall, IDS", state="dim", head_size=13,
                sub_size=11),
            Box(x + 0.15, TOP + 1.85, 1.78, 0.82, "NRP node", "Science DMZ", state="orange", head_size=14,
                sub_size=11.5),
            Arrow(x + 1.04, TOP + 2.67, x + 1.04, TOP + 3.45, head=False, width=2.5, color=NAVY,
                  hl=[2] if i != 1 else None)]
NET_Y = TOP + 3.76                                   # the middle of the R&E bar
net += [Box(6.15, TOP + 3.45, 6.52, 0.62, "R&E networks", "regional networks, Internet2, international links",
            state="active", head_size=15, sub_size=12),
        Arrow(cx[0] + 1.93, TOP + 2.26, cx[1] + 0.15, TOP + 2.26, dashed=True, color=ORANGE, width=2.5, head=False,
              step=1),
        Arrow(cx[1] + 1.93, TOP + 2.26, cx[2] + 0.15, TOP + 2.26, dashed=True, color=ORANGE, width=2.5, head=False,
              step=1),
        Text(6.15, TOP + 4.25, 6.52, 0.9, [T("Dashed: the Calico VXLAN overlay. A pod on any node reaches a pod on "
                                             "any other node directly.", size=14, color=MUTED, align="c")], only=[1]),
        Text(6.15, TOP + 4.25, 6.52, 0.9, [T("Orange dot: what the pods see, one hop on the overlay. Gold dot: what "
                                             "the network carries, the same packet inside VXLAN, node to node.",
                                             size=14, color=MUTED, align="c")], step=2),
        # gold: the real path, down through the R&E networks and up; orange: the pods' view, straight across
        packet("netunder", {2: [(cx[0] + 1.04, TOP + 2.26), (cx[0] + 1.04, NET_Y), (cx[2] + 1.04, NET_Y),
                                (cx[2] + 1.04, TOP + 2.26)]}, speed=2.6, loop=True),
        packet("netunder", {2: [(cx[0] + 1.04, TOP + 2.26), (cx[2] + 1.04, TOP + 2.26)]}, speed=1.75, loop=True,
               size=22, color="var(--orange)")]
add("The Network Underneath", net, steps=2, cls="netunder", secs=75, notes="""
The network is the foundation, and it's the PRP heritage. Nodes go in the campus Science DMZ, outside the campus firewall and IDS, at 10 to 100 gig, with jumbo frames end to end. The regional networks and Internet2, the same Internet2 that hosts some of the nodes you saw on the map, carry the traffic.

[click] On top of that, Calico builds the pod network as a VXLAN overlay, dual-stack on most nodes. To a pod, a pod at another campus is one hop away.

[click] What actually happens: Calico wraps the pod's packet in a UDP packet addressed from node A to node C, and that crosses the real path, down through the R&E networks and back up. The orange dot is what the pods see; the gold dot is what your network carries. That's what makes one cluster across a hundred sites behave like one cluster, and it's why jumbo frames matter: the wrapper adds 50 bytes to every packet.
""")

# ── Policy Lives in the Cluster: the node filters for itself ──────────────────────────────────────────────
ports = [["From the internet", "Why"], ["22/tcp", "SSH, for NRP operators"],
         ["443/tcp", "HTTPS; open on every node"],
         ["ICMP", "ping, and path MTU discovery for jumbo frames"],
         ["8443/tcp", "object reads over HTTPS and XRootD (data caches)"],
         ["8444/tcp", "Pelican tokens, director health checks, metrics"],
         ["50000–51000/tcp", "GridFTP data channels"]]
PY0 = TOP + 0.15
pol = [Bullets(X0, TOP + 0.15, 5.6, 5.2, [
    "Nodes sit outside campus firewalls, so the cluster filters traffic **at each node** itself",
    "One **Calico GlobalNetworkPolicy** for every node, written once and stored in the cluster",
    ("From other NRP nodes: everything is allowed", 0, 1),
    ("From the internet: only the ports in the table", 0, 1),
    ("A new node is covered the moment it joins; campuses keep no per-node firewall rules, and turn local "
     "iptables and firewalld off", 0, 2),
    ("Why: nodes come and go every week, faster than any campus change process", 0, 2)], size=17, gap=9),
    Box(6.55, PY0 + 0.3, 1.3, 0.95, "Internet", "any address", state="white", head_size=15, sub_size=11.5),
    Frame(9.0, PY0, 0.14, 1.55, fill="E9B55C", line=None, radius=0.02),
    Text(8.55, PY0 + 1.6, 1.05, 0.3, T("the policy", size=12, bold=True, color=AMBER, align="c")),
    Box(9.14, PY0, 1.7, 1.55, "NRP node", "filters at its own interfaces", head_size=15, sub_size=11.5),
    Box(11.3, PY0 + 0.3, 1.43, 0.95, "Other NRP nodes", "any port", state="white", head_size=14, sub_size=11.5),
    Text(7.9, PY0 + 0.08, 1.05, 0.3, T("443 ✓", size=14, bold=True, color=GREEN, align="c"), step=1),
    Text(7.9, PY0 + 1.13, 1.05, 0.3, T("3306 ✗", size=14, bold=True, color=RED, align="c"), step=1),
    *[packet("policy", {k: path for k in (1, 2)}, speed=sp, loop=True, size=22, color=col) for path, sp, col in [
        ([(7.85, PY0 + 0.5), (9.4, PY0 + 0.5)], 1.2, "var(--green)"),          # 443: through the wall
        ([(7.85, PY0 + 1.05), (8.98, PY0 + 1.05)], 0.75, "var(--red)"),         # 3306: stops at the wall
        ([(11.3, PY0 + 0.78), (10.62, PY0 + 0.78)], 0.6, "var(--green)")]],      # another node: anything
    Table(6.55, TOP + 2.25, 6.18, 2.9, ports, [1.9, 4.28], size=13, mono=(0,), row_h=0.41, cls="rows"),
    Text(6.55, TOP + 5.2, 6.18, 0.3, T("The last three only on nodes that run a data cache, an origin or a Globus "
                                       "endpoint.", size=12, color=MUTED)),
    Link(X0, 6.3, 5.6, 0.3, "https://nrp.ai/documentation/admindocs/participating/network/", size=13)]
add("Policy Lives in the Cluster", pol, steps=2, cls="policy", secs=70, notes="""
How we filter, which is usually the first question from network people. Because the nodes sit in the Science DMZ, outside the campus firewall, the campus isn't filtering for them. So the cluster does it at every node: one Calico GlobalNetworkPolicy, written once, applied to each node's own interfaces. It filters before Kubernetes rewrites a destination for a Service, so it sees what the packet asked for.

[click] The rule is simple. Between NRP nodes, everything is allowed, which is what lets pods talk across the overlay. From the internet, only a short list: SSH for operators, 443, ICMP for path MTU discovery, which jumbo frames need, and the data-cache and GridFTP ports only on the nodes that run those services. Everything else, a database port for example, is dropped at the node.

[click] The point is churn. A new node is covered the moment it joins, with nothing for the campus to configure, and we ask campuses to turn off local iptables and firewalld because they fight with the cluster policy. Nodes come and go every week; no campus change process keeps up with that.
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
It's one cluster with one control plane, but it spans a continent, so every node carries topology labels: region, zone and site. Workloads can spread across zones for resilience, or stay near their data. The demo counts nodes by region with exactly these labels.

Storage follows the regions. Rook runs {len(ceph)} Ceph clusters, one per region or large site, about {PB:.0f} petabytes raw in total; the big one is the original West Coast pool. Users get CephFS for shared files, RBD block volumes and S3. Linstor, which is DRBD underneath, gives fast replicated block storage for things that need it. CVMFS for software distribution, and local NVMe for scratch. The rule for users: pick the storage in the region where you compute.
""")

# ── More Than GPUs ──────────────────────────────────────────────────────────────────────────────────────
hw = [("NVIDIA GPUs", f"{GPUS:,} in {GPU_MODELS} models, GTX 1080 Ti to H200"), ("AMD GPUs", "ROCm device plugin"),
      ("Qualcomm Cloud AI 100", "inference cards, requested like a GPU"), ("Xilinx Alveo FPGAs", "Vivado and Vitis"),
      ("ESnet SmartNIC", "FPGA network cards you program in P4"),
      ("ARM64 nodes", f"a second CPU architecture ({S['arch'].get('arm64', 0)} nodes): needs multi-arch images")]
rt = [("Containers", "runc, plus the NVIDIA runtime"), ("Kata VMs", "a lightweight VM per pod"),
      ("Sysbox", "system containers: Docker inside a pod"), ("KubeVirt", "full VMs: Ubuntu, Windows, Talos"),
      ("Multus and SR-IOV", "extra NICs in a pod, for network research"),
      ("Confidential VMs", "Kata with AMD SNP or Intel TDX, GPUs included")]
he = [Text(X0, TOP + 0.05, 6.0, 0.4, T("Hardware beyond x86 and NVIDIA", size=19, bold=True, color=NAVY)),
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
add("More Than GPUs", he, optional=True, secs=50, notes=f"""
It isn't only NVIDIA GPUs on x86. Accelerators: AMD GPUs, Qualcomm inference cards and Xilinx FPGAs. ESnet's SmartNICs are FPGA network cards you program in P4, for network research rather than compute. And a few ARM nodes, a second CPU architecture, so images need to be built for both. On the runtime side: ordinary containers; Kata, which gives each pod its own lightweight VM, and which comes back in a few slides; Sysbox for Docker-in-a-pod; KubeVirt for full VMs including Windows; Multus with SR-IOV to give a pod extra NICs for network research; and confidential VMs, Kata with SNP or TDX. There are {len(S['runtimeclasses'])} runtime classes defined, most of them Kata variants.
""")

# ── Getting Traffic In: web traffic through the ingress nodes; anything else through MetalLB and BGP ─────────
A_Y, B_Y, C_Y = TOP + 0.15, TOP + 1.42, TOP + 2.62          # rows: web path; DNS and cert-manager; not HTTP
COLS = [(X0, 1.55), (3.35, 2.75), (7.3, 2.0), (10.5, 2.23)]  # x, width of the four columns
mid = [x + w / 2 for x, w in COLS]
ing = [Box(COLS[0][0], A_Y, COLS[0][1], 0.95, "Client", "anywhere", head_size=16, hl=[1]),
       Box(COLS[1][0], A_Y, COLS[1][1], 0.95, "Ingress node", f"HAProxy and Envoy Gateway, on "
           f"{S['haproxy_ingress_nodes']} nodes", head_size=16, sub_size=12, hl=[1, 2]),
       Box(COLS[2][0], A_Y, COLS[2][1], 0.95, "Service", "in your namespace", head_size=16, sub_size=12, hl=[3]),
       Box(COLS[3][0], A_Y, COLS[3][1], 0.95, "Your pods", "on any node", head_size=16, sub_size=12, hl=[3, 4]),
       Arrow(COLS[0][0] + COLS[0][1], A_Y + 0.47, COLS[1][0], A_Y + 0.47, hl=[1]),
       Arrow(COLS[1][0] + COLS[1][1], A_Y + 0.47, COLS[2][0], A_Y + 0.47, hl=[3]),
       Arrow(COLS[2][0] + COLS[2][1], A_Y + 0.47, COLS[3][0], A_Y + 0.47, hl=[3]),
       Box(X0, B_Y, 2.2, 0.8, "DNS", "Constellix: the name → an ingress node", state="white", head_size=15,
           sub_size=11.5, hl=[1]),
       Arrow(mid[0], B_Y, mid[0], A_Y + 0.95, dashed=True, head=False, hl=[1]),
       Box(COLS[1][0], B_Y, COLS[1][1], 0.8, "cert-manager", "renews the *.nrp-nautilus.io certificate",
           state="white", head_size=15, sub_size=11.5, hl=[2]),
       Arrow(mid[1], B_Y, mid[1], A_Y + 0.95, dashed=True, hl=[2]),
       # not HTTP: its own address, announced by MetalLB over BGP (shown at step 4)
       Box(X0, C_Y, 2.2, 0.8, "MetalLB", "2 speaker nodes at SDSC", head_size=15, sub_size=11.5, step=4, hl=[4]),
       Arrow(X0 + 2.2, C_Y + 0.4, COLS[1][0], C_Y + 0.4, dashed=True, step=4, hl=[4]),
       Text(X0 + 2.2, C_Y - 0.02, 0.55, 0.3, T("BGP", size=12, bold=True, color=BLUE, align="c"), step=4),
       Box(COLS[1][0], C_Y, COLS[1][1], 0.8, "SDSC router", "AS 26397; learns the IP by BGP", head_size=15,
           sub_size=11.5, step=4, hl=[4]),
       Box(COLS[2][0], C_Y, COLS[2][1], 0.8, "LB Service", "its own public IP", head_size=15, sub_size=11.5,
           step=4, hl=[4]),
       Arrow(COLS[1][0] + COLS[1][1], C_Y + 0.4, COLS[2][0], C_Y + 0.4, step=4, hl=[4]),
       Arrow(COLS[2][0] + COLS[2][1], C_Y + 0.4, mid[3] - 0.3, A_Y + 0.95, step=4, hl=[4]),
       packet("ingress", {1: [(mid[0], A_Y + 0.95), (mid[0], B_Y + 0.02), (mid[0], A_Y + 0.95),
                              (COLS[0][0] + COLS[0][1], A_Y + 0.47), (COLS[1][0] - 0.12, A_Y + 0.47)],
                          2: [(COLS[1][0] - 0.12, A_Y + 0.47)],
                          3: [(COLS[1][0] - 0.12, A_Y + 0.47), (COLS[2][0] - 0.12, A_Y + 0.47),
                              (COLS[3][0] - 0.12, A_Y + 0.47)]}, speed=3.0),
       packet("ingress", {2: [(mid[1], B_Y - 0.02), (mid[1], A_Y + 0.97)]}, speed=0.8, size=22,
              color="var(--orange)"),
       packet("ingress", {4: [(X0 + 2.2, C_Y + 0.4), (COLS[1][0] - 0.05, C_Y + 0.4)]}, speed=0.5, size=22,
              color="var(--orange)"),
       packet("ingress", {4: [(COLS[1][0] + COLS[1][1], C_Y + 0.4), (COLS[2][0] - 0.1, C_Y + 0.4),
                              (COLS[2][0] + COLS[2][1], C_Y + 0.4), (mid[3] - 0.3, A_Y + 0.98)]}, speed=2.2),
       Text(X0, TOP + 5.12, W, 0.3, T(f"{S['ingresses']:,} Ingress objects (HAProxy) and {S['httproutes']} Gateway "
                                      "API routes (Envoy Gateway); users create them in their own namespace.",
                                      size=13, color=MUTED))]
ICAPS = {0: ("A request from the internet to a pod", "Web traffic comes in through ingress nodes; anything else gets "
             "its own address."),
         1: ("1. Find it", f"A name under nrp-nautilus.io resolves to one of the {S['haproxy_ingress_nodes']} "
             "ingress nodes, which sit at sites in the US, Europe and Korea. The client connects to it on port 443."),
         2: ("2. Decrypt", "HAProxy on that node ends TLS with the *.nrp-nautilus.io certificate that cert-manager "
             "renews from Let's Encrypt, reads the host name, and finds the matching Ingress rule."),
         3: ("3. Deliver", "The rule names a Service in the owner's namespace. The Service spreads requests over its "
             "pods, wherever they run, across the overlay."),
         4: ("Not HTTP?", "A LoadBalancer Service gets its own public IP. MetalLB, on two nodes at SDSC, announces it "
             "to SDSC's router over BGP, for IPv4 and IPv6.")}
for k, (h, b) in ICAPS.items():
    ing.append(Text(X0, TOP + 3.65, W, 1.4, [T(h, size=21, bold=True, color=NAVY), T(b, size=18, color=BODY,
                                                                                     before=5)], only=[k]))
add("Getting Traffic In", ing, steps=4, cls="ingress", builds=True, secs=90, notes=f"""
How a request from the internet reaches a pod. Two words first: a Service is a stable address for a set of pods, and an Ingress is a rule that maps a host name to a Service.

[click] Find it. Every name under nrp-nautilus.io resolves, through Constellix DNS, to one of {S['haproxy_ingress_nodes']} ingress nodes. They're ordinary cluster nodes at sites in the US, Europe and Korea, running HAProxy and Envoy Gateway on ports 80 and 443.

[click] Decrypt. HAProxy ends TLS there, with the wildcard certificate for nrp-nautilus.io that cert-manager renews from Let's Encrypt through a DNS challenge. Then it reads the host name and finds the Ingress rule. Envoy Gateway does the same job for the newer Gateway API routes; remember it, because the AI gateway later is built on it.

[click] Deliver. The rule points at a Service in the owner's namespace, and the Service spreads requests over its pods, wherever they are, over the overlay from the network slide. There are about a thousand Ingress objects today. For users it's self-service: create an Ingress in your namespace and DNS and TLS come with it.

[click] Not HTTP? A LoadBalancer Service gets its own public IP from an SDSC range. MetalLB runs on two speaker nodes at SDSC and announces those addresses to SDSC's router over BGP, IPv4 and IPv6. About forty services use that today.
""")
