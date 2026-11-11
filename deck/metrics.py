"""Seven days of cluster-wide CPU, memory and GPU use from Thanos -> data/metrics.json (read-only).

    python3 deck/metrics.py

Queries the thanos-querier service through the Kubernetes API server's service proxy, so it needs
kubectl access that can proxy to the monitoring namespace (an admin kubeconfig). The "Watching the
Cluster" slide draws these as the Grafana panels; without the file it falls back to flat lines.
"""
import json
import subprocess
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "metrics.json"
PROXY = "/api/v1/namespaces/monitoring/services/thanos-querier:9090/proxy/api/v1/query_range"
QUERIES = {
    "cpu": '100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[10m])))',
    "mem": "100 * (1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes))",
    "gpu": "avg(DCGM_FI_DEV_GPU_UTIL)",
}


def query(q, start, end, step):
    qs = urllib.parse.urlencode({"query": q, "start": start, "end": end, "step": step})
    r = subprocess.run(["kubectl", "get", "--raw", f"{PROXY}?{qs}"], capture_output=True, text=True, timeout=300)
    d = json.loads(r.stdout)
    res = d["data"]["result"]
    return [[int(t), round(float(v), 2)] for t, v in res[0]["values"]] if res else []


if __name__ == "__main__":
    end = int(time.time()) // 3600 * 3600
    start = end - 7 * 86400
    out = {"start": start, "end": end, "step": 3600}
    for k, q in QUERIES.items():
        out[k] = query(q, start, end, 3600)
        print(k, len(out[k]), "points", out[k][-1] if out[k] else "")
    OUT.write_text(json.dumps(out))
    print(OUT)
