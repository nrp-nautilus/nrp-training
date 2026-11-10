"""Snapshot NRP's GPU fleet from the cluster into data/gpu_fleet.csv.

    python3 deck/snapshot_fleet.py      # needs kubectl with an NRP kubeconfig

One row per GPU model: physical GPUs (the nvidia.com/gpu.count label summed over nodes),
nodes, memory per GPU (MiB, from nvidia.com/gpu.memory) and architecture family. Rerun it
before the talk, then make_figures.py and build_deck.py, to refresh every GPU number.
"""
import csv
import json
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent

nodes = json.loads(subprocess.run(["kubectl", "get", "nodes", "-o", "json"], check=True,
                                  capture_output=True, text=True).stdout)["items"]
rows = defaultdict(lambda: {"gpus": 0, "nodes": 0, "memory_mib": 0, "family": ""})
all_nodes = len(nodes)
for n in nodes:
    lab = n["metadata"]["labels"]
    prod = lab.get("nvidia.com/gpu.product")
    if not prod:
        continue
    r = rows[prod]
    r["gpus"] += int(lab.get("nvidia.com/gpu.count", 0) or 0)
    r["nodes"] += 1
    r["memory_mib"] = max(r["memory_mib"], int(lab.get("nvidia.com/gpu.memory", 0) or 0))
    r["family"] = lab.get("nvidia.com/gpu.family", r["family"])

out = HERE / "data" / "gpu_fleet.csv"
with out.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["product", "gpus", "nodes", "memory_mib", "family"])
    for prod, r in sorted(rows.items(), key=lambda kv: -kv[1]["gpus"]):
        if r["gpus"]:
            w.writerow([prod, r["gpus"], r["nodes"], r["memory_mib"], r["family"]])
(HERE / "data" / "SNAPSHOT").write_text(f"{date.today().isoformat()} {all_nodes}\n")
print(f"{out}: {sum(r['gpus'] for r in rows.values()):,} GPUs on "
      f"{sum(r['nodes'] for r in rows.values())} GPU nodes ({all_nodes} nodes in all)")
