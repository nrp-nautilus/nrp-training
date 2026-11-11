"""Live data for two operations slides -> data/metrics.json (read-only).

    python3 deck/metrics.py              # both
    python3 deck/metrics.py thanos       # only the Grafana panels
    python3 deck/metrics.py maddash      # only the perfSONAR grid

thanos:  seven days of cluster-wide CPU, memory and GPU use, hourly, from the thanos-querier service
         through the Kubernetes API server's service proxy (needs a kubeconfig that can proxy to the
         monitoring namespace, i.e. admin read). "Watching the Cluster" draws them as Grafana panels.
maddash: the all-to-all packet-loss grid from MaDDash's public JSON API at perfsonar.nrp-nautilus.io
         (no login). "Measuring the Network" draws it.

Each part keeps the other's data in the file, so they can be refreshed separately. Without the file,
the slides fall back to labeled illustrative values.
"""
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "metrics.json"
PROXY = "/api/v1/namespaces/monitoring/services/thanos-querier:9090/proxy/api/v1/query_range"
# The node-exporter recording rules are precomputed per node, so these stay cheap over a week; the raw
# rate(node_cpu_seconds_total) over every core of every node times out through the proxy.
QUERIES = {
    "cpu": "100 * avg(instance:node_cpu_utilisation:rate5m)",          # average over nodes
    "mem": "100 * avg(instance:node_memory_utilisation:ratio)",        # average over nodes
    "gpu": "avg(DCGM_FI_DEV_GPU_UTIL)",                                # average over GPUs
}
MADDASH = "https://perfsonar.nrp-nautilus.io/maddash/grids/Nautilus+Mesh+-+Latency+a2a+-+Loss"


def query(q, start, end, step):
    qs = urllib.parse.urlencode({"query": q, "start": start, "end": end, "step": step})
    r = subprocess.run(["kubectl", "get", "--raw", f"{PROXY}?{qs}", "--request-timeout=280s"],
                       capture_output=True, text=True, timeout=300)
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[:300])
    res = json.loads(r.stdout)["data"]["result"]
    return [[int(t), round(float(v), 2)] for t, v in res[0]["values"]] if res else []


def thanos():
    end = int(time.time()) // 3600 * 3600
    start = end - 7 * 86400
    out = {"start": start, "end": end, "step": 3600}
    for k, q in QUERIES.items():
        pts = []
        for a in range(start, end, 86400):          # a day per request keeps each query small
            pts += query(q, a, min(a + 86400 - 3600, end), 3600)
        out[k] = pts
        print(k, len(pts), "points, last", pts[-1] if pts else None)
    return out


def maddash():
    with urllib.request.urlopen(MADDASH, timeout=60) as f:
        d = json.load(f)
    # one status per cell: 0 loss <= 0.001%, 1 > 0.001%, 2 >= 0.1%, 3 no data; None on the diagonal
    grid = [[(min(h.get("status", 3) for h in cell) if cell else None) for cell in row] for row in d["grid"]]
    rows = [r["name"] if isinstance(r, dict) else r for r in d["rows"]]
    print("maddash", len(grid), "x", len(grid[0]), "updated", time.strftime("%d %b %Y", time.gmtime(d["lastUpdateTime"])))
    return {"rows": rows, "grid": grid, "labels": d["statusLabels"][:4], "updated": d["lastUpdateTime"]}


if __name__ == "__main__":
    parts = sys.argv[1:] or ["thanos", "maddash"]
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    if "thanos" in parts:
        data["thanos"] = thanos()
    if "maddash" in parts:
        data["maddash"] = maddash()
    OUT.write_text(json.dumps(data))
    print(OUT)
