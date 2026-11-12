# Presenter reference: Inside the National Research Platform (SCinet, SC26)

For the presenter, not for the site. Slides are named by title, because the numbers are changing.
Cluster numbers come from the 10 Nov 2026 snapshot (`data/snapshot.json`) and from read-only
queries on 11 Nov 2026.

**Contents:** [Answers to your questions](#answers-to-your-questions) ·
[Glossary](#glossary) ([What NRP is](#what-nrp-is) · [How it's built](#how-its-built) ·
[How we run it](#how-we-run-it) · [AI](#ai) · [Using it](#using-it)) ·
[Where to read more](#where-to-read-more)

---

## Answers to your questions

### "Policy Lives in the Cluster": what's the point?

Most campus servers sit behind the campus firewall. NRP nodes don't. They sit in the campus
**Science DMZ**, outside that firewall, so big data transfers aren't slowed by it. So the node needs
another way to filter traffic.

NRP doesn't ask each campus to write firewall rules for each node. The cluster filters at every node
itself:

- One **Calico GlobalNetworkPolicy** is written once and applied to every node's own network
  interfaces ("host endpoints"), wherever the node is.
- Traffic between NRP nodes (a central list of addresses, a "network set") is allowed.
- From the internet, only a short list of ports is open: 22 for operators, 443, ICMP, and data ports
  on the few nodes that run caches, origins or Globus.
- **"Before NAT"** (Calico calls it *preDNAT*): Kubernetes rewrites a packet's destination address
  when it's for a Service. A preDNAT rule sees the packet as it arrived from the internet, before
  that rewrite. So it can block, say, a NodePort before Kubernetes forwards it anywhere.
- Local `iptables` and `firewalld` rules stay off: they would fight with Calico's rules, which are
  also iptables rules.

Why this matters: nodes join and leave every week. A new node is covered the moment it joins, with
no ticket to the campus network team. The talking point for this audience is *policy as code, in
one place, for a firewall-less edge*.

### "More Than GPUs": is ARM64 an accelerator? Is a SmartNIC?

No to both, strictly.

- **ARM64** is a CPU architecture, the alternative to x86-64 (amd64). The cluster has 3 ARM64 nodes
  and 531 amd64 nodes. They matter because images must be built for both architectures
  ("multi-arch") to run there.
- **ESnet SmartNIC** is a network card with an FPGA on it, which you program to process packets at
  line rate (P4 pipelines). It speeds up networking, not general computation. It's there for network
  research.
- The Xilinx Alveo FPGAs, AMD GPUs and Qualcomm Cloud AI 100 cards are accelerators.

The column is now headed "Hardware beyond x86 and NVIDIA", and the ARM64 and SmartNIC boxes say what they are.

### "Getting Traffic In": the terms, and what really happens

What happens when someone opens `https://something.nrp-nautilus.io`:

1. **DNS.** Every `*.nrp-nautilus.io` name points (CNAME) to `nrp-nautilus.io`, served by
   **Constellix** DNS. On 11 Nov it answered `163.253.29.25`, which is `osdf1.chic.net.internet2.edu`:
   an Internet2-hosted NRP node in Chicago. How Constellix picks the answer (by location, by
   health) isn't something we checked.
2. **The ingress node.** **HAProxy** runs as an ingress controller on **19 nodes** around the world
   (Internet2 Chicago, New York and Cincinnati, CENIC, AMPATH, CESNET, KREONET, Clemson, Missouri,
   Delaware, Buffalo, NYSERNet, and SDSC/Calit2 nodes). Each listens on ports 80 and 443 of its node
   (a `hostPort`). The **Envoy Gateway** proxies run on the same 19 nodes.
3. **TLS ends there** ("TLS termination"). HAProxy decrypts HTTPS using a wildcard certificate for
   `*.nrp-nautilus.io`. **cert-manager** keeps that certificate renewed from Let's Encrypt by proving
   control of the domain through Constellix DNS (a DNS-01 challenge). Of the 998 HAProxy Ingress
   objects, 979 use TLS and 813 use this default wildcard. Groups with their own domain get their
   own Let's Encrypt certificates. There are 311 cert-manager Certificates on the cluster.
4. **The Ingress rule.** HAProxy reads the host name and path and finds the matching **Ingress**
   object (1,006 in all), or an **HTTPRoute** for Envoy Gateway (33).
5. **Service, then pod.** The rule points to a **Service** in someone's namespace. The Service
   forwards to one of its pods, on any node anywhere, over the Calico overlay.

`ellm.nrp-nautilus.io` follows the same path: HAProxy, then an Ingress in `envoy-gateway-system`
that points at the Envoy AI Gateway's Service.

**MetalLB is a separate path, not part of the web path above.** It's for a Service that needs its
own public IP address: non-HTTP traffic, or a dedicated address. Such a Service has type
`LoadBalancer` (42 today). MetalLB gives it an address from SDSC's ranges (`67.58.49.48/28`,
`67.58.49.64/27`, and an IPv6 `/64`). Two "speaker" nodes announce those addresses to SDSC's PRISM
router (AS 26397) over **BGP**, IPv4 and IPv6, so the router knows where to send the traffic.
Envoy Gateway's `gw` and `grpc` gateways are two of these.

The old slide drew client → router (learned by BGP) → ingress for all traffic. That was wrong for
the web path. The slide is redrawn: four steps (find it, decrypt, deliver, not HTTP?), each lighting
its own boxes, with a dot that visits each one, cert-manager included.

### "Measuring the Network": how perfSONAR works

**perfSONAR** is an open-source toolkit for measuring network paths between hosts. R&E networks use
it to find the problems that make transfers slow: packet loss, a small MTU somewhere, a bad route.

- A **testpoint** is the light perfSONAR install. Its scheduler, **pScheduler**, runs tests on a
  timetable using standard tools:
  - **iperf3** for throughput;
  - **OWAMP** for one-way latency, loss and jitter;
  - **traceroute** for the path.
- **pSConfig** is the shared test plan: which hosts test to which, with which tools, how often. Each
  testpoint reads it and schedules its share.
- Results go to a measurement archive. **MaDDash** draws them as a grid of host pairs, each cell
  colored by thresholds (green, yellow, red). One glance shows which paths are bad.

On NRP:

- Each node runs two testpoints (526 each): `testpoint-h` on the host network (the node's public
  IP) and `testpoint` in the pod network (its Calico overlay IP). Running the same tests on both
  separates a network problem from an overlay problem.
- The mesh config (pSConfig JSON) is served by the `meshconfig` service at
  meshconfig.nrp-nautilus.io. One node per site carries the label `nautilus.io/a2a-latency`; those
  nodes form the all-to-all mesh: 97 sites.
- The all-to-all tests: continuous one-way latency and loss (600 packets at one a second),
  throughput every 18 h for 15 s, and traceroute every 6 h. Smaller meshes exist for Guam, SoX,
  NJEdge and the OSDF caches.
- Results go to an archive (Esmond on perfsonar.nrp-nautilus.io; OpenSearch for newer tests).
  MaDDash draws the grid: rows are sources, columns destinations; green ≤ 0.001% loss, yellow more,
  red ≥ 0.1%, gray no data. A red column points near that destination; a red row, near the source.
- What it buys you: when a user says "the cluster is slow", you can show whether it's their path.

The slide now has three steps: one site's tests to every other, then the whole mesh (the old step 2
drew it too faint to see), then the real MaDDash loss grid from 11 Nov.

### "Security": what each example means

- **Identity:** a campus login alone gives you nothing; a namespace admin has to add you. Access is
  by group, not just by login.
- **Detect:** Falco watches system calls in containers. NRP's own rules look for crypto-miner
  binaries and command lines, connections to mining pools, and malicious proxy software. Falco
  Talon is the response engine: its rules kill the pod for those detections.
- **Prevent:** Gatekeeper checks every object before it's created. Its constraints deny privileged
  containers outside admin namespaces; pods that set `CUDA_VISIBLE_DEVICES` themselves (a way to
  reach GPUs the scheduler didn't assign); user LoadBalancer and NodePort Services; user pods that
  tolerate system taints; and role bindings to anonymous users.
- **Audit:** the IPMI scanner alerts operators if a node's BMC, the out-of-band management
  controller, answers from the internet.

### "The LLM Service": how are Anthropic calls handled?

You're right: everything underneath is OpenAI-style.

- Every model server is vLLM, and every backend the gateway knows is declared with the OpenAI schema.
- Claude Code points at **`https://ellm.nrp-nautilus.io/anthropic`** (`ANTHROPIC_BASE_URL`, from
  the NRP client-config docs), so it sends Anthropic **Messages API** requests to
  `/anthropic/v1/messages`.
- **Envoy AI Gateway** (v1.0.0 on the cluster) translates them. Its Anthropic-to-OpenAI translator
  (`internal/translator/anthropic_openai.go` upstream):
  - rewrites the request into an OpenAI `/v1/chat/completions` call to the vLLM pods;
  - converts the answer back into Anthropic format, including the streamed version (SSE events).
- Routing, auth and the rate limit are the same as for OpenAI calls. The `model` field becomes the
  `x-ai-eg-model` header either way.
- The NRP docs warn that "not all NRP models route cleanly" through it. Tool calls and reasoning
  formats differ by model, so some don't translate cleanly.

So the slide can show two endpoints: `/v1` (OpenAI-compatible) and `/anthropic` (Anthropic-compatible,
translated at the gateway).

### "Ask for a Task, Not a Model": do some models get better priority?

No. "Priority" there is the **fallback order inside one task name**, not a ranking of models or
users.

- The `coding` rule lists four backends with priorities 0, 1, 2, 3: `deepseek-v4-flash`, then
  `qwen3`, then `gemma`, then `qwen3-small`. Envoy sends every `coding` request to priority 0.
- It moves to priority 1 only if priority 0 is unhealthy: failed its health checks, or ejected after
  5xx errors. Requests on that rule may run up to 1,200 s.
- Every user is treated the same. The rate limit (48,000 output tokens a minute) is per token and
  per model, so a user's `coding` traffic counts against whichever model answered.
- One real difference between models: per-user concurrency limits. Your 7GRP backup slide
  ("Context is a memory budget", mid-August config) had the largest models capped at 2 concurrent
  requests per user and smaller ones at 8 or 16. That's about memory, not preference.

### "Sharing GPUs Fairly" and "How a Node Joins": the correction

Hardware owners don't get a priority class. The mechanism:

- **Reservation taints.** On request, admins put a taint on the owner's nodes,
  `nautilus.io/reservation=<group>:NoSchedule`. Only pods that **tolerate** that taint can start
  there, and the group adds the toleration to its own pods. Today 119 nodes carry a reservation, for
  23 groups (the largest: `osdf` 31 nodes, `csu-tide` 15).
- **Opportunistic work.** The `opportunistic` priority class (value −2,000,000,000; "can be
  preempted by any other pod") fills idle GPUs. Any normal pod that needs the GPU preempts it.
  - 232 pods run that way today, 208 of them in `osg-opportunistic`: Open Science Grid glideins.
  - Most opportunistic pods don't tolerate reservation taints, so they fill idle GPUs on unreserved
    nodes. A few (4 today) do.
- **`nice`** (−10) is for pods that can live with occasional preemption.
- **The `owner` class exists but isn't for owners.** Its description is "pods that provide services
  for a node", and the LLM model servers use it (value 10, just above ordinary pods, which get 0
  because the cluster has no default class). Avoid the word "owner" for this on the slides.
- **The contributor guide's wording:** "From then on the node is yours first", and "when it would
  sit idle, the rest of the pool runs on it."

---

### The CPU count: why the deck once said 59,352

The first version of the deck summed `status.capacity.cpu` over every Node object. Two of those
objects aren't machines: `admiralty-ncmir-mm-expanse-…` and `admiralty-ndp-voyager` are virtual
nodes from Admiralty, the multicluster scheduler. Each stands in for a remote cluster and reports
that cluster's capacity as its own: 13,800 and 10,104 CPUs.

| | Nodes | CPUs |
|---|---|---|
| Every Node object | 536 | 59,352 |
| The two Admiralty virtual nodes | 2 | 23,904 |
| Physical NRP nodes (what the deck shows now) | 534 | 35,448 |
| Of those, not on dash.nrp-nautilus.io | 21 | 2,096 |
| The dashboard | 513 | 33,352 |

The 21 nodes missing from the dashboard are mostly Fresno State's new nodes. Both the deck and the
dashboard count hardware threads; about 77% of them are on nodes with hyperthreading on, so physical
cores number about 21,800. The 7GRP talk's "35k cores" was the physical-node total.

## Glossary

Grouped by the part of the talk where the term first shows up; alphabetical within each group.

### What NRP is

| Term | What it is |
|---|---|
| **Container** | A process packaged with its own filesystem: the code plus every library it needs. Built once from a Dockerfile as an **image**, it runs the same on any node. |
| **Container image** | The packaged filesystem a container starts from, stored in a registry and pulled by the node. |
| **Deployment** | A Kubernetes object that keeps N copies of a pod running and replaces any that die. Used for services. |
| **Internet2** | The US national research and education network. On NRP it also hosts nodes: 54 nodes at 51 Internet2 sites. |
| **Job** | A Kubernetes object for batch work: runs pods until they finish successfully, then stops. |
| **Kubernetes** | Software that runs containers across many machines. You declare what should run; it schedules pods onto nodes and keeps them running. NRP is one cluster, **Nautilus**, on Kubernetes v1.34. |
| **Namespace** | A named space in the cluster for one group's objects, with its own access rules and quotas. On NRP: one per lab, course or service; 2,334 today. |
| **Nautilus** | The name of NRP's Kubernetes cluster: 534 nodes, 1,460 GPUs in 33 models, 35,448 CPUs (hardware threads), 129 dashboard sites. |
| **Node** | One machine in the cluster. |
| **NSF Category II** | An NSF award type for innovative, experimental computing resources. NRP's 2021 award (OAC-2112167) is one. |
| **Pod** | The smallest unit Kubernetes runs: one or more containers that share a network address and storage. |
| **PRP (Pacific Research Platform)** | NRP's 2015 predecessor: data transfer nodes (FIONAs) in campus Science DMZs on CENIC and Pacific Wave. |
| **Scheduler** | The Kubernetes component that picks a node for each new pod, based on the resources it asks for, its labels and taints. |
| **Service** | A stable name and address in front of a set of pods. Traffic to the Service goes to one of the pods. |
| **StatefulSet** | Like a Deployment, but each pod keeps a fixed name and its own volume. NRP's model servers are StatefulSets. |

### How it's built

| Term | What it is |
|---|---|
| **AMD ROCm** | AMD's GPU software stack, the counterpart of CUDA. A ROCm device plugin lets pods request AMD GPUs. |
| **ARM64** | A CPU architecture (also called aarch64), not an accelerator. 3 nodes on NRP; images need an ARM64 build to run there. |
| **BGP** | Border Gateway Protocol: how routers tell each other which IP addresses they can reach. MetalLB uses it to announce service addresses to SDSC's router. Calico's own BGP settings use route reflectors (AS 64512). |
| **Calico** | The cluster's network plugin: gives every pod an address, carries pod traffic between nodes, and enforces network policy. 309 nodes run its IPv6 daemon. |
| **CENIC** | California's research and education network, PRP's original backbone. |
| **Ceph** | Distributed storage software. Three interfaces: **CephFS** (a shared filesystem), **RBD** (block volumes, like a disk), **S3** (object storage, Amazon's API). NRP has 9 Ceph clusters, 14.9 PB raw. |
| **cert-manager** | A Kubernetes add-on that requests and renews TLS certificates automatically, most often from Let's Encrypt. 311 certificates on NRP, including the `*.nrp-nautilus.io` wildcard. |
| **Confidential VMs (SEV-SNP, TDX)** | VMs whose memory is encrypted by the CPU (AMD SEV-SNP, Intel TDX), so even the host's admins can't read it. On NRP, Kata VMs with these, GPUs included. |
| **Constellix** | The DNS provider for `nrp-nautilus.io`. cert-manager uses its API to prove domain control for the wildcard certificate. |
| **CVMFS** | CERN VM File System: a read-only, cached, HTTP-distributed filesystem for software. Software appears under `/cvmfs` without being installed on each node. |
| **DNAT / NAT** | Network address translation: rewriting a packet's addresses. Kubernetes uses destination NAT to send traffic for a Service's address to a pod's address. |
| **DNS-01 / ACME** | ACME is the protocol Let's Encrypt uses to issue certificates. In a DNS-01 challenge you prove you control a domain by creating a DNS record; it's the only way to get a wildcard certificate. |
| **Dual-stack** | Running IPv4 and IPv6 side by side. |
| **Envoy / Envoy Gateway** | Envoy is a high-performance proxy. Envoy Gateway runs Envoy as a Kubernetes ingress driven by the Gateway API. On NRP its proxies run on the same 19 nodes as HAProxy, and two of its gateways have MetalLB addresses. |
| **ESnet** | The US Department of Energy's science network. Its SmartNIC project provides open FPGA designs for network cards. |
| **FPGA / Xilinx Alveo** | A chip you can rewire for one task. Alveo is AMD-Xilinx's FPGA card line, programmed with Vivado and Vitis. |
| **Gateway API / HTTPRoute** | The newer Kubernetes API for ingress. A **Gateway** is a listener; an **HTTPRoute** maps host names and paths to Services. 33 HTTPRoutes on NRP. |
| **GlobalNetworkPolicy** | A Calico policy that applies cluster-wide, including to the nodes' own interfaces (host endpoints). NRP's host firewall is one of these. |
| **HAProxy** | A widely used load balancer and proxy. NRP's main ingress controller: on 19 nodes, ports 80 and 443, ending TLS and routing by Ingress rules. |
| **Ingress** | A Kubernetes object that maps a host name and path to a Service, for HTTP and HTTPS. 1,006 on NRP; users create them in their own namespace. |
| **iptables / firewalld** | Linux's packet-filter rules, and a service that manages them. Turned off on NRP nodes because Calico manages the rules. |
| **Jumbo frames / MTU** | MTU is the largest packet a link carries. Standard is 1,500 bytes; jumbo frames are 9,000, so fewer packets carry the same data. NRP uses MTU 9000 between nodes. |
| **KubeVirt** | Runs full virtual machines (Ubuntu, Windows, Talos) as Kubernetes objects. |
| **Kata Containers** | Runs each pod inside its own lightweight VM, so a container can't touch the node's kernel. NRP's CI uses it. |
| **Let's Encrypt** | A free certificate authority that issues TLS certificates automatically through ACME. |
| **Linstor / DRBD** | DRBD replicates a block device over the network, disk to disk; Linstor manages DRBD volumes in Kubernetes. Fast replicated block storage, used for model weights. |
| **MetalLB** | Gives `LoadBalancer` Services a public IP on bare-metal clusters. On NRP: 42 such Services, addresses from SDSC ranges, announced over BGP to SDSC's PRISM router from 2 speaker nodes. Not on the main web path. |
| **Multus** | Lets a pod have more than one network interface, for network research. |
| **Node labels / topology** | Key-value tags on nodes. NRP labels every node with region, zone (143) and site, and GPU nodes with the GPU model. Pods select or spread over nodes by them. |
| **NVMe** | Fast local SSDs. Used for scratch space. |
| **Overlay network / VXLAN** | An overlay is a virtual network built on top of the physical one. VXLAN wraps each pod packet in a UDP packet between the two nodes' real addresses. NRP's pods talk over a Calico VXLAN overlay. |
| **P4** | A language for programming how a network device processes packets. |
| **Pacific Wave** | A West Coast research and education exchange point, part of PRP's original fabric. |
| **Path MTU discovery** | How a sender learns the smallest MTU along a path: routers send back ICMP "too big" messages. If ICMP is blocked, jumbo-frame paths silently break. That's why NRP keeps ICMP open. |
| **Qualcomm Cloud AI 100** | A low-power inference accelerator card, requested by pods like a GPU. |
| **R&E networks** | Research and education networks: regional (CENIC, GPN, NYSERNet ...), national (Internet2, ESnet) and international links. |
| **Rook** | Runs Ceph inside Kubernetes as an operator: it deploys and heals the Ceph daemons. |
| **runc** | The standard low-level program that starts containers. |
| **Science DMZ** | A part of a campus network built for research data: outside the campus firewall, with fast paths and its own security measures. NRP nodes go there. |
| **SmartNIC** | A network card that can run its own programs (here, an FPGA) to process packets. Network hardware, not a compute accelerator. |
| **SR-IOV** | Lets one physical network card appear as several, so a pod gets direct, fast access to the hardware. |
| **Sysbox** | A container runtime for "system containers" that can run Docker or systemd inside, without being privileged. |
| **TLS termination** | Where HTTPS is decrypted. On NRP, at the ingress node; traffic continues inside the cluster from there. |
| **VIP** | Virtual IP: an address that belongs to a service rather than one machine. Here, a MetalLB address. |

### How we run it

| Term | What it is |
|---|---|
| **Alertmanager** | Takes alerts from Prometheus and routes them (deduplicated, grouped) to people. 3 replicas on NRP. |
| **Argo CD** | A GitOps tool: watches git repos and makes the cluster match them. 20 applications on NRP, GitLab among them. |
| **Authentik** | An open-source identity provider; NRP's login service. |
| **CILogon** | Federated login for research: sign in with your campus account (via InCommon and eduGAIN). |
| **Container registry** | Stores images. NRP's is built into GitLab: gitlab-registry.nrp-nautilus.io, pulled from inside the cluster. |
| **CVE** | A public ID for a known security vulnerability. NRP rolls out mitigations through Argo CD. |
| **DCGM** | NVIDIA's Data Center GPU Manager. Its exporter reports GPU use, memory and power to Prometheus. |
| **Diode** | NetBox Labs' service for pushing discovered data into NetBox. |
| **Docker-in-Docker (dind)** | A Docker daemon running inside a container, so a CI job can run `docker build`. NRP's Docker runner does this inside a Kata VM. |
| **Drift / self-heal** | Drift: the cluster no longer matches git, usually after a manual change. With self-heal on, Argo CD puts it back. |
| **Elastic** | The Elasticsearch stack, for searching logs. NRP sends syslog from every node there, SSH logins included. |
| **Falco / Falco Talon** | Falco watches system calls at runtime and alerts on suspicious behavior, such as a crypto miner in a pod. Talon acts on Falco alerts automatically, for example by deleting the pod. |
| **Gatekeeper / OPA** | Open Policy Agent is a policy engine; Gatekeeper uses it to reject Kubernetes objects that break rules when they're created. |
| **GitLab** | Code hosting with issues, CI and a registry. NRP's is self-hosted at gitlab.nrp-nautilus.io (GitLab 19.5). |
| **GitLab runner** | The program that runs CI jobs. NRP has four shared runner flavors, all in namespace `gitlab-ci-kata`, all in Kata VMs. The default one is unprivileged, up to 12 CPUs and 50 GiB. The Docker one runs Docker-in-Docker, privileged inside its VM. Two more serve projects on gitlab.com and on SDSC's own GitLab. |
| **GitOps** | Running a system from git: the desired state is in a repo, changes go through commits, and a tool makes reality match. |
| **Grafana** | Dashboards on top of Prometheus and Thanos. |
| **Helm** | The Kubernetes package manager: a chart is a templated set of manifests plus a values file. |
| **IceCube / LIGO** | A neutrino observatory at the South Pole and a gravitational-wave observatory. Both run work through OSG, some of it on idle NRP GPUs. |
| **IPMI / BMC** | The baseboard management controller is a small computer on the motherboard for remote power and console control; IPMI is its protocol. It must never be reachable from the internet. NRP scans for that. |
| **Kaniko** | Builds container images from a Dockerfile without a Docker daemon. NRP's docs use it in CI. |
| **kube-state-metrics** | Exports the state of Kubernetes objects (pods, Jobs, nodes) as Prometheus metrics. |
| **Kubernetes executor** | GitLab runner mode in which each CI job runs as a pod in the cluster. |
| **Kueue** | A Kubernetes job-queueing system: quotas and admission for batch work. On NRP it's small today: 4 cluster queues, two of them for contributed node pools. |
| **kured** | The Kubernetes reboot daemon: reboots nodes after kernel updates, a few at a time. |
| **LLDP / lldpd** | The Link Layer Discovery Protocol: switches announce their name and port on each link. lldpd listens, so the NetBox agent learns which switch port each NIC is cabled to. |
| **NetBox** | The source of truth for network infrastructure: devices, interfaces, IPs, cables, sites. NRP runs NetBox 4; an agent on 529 nodes keeps it current. |
| **node-exporter** | Prometheus's exporter for host metrics (CPU, memory, disk, network). On every node. |
| **Nornir** | A Python framework for network automation. |
| **NRPE / Nagios** | Nagios is a classic monitoring system; NRPE is its agent for running checks on a host. |
| **OSG / glidein** | The Open Science Grid (OSPool) is a national pool of shared computing. A glidein is a pilot job that joins a node to OSG's pool and pulls work. On NRP, glideins run at opportunistic priority. |
| **perfSONAR** | Network measurement toolkit; see the answer above. A testpoint pod on 526 nodes; a 97-site mesh. |
| **Pod preemption** | The scheduler evicts lower-priority pods to make room for a higher-priority pod. |
| **Priority class** | A named priority for pods. NRP's: `opportunistic` (lowest; preempted by anything), `nice` (−10), and `owner` (10, for service pods, not hardware owners). |
| **Prometheus** | Collects metrics by scraping endpoints every few seconds and stores them as time series. 2 replicas on NRP, run by the Prometheus operator. |
| **pScheduler / pSConfig / OWAMP / iperf3 / MaDDash** | perfSONAR's parts: see the answer above. |
| **self-node-remediation** | Detects nodes that stop responding, fences them (reboots them) and lets their pods move. |
| **Taint / toleration** | A taint on a node keeps pods off it, unless a pod has the matching toleration. NRP reserves owners' nodes this way (119 nodes, 23 groups). |
| **Thanos** | Sits on top of Prometheus for long-term storage and one query view across instances: querier (14 replicas), store, compactor. |
| **Wazuh** | Open-source security monitoring: log analysis, intrusion detection and integrity checks. |

### AI

| Term | What it is |
|---|---|
| **AIGatewayRoute** | Envoy AI Gateway's route object: matches the `x-ai-eg-model` header to backends, with fallback priorities. Up to 16 rules per object, so NRP splits them across several. |
| **Anthropic Messages API** | Anthropic's request format (`/v1/messages`). NRP accepts it at `https://ellm.nrp-nautilus.io/anthropic`; the gateway translates it to OpenAI format. |
| **BF16, FP8, NVFP4, MXFP4, INT4** | Number formats for model weights: 2 bytes, 1 byte, and about half a byte per weight. NVFP4 is NVIDIA's 4-bit float; MXFP4 is the open 4-bit format gpt-oss ships in. Smaller formats fit bigger models in less GPU memory. Example: GLM-5.3 is 465 GB in NVFP4 on four 141 GB H200s; in BF16 it would be about 1.5 TB. |
| **ClickHouse** | A fast column-oriented database for analytics; holds the AI service's telemetry. |
| **Embeddings** | Vectors that represent the meaning of text, for search and retrieval. NRP serves `qwen3-embedding`. |
| **Endpoint picker (EPP)** | The InferencePool's scheduler: picks the pod for each request by queue depth, KV-cache use and prefix-cache hits. |
| **Envoy AI Gateway** | Envoy Gateway's AI extension (v1.0.0 on NRP): reads the model from the request, routes it, counts tokens for rate limits, and translates between API formats. |
| **ext_authz** | Envoy's hook to ask an external service whether to allow a request. NRP's is `llm-auth`, over gRPC. |
| **Fail closed** | If the auth service can't answer, the request is denied rather than let through. |
| **Gateway API inference extension** | The Kubernetes project that defines InferencePool and the endpoint picker. |
| **gRPC** | A fast RPC protocol over HTTP/2. |
| **Headless Service** | A Service with no shared address; DNS returns each pod's own address. Used so multi-node model pods can find each other. |
| **Health checks / outlier ejection** | Active: probe `/health` every 10 s. Passive: after two 5xx errors in a row, stop sending a pod traffic for 30 s, never more than half the pool. |
| **InferencePool** | A pool of model-server pods, selected by label, with an endpoint picker in front. |
| **KV cache** | GPU memory that holds the attention state of every token in flight. It limits how many requests and how much context a model server handles at once. |
| **LeaderWorkerSet** | A Kubernetes API for groups of pods that start and restart together (multi-node inference). Not installed on Nautilus, so NRP uses its own supervisor. |
| **MCP** | Model Context Protocol: a standard for giving LLM agents tools and data. NRP has an MCP route on the gateway and an accounting MCP server. |
| **Milvus / Qdrant** | Vector databases, for storing and searching embeddings. |
| **NCCL** | NVIDIA's library for GPU-to-GPU communication, within a node or over the network. |
| **NetworkPolicy** | A Kubernetes rule for which pods may talk to which. |
| **NVLink** | NVIDIA's fast GPU-to-GPU link inside a node. |
| **Open WebUI** | A browser chat interface for models. |
| **OpenAI-compatible API** | The request format OpenAI's API uses (`/v1/chat/completions`, `/v1/models`), which most tools speak. NRP's endpoint is `https://ellm.nrp-nautilus.io/v1`. |
| **OpenTelemetry** | The open standard for traces, metrics and logs. vLLM sends traces to an OpenTelemetry collector. |
| **Parallelism (tensor, pipeline, expert)** | Ways to split a model across GPUs. Tensor: each layer's matrices are split across GPUs in a node. Pipeline: the layers are split into stages, often across nodes. Expert: a mixture-of-experts model's experts are spread over GPUs. DeepSeek runs tensor 4 × pipeline 2 across two 4-GPU H100 nodes. |
| **Prefix caching** | Reusing the KV cache for a prompt prefix seen before (a system prompt, chat history), so it isn't recomputed. Most of an agent's prompt is repeated, so this matters a lot. |
| **Quantization** | Storing weights in fewer bits (FP8, 4-bit) so a model fits on fewer or smaller GPUs, at a small accuracy cost. |
| **Rate-limit headers** | `x-ratelimit-limit`, `-remaining` and `-reset` in each response. On NRP: 48,000 output tokens a minute, per token and model. |
| **SearXNG** | A self-hosted meta search engine; gives tools and chat a web search. |
| **SGLang** | A model server like vLLM. |
| **TEI** | Hugging Face Text Embeddings Inference, a server for embedding models. |
| **vLLM** | The open-source model server behind NRP's LLMs: batching, paged KV cache, prefix caching, and an OpenAI-compatible API. |

### Using it

| Term | What it is |
|---|---|
| **Coder** | VS Code in the browser, in your own namespace: coder.nrp-nautilus.io. |
| **FABRIC** | An NSF network research testbed with programmable nodes and links across the US and abroad. |
| **Federation** | Connecting another Kubernetes cluster so work can run across both. |
| **InterLink** | Makes a Slurm (or other) cluster appear as a virtual node in Kubernetes, so pods sent there run as batch jobs. |
| **JupyterHub** | Multi-user notebook servers: log in, pick an image and a GPU, get a notebook. |
| **SENSE** | A DOE/ESnet project for end-to-end, software-defined network paths between sites. |

---

## Where to read more

**NRP**

- Network requirements and ports: https://nrp.ai/documentation/admindocs/participating/network/
- Joining as a contributor: https://nrp.ai/documentation/admindocs/participating/new-contributor-guide/
- Upgrade runbooks: https://nrp.ai/documentation/admindocs/upgrades/intro/
- GitLab and CI for users: https://nrp.ai/documentation/userdocs/development/gitlab/
- The LLM service: https://nrp.ai/documentation/userdocs/ai/llm-managed/
- LLM client configs (Claude Code, OpenCode ...): https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs
- Cluster policies: https://nrp.ai/documentation/userdocs/start/policies/

**Projects**

- Kubernetes: https://kubernetes.io/docs/
- Calico policy, including host endpoints and preDNAT: https://docs.tigera.io/calico/latest/network-policy/
- MetalLB: https://metallb.io/
- HAProxy Ingress: https://haproxy-ingress.github.io/
- Envoy Gateway: https://gateway.envoyproxy.io/
- Envoy AI Gateway source: https://github.com/envoyproxy/ai-gateway
- cert-manager: https://cert-manager.io/docs/
- Rook and Ceph: https://rook.io/docs/ and https://docs.ceph.com/
- Argo CD: https://argo-cd.readthedocs.io/
- NetBox: https://netboxlabs.com/docs/netbox/
- perfSONAR: https://docs.perfsonar.net/
- Prometheus and Thanos: https://prometheus.io/docs/ and https://thanos.io/
- Falco: https://falco.org/docs/
- Gatekeeper: https://open-policy-agent.github.io/gatekeeper/
- Kata Containers: https://katacontainers.io/
- vLLM: https://docs.vllm.ai/
- Gateway API inference extension: https://gateway-api-inference-extension.sigs.k8s.io/
