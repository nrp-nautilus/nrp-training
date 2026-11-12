"""Snapshot the numbers the SCinet deck quotes, from the live cluster (read-only; needs kubectl).

    python3 deck/snapshot.py        # -> data/snapshot.json

Everything here is a read: node labels and capacity, workload counts in a few infrastructure
namespaces, the Argo CD applications, the Ceph clusters, and the AI gateway's routes and model
servers. Secrets are never read. Rerun it the morning of the talk if you want today's numbers;
both builders read data/snapshot.json.
"""
import json
import re
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "snapshot.json"


def kj(*args):
    out = subprocess.run(["kubectl", *args, "-o", "json"], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def items(*args):
    return kj("get", *args)["items"]


def desired(ns, kind, name):
    try:
        o = kj("get", kind, name, "-n", ns)
    except subprocess.CalledProcessError:
        return 0
    return o["status"].get("desiredNumberScheduled", o["spec"].get("replicas", 0))


snap = {"date": str(date.today())}

# ── nodes, cores, GPUs, regions ─────────────────────────────────────────────────────
# Virtual nodes (Admiralty, virtual-kubelet) stand in for whole remote clusters and report those clusters'
# capacity as their own, so they're left out of every count: they're not NRP hardware.
all_nodes = items("nodes")
nodes = [n for n in all_nodes if n["metadata"]["labels"].get("type") != "virtual-kubelet"]
snap["virtual_nodes"] = [dict(name=n["metadata"]["name"], cpu=int(n["status"]["capacity"].get("cpu", "0")))
                         for n in all_nodes if n not in nodes]
fleet, regions, zones, mem, arch = Counter(), Counter(), set(), {}, Counter()
cores = 0                     # logical CPUs (hardware threads), as Kubernetes counts them
for n in nodes:
    lab = n["metadata"]["labels"]
    cores += int(n["status"]["capacity"].get("cpu", "0"))
    regions[lab.get("topology.kubernetes.io/region", "none")] += 1
    zones.add(lab.get("topology.kubernetes.io/zone"))
    arch[lab.get("kubernetes.io/arch", "?")] += 1
    g = int(lab.get("nvidia.com/gpu.count", "0") or 0)
    if g:
        p = lab.get("nvidia.com/gpu.product", "?")
        fleet[p] += g
        mem[p] = int(lab.get("nvidia.com/gpu.memory", "0") or 0)
version = kj("version")["serverVersion"]["gitVersion"]
snap.update(nodes=len(nodes), cores=cores, gpus=sum(fleet.values()), gpu_models=len(fleet),
            zones=len(zones - {None}), regions=dict(regions.most_common()), arch=dict(arch), k8s=version,
            fleet=[dict(product=p, gpus=c, memory_mib=mem[p]) for p, c in fleet.most_common()])

# ── what runs where ─────────────────────────────────────────────────────────────────
snap["namespaces"] = len(items("namespaces"))
snap["ingresses"] = len(items("ingress", "-A"))
snap["httproutes"] = len(items("httproutes", "-A"))
snap["node_exporter"] = desired("monitoring", "ds", "node-exporter")
snap["thanos_querier"] = desired("monitoring", "deploy", "thanos-querier")
snap["netbox_agents"] = desired("netbox-agent", "ds", "agent")
snap["perfsonar_testpoints"] = desired("perfsonar", "ds", "testpoint")
snap["haproxy_ingress_nodes"] = desired("haproxy", "ds", "haproxy-ingress")
snap["calico_nodes"] = desired("kube-system", "ds", "calico-node") + desired("kube-system", "ds", "calico-node-ipv6")
snap["calico_ipv6_nodes"] = desired("kube-system", "ds", "calico-node-ipv6")
snap["a2a_zones"] = sorted({n["metadata"]["labels"].get("topology.kubernetes.io/zone", "")
                            for n in nodes if "nautilus.io/a2a-latency" in n["metadata"]["labels"]} - {""})
i2 = [n["metadata"]["labels"].get("netbox.io/site", "") for n in nodes]
snap["i2_nodes"] = sum(s.startswith("i2") for s in i2)
snap["i2_sites"] = len({s for s in i2 if s.startswith("i2")})
snap["runtimeclasses"] =sorted(r["metadata"]["name"] for r in items("runtimeclass"))
snap["device_plugins"] = sorted(d["metadata"]["name"] for d in items("ds", "-n", "kube-system")
                                if "device" in d["metadata"]["name"])

# ── GitOps ──────────────────────────────────────────────────────────────────────────
apps = []
for a in items("applications.argoproj.io", "-A"):
    sp = a["spec"]
    src = sp.get("source") or (sp.get("sources") or [{}])[0]
    auto = (sp.get("syncPolicy") or {}).get("automated")
    apps.append(dict(name=a["metadata"]["name"], repo=src.get("repoURL", ""), chart=src.get("chart", ""),
                     namespace=sp["destination"].get("namespace", ""),
                     auto=bool(auto) and auto.get("enabled", True) is not False,
                     self_heal=bool(auto and auto.get("selfHeal")), prune=bool(auto and auto.get("prune")),
                     status=f'{a.get("status", {}).get("sync", {}).get("status")}/'
                            f'{a.get("status", {}).get("health", {}).get("status")}'))
snap["argo_apps"] = apps

gl = {d["metadata"]["name"]: d["spec"]["template"]["spec"]["containers"][0]["image"].rsplit(":", 1)[-1]
      for d in items("deploy", "-n", "gitlab")}
snap["gitlab_version"] = gl.get("gitlab", "")
snap["gitlab_runners"] = sorted(k for k in gl if k.startswith("gitlab-runner"))

# ── storage ─────────────────────────────────────────────────────────────────────────
snap["ceph"] = sorted(([dict(name=c["metadata"]["name"],
                             total=c.get("status", {}).get("ceph", {}).get("capacity", {}).get("bytesTotal", 0),
                             used=c.get("status", {}).get("ceph", {}).get("capacity", {}).get("bytesUsed", 0))
                        for c in items("cephcluster", "-A")]), key=lambda c: -c["total"])
snap["storageclasses"] = sorted({s["provisioner"] for s in items("storageclass")})

# ── the LLM service ─────────────────────────────────────────────────────────────────
routes = []
for r in items("aigatewayroute", "-n", "nrp-llm"):
    for rule in r["spec"].get("rules", []):
        names = [h["value"] for m in rule.get("matches", []) for h in m.get("headers", [])
                 if h.get("name") == "x-ai-eg-model"]
        refs = [dict(name=b["name"], kind=b.get("kind", "AIServiceBackend"), priority=b.get("priority", 0))
                for b in rule.get("backendRefs", [])]
        routes.append(dict(route=r["metadata"]["name"], models=names, backends=refs))
snap["llm_routes"] = [r for r in routes if not r["route"].startswith("rl-test")]
snap["inference_pools"] = sorted(p["metadata"]["name"] for p in items("inferencepools.inference.networking.k8s.io",
                                                                      "-n", "nrp-llm"))
servers = []
LLM_NS = ["nrp-llm", "sdsc-llm"]                 # gpt-oss is served from sdsc-llm
for w in [w for ns in LLM_NS for w in items("sts,deploy", "-n", ns)]:
    t = w["spec"]["template"]["spec"]
    for c in t["containers"]:
        lim = c.get("resources", {}).get("limits", {})
        gpu = {k: int(v) for k, v in lim.items() if k.startswith("nvidia.com/") or "gpu" in k}
        if not gpu or "vllm" not in c["image"]:
            continue
        args = " ".join(c.get("args", []) + c.get("command", []))
        model = re.findall(r"(?:serve|--model)[= ]+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", args)
        par = dict(re.findall(r"--(tensor|pipeline|data)-parallel-size[= ](\d+)", args))
        servers.append(dict(name=w["metadata"]["name"], replicas=w["spec"].get("replicas", 0), gpu=gpu,
                            model=model[0] if model else "", tp=int(par.get("tensor", 1)),
                            pp=int(par.get("pipeline", 1)), image=c["image"].rsplit("/", 1)[-1][:40],
                            priority=t.get("priorityClassName", "")))
snap["llm_servers"] = servers
snap["llm_gpus"] = sum(s["replicas"] * sum(s["gpu"].values()) for s in servers)

# where each model server pod runs (heads and workers): the node's NetBox site (the dashboard's site slug) and GPU
by_node = {n["metadata"]["name"]: n["metadata"]["labels"] for n in nodes}
names = {s["name"] for s in servers}
place = []
for p in [p for ns in LLM_NS for p in items("pods", "-n", ns)]:
    owner = (p["metadata"].get("ownerReferences") or [{}])[0]
    wl = owner.get("name", "")
    if owner.get("kind") == "ReplicaSet":
        wl = wl.rsplit("-", 1)[0]
    lab = by_node.get(p["spec"].get("nodeName", ""), {})
    if wl not in names or p["status"].get("phase") != "Running" or not lab:
        continue
    place.append(dict(pod=p["metadata"]["name"], workload=wl,
                      site=lab.get("netbox.io/site") or lab.get("topology.kubernetes.io/zone", ""),
                      zone=lab.get("topology.kubernetes.io/zone", ""), gpu=lab.get("nvidia.com/gpu.product", "")))
snap["llm_placement"] = place

OUT.write_text(json.dumps(snap, indent=1))
print(f"{OUT}: {snap['nodes']} nodes, {snap['gpus']} GPUs in {snap['gpu_models']} models, {snap["cores"]} CPUs, "
      f"{len(apps)} Argo apps, {len(servers)} vLLM workloads on {snap['llm_gpus']} GPUs, "
      f"{sum(c['total'] for c in snap['ceph']) / 1e15:.1f} PB raw Ceph")
