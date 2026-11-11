"""Backup slides, after Questions.

Part of the SCinet deck: slides.py imports the section files in order. Shared constants and
helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
"""
from common import *  # noqa: F401,F403

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
For the curious, the actual list. Security tooling, Falco and Wazuh and a CVE mitigation repo; Grafana; NetBox and its agent; Kueue; the onboarding site; Open WebUI; GitLab. Most sync automatically with self-heal; a few are manual on purpose.
""")

# The GitLab runners, from their config maps in the gitlab namespace (11 Nov 2026)
runners = [["Runner", "For", "Privileged", "Jobs at once", "Limits a job can raise to"],
           ["gitlab-runner-kata-default", "every project on gitlab.nrp-nautilus.io (the default)", "no", "10",
            "12 CPUs, 50 GiB"],
           ["gitlab-runner-kata", "Docker builds: Docker-in-Docker (`docker:28-dind`)", "yes, inside its VM", "3",
            "Docker gets 48 GiB of memory for image layers"],
           ["gitlab-runner-gitlab", "projects on gitlab.com", "no", "2", "12 CPUs, 24 GiB"],
           ["gitlab-runner-sdsc", "SDSC's own GitLab, hpc-gitlab.sdsc.edu", "no", "2", "12 CPUs, 24 GiB"]]
add("Runner Flavors", [
    Table(X0, TOP + 0.1, W, 2.9, runners, [2.75, 3.85, 1.6, 1.25, 2.68], size=13.5, row_h=0.56, mono=(0,), cls="rows"),
    Bullets(X0, TOP + 3.3, W, 2.0, [
        "All four run each job in its own **Kata VM**, in namespace `gitlab-ci-kata`, on x86 nodes tainted "
        "`nautilus.io/testing=kata`",
        "Pull policy `always` (except the Docker runner): a job can't start another project's private image from a "
        "node's cache",
        "Groups can also run their own runners in their namespaces, e.g. `ihv-cenic` and `unl-dtih`"], size=16, gap=8),
], notes="""
Backup: the four runner flavors. The default one takes every project on our GitLab: no privilege, ten jobs at once, limits users can raise to 12 CPUs and 50 gigs, and it pulls images every time so one project can't reuse another's private image from a node's cache. The Docker runner is privileged, with Docker-in-Docker and 48 gigs of memory for image layers, which big CUDA images need, but still inside its own Kata VM. Two more serve projects that live on gitlab.com and on SDSC's own GitLab. Groups can also bring their own runners into their namespaces.
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
], notes="""
Backup: the NetBox agent's config, from the cluster, minus the token. Two details worth stealing. It ignores the interfaces Calico and VXLAN create, so NetBox only holds physical interfaces. And the site is a command: it asks Kubernetes for the node's site label. The loop: start lldpd, wait at least thirty seconds so LLDP has found its neighbours, then run once a day with jitter.
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
