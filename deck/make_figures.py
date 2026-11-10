"""Draw the deck's plots from data/ into figures/.

    python3 deck/make_figures.py

fleet_by_memory.png: GPUs by model, colored by memory per GPU, from data/gpu_fleet.csv
(written by snapshot_fleet.py). Style follows the HPC-CI webinar figures.
"""
import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)
DPI = 200
from datetime import date
SNAP_DATE = f"{date.fromisoformat((HERE / 'data' / 'SNAPSHOT').read_text().split()[0]):%-d %b %Y}"

INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
RAMP = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

mpl.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.family": "sans-serif",
    "font.sans-serif": ["Source Sans 3", "Source Sans Pro", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 12, "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.titlecolor": INK, "axes.titlepad": 10, "axes.labelsize": 12, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "xtick.labelsize": 11, "ytick.labelsize": 11,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "axes.edgecolor": BASE, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 11, "legend.labelcolor": INK2,
})

TIERS = [(17_000, "Up to 16 GB"), (25_000, "20–24 GB"), (50_000, "32–48 GB"), (10**9, "80 GB and up")]


def tier(mib):
    for i, (top, _) in enumerate(TIERS):
        if mib < top:
            return i
    return len(TIERS) - 1


def short(p):
    if "MIG-1g.10gb" in p:
        return "A100 slices (MIG, 10 GB)"
    for a, b in [("NVIDIA-", ""), ("GeForce-", ""), ("Tesla-", ""), ("-Max-Q-Workstation-Edition", ""),
                 ("-Generation", ""), ("-SXM4-80GB", " 80GB SXM"), ("-80GB-PCIe", " 80GB PCIe"), ("-80GB-HBM3", ""),
                 ("-PCIE-", " "), ("-SXM2-", " "), ("-NVL", "")]:
        p = p.replace(a, b)
    return p.replace("-", " ")


def load():
    with (HERE / "data" / "gpu_fleet.csv").open() as f:
        return [dict(r, gpus=int(r["gpus"]), memory_mib=int(r["memory_mib"])) for r in csv.DictReader(f)]


def fig_fleet():
    rows = load()
    total = sum(r["gpus"] for r in rows)
    top = sorted(rows, key=lambda r: -r["gpus"])[:15]
    rest = [r for r in rows if r not in top]
    labels = [short(r["product"]) for r in top] + [f"{len(rest)} other models"]
    vals = [r["gpus"] for r in top] + [sum(r["gpus"] for r in rest)]
    cols = [RAMP[tier(r["memory_mib"])] for r in top] + [BASE]
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    y = np.arange(len(labels))[::-1]
    ax.barh(y, vals, color=cols, height=0.72, edgecolor="white", linewidth=1.5)
    ax.set_yticks(y, labels)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    for yi, v in zip(y, vals):
        ax.text(v + max(vals) * 0.012, yi, f"{v:,}", va="center", fontsize=10.5, color=INK2)
    ax.set_xlim(0, max(vals) * 1.12)
    ax.set_xlabel(f"GPUs on the cluster, {SNAP_DATE} (kubectl node labels)")
    handles = [mpl.patches.Patch(color=RAMP[i], label=lab) for i, (_, lab) in enumerate(TIERS)]
    ax.legend(handles=handles, loc="lower right", title="Memory per GPU", title_fontsize=10.5, fontsize=10.5)
    ax.set_title(f"{total:,} GPUs across {len(rows)} models", fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / "fleet_by_memory.png", dpi=DPI)
    plt.close(fig)
    print("figures/fleet_by_memory.png")


def tier_table():
    """GPU counts per memory tier, for the slide that maps tiers to jobs."""
    rows = load()
    out = {lab: 0 for _, lab in TIERS}
    for r in rows:
        out[TIERS[tier(r["memory_mib"])][1]] += r["gpus"]
    return out


if __name__ == "__main__":
    fig_fleet()
    for k, v in tier_table().items():
        print(f"  {k:14s} {v:5d}")
