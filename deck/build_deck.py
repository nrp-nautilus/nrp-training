"""Build the UCLA Health Research Tech Talk deck on the SDSC template.

    python3 deck/snapshot_fleet.py          # optional: refresh GPU numbers from the cluster (needs kubectl)
    python3 deck/make_figures.py            # data/ -> figures/
    python3 deck/build_deck.py              # -> slides/ucla-health-nrp.pptx
    python3 deck/build_deck.py alts OUT     # the A/B/C versions of the "What is NRP?" and policy slides

Style: short topic titles with no subtitles, plain bullets, one real visual per slide (a
screenshot, a chart, a diagram or code), the template's own section headers. "Access Methods"
is a fake animation: several copies of one slide, paged through in the PDF, all showing the
same slide number.

Needs python-pptx, Pillow, lxml and matplotlib. The layout kit (deckkit.py) and template come
from the SDSC HPC-CI webinar deck. Speaker notes on every slide start with a planned time.
After you edit the .pptx in PowerPoint, treat it as the source; rerunning this overwrites it.
"""
import csv
import sys
from datetime import date
from pathlib import Path

from pptx.util import Inches, Pt

from deckkit import (BLUE, BODY, CARD, GOLD, LIGHT, MONO, MUTED, NAVY, ORANGE, SANS, SANS_BLACK, WHITE, Deck, P,
                     X0, fill_tf)
from sweep import RUN_CAPTION, RUN_CMD, RUN_JOB, RUN_WAYS, SWEEP, SWEEP_T, apply_lines, get_pods

HERE = Path(__file__).resolve().parent
TRAINING = HERE.parent
IMG = HERE / "assets" / "images"
FIG = HERE / "figures"
ALTS = len(sys.argv) > 1 and sys.argv[1] == "alts"
OUT = Path(sys.argv[2]) if ALTS else TRAINING / "slides" / "ucla-health-nrp.pptx"
V4 = "A"     # "What is NRP?": A bullets + map, B map-forward, C numbers table
V17 = "B"    # GPU policy:     A rules list, B do / don't, C rules -> YAML

# ── numbers from the fleet snapshot ─────────────────────────────────────────────────
SNAP_DAY, SNAP_NODES = (HERE / "data" / "SNAPSHOT").read_text().split()
SNAP = f"{date.fromisoformat(SNAP_DAY):%-d %b %Y}"
with (HERE / "data" / "gpu_fleet.csv").open() as f:
    FLEET = [dict(r, gpus=int(r["gpus"]), memory_mib=int(r["memory_mib"])) for r in csv.DictReader(f)]
GPUS = sum(r["gpus"] for r in FLEET)
GPU_MODELS = len(FLEET)
NODES = int(SNAP_NODES)
TIERS = [(17_000, "Up to 16 GB"), (25_000, "20–24 GB"), (50_000, "32–48 GB"), (10**9, "80 GB and up")]


def tier_count(i):
    lo = TIERS[i - 1][0] if i else 0
    return sum(r["gpus"] for r in FLEET if lo <= r["memory_mib"] < TIERS[i][0])


T16, T24, T48, T80 = (tier_count(i) for i in range(4))

deck = Deck(HERE / "assets" / "sdsc_template.pptx")
TOP = 1.45          # content top, just under the title
FOOT = "NRP"


# ── helpers ─────────────────────────────────────────────────────────────────────────
def bullets(s, x, y, w, h, items, size=20, color=BODY, gap=9):
    """Plain bullets. An item is a string, or (string, 1) for a sub-bullet."""
    paras = []
    for it in items:
        text, lvl = (it, 0) if isinstance(it, str) else it
        paras.append(P(text, size=size if lvl == 0 else size - 3, color=color, bullet=True, level=lvl,
                       accent=NAVY if color == BODY else GOLD, before=(gap if lvl == 0 else 3) if paras else 0,
                       line=1.04))
    return s.text(x, y, w, h, paras)


def heading(s, x, y, w, text, size=21, color=NAVY):
    return s.text(x, y, w, 0.45, P(text, size=size, bold=True, color=color))


def section(title, notes):
    s = deck.slide(layout="Section Header - Reverse", section=FOOT)
    for ph in list(s.s.placeholders):
        if ph.placeholder_format.idx != 0:
            ph._element.getparent().remove(ph._element)
    tf = s.s.shapes.title.text_frame
    tf.text = ""
    tf.paragraphs[0].add_run().text = title
    s.notes(notes)
    return s


def slide(title, cont=False):
    return deck.slide(title=title, section=FOOT, cont=cont)


DIM_FILL, DIM_TEXT, DIM_SUB, DIM_LINE = "F3F4F6", "A3ABB6", "B9C0C9", "D5DAE0"


def box(s, x, y, w, h, head, sub=None, state="normal", head_size=16, sub_size=12.5, mono_sub=False, align="c"):
    """A plain rounded box with a bold line and an optional second line. state: normal, active, dim."""
    fill, hc, sc, line = {"normal": (CARD, NAVY, BODY, "C9D4E3"), "active": (NAVY, WHITE, LIGHT, None),
                          "dim": (DIM_FILL, DIM_TEXT, DIM_SUB, "E3E6EA")}[state]
    s.rect(x, y, w, h, fill=fill, radius=0.08, line=line)
    paras = [P(head, size=head_size, bold=True, color=hc, align=align, line=0.95)]
    if sub:
        paras.append(P(sub, size=sub_size, color=sc, align=align, line=0.98, before=2,
                       font=MONO if mono_sub else SANS))
    s.text(x + 0.08, y, w - 0.16, h, paras, anchor="m")


def arrow(s, x1, y1, x2, y2, state="normal"):
    color, width = {"normal": (MUTED, 1.5), "active": (BLUE, 2.5), "dim": (DIM_LINE, 1.25)}[state]
    s.line(x1, y1, x2, y2, color=color, width=width)


# ═════════════════════════════════════════════════════════════════════════════════════
# The two slides with alternative layouts
# ═════════════════════════════════════════════════════════════════════════════════════
NOTES_4 = f"""
[0:02] NRP is a partnership that runs one national Kubernetes cluster, called Nautilus. SDSC, Nebraska and MGHPCC run the operations; NSF funds it; and more than seventy institutions contribute the hardware. UCLA is one of them. It's free for non-commercial research and education, and you sign in with your UCLA login.

The map is where the hardware lives. As of this week that's {GPUS:,} GPUs in {GPU_MODELS} different models on {NODES} nodes, petabytes of storage, and services on top: JupyterHub, GitLab, S3, a vector database and hosted AI models.

The model behind it is a potluck: a campus contributes nodes, keeps priority on them, and when they're idle everyone else can use them. One team operates the whole stack, so a campus with hardware but no operations team can still take part.
"""


NOTES_4_STEPS = [
    """[0:02] NRP is a partnership that runs one national Kubernetes cluster, called Nautilus. Three sites run the operations: SDSC at UC San Diego, the University of Nebraska–Lincoln, and MGHPCC in Massachusetts. NSF funds it.""",
    """More than seventy institutions contribute the hardware, and UCLA is one of them: there are UCLA nodes in the cluster today.""",
    f"""Here's the rest. Every pin is a real site, from the dashboard's own data. As of this week that's {GPUS:,} GPUs in {GPU_MODELS} different models on {NODES} nodes, petabytes of storage, and services on top: JupyterHub, GitLab, S3, a vector database and hosted AI models. A few more sites are off this map, in Hawaii, Guam, Korea, Brazil and Europe.

The model behind it is a potluck: a campus contributes nodes, keeps priority on them, and when they're idle everyone else can use them. One team operates the whole stack, so a campus with hardware but no operations team can still take part.""",
    """It's free for non-commercial research and education, and you sign in with your UCLA login.""",
]


def what_is_nrp(v):
    if v == "A":      # bullets left, the site map right; a fake animation: the operators, UCLA, then every site
        sys.path.insert(0, str(HERE))
        from make_map import geometry, offmap_note
        note = offmap_note(geometry(890))
        items = [["A national **Kubernetes** cluster, **Nautilus**, for research and education",
                  "Run by SDSC (UC San Diego), Nebraska–Lincoln and MGHPCC; funded by NSF"],
                 ["Hardware contributed by 70+ institutions, UCLA among them"],
                 ["Scale today:", (f"{NODES} nodes", 1), (f"{GPUS:,} GPUs in {GPU_MODELS} models", 1),
                  ("Petabytes of storage", 1)],
                 ["Free for non-commercial research and education"]]
        for step in range(4):
            s = slide("What is NRP?", cont=step > 0)
            bullets(s, X0, TOP + 0.15, 5.7, 5.2, [b for grp in items[:step + 1] for b in grp])
            s.link(6.55, TOP + 0.05, 6.18, 0.3, "https://dash.nrp-nautilus.io", size=14, align="r")
            s.image(FIG / f"map_{min(step, 2)}.png", 6.55, TOP + 0.45, 6.18, 4.1, align="r", valign="t")
            if step >= 2:
                s.text(6.55, TOP + 4.6, 6.18, 0.5, [P("Site locations from the NRP dashboard, 10 Nov 2026", size=12,
                                                      color=MUTED, align="r"),
                                                    P(note, size=12, color=MUTED, align="r")])
            s.text(X0, 6.74, 7.0, 0.2, P(f"GPUs and nodes: cluster snapshot, {SNAP}", size=10, color=MUTED))
            s.notes(NOTES_4_STEPS[step])
        return
    s = slide("What is NRP?")
    if v == "B":      # map-forward: one sentence, the map large, one line of numbers
        s.text(X0, TOP + 0.05, 12.1, 0.6, P("A national Kubernetes cluster for research and education, on hardware "
                                             "that 70+ institutions contribute. Free for non-commercial use.",
                                             size=20, color=BODY, line=1.02))
        s.image(IMG / "dash_map.png", X0, TOP + 0.8, 12.13, 3.85, align="c", valign="t", border="DDE8F2")
        s.text(X0, 6.2, 12.13, 0.5, P(f"{NODES} nodes   ·   {GPUS:,} GPUs in {GPU_MODELS} models   ·   petabytes of "
                                      "storage   ·   JupyterHub, hosted LLMs, S3", size=20, bold=True, color=NAVY,
                                      align="c"))
    else:             # numbers as a plain table beside short bullets, no map
        bullets(s, X0, TOP + 0.15, 6.2, 5.0, [
            "A national **Kubernetes** cluster, **Nautilus**, for research and education",
            "Run by SDSC (UC San Diego), Nebraska–Lincoln and MGHPCC; funded by NSF",
            "Campuses contribute hardware and keep priority on it; idle capacity is shared",
            "One team operates everything from the firmware up",
            "Free for non-commercial research and education; sign in with your UCLA login"])
        rows = [["NRP today", ""], ["Nodes", f"{NODES}"], ["GPUs", f"{GPUS:,}"], ["GPU models", f"{GPU_MODELS}"],
                ["Contributing institutions", "70+"], ["Storage", "petabytes (Ceph, S3)"],
                ["Services", "JupyterHub, hosted LLMs, GitLab, vector DB"]]
        s.table(7.25, TOP + 0.2, 5.48, [2.4, 3.1], rows, size=16, head_size=16, row_h=0.62)
    s.text(X0, 6.74, 7.0, 0.2, P(f"GPUs and nodes: cluster snapshot, {SNAP}", size=10, color=MUTED))
    s.notes(NOTES_4)


NOTES_17 = """
[0:21] Before you run anything, the policy, because this is a shared cluster and the rules are what keep GPUs available. The short version: if you request something, use it, and free it when you're done.

Concretely: GPUs you request should be more than 40% utilized; CPU use should be between 20 and 200% of what you asked for, and memory between 20 and 150%. Limits have to be within 20% of requests. Admins watch utilization, and namespaces that keep requesting resources they don't use get banned. Putting sleep in a Job, to hold a GPU, is a bannable offense on its own.

Interactive pods, ones with no Job or Deployment behind them, are deleted after six hours and can have at most two GPUs. A100s are available through a request form; H100s and H200s are reserved, but you can borrow idle ones with the opportunistic priority class if your job can be preempted. The full policy page is linked.
"""


def gpu_policy(v):
    url = "https://nrp.ai/documentation/userdocs/start/policies/"
    if v == "A":      # your "Pause for Policy" slide, with the current numbers
        s = slide("Pause for Policy")
        s.link(X0, TOP + 0.05, 9.0, 0.3, url, size=14)
        bullets(s, X0, TOP + 0.55, 6.4, 5.0, [
            "**Golden rule:** if you request it, use it; free it when you're done",
            "**Use what you request:**",
            ("GPU: more than 40% utilized", 1), ("CPU: 20–200% of the request", 1), ("Memory: 20–150% of the request", 1),
            "**Limits** within 20% of requests",
            "**Bannable:** `sleep` in a Job"])
        bullets(s, 7.25, TOP + 0.55, 5.48, 5.0, [
            "Interactive pods: deleted after 6 hours, at most 2 GPUs",
            "Batch work goes in a **Job** that exits when it's done",
            "A100s by request: nrp.ai/reservations",
            "H100s and H200s are reserved; borrow idle ones with `priorityClassName: opportunistic`",
            "Keep data on a persistent volume, not the pod's disk"], size=18)
    elif v == "B":    # do / don't
        s = slide("Using GPUs Fairly")
        heading(s, X0, TOP + 0.1, 5.9, "Do")
        bullets(s, X0, TOP + 0.6, 5.9, 4.6, [
            "Run batch work as a **Job** that exits",
            "Request what you'll use; keep limits within 20% of requests",
            "Keep data on a persistent volume or in S3",
            "Run a sweep as many one-GPU jobs",
            "Borrow idle A100/H100s with `priorityClassName: opportunistic`, and checkpoint"], size=19)
        heading(s, 6.83, TOP + 0.1, 5.9, "Don't")
        bullets(s, 6.83, TOP + 0.6, 5.9, 4.6, [
            "Leave a notebook holding a GPU overnight",
            "Put `sleep` in a Job to keep a GPU (bannable)",
            "Ask for 4 GPUs \"just in case\": use must stay above 40%",
            "Keep results on the pod's own disk; it vanishes with the pod"], size=19)
        s.link(X0, 6.3, 9.0, 0.3, url, size=14)
    else:             # each rule next to what it means in your YAML
        s = slide("GPU Policy in Practice")
        rows = [["Rule", "In your job"],
                ["Free the GPU when you're done", "kind: Job  ·  ttlSecondsAfterFinished: 3600"],
                ["GPUs more than 40% utilized", "nvidia.com/gpu: 1, not 4 \"just in case\""],
                ["Limits within 20% of requests", "requests and limits the same"],
                ["No sleep in Jobs (bannable)", "the command runs your script, then exits"],
                ["Keep data", "a persistentVolumeClaim, or S3"],
                ["Big GPUs", "A100: nrp.ai/reservations  ·  idle ones: priorityClassName: opportunistic"]]
        s.table(X0, TOP + 0.1, 12.13, [4.2, 7.9], rows, size=16, head_size=16, row_h=0.62, mono_cols=(1,))
        s.link(X0, 6.3, 9.0, 0.3, url, size=14)
    s.notes(NOTES_17)


# ═════════════════════════════════════════════════════════════════════════════════════
# Diagram slides
# ═════════════════════════════════════════════════════════════════════════════════════
def kubernetes_intro():
    s = slide("Kubernetes and Containers")
    bullets(s, X0, TOP + 0.15, 5.3, 5.1, [
        "**Container image:** your code plus everything it needs (Python, PyTorch, CUDA), in one package",
        "Runs the same on a laptop, a cluster or the cloud",
        "**Kubernetes** runs containers across many machines",
        "You say what you need (CPUs, memory, a GPU); it finds a machine that has it",
        f"NRP is one Kubernetes cluster: {NODES} nodes"], size=19)
    sx, sw = 6.25, 2.55
    s.text(sx - 0.1, TOP + 0.2, sw + 0.2, 0.4, P("Container image", size=17, bold=True, color=ORANGE, align="c"))
    layers = [("train.py", "your code"), ("PyTorch, NumPy", None), ("CUDA libraries", None), ("Linux", None)]
    for i, (head, sub) in enumerate(layers):
        box(s, sx, TOP + 0.75 + i * 0.68, sw, 0.6, head, sub, state="active" if i == 0 else "normal",
            head_size=15, sub_size=11.5)
    img = s.rect(sx - 0.1, TOP + 0.63, sw + 0.2, 2.86, fill=None, radius=0.06, line=ORANGE)
    img.line.width = Pt(3)
    s.text(sx - 0.1, TOP + 3.58, sw + 0.2, 0.5, P("built once, from a Dockerfile", size=14, color=BODY, align="c"))
    arrow(s, sx + sw + 0.1, TOP + 2.1, 9.45, TOP + 2.1)
    cx, cw = 9.55, 3.18
    s.rect(cx, TOP + 0.15, cw, 4.35, fill=None, radius=0.04, line="B9C7D8")
    s.text(cx + 0.15, TOP + 0.22, cw - 0.3, 0.4, P("Kubernetes cluster", size=15, bold=True, color=NAVY))
    nodes = [("Node", "64 CPU cores", False), ("Node", "8 × A10 GPUs", True), ("Node", "4 × A100 GPUs", False)]
    for i, (head, sub, ours) in enumerate(nodes):
        y = TOP + 0.75 + i * 1.2
        s.rect(cx + 0.2, y, cw - 0.4, 1.0, fill=WHITE, radius=0.06, line="C9D4E3")
        s.text(cx + 0.35, y + 0.08, 1.6, 0.85, [P(head, size=14, bold=True, color=NAVY),
                                                 P(sub, size=12, color=BODY)], anchor="m")
        if ours:
            chip = s.rect(cx + 1.75, y + 0.2, 1.05, 0.6, fill="FDEBE3", radius=0.1, line=ORANGE)
            chip.line.width = Pt(2.5)
            s.text(cx + 1.75, y + 0.2, 1.05, 0.6, P("your container", size=11, bold=True, color=NAVY, align="c",
                                                     line=0.9), anchor="m")
    s.text(cx, TOP + 4.55, cw, 0.6, P("the scheduler picks a node with a free GPU", size=13, color=MUTED,
                                      align="c"))
    s.notes("""
[0:04] NRP is a Kubernetes cluster, so one slide on what that means, and then it mostly disappears behind the tools.

Your software runs in a container. Start with the pieces your work needs: your code, Python and PyTorch, the CUDA libraries, down to the operating system. A container image packages all of that into one thing. You build it once, from a short recipe called a Dockerfile, or use one someone else built, and it runs the same on your laptop, on NRP or in the cloud.

Kubernetes runs those containers across many machines. You don't pick the machine: you say what you need, two CPUs, some memory, one GPU, and the scheduler finds a node that has it free. NRP is one such cluster, with a few hundred nodes.
""")


# access methods, as a fake animation: an overview, then one build per door
LANES = [
    ("llm", [("Hosted LLMs", "browser chat or an API key"), ("AI gateway", "checks your token, routes"),
             ("Model servers", "open-weight models on NRP GPUs")]),
    ("jh", [("JupyterHub", "log in, pick an image and a GPU"), ("Your notebook server", "a container started for you"),
            ("A CPU or GPU node", "chosen by Kubernetes")]),
    ("k8s", [("Kubernetes", "kubectl apply -f job.yaml"), ("Scheduler", "finds a node with what you asked for"),
             ("Your pods", "run, write results, exit")]),
]


def access_diagram(s, active=None):
    ly, lh, gap = TOP + 0.15, 0.68, 0.14
    s.rect(X0, ly, 1.05, 3 * lh + 2 * gap, fill=NAVY, radius=0.08)
    s.text(X0, ly, 1.05, 3 * lh + 2 * gap, P("You", size=18, bold=True, color=WHITE, align="c"), anchor="m")
    xs = [(2.2, 3.15), (5.9, 3.15), (9.58, 3.15)]
    for i, (key, boxes) in enumerate(LANES):
        y = ly + i * (lh + gap)
        st = "normal" if active is None else ("active" if key == active else "dim")
        arrow(s, X0 + 1.05, y + lh / 2, xs[0][0], y + lh / 2, st)
        for j, ((head, sub), (bx, bw)) in enumerate(zip(boxes, xs)):
            box(s, bx, y, bw, lh, head, sub, state=st, head_size=15, sub_size=11.5,
                mono_sub=(key == "k8s" and j == 0))
            if j < 2:
                arrow(s, bx + bw, y + lh / 2, xs[j + 1][0], y + lh / 2, st)
    return ly + 3 * lh + 2 * gap


def batch_jobs(s, y0):
    """Batch jobs as you'd see them: kubectl apply and get pods in a terminal, and where the pods landed."""
    s.text(X0, y0, 5.6, 0.35, P("Your jobs", size=14, bold=True, color=NAVY))
    s.code(X0, y0 + 0.4, 5.75, 2.2, "\n".join(apply_lines() + get_pods(3)), size=11, min_size=10)
    arrow(s, X0 + 5.82, y0 + 1.27, 6.88, y0 + 1.27)
    nodes = [("GPU node · 4 × A10", ["lr-0.1", "lr-0.01", None, None]),
             ("GPU node · 4 × RTX 3090", [None, None, None, None])]
    for k, (head, slots) in enumerate(nodes):
        nx = 6.95 + k * 2.95
        s.rect(nx, y0 + 0.35, 2.78, 1.85, fill=WHITE, radius=0.05, line="B9C7D8")
        s.text(nx + 0.12, y0 + 0.4, 2.6, 0.4, P(head, size=12.5, bold=True, color=NAVY))
        for j, who in enumerate(slots):
            gx = nx + 0.12 + j * 0.65
            fill, txt, col = (NAVY, who, WHITE) if who else ("DDE1E6", "busy", "6B7480")
            s.rect(gx, y0 + 0.95, 0.58, 0.95, fill=fill, radius=0.08)
            s.text(gx, y0 + 0.95, 0.58, 0.95, P(txt, size=9.5, bold=True, color=col, align="c", line=0.9),
                   anchor="m")
    s.text(6.95, y0 + 2.3, 5.78, 0.5, P("lr-0.001 waits in Pending until a GPU frees up; a finished job releases "
                                         "its GPU", size=13, color=MUTED))


def access_methods():
    notes = {
        None: """[0:05] Unlike a traditional HPC cluster, there's no login node where you SSH in and submit to a queue. There are three ways in, depending on how much infrastructure you want to touch. I'll step through them.""",
        "llm": """[0:06] The lowest barrier: the hosted language models. You chat in a browser, or call them from your own code with a token. Your request goes through a gateway that checks the token and routes it to a model server running on NRP's GPUs. Nothing for you to run.""",
        "jh": """[0:06] JupyterHub: you log in, pick an image and how many CPUs, how much memory and whether you want a GPU, and Kubernetes starts a notebook server for you on a node that has them. Most people start here, and it's where the demo runs.""",
        "k8s": """[0:07] And Kubernetes itself: you describe a job in a short YAML file and submit it with kubectl. Here that's a folder with three training jobs, a small learning-rate sweep. kubectl get pods shows what the scheduler did: two found a free GPU and are Running, and the third waits in Pending. When the first one finishes it gives its GPU back, and the waiting job takes it. That's how you run a sweep: many small jobs, run as GPUs become free.""",
    }
    for i, key in enumerate([None, "llm", "jh", "k8s"]):
        s = slide("Access Methods", cont=i > 0)
        bottom = access_diagram(s, key) + 0.35
        if key is None:
            s.text(X0, bottom + 0.1, 12.13, 1.6, [
                P("No login node and no batch queue: pick the door that matches how much infrastructure you want "
                  "to touch.", size=20, color=BODY, line=1.04),
                P("Most people start with JupyterHub or the hosted LLMs.", size=20, color=BODY, before=10)])
        elif key == "llm":
            s.image(IMG / "openwebui_crop.png", X0, bottom, 4.6, 2.5, align="l", valign="t", border="3A3A3A")
            s.code(5.55, bottom, 7.18, 1.95, """from openai import OpenAI
client = OpenAI(base_url="https://ellm.nrp-nautilus.io/v1",
                api_key=TOKEN)        # from nrp.ai/llmtoken
client.chat.completions.create(model="gpt-oss",
    messages=[{"role": "user", "content": "Hi"}])""", size=12.5)
            s.text(5.55, bottom + 2.05, 7.18, 0.45, P("In the browser at nrp-openwebui.nrp-nautilus.io, or from "
                                                     "any code that speaks the OpenAI API", size=14, color=MUTED))
        elif key == "jh":
            s.image(IMG / "jupyterlab_gpu.png", X0, bottom, 4.6, 2.5, align="l", valign="t")
            bullets(s, 5.55, bottom + 0.05, 7.18, 2.5, [
                "Log in with your campus account through CILogon",
                "Choose an image, CPUs, memory and a GPU type",
                "NRP's hubs: jupyterhub-west.nrp-nautilus.io and jupyterhub-east.nrp-nautilus.io",
                "Today's demo: jh-training.nrp-nautilus.io"], size=17, gap=7)
        else:
            batch_jobs(s, bottom - 0.05)
        s.notes(notes[key])


def what_nrp_is_for():
    s = slide("What NRP Is For")
    segs = [("Public or synthetic data", "public datasets, simulations, benchmark and synthetic data", "D3EEE1"),
            ("De-identified data", "if your IRB and data use agreement allow it", "E6F1D3"),
            ("Protected health information", "PHI or identifiable patient data, including in LLM prompts", "F6D6D3")]
    w = 12.13 / 3
    y = TOP + 0.75
    s.line(X0 + 0.05, y - 0.18, X0 + 2 * w - 0.05, y - 0.18, color="1B7F55", width=2.5, arrow=False)
    s.text(X0, y - 0.62, 2 * w, 0.4, P("OK on NRP", size=17, bold=True, color="1B7F55", align="c"))
    s.line(X0 + 2 * w + 0.05, y - 0.18, X0 + 3 * w - 0.05, y - 0.18, color="B3261E", width=2.5, arrow=False)
    s.text(X0 + 2 * w, y - 0.62, w, 0.4, P("Not on NRP", size=17, bold=True, color="B3261E", align="c"))
    for i, (head, sub, fill) in enumerate(segs):
        x = X0 + i * w
        s.rect(x + 0.03, y, w - 0.06, 0.85, fill=fill, radius=0.06)
        s.text(x + 0.1, y, w - 0.2, 0.85, P(head, size=18, bold=True, color=NAVY, align="c"), anchor="m")
        s.text(x + 0.15, y + 0.95, w - 0.3, 0.8, P(sub, size=15, color=BODY, align="c", line=1.02))
    s.text(X0, TOP + 2.85, 12.13, 0.4, P("Good uses", size=19, bold=True, color=NAVY))
    s.text(X0, TOP + 3.3, 12.13, 0.5, P("model development and training  ·  image analysis  ·  simulation  ·  "
                                        "teaching  ·  LLMs on non-sensitive text", size=18, color=BODY))
    s.text(X0, TOP + 3.95, 12.13, 0.45, P("Also not for: commercial work, or services that need guaranteed uptime "
                                          "(it is a shared, best-effort cluster)", size=16, color=MUTED))
    s.text(X0, 5.95, 12.13, 0.6, P("NRP is **not HIPAA compliant**. Keep PHI in UCLA Health's approved environments.",
                                   size=21, color="B3261E"))
    s.notes("""
[0:08] Given the audience, this slide matters. Think of your data on a spectrum. Public and synthetic data, simulations, benchmark sets: all fine on NRP. De-identified data is fine too, as long as your IRB and your data use agreement allow it to be processed outside UCLA. Protected health information is not: NRP is not HIPAA compliant, and that includes pasting identifiable patient data into a prompt to the hosted models.

What it's great for: developing and training models, image analysis, simulation, teaching, and trying open-weight language models on text that isn't sensitive. It's also not for commercial work, and since it's a shared, best-effort cluster, not for a service that has to be up at three in the morning.
""")


def namespaces():
    s = slide("What is a Namespace?")
    bullets(s, X0, TOP + 0.15, 4.75, 5.1, [
        "Your group's workspace on the cluster",
        "One per lab, project or course; the PI or instructor is its admin and adds members",
        "Needed for GPU jobs, storage, your own JupyterHub, and **API access** to the hosted LLMs",
        "Not needed to chat with the LLMs in the browser",
        "What's inside is visible only to its members"], size=18)
    cx, cw = 5.7, 7.03
    s.rect(cx, TOP + 0.1, cw, 5.1, fill=None, radius=0.03, line="B9C7D8")
    s.text(cx + 0.2, TOP + 0.18, 4.0, 0.4, P("Nautilus cluster", size=15, bold=True, color=NAVY))
    spaces = [("lab-smith", "Dr. Smith (admin) and 3 students", "GPU jobs · a data volume · LLM tokens", "normal"),
              ("bio-course", "the instructor (admin) and 40 students", "a course JupyterHub · shared datasets",
               "normal"),
              ("another-lab", "their members only", "you can't see their jobs or data", "dim")]
    for i, (name, people, inside, st) in enumerate(spaces):
        y = TOP + 0.7 + i * 1.47
        fill, nc, tc, line = ((CARD, NAVY, BODY, "C9D4E3") if st == "normal" else
                              (DIM_FILL, DIM_TEXT, DIM_SUB, "E3E6EA"))
        s.rect(cx + 0.2, y, cw - 0.4, 1.27, fill=fill, radius=0.06, line=line)
        s.text(cx + 0.4, y, 2.0, 1.27, P(name, size=16, bold=True, color=nc, font=MONO), anchor="m")
        s.text(cx + 2.45, y + 0.1, cw - 2.85, 1.07, [P(people, size=15, bold=True, color=nc, line=1.0),
                                                     P(inside, size=14, color=tc, before=4, line=1.0)], anchor="m")
    s.notes("""
[0:09] The one Kubernetes idea you need today: a namespace. Think of it as your group's workspace on the cluster. A lab, a project or a course gets one; a PI or instructor owns it and adds the members.

You need a namespace to run GPU jobs, to keep data on the cluster, to run your own JupyterHub, and to get API access to the hosted language models; the token page ties your usage to a namespace. You don't need one to chat with the models in the browser.

And it's private: what you create inside, your jobs and your data volumes, is visible only to the namespace's members. Another lab next door can't see into yours, and you can't see into theirs.
""")


def talking_to_cluster():
    s = slide("Talking to the Cluster")
    steps = [("Your laptop", "kubectl + ~/.kube/config"), ("CILogon", "your UCLA login, once"),
             ("Nautilus API", "checks who you are"), ("Your namespace", "jobs, pods, data")]
    bw, gap = 2.75, 0.38
    for i, (head, sub) in enumerate(steps):
        x = X0 + i * (bw + gap)
        box(s, x, TOP + 0.15, bw, 0.78, head, sub, state="active" if i == 0 else "normal", head_size=15,
            sub_size=12, mono_sub=(i == 0))
        if i < 3:
            arrow(s, x + bw, TOP + 0.54, x + bw + gap, TOP + 0.54)
    s.text(X0, TOP + 1.35, 5.9, 3.9, [
        P("1.  Install **kubectl** and the **kubelogin** plugin", size=18, color=BODY, line=1.04),
        P("2.  Download your config from **nrp.ai/config**, save it as ~/.kube/config", size=18, color=BODY,
          before=12, line=1.04),
        P("3.  Run any kubectl command: a browser opens for the UCLA login", size=18, color=BODY, before=12,
          line=1.04),
        P("4.  Work in your namespace", size=18, color=BODY, before=12),
        P("On the training JupyterHub this is already set up.", size=16, color=MUTED, before=18)])
    s.code(6.83, TOP + 1.35, 5.9, 3.55, """# one-time setup
mkdir -p ~/.kube
curl -o ~/.kube/config -fSL https://nrp.ai/config

# first command: a browser opens for CILogon
kubectl get pods -n my-lab
No resources found in my-lab namespace.

# make my-lab your default namespace
kubectl config set contexts.nautilus.namespace my-lab""", size=12.5)
    s.link(6.83, TOP + 5.0, 5.9, 0.3, "https://nrp.ai/documentation/userdocs/start/getting-started/", size=12)
    s.notes("""
[0:12] Once you're in a namespace, you talk to the cluster with kubectl, the Kubernetes command-line tool. Setup is one time: install kubectl and the kubelogin plugin, download your config file from nrp.ai/config, and save it as .kube/config in your home folder.

The first time you run a command, a browser window opens for CILogon, you log in with UCLA, and from then on kubectl just works; the token renews itself. "No resources found" is the good answer: it means you have access and nothing running yet. Set your namespace as the default and you can stop typing -n.

On the training JupyterHub all of this is already done, which is why the demo can skip it.
""")


def organizing_groups():
    s = slide("Organizing Groups at UCLA")
    top_x, top_w = 0.9, 6.3
    s.rect(top_x + 1.15, TOP + 0.3, 4.0, 0.95, fill=NAVY, radius=0.08)
    s.text(top_x + 1.25, TOP + 0.3, 3.8, 0.95, [P("UCLA group", size=19, bold=True, color=WHITE, align="c",
                                                  line=0.95),
                                                P("a department, or IT", size=13.5, color=LIGHT, align="c")],
           anchor="m")
    kids = [("Lab A", "a PI and students"), ("Lab B", "its own data"), ("Course", "a class hub"),
            ("Operations", "shared tools")]
    kw = 1.42
    for i, (head, sub_) in enumerate(kids):
        x = top_x + i * (kw + 0.21)
        s.line(top_x + top_w / 2, TOP + 1.25, x + kw / 2, TOP + 2.0, color=MUTED, width=1.5, arrow=False)
        s.rect(x, TOP + 2.0, kw, 0.95, fill=CARD, radius=0.08, line="B9C7D8")
        s.text(x + 0.05, TOP + 2.0, kw - 0.1, 0.95, [P(head, size=16, bold=True, color=NAVY, align="c", line=0.95),
                                                      P(sub_, size=12.5, color=BODY, align="c")], anchor="m")
    s.text(top_x, TOP + 3.4, top_w, 1.6, P("Data lives on volumes inside a namespace, so each lab's data is visible "
                                           "only to its members.", size=16, color=MUTED, line=1.04))
    bullets(s, 7.6, TOP + 0.25, 5.13, 5.0, [
        "Namespaces can be nested under a campus-level group",
        "Its admins create namespaces for labs and courses, and name their admins",
        "Fresno State does this through central IT and HPC staff",
        "UCLA has no campus-level admin yet: a department or group could take that role"], size=18)
    s.notes("""
Backup, for questions about campus organization. Namespaces can be nested. A campus-level group, say a department or an IT group, sits at the top; its admins create namespaces for labs, courses or an operations team, and appoint admins for each. At Fresno State, central IT and HPC staff manage the campus group and the groups under it.

UCLA doesn't have a designated campus-level admin yet. A department, or a group like Clifford's, could request a namespace, become its admin, and create subgroups. The benefit is access control: data lives on volumes inside a namespace, so each lab's data is visible only to its own members.
""")


def using_llms():
    shots = [("claude_code_nrp.png", "Claude Code on NRP's gpt-oss, asked about the demo's GPU job"),
             ("opencode_nrp.png", "opencode on NRP's qwen3, same question")]
    shots = [(f, c) for f, c in shots if (IMG / f).exists()] or [("opencode_crop.png", "opencode on an NRP model")]
    notes = ["""[0:23] Four ways to use them. The easiest is the browser: Open WebUI at nrp-openwebui. Sign in with your NRP login and pick any model; it's the best way to compare models or to give non-programmers access. Second, code: the standard OpenAI Python library works unchanged; you set the base URL to NRP's and use a token from nrp.ai/llmtoken. Third, Jupyter AI inside JupyterHub, which is what I'll demo.

And fourth, coding agents. This is Claude Code, the same tool many of you know, running on gpt-oss served by NRP, through NRP's Anthropic-compatible endpoint. I asked it about the GPU job file from the demo.""",
             """[0:24] And the same question in opencode, an open-source coding agent, on NRP's qwen3. Both answers are right, and both took seconds. The NRP docs have tested configurations for these and several other tools."""]
    for i, (f, cap) in enumerate(shots):
        s = slide("Using the LLMs", cont=i > 0)
        bullets(s, X0, TOP + 0.15, 3.85, 5.1, [
            "**In the browser:** Open WebUI",
            ("nrp-openwebui.nrp-nautilus.io", 1),
            "**From code:** the standard OpenAI library; token from nrp.ai/llmtoken",
            "**In JupyterHub:** Jupyter AI (in the demo)",
            "**Coding agents:** Claude Code, opencode, VS Code and others",
            ("tested configurations in the NRP docs", 1)], size=17)
        s.text(4.7, TOP + 0.1, 8.03, 0.35, P(cap, size=14, bold=True, color=NAVY))
        s.image(IMG / f, 4.7, TOP + 0.5, 8.03, 4.75, align="l", valign="t", border="3A3A3A")
        s.notes(notes[min(i, 1)])

if ALTS:
    for v in "ABC":
        what_is_nrp(v)
    for v in "ABC":
        gpu_policy(v)
    deck.save(OUT)
    print(OUT)
    sys.exit()

# ═════════════════════════════════════════════════════════════════════════════════════
# OPENING
# ═════════════════════════════════════════════════════════════════════════════════════
s = deck.slide(layout="1_Title Slide", section=None)
t = s.s.shapes.title
t.left, t.top, t.width, t.height = Inches(0.67), Inches(1.0), Inches(12.0), Inches(2.4)
tf = t.text_frame
tf.text = ""
for i, line in enumerate(["The National Research Platform", "for AI-Enabled Research"]):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.line_spacing = 0.8
    r = p.add_run(); r.text = line; r.font.size = Pt(44); r.font.italic = False
sub = [ph for ph in s.s.placeholders if ph.placeholder_format.idx == 1][0]
sub.left, sub.top, sub.width, sub.height = Inches(0.67), Inches(3.75), Inches(9.6), Inches(2.5)
fill_tf(sub.text_frame, [
    P("GPUs and AI for research and education", size=32, font=SANS_BLACK, color=GOLD, after=14),
    P("**Daniel Diaz**  ·  San Diego Supercomputer Center, UC San Diego", size=21, color=WHITE, after=6),
    P("UCLA Health IT Research Tech Talk  ·  10 November 2026", size=17, color="E7E6E6"),
])
s.notes("""
[0:00] Thanks for having me. I'm Daniel Diaz, a computational research scientist at SDSC. I'm one of the administrators of the National Research Platform, and I also use it for my own machine-learning work in particle physics, so I'll talk about it from both sides.

The question for today is: what can you actually do with NRP? For this group that mostly means two things, GPUs and AI, so that's where most of the time goes.
""")

s = slide("Agenda")
bullets(s, X0, TOP + 0.15, 9.5, 4.4, [
    "What is NRP?",
    "Getting access, and what a namespace is",
    "GPUs: what's available, and how to run a GPU job",
    "AI services: hosted LLMs and Jupyter AI",
    "JupyterHub for labs and classes",
    "Live demo",
    "Questions"], size=22, gap=12)
s.text(X0, 5.85, 12.1, 0.4, P("Slides, the demo notebooks and the GPU job:", size=18, color=BODY))
s.link(X0, 6.25, 12.1, 0.4, "https://training.nrp-nautilus.io/ucla-health", size=18)
s.notes("""
[0:01] The plan: what NRP is, in a few minutes; how you get in, including the one new idea you need, a namespace; then the two big ones, GPUs and the AI services; a quick word on JupyterHub for labs and classes; and a live demo of both the AI and the GPU side, then questions.

Everything I show is on the training site at the bottom, including the notebooks and the GPU job, so you don't need to copy anything down. Questions are welcome in the chat at any point; Clifford will pass them along.
""")

# ═════════════════════════════════════════════════════════════════════════════════════
# THE PLATFORM
# ═════════════════════════════════════════════════════════════════════════════════════
section("The Platform", "[0:02] Quick context first, for anyone new to NRP.")
what_is_nrp(V4)
kubernetes_intro()
access_methods()
what_nrp_is_for()

# ═════════════════════════════════════════════════════════════════════════════════════
# GETTING ACCESS
# ═════════════════════════════════════════════════════════════════════════════════════
section("Getting Access", "[0:09] How you get in. One new word here: namespace.")
namespaces()

s = slide("Getting Access")
s.text(X0, TOP + 0.15, 6.3, 5.1, [
    P("1.  Log in at **nrp.ai**", size=20, color=BODY),
    P("Log In → CILogon → choose **UCLA** → your UCLA login", size=17, color=BODY, before=3),
    P("2.  Get into a namespace", size=20, color=BODY, before=16),
    P("Request one at **get-started.nrp-nautilus.io**", size=17, color=BODY, before=3),
    P("Or ask an existing namespace admin to add you", size=17, color=BODY, before=3),
    P("3.  Start working", size=20, color=BODY, before=16),
    P("JupyterHub, kubectl, or an LLM token from **nrp.ai/llmtoken**", size=17, color=BODY, before=3),
    P("**Who can request a namespace:** faculty, staff, postdocs and research scientists. "
      "**Students:** your PI or instructor requests it and adds you.", size=17, color=BODY, before=22,
      line=1.04),
])
s.link(7.2, TOP + 0.05, 5.53, 0.3, "https://get-started.nrp-nautilus.io", size=14, align="r")
s.image(IMG / "namespace_form.png", 7.2, TOP + 0.42, 5.53, 4.8, align="r", valign="t", border="DDE8F2")
s.notes("""
[0:10] Three steps. First, go to nrp.ai and click Log In. That takes you to CILogon, where you pick UCLA and use your normal UCLA login. That creates your NRP identity; nothing is allocated yet, but everything hangs off that identity. Use the same provider every time.

Second, get into a namespace. If you're faculty, staff, a postdoc or a research scientist, you can request one with the form on the right, at get-started.nrp-nautilus.io; a person reviews it, usually within a working day. Students go through their PI or instructor, who requests the namespace and adds them. Or, if your group already has one, the admin just adds you.

Third, start working: JupyterHub, kubectl on your laptop, or a token for the language models. kubectl is the next slide.
""")

talking_to_cluster()

# ═════════════════════════════════════════════════════════════════════════════════════
# GPUS
# ═════════════════════════════════════════════════════════════════════════════════════
section("GPUs", "[0:13] GPUs. This is the part most people ask about, because getting a GPU is hard almost everywhere.")

s = slide("GPUs on NRP")
bullets(s, X0, TOP + 0.15, 5.0, 5.0, [
    f"{GPUS:,} GPUs in {GPU_MODELS} models, contributed by campuses",
    "Most common: A10 and RTX 3090, 24 GB each",
    "About 140 A100s with 80 GB, plus H100s and H200s",
    "Ask for the GPU memory your job needs, not a brand name",
    "What's free right now: **nrp.ai/viz/resources**"], size=19)
s.image(FIG / "fleet_by_memory.png", 5.75, TOP, 6.98, 5.25, align="r", valign="t")
s.notes(f"""
[0:13] This is the fleet as of this week: {GPUS:,} GPUs in {GPU_MODELS} models. Because campuses contribute what they buy, it's deliberately varied. The biggest groups are A10s and RTX 3090s, both with 24 GB of memory; there are about a hundred and forty A100s with 80 GB, and smaller numbers of H100s and H200s.

The color is memory per GPU, because that's the number that decides whether your model fits. {T24:,} GPUs have 20 to 24 GB, which covers most deep learning; {T16:,} have 16 GB or less, fine for teaching and smaller models; {T48:,} have 32 to 48 GB; and {T80:,} have 80 GB or more, which you get by request. The habit to build: ask for what the job needs, not a particular card. The resources page shows what's free right now.
""")

s = slide("Choosing a GPU")
rows = [["GPU memory", "Examples", "Good for", "How to ask"],
        ["Up to 16 GB", "RTX 2080 Ti, GTX 1080 Ti, A4000, A100 slices",
         "Teaching, debugging, classic ML, small CNNs", "nvidia.com/gpu: 1"],
        ["20–24 GB", "A10, RTX 3090, L4, RTX 4090",
         "Most deep learning; fine-tuning and serving models up to ~8B parameters", "nvidia.com/gpu: 1 + memory or model"],
        ["32–48 GB", "L40, V100 32 GB, RTX A6000, A40",
         "Bigger models and batches; serving models up to ~30B", "nvidia.com/gpu, or rtxa6000 / a40"],
        ["80 GB and up", "A100 80 GB, H100, H200",
         "Large training runs and large models", "A100: access request; H100/H200 reserved"]]
s.table(X0, TOP + 0.1, 12.13, [1.55, 3.0, 4.0, 3.55], rows, size=15, head_size=15, row_h=0.82)
s.text(X0, 5.75, 12.13, 0.4, P("Current PyTorch builds need **Turing or newer**: on a GTX 1080 Ti or V100, use an "
                               "older image.", size=16, color=BODY))
s.link(X0, 6.25, 12.13, 0.3, "https://nrp.ai/documentation/userdocs/running/gpu-pods/", size=14)
s.notes("""
[0:15] How to choose. Up to 16 GB, the 2080 Tis and 1080 Tis and A100 slices, is plenty for teaching, debugging, classic machine learning and small convolutional networks. The 24 GB tier, A10s, 3090s, L4s, handles most deep learning, including fine-tuning or serving language models up to about eight billion parameters. The 48 GB tier is for bigger models and batches. And the 80 GB cards, A100s, H100s and H200s, are for large training runs; A100s are available through an access request, and the H100s and H200s are reserved for the groups that contributed them and for the LLM service.

For most of these you just ask for nvidia.com/gpu: 1 and optionally say how much memory you need; a few models have their own resource names, listed on the GPU pods page. One gotcha we hit preparing this: current PyTorch builds no longer run on the oldest cards, so start small but not too old.
""")

GX, GW, LANE_Y, LANE_H, LANE_GAP = 7.35, 5.38, TOP + 2.45, 0.4, 0.08     # the sweep schedule, as in the HTML

s = slide("Ways to Run Work")
for i, (head, items) in enumerate(RUN_WAYS):
    y = TOP + 0.1 + i * 1.65
    heading(s, X0, y, 5.55, head, size=19)
    bullets(s, X0, y + 0.42, 5.55, 1.15, items, size=15.5, gap=4)
heading(s, 6.55, TOP + 0.1, 6.18, "Batch: a Job", size=19)
bullets(s, 6.55, TOP + 0.52, 6.18, 0.8, RUN_JOB, size=15.5, gap=4)
s.code(6.55, TOP + 1.3, 6.18, 0.62, RUN_CMD, size=12)
for g in range(4):
    y = LANE_Y + g * (LANE_H + LANE_GAP)
    s.text(6.55, y, 0.75, LANE_H, P(f"GPU {g + 1}", size=12, bold=True, color=NAVY), anchor="m")
    s.rect(GX, y, GW, LANE_H, fill="F3F4F6", radius=0.12)
for job, g, t0, t1 in SWEEP:
    y = LANE_Y + g * (LANE_H + LANE_GAP)
    x, w = GX + t0 / SWEEP_T * GW, (t1 - t0) / SWEEP_T * GW
    s.rect(x + 0.02, y + 0.03, w - 0.04, LANE_H - 0.06, fill="8FB0CF", radius=0.18)
    s.text(x, y, w, LANE_H, P(job, size=11, bold=True, color=NAVY, align="c", font=MONO), anchor="m")
ay = LANE_Y + 4 * (LANE_H + LANE_GAP) - 0.02
s.line(GX, ay, GX + GW, ay, color=MUTED, width=1.25)
s.text(GX + GW - 1.0, ay + 0.02, 1.0, 0.3, P("time", size=11, color=MUTED, align="r"))
s.text(6.55, ay + 0.32, 6.18, 0.6, P(RUN_CAPTION, size=13.5, color=MUTED, line=1.0))
s.notes("""
[0:16] Four ways to run something, from most interactive to most hands-off. JupyterHub: you pick a GPU from the start menu and your notebook sees it straight away, which is right for exploring, debugging and teaching. On NRP's own hub, your server stops an hour after you close the browser, and every hub on NRP has to stop idle servers within six hours, so the GPU goes back to the pool.

A pod is the same idea from kubectl: start a container and exec into it for a shell. A pod with nothing managing it counts as interactive: it's deleted after six hours and can have at most two GPUs.

A Deployment is for a service that should stay up, a web app or a small database; Kubernetes restarts it if it crashes. Deployments are removed after two weeks unless the admins grant an exception, and one that sits mostly idle can't request a GPU.

And for the real work, a Job. You describe the run in a short file and submit it; the cluster waits for a matching GPU, runs it, and when your script exits the GPU goes back. Submit many at once for a sweep: here six jobs on four GPUs. Four start right away, two wait in Pending and take the first GPUs that free up, and at the end all four GPUs are free for someone else. The next slide is what's inside one of those files.
""")

s = slide("A GPU Job")
s.code(X0, TOP + 0.1, 8.25, 5.2, """apiVersion: batch/v1
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
              - {key: nvidia.com/gpu.compute.major, operator: Gt, values: ["7"]}""", size=12, lang="yaml")
s.text(9.1, TOP + 0.2, 3.63, 5.0, [
    P("(1) **Where:** your namespace", size=17, color=BODY, line=1.04),
    P("(2) **What:** a container image, and the command to run", size=17, color=BODY, before=14, line=1.04),
    P("(3) **Resources:** 2 CPUs, 6 GB of memory, one GPU", size=17, color=BODY, before=14, line=1.04),
    P("(4) **Which GPU:** more than 20 GB, Ampere or newer; or name exact models", size=17, color=BODY,
      before=14, line=1.04)])
s.notes("""
[0:18] Here's what a GPU job looks like, and it's less than it seems. Four things matter.

One: where it runs, your namespace. Two: what it runs, a container image, here the official PyTorch image, and the command to start your code. Three: what it needs, two CPUs, 6 GB of memory and one GPU; the scheduler reserves exactly that, no more. Four: which GPU. This one says more than 20 GB of memory and Ampere or newer, which on NRP means A10s, 3090s, L4s and up. The second line is a lesson from testing this demo: current PyTorch builds no longer run on older cards like the V100 or the 1080 Ti, so the job asks for a newer generation. You can also name exact models, using the GPU product label.

The rest is boilerplate you copy. The full file, with the training script inside it, is in the workspace on the training site.
""")

s = slide("Running the Job")
s.code(X0, TOP + 0.1, 6.3, 3.0, """# submit
kubectl apply -f gpu-job.yaml

# watch: Pending → Running → Completed
kubectl get pods -l job-name=gpu-train-daniel

# read the output
kubectl logs -f job/gpu-train-daniel

# clean up
kubectl delete job gpu-train-daniel""", size=14)
s.text(X0, TOP + 3.3, 6.3, 1.9, [
    P("Stuck in **Pending**? `kubectl describe pod` says why, usually that no matching GPU is free.",
      size=17, color=BODY, line=1.04),
    P("Our test: under 30 s from submit to done on an A10 that had the image; several minutes in Pending "
      "when the cluster was full.", size=17, color=BODY, before=10, line=1.04)])
demo_out = (HERE / "data" / "demo_job_output.txt").read_text().strip()
s.code(7.15, TOP + 0.1, 5.58, 3.55, demo_out, size=12.5, title="Output, 9 Nov 2026")
s.notes("""
[0:19] Running it is four commands. kubectl apply submits it. kubectl get pods shows it going from Pending, waiting for a GPU, to Running, to Completed. kubectl logs shows the output, live with -f. And kubectl delete cleans up, though this job also deletes itself an hour after it finishes.

On the right is what the demo job printed: which GPU it got, the same matrix multiply on two CPU cores and on the GPU, and three passes of training a small network on handwritten digits. If a job sits in Pending, kubectl describe pod tells you why, usually that no GPU of the kind you asked for is free. That's the moment to ask for something more common.
""")

gpu_policy(V17)

# ═════════════════════════════════════════════════════════════════════════════════════
# AI SERVICES
# ═════════════════════════════════════════════════════════════════════════════════════
section("AI Services", "[0:22] AI. Some of NRP's GPUs serve open-weight language models as a shared service.")

s = slide("Hosted LLMs")
bullets(s, X0, TOP + 0.15, 5.3, 5.0, [
    "Open-weight models on NRP GPUs, behind one OpenAI-compatible endpoint:",
    ("ellm.nrp-nautilus.io/v1", 1),
    "Free for non-commercial research and education",
    "Prompts are processed on NRP hardware, not sent to a commercial provider",
    "Still not for PHI",
    "About 7.1 billion tokens a day (September 2026)"], size=18)
rows = [["Model", "Good for"],
        ["qwen3, qwen3-small", "Hard reasoning, long documents, images"],
        ["gpt-oss", "General chat, reproducible research"],
        ["glm-5, kimi, minimax", "Agentic coding"],
        ["deepseek-v4-flash", "Whole codebases, very long documents"],
        ["gemma, gemma-small", "Images, video, audio transcription"],
        ["qwen3-embedding", "Search and RAG (embeddings)"]]
s.table(6.3, TOP + 0.2, 6.43, [2.5, 3.93], rows, size=14.5, head_size=15, row_h=0.6, mono_cols=(0,))
s.link(6.3, TOP + 4.55, 6.43, 0.3, "https://nrp.ai/documentation/userdocs/ai/llm-managed/models/", size=13)
s.text(6.3, TOP + 4.9, 6.43, 0.3, P("Uses from the models page, 26 Oct 2026. The catalog rotates.", size=12,
                                    color=MUTED))
s.notes("""
[0:22] Part of the GPU fleet serves open-weight language models as a shared service, behind one address that speaks the OpenAI API. You choose the model by name. It's free for research and education, and your prompts are processed on NRP hardware rather than sent to a commercial provider. That still doesn't make it a place for PHI.

It's used a lot: about seven billion tokens a day in September. On the right is the current catalog with what the docs recommend each model for: qwen3 for hard reasoning and long documents, gpt-oss for general use and reproducible work, a set of coding models, deepseek for very long inputs, gemma for images, video and audio, and an embedding model for search. The catalog rotates as better open models come out, so check the page before you pin a name into a pipeline.
""")

using_llms()

s = slide("Jupyter AI")
s.image(IMG / "jupyter-ai.png", X0, TOP + 0.1, 2.6, 5.15, valign="t", border="DDE8F2")
s.image(IMG / "jupyter-ai2.png", X0 + 2.8, TOP + 0.1, 1.85, 5.15, valign="t", border="DDE8F2")
bullets(s, 5.75, TOP + 0.15, 6.98, 3.1, [
    "Already pointed at NRP's models on the training hub, and on any course hub you run",
    "**Chat panel:** ask about code, an error or a concept",
    "**/fix:** select a cell that crashed; it explains and proposes a fix",
    "**%%ai magics:** {variables} in a prompt become their live values, so the model sees your data"], size=17,
        gap=8)
s.code(5.75, TOP + 3.55, 6.98, 1.7, """%%ai openai-chat:gpt-oss
Here is a summary of my dataset: {summary}
Which columns would you check first, and why?""", size=13)
s.notes("""
[0:25] Jupyter AI puts an assistant beside the notebook. On NRP's training hub, and on any course hub you set up, it's already pointed at the hosted models, so nobody pastes a key.

Three things in it. The chat panel, for questions about code or concepts. /fix, which takes a cell that crashed and explains and fixes the error. And the %%ai magics, which are the interesting part: anything you put in curly braces is replaced by the live value of that variable, so you can hand the model a summary of your actual data and ask about it. The chat panel can't see your notebook; the magics can. That's what I'll show in the demo.
""")

s = slide("Running Your Own Models")
bullets(s, X0, TOP + 0.15, 12.13, 4.3, [
    "**Serve your own model:** vLLM or SGLang on a GPU in your namespace, your weights or your fine-tune behind "
    "the same OpenAI API; ask the admins before running one as a long-lived service",
    "**Train and fine-tune:** PyTorch and Hugging Face in GPU jobs, from one GPU to eight on a node",
    "**Search your documents (RAG):** qwen3-embedding and NRP's managed Milvus vector database",
    "**Inference accelerators:** Qualcomm Cloud AI 100 cards, requested in a job like a GPU"], size=20, gap=14)
s.text(X0, 5.45, 12.13, 0.4, P("Worked examples: the PEARC26 tutorial (serving, RAG), and a physics neural network "
                               "trained in GPU jobs (CMS HATS)", size=17, color=BODY))
s.link(X0, 5.9, 12.13, 0.35, "https://training.nrp-nautilus.io", size=16)
s.notes("""
[0:26] The hosted models are the easy start, but the same GPUs let you build your own. You can serve your own model with vLLM or SGLang on a GPU in your namespace, for example a model you fine-tuned, and it speaks the same OpenAI API. Talk to us before you run one as a service that stays up: a long-running Deployment that holds a GPU needs an exception from the admins. You can train and fine-tune in GPU jobs, one GPU or up to eight on a node. You can build retrieval over your own documents with the embedding model and NRP's managed Milvus vector database. And there are Qualcomm inference cards you request like a GPU.

Each of these has a worked example on the training site: the PEARC26 tutorial covers serving and RAG, and the CMS training trains a physics neural network in GPU jobs, which is the bigger version of today's demo.
""")

# ═════════════════════════════════════════════════════════════════════════════════════
# LABS AND CLASSES
# ═════════════════════════════════════════════════════════════════════════════════════
section("Labs and Classes", "[0:27] Briefly, labs and classes.")

s = slide("JupyterHub for Classes")
rows = [["Your class needs", "A hub on NRP gives it"],
        ["The same environment for every student", "A container image you choose"],
        ["No laptop setup on day one", "JupyterLab in the browser, with campus login"],
        ["GPUs for a neural-network unit", "GPU options on the start menu, with limits"],
        ["An AI assistant, without per-seat fees", "Jupyter AI and the hosted LLMs, preconfigured"],
        ["Shared datasets and notebooks", "One shared volume in every server"]]
s.table(X0, TOP + 0.15, 7.6, [3.65, 3.95], rows, size=15, row_h=0.72, bold_first=True)
bullets(s, 8.6, TOP + 0.2, 4.13, 5.0, [
    "**Instructors:** contact us; we'll help you set up a hub for your lab or course",
    "It's one configuration file in a namespace you own",
    "**Students:** if your course needs GPUs, ask your professor to get in touch"], size=18)
s.notes("""
[0:27] A high-level word on teaching, because it came up when we planned this. If you run a lab or a course, you can have your own JupyterHub on NRP. Every student gets the same environment in the browser with their campus login, GPUs from a menu for the neural-network unit, the AI assistant already configured with no per-seat fees, and a shared folder for datasets.

For example, a master's course where students train neural networks and a laptop isn't enough is exactly the case this is for. It's one configuration file in a namespace you own, and we help you set it up, so instructors: contact us. Students: if your course needs GPUs, ask your professor to get in touch.
""")

s = slide("Getting Started")
s.text(X0, TOP + 0.2, 7.4, 5.1, [
    P("1.  Log in: **nrp.ai** (CILogon → UCLA)", size=22, color=BODY),
    P("2.  Request a namespace: **get-started.nrp-nautilus.io**", size=22, color=BODY, before=22),
    P("PIs, faculty, staff, postdocs; students ask their PI", size=18, color=MUTED, before=3),
    P("3.  Try the LLMs: **nrp-openwebui.nrp-nautilus.io**", size=22, color=BODY, before=22),
    P("4.  Run your first GPU job:", size=22, color=BODY, before=22),
    P("**training.nrp-nautilus.io/ucla-health**", size=22, color=BODY, before=3)])
heading(s, 8.4, TOP + 0.2, 4.33, "Help", size=22)
bullets(s, 8.4, TOP + 0.75, 4.33, 4.6, [
    "Documentation: nrp.ai/documentation",
    "Support chat and email: nrp.ai/contact",
    "Labs, courses or a UCLA campus group: d4diaz@ucsd.edu"], size=19, gap=14)
s.notes("""
[0:28] To get started: log in at nrp.ai with your UCLA account. If you're a PI, faculty, staff or a postdoc, request a namespace at get-started.nrp-nautilus.io. Try the language models in the browser at nrp-openwebui. And for your first GPU job, everything from today, the notebooks and the job file, is on the training site.

For help, the documentation is good, and the support chat is the fastest way to reach the team. For anything bigger, a lab hub, a course, or setting up a UCLA campus group, email me. Now the demo.
""")

# ═════════════════════════════════════════════════════════════════════════════════════
# LIVE DEMO
# ═════════════════════════════════════════════════════════════════════════════════════
section("Live Demo", """[0:29] About twelve minutes, two parts.

Part 1 (about 6 min), in JupyterHub at jh-training.nrp-nautilus.io, notebook workspace/notebooks/1_ai.ipynb: list the models, ask one a question from Python, give it a summary of a public dataset with %%ai, then the broken cells with the Jupyter AI chat panel and /fix, and the silent bug with %%ai and live values.

Part 2 (about 6 min): nrp.ai/viz/resources to show GPUs live; then workspace/notebooks/2_gpu.ipynb: nvidia-smi and the CPU vs GPU matrix multiply in the session; then submit yamls/gpu-job.yaml, watch Pending -> Running, and stream the logs.

[Before the talk: open both notebooks, spawn the session with a GPU, and submit one copy of the job at about 11:45 so a finished run is ready to show if the live one waits for a GPU. Run sheet: deck/README.md.]""")

# ═════════════════════════════════════════════════════════════════════════════════════
# CLOSE
# ═════════════════════════════════════════════════════════════════════════════════════
s = slide("Acknowledgments")
bullets(s, X0, TOP + 0.15, 12.13, 5.0, [
    "NRP is supported by NSF awards OAC-1541349, OAC-1826967, OAC-2030508, OAC-1841530, OAC-2005369, "
    "OAC-2112167, CISE-1713149, CISE-2100237 and CISE-2120019",
    "Networks: CENIC, Pacific Wave, Internet2, MREN, GPN, NYSERNet, FLR, NEREN, Sun Corridor, OARnet, SCLR "
    "and the Albuquerque GigaPoP",
    "The NRP operations teams at SDSC, the University of Nebraska–Lincoln and MGHPCC, and the campuses that "
    "host and share their hardware, UCLA among them",
    "Clifford and UCLA Health IT's Research Tech Talks, for hosting"], size=18, gap=14)
s.notes("[0:41] Thanks to NSF, the regional networks, the NRP operations teams and the contributing campuses, "
        "and to Clifford and UCLA Health IT for hosting.")

s = deck.slide(title="Questions?", layout="Title Only - Reverse", section=FOOT)
links = [("Today's materials", "training.nrp-nautilus.io/ucla-health"), ("Portal and login", "nrp.ai"),
         ("Request a namespace", "get-started.nrp-nautilus.io"), ("Chat with the LLMs", "nrp-openwebui.nrp-nautilus.io"),
         ("LLM token", "nrp.ai/llmtoken"), ("GPUs free right now", "nrp.ai/viz/resources"),
         ("GPU jobs, docs", "nrp.ai/documentation/userdocs/running/gpu-pods"),
         ("Support", "nrp.ai/contact")]
for i, (lab, url) in enumerate(links):
    y = 1.70 + i * 0.56
    s.text(X0, y, 3.1, 0.5, P(lab, size=17, color=LIGHT), anchor="m")
    s.text(X0 + 3.15, y, 6.6, 0.5, P(url, size=15, bold=True, color=GOLD, font=MONO), anchor="m")
s.text(X0, 6.25, 12.1, 0.45, P("Daniel Diaz  ·  d4diaz@ucsd.edu", size=19, bold=True, color=WHITE))
s.notes("[0:42] Questions. All the links are on the slide, and everything is on the training site.")

# ═════════════════════════════════════════════════════════════════════════════════════
# BACKUP
# ═════════════════════════════════════════════════════════════════════════════════════
section("Backup", "Backup slides for questions.")

s = slide("Glossary")
gl = [("Kubernetes", "Software that runs containers across many machines; NRP's cluster is one"),
      ("Container", "Your software and everything it needs, packaged to run anywhere"),
      ("Pod", "One or more containers running together on one machine"),
      ("Job", "A pod that runs to completion, then releases its resources"),
      ("Namespace", "Your group's workspace on the cluster: members, jobs, data"),
      ("Volume (PVC)", "Storage in your namespace that outlives any one pod"),
      ("kubectl", "The command-line tool you use to talk to the cluster"),
      ("GPU memory", "How big a model or batch fits on one GPU; the main number to ask for"),
      ("Open-weight model", "A model whose weights are published for anyone to run"),
      ("Token (LLM)", "A piece of a word, about ¾ of an English word"),
      ("Embedding", "A vector that captures meaning, for search and RAG"),
      ("RAG", "Look up relevant text first, then ask the model to answer from it")]
rows = [["Term", "Meaning"]] + [[a, b] for a, b in gl]
s.table(X0, TOP + 0.05, 12.13, [2.4, 9.7], rows, size=14, row_h=0.39)
s.notes("Backup: definitions.")

organizing_groups()

s = slide("GPU Resource Keys")
rows = [["GPU", "Request it as", "Notes"],
        ["Most GPUs (A10, 3090, L4, 2080 Ti, L40, V100 ...)", "nvidia.com/gpu: 1", "Pick a model or memory with node affinity"],
        ["NVIDIA RTX A6000", "nvidia.com/rtxa6000: 1", "48 GB"],
        ["NVIDIA A40", "nvidia.com/a40: 1", "48 GB"],
        ["NVIDIA A100 (80 GB)", "nvidia.com/a100: 1", "Quota is zero by default: access request at nrp.ai/reservations"],
        ["A100 slice (MIG 1g.10gb)", "nvidia.com/mig-small: 1", "10 GB slice of an A100"],
        ["NVIDIA H100 / H200 / GH200", "nvidia.com/h100 · h200 · gh200", "Reserved for contributors and LLM serving"],
        ["Any of the big ones, preemptibly", "priorityClassName: opportunistic", "Runs on idle capacity; can be preempted"]]
s.table(X0, TOP + 0.1, 12.13, [4.1, 3.6, 4.4], rows, size=14, row_h=0.56, mono_cols=(1,))
s.text(X0, 6.25, 12.13, 0.3, P("Check live with kubectl get nodes -L nvidia.com/gpu.product", size=14, color=MUTED))
s.notes("Backup: resource keys from nrp.ai/documentation/userdocs/running/gpu-pods.")

s = slide("%%ai Magics")
s.code(X0, TOP + 0.1, 6.9, 5.15, """%load_ext jupyter_ai_magics

%%ai openai-chat:gpt-oss
What is the National Research Platform, in two sentences?

# explain the most recent traceback, no copy-paste
%ai error openai-chat:gpt-oss

# {variables} are replaced by their live values
%%ai openai-chat:gpt-oss
My readings are {readings} and my code printed {average}.
Is that the mean of every reading after the first?""", size=13)
bullets(s, 7.75, TOP + 0.15, 4.98, 5.1, [
    "The chat panel can't see the kernel; the magics can",
    "%ai error reads the last traceback",
    "The silent bug: code that runs and prints the wrong number has no traceback, so you have to say what you meant",
    "%ai list is Jupyter AI's built-in list, not NRP's catalog; the name you type passes through to NRP"], size=16)
s.notes("Backup: the magics in more detail, as used in the demo notebook.")

deck.save(OUT)
from deckkit import CODE_WARNINGS  # noqa: E402

print(f"{OUT}  ({len(deck.p.slides)} slides, {deck.n} numbered)")
for w in CODE_WARNINGS:
    print("  WARNING", w)
