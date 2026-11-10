"""Build the animated HTML version of the deck: one self-contained file on a fixed 1920x1080 stage.

    python3 deck/build_html.py        # -> slides/ucla-health-nrp.html (run build_deck.py first: notes come from the pptx)

Same slides, layout and SDSC look as the PowerPoint, with step animations where the pptx uses
fake animations. Present it from a browser (or from the training site):

    → ↓ Space PgDn   next step, then next slide        ← ↑ PgUp   back
    N   speaker notes       F   full screen       Home / End   first / last slide
    #12 in the URL jumps to slide 12, #12.3 to its third step;  ?print shows every slide in its final
    state (for a PDF).

Fonts come from Google Fonts (Teko, Source Sans 3, Source Code Pro); without internet the browser
falls back to system fonts. Images are embedded, so the file works on its own.
"""
import base64
import csv
import re
from html import escape
from pathlib import Path

from pptx import Presentation

from make_map import LABEL_AT, LABEL_PX, PIN_STYLE, geometry, offmap_note, pin_path
from sweep import RUN_CAPTION, RUN_CMD, RUN_JOB, RUN_WAYS, SWEEP, SWEEP_T, apply_lines, get_pods

HERE = Path(__file__).resolve().parent
TRAINING = HERE.parent
IMG = HERE / "assets" / "images"
TPL = HERE / "assets" / "template"
OUT = TRAINING / "slides" / "ucla-health-nrp.html"
PPTX = HERE / "presenter" / "ucla-health-nrp.pptx"     # the copy with speaker notes, from build_deck.py
PRESENTER_OUT = HERE / "presenter" / "ucla-health-nrp.html"

PX = 144                      # pixels per inch on the 1920x1080 stage (13.333 in wide), so 1 pt = 2 px


def uri(path):
    ext = path.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml"}[ext]
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


# ── numbers, the same sources as build_deck.py ─────────────────────────────────────
SNAP_DAY, SNAP_NODES = (HERE / "data" / "SNAPSHOT").read_text().split()
with (HERE / "data" / "gpu_fleet.csv").open() as f:
    FLEET = [dict(r, gpus=int(r["gpus"]), memory_mib=int(r["memory_mib"])) for r in csv.DictReader(f)]
GPUS, GPU_MODELS, NODES = sum(r["gpus"] for r in FLEET), len(FLEET), int(SNAP_NODES)
DEMO_OUT = (HERE / "data" / "demo_job_output.txt").read_text().strip().splitlines()

# ── notes from the pptx, by slide title; build copies are joined ───────────────────
NOTES = {}
for sl in Presentation(PPTX).slides:
    t = sl.shapes.title.text_frame.text.replace("\n", " ") if sl.shapes.title is not None else ""
    n = sl.notes_slide.notes_text_frame.text.strip() if sl.has_notes_slide else ""
    key = t or n[:20]
    if n and n not in NOTES.get(key, ""):
        NOTES[key] = (NOTES.get(key, "") + "\n\n" + n).strip()


# ── tiny HTML helpers ────────────────────────────────────────────────────────────────
def md(t):
    t = escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


def pos(x, y, w=None, h=None):
    s = f"left:{x * PX:.0f}px;top:{y * PX:.0f}px;"
    if w is not None:
        s += f"width:{w * PX:.0f}px;"
    if h is not None:
        s += f"height:{h * PX:.0f}px;"
    return s


def at(x, y, w, h, inner, cls="", step=None, only=None, style=""):
    a = f' data-s="{step}"' if step is not None else ""
    a += f' data-only="{only}"' if only is not None else ""
    return f'<div class="a {cls}"{a} style="{pos(x, y, w, h)}{style}">{inner}</div>'


def ul(items, size=20):
    li = []
    for it in items:
        text, lvl = (it, 0) if isinstance(it, str) else it
        li.append(f'<li class="l{lvl}">{md(text)}</li>')
    return f'<ul class="bl" style="font-size:{size * 2}px">{"".join(li)}</ul>'


def code(text, size=13, title=None, cls=""):
    lines = []
    for ln in text.strip("\n").split("\n"):
        e = escape(ln)
        e = re.sub(r"(^\s*#.*$|\s#\s.*$)", r'<span class="cm">\1</span>', e)
        e = re.sub(r"(&quot;[^&]*?&quot;)", r'<span class="st">\1</span>', e)
        lines.append(f'<span class="ln">{e or " "}</span>')
    t = f'<div class="ct">{escape(title)}</div>' if title else ""
    return f'<div class="code {cls}" style="font-size:{size * 2}px">{t}<pre>{"".join(lines)}</pre></div>'


def img(path, cls="", fit="contain"):
    return f'<img class="im {cls}" src="{uri(path)}" style="object-fit:{fit}" alt="">'


def table(rows, widths, size=15, mono=()):
    tot = sum(widths)
    cg = "".join(f'<col style="width:{w / tot * 100:.1f}%">' for w in widths)
    head = "".join(f"<th>{md(c)}</th>" for c in rows[0])
    body = ""
    for r in rows[1:]:
        body += "<tr>" + "".join(f'<td class="{"mono" if j in mono else ""}">{md(c)}</td>'
                                 for j, c in enumerate(r)) + "</tr>"
    return (f'<table class="tb" style="font-size:{size * 2}px"><colgroup>{cg}</colgroup>'
            f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")


def box(head, sub=None, cls=""):
    s = f'<span class="bs">{md(sub)}</span>' if sub else ""
    return f'<div class="bx {cls}"><span class="bh">{md(head)}</span>{s}</div>'


def link(url, text=None, size=14, align="left"):
    return (f'<a class="lk" href="{escape(url)}" target="_blank" rel="noopener" '
            f'style="font-size:{size * 2}px;text-align:{align}">{escape(text or url)}</a>')


SLIDES = []
NUM = [0]


def slide(title, body, notes_key=None, steps=0, cls="", kind="content"):
    NUM[0] += 1
    notes = NOTES.get(notes_key or title, "")
    SLIDES.append(dict(title=title, body=body, notes=notes, steps=steps, cls=cls, kind=kind, n=NUM[0]))


def section(title):
    slide(title, "", notes_key=title, kind="section")


TOP = 1.45
X0 = 0.6

# ═════════════════════════════════════════════════════════════════════════════════════
# SLIDES
# ═════════════════════════════════════════════════════════════════════════════════════
slide("The National Research Platform for AI-Enabled Research", "", kind="title",
      notes_key="The National Research Platform for AI-Enabled Research")

slide("Agenda",
      at(X0, TOP + 0.15, 9.5, 4.4, ul(["What is NRP?", "Getting access, and what a namespace is",
                                       "GPUs: what's available, and how to run a GPU job",
                                       "AI services: hosted LLMs and Jupyter AI", "JupyterHub for labs and classes",
                                       "Live demo", "Questions"], 22), "stagger") +
      at(X0, 5.85, 12.1, 0.4, '<p style="font-size:36px">Slides, the demo notebooks and the GPU job:</p>') +
      at(X0, 6.25, 12.1, 0.4, link("https://training.nrp-nautilus.io/ucla-health", size=18)))

section("The Platform")

# What is NRP?: the operators' sites, then UCLA, then every site drops onto the map (real dashboard locations)
GEO = geometry(890)


def usmap():
    w, h = GEO["width"], GEO["height"]
    land = "".join("M" + "L".join(f"{x:g},{y:g}" for x, y in pts) + "Z" for pts in GEO["paths"])
    svg = (f'<svg class="usmap" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}">'
           f'<path class="land" d="{land}"/><defs>'
           + "".join(f'<path id="pin-{k}" d="{pin_path(r)}"/>' for k, (_, r) in PIN_STYLE.items()) + "</defs>")
    order = {"other": 0, "ucla": 1, "ops": 2}
    ops = [p for p in GEO["pins"] if p["kind"] == "ops"]
    for p in sorted(GEO["pins"], key=lambda p: order[p["kind"]]):
        r = PIN_STYLE[p["kind"]][1]
        d = {"ops": 0.35 + 0.3 * ops.index(p) if p in ops else 0, "ucla": 0.1,
             "other": 0.05 + 1.6 * p["x"] / w}[p["kind"]]            # the rest sweep in west to east
        svg += (f'<g transform="translate({p["x"]:.1f},{p["y"]:.1f})"><g class="pin k-{p["kind"]}" '
                f'style="--d:{d:.2f}s"><use href="#pin-{p["kind"]}"/><circle cy="{-1.6 * r:.1f}" '
                f'r="{0.38 * r:.1f}"/></g></g>')
    for p in GEO["pins"]:
        if p["label"]:
            dx, dy, anchor = LABEL_AT[p["label"]]
            d = 0.6 + 0.3 * ops.index(p) if p in ops else 0.3
            svg += (f'<text class="pl k-{p["kind"]}" style="--d:{d:.2f}s" x="{p["x"] + dx:.1f}" y="{p["y"] + dy:.1f}" '
                    f'text-anchor="{anchor}" dominant-baseline="central">{escape(p["label"])}</text>')
    return svg + "</svg>"


def ul_steps(items, size=20):
    """Bullets that build: an item is (text, level, step)."""
    li = ""
    for t, lvl, st in items:
        attr = f' data-s="{st}"' if st else ""
        li += f'<li class="l{lvl}"{attr}>{md(t)}</li>'
    return f'<ul class="bl" style="font-size:{size * 2}px">{li}</ul>'


slide("What is NRP?",
      at(X0, TOP + 0.15, 5.7, 5.2, ul_steps([
          ("A national **Kubernetes** cluster, **Nautilus**, for research and education", 0, 0),
          ("Run by SDSC (UC San Diego), Nebraska–Lincoln and MGHPCC; funded by NSF", 0, 0),
          ("Hardware contributed by 70+ institutions, UCLA among them", 0, 1), ("Scale today:", 0, 2),
          (f"{NODES} nodes", 1, 2), (f"{GPUS:,} GPUs in {GPU_MODELS} models", 1, 2), ("Petabytes of storage", 1, 2),
          ("Free for non-commercial research and education", 0, 3)], 20)) +
      at(6.55, TOP + 0.05, 6.18, 0.3, link("https://dash.nrp-nautilus.io", size=14, align="right")) +
      at(6.55, TOP + 0.45, 6.18, 4.1, usmap()) +
      at(6.55, TOP + 4.6, 6.18, 0.5, f'<p class="cap" style="text-align:right;font-size:24px">Site locations from the '
         f'NRP dashboard, 10 Nov 2026<br>{offmap_note(GEO)}</p>', step=2),
      steps=3, cls="whatnrp")

# Kubernetes and containers: layers stack up, the cluster appears, the container moves into a GPU node
layers = [("train.py", "your code"), ("PyTorch, NumPy", None), ("CUDA libraries", None), ("Linux", None)]
k8s = at(X0, TOP + 0.15, 5.3, 5.1, ul([
    "**Container image:** your code plus everything it needs (Python, PyTorch, CUDA), in one package",
    "Runs the same on a laptop, a cluster or the cloud", "**Kubernetes** runs containers across many machines",
    "You say what you need (CPUs, memory, a GPU); it finds a machine that has it",
    f"NRP is one Kubernetes cluster: {NODES} nodes"], 19))
# step 1 the pieces stack up; 2 an orange box draws around them: that's the image; 3 the cluster; 4 a container
# in the same orange lifts off the image and lands on a GPU node
for i, (h, sub) in enumerate(reversed(layers)):          # bottom layer first
    k = len(layers) - 1 - i
    k8s += at(6.25, TOP + 0.75 + k * 0.68, 2.55, 0.6, box(h, sub, "active" if k == 0 else ""), "layer", step=1,
              style=f"transition-delay:{i * 0.18:.2f}s")
k8s += at(6.15, TOP + 0.2, 2.75, 0.4, '<p class="dh" style="color:var(--orange)">Container image</p>', step=2)
k8s += at(6.15, TOP + 0.63, 2.75, 2.86, '<svg class="imgbox" viewBox="0 0 396 412"><rect x="3" y="3" width="390" '
          'height="406" rx="16" pathLength="1"/></svg>', step=2)
k8s += at(6.15, TOP + 3.58, 2.75, 0.5, '<p class="cap c" style="color:var(--body);font-size:28px">built once, from a '
          'Dockerfile</p>', step=2)
k8s += at(8.9, TOP + 2.0, 0.55, 0.2, '<div class="arr"></div>', step=3)
cl = '<div class="cluster"><p class="dh l">Kubernetes cluster</p>'
for h, sub in [("Node", "64 CPU cores"), ("Node", "8 × A10 GPUs"), ("Node", "4 × A100 GPUs")]:
    cl += f'<div class="node"><b>{h}</b><span>{sub}</span></div>'
cl += '</div>'
k8s += at(9.55, TOP + 0.15, 3.18, 4.35, cl, step=3)
k8s += at(9.55, TOP + 4.55, 3.18, 0.5, '<p class="cap c">the scheduler picks a node with a free GPU</p>', step=3)
k8s += at(6.15, TOP + 0.63, 2.75, 2.86, '<div class="chip">your container</div>', "mover", step=4)
slide("Kubernetes and Containers", k8s, steps=4, cls="k8sintro")

# Access methods: overview, then each door highlighted; the Kubernetes door animates a sweep of jobs
LANES = [("llm", [("Hosted LLMs", "browser chat or an API key"), ("AI gateway", "checks your token, routes"),
                  ("Model servers", "open-weight models on NRP GPUs")]),
         ("jh", [("JupyterHub", "log in, pick an image and a GPU"), ("Your notebook server", "a container started for you"),
                 ("A CPU or GPU node", "chosen by Kubernetes")]),
         ("k8s", [("Kubernetes", "`kubectl apply -f job.yaml`"), ("Scheduler", "finds a node with what you asked for"),
                  ("Your pods", "run, write results, exit")])]
ly, lh, gap = TOP + 0.15, 0.68, 0.14
acc = at(X0, ly, 1.05, 3 * lh + 2 * gap, '<div class="you">You</div>')
xs = [(2.2, 3.15), (5.9, 3.15), (9.58, 3.15)]
for i, (key, boxes) in enumerate(LANES):
    y = ly + i * (lh + gap)
    acc += at(X0 + 1.05, y + lh / 2 - 0.02, xs[0][0] - X0 - 1.05, 0.04, '<div class="arr"></div>', f"lane l-{key}")
    for j, ((h, sub), (bx, bw)) in enumerate(zip(boxes, xs)):
        acc += at(bx, y, bw, lh, box(h, sub), f"lane l-{key}")
        if j < 2:
            acc += at(bx + bw, y + lh / 2 - 0.02, xs[j + 1][0] - bx - bw, 0.04, '<div class="arr"></div>',
                      f"lane l-{key}")
b0 = ly + 3 * lh + 2 * gap + 0.35
acc += at(X0, b0 + 0.1, 12.13, 1.6, '<p style="font-size:40px">No login node and no batch queue: pick the door that '
          'matches how much infrastructure you want to touch.</p><p style="font-size:40px;margin-top:20px">Most '
          'people start with JupyterHub or the hosted LLMs.</p>', only="0")
acc += at(X0, b0, 4.6, 2.5, img(IMG / "openwebui_crop.png", "framed dark"), only="1")
acc += at(5.55, b0, 7.18, 1.95, code("""from openai import OpenAI
client = OpenAI(base_url="https://ellm.nrp-nautilus.io/v1",
                api_key=TOKEN)        # from nrp.ai/llmtoken
client.chat.completions.create(model="gpt-oss",
    messages=[{"role": "user", "content": "Hi"}])""", 12.5), only="1")
acc += at(5.55, b0 + 2.05, 7.18, 0.45, '<p class="cap">In the browser at nrp-openwebui.nrp-nautilus.io, or from any '
          'code that speaks the OpenAI API</p>', only="1")
acc += at(X0, b0, 4.6, 2.5, img(IMG / "jupyterlab_gpu.png"), only="2")
acc += at(5.55, b0 + 0.05, 7.18, 2.5, ul(["Log in with your campus account through CILogon",
                                          "Choose an image, CPUs, memory and a GPU type",
                                          "NRP's hubs: jupyterhub-west.nrp-nautilus.io and jupyterhub-east.nrp-nautilus.io",
                                          "Today's demo: jh-training.nrp-nautilus.io"], 17), only="2")
# the sweep: what kubectl shows, and where the pods landed; on the last step the first job has finished and the
# pending one has taken its GPU


def term_lines(lines):
    return "".join(f'<span class="ln{" cmd" if l.startswith("$ ") else ""}">{escape(l)}</span>' for l in lines)


kt = (f'<div class="code kterm" style="font-size:22px"><pre>{term_lines(apply_lines())}<span class="swap">'
      f'<span class="v3">{term_lines(get_pods(3))}</span><span class="v4">{term_lines(get_pods(4))}</span>'
      f'</span></pre></div>')
sweep = at(X0, b0 - 0.05, 5.75, 0.4, '<p class="dh l">Your jobs</p>')
sweep += at(X0, b0 + 0.35, 5.75, 2.2, kt)
sweep += at(X0 + 5.82, b0 + 1.2, 0.48, 0.04, '<div class="arr"></div>')
for k, (head, slots) in enumerate([("GPU node · 4 × A10", ["s0", "s1", "busy", "busy"]),
                                   ("GPU node · 4 × RTX 3090", ["busy"] * 4)]):
    gx = 6.95 + k * 2.95
    inner = f'<p class="dh l">{head}</p><div class="slots">'
    for sid in slots:
        if sid == "busy":
            inner += '<div class="slot busy">busy</div>'
        elif sid == "s0":
            inner += '<div class="slot mine s0"><i class="a1">lr-0.1</i><i class="a2">lr-0.001</i></div>'
        else:
            inner += '<div class="slot mine">lr-0.01</div>'
    inner += "</div>"
    sweep += at(gx, b0 + 0.3, 2.78, 1.85, f'<div class="gnode">{inner}</div>')
sweep += at(6.95, b0 + 2.25, 5.78, 0.5, '<p class="cap">lr-0.001 waits in Pending until a GPU frees up; a finished '
            'job releases its GPU</p>')
acc += f'<div class="sweep" data-only="3 4">{sweep}</div>'
slide("Access Methods", acc, steps=4, cls="access")

# What NRP is for: the data spectrum builds left to right
segs = [("Public or synthetic data", "public datasets, simulations, benchmark and synthetic data", "#D3EEE1"),
        ("De-identified data", "if your IRB and data use agreement allow it", "#E6F1D3"),
        ("Protected health information", "PHI or identifiable patient data, including in LLM prompts", "#F6D6D3")]
w = 12.13 / 3
y = TOP + 0.75
spec = ""
for i, (h, sub, fill) in enumerate(segs):
    x = X0 + i * w
    spec += at(x + 0.03, y, w - 0.06, 0.85, f'<div class="seg" style="background:{fill}">{h}</div>', "rise",
               style=f"transition-delay:{i * 0.25:.2f}s")
    spec += at(x + 0.15, y + 0.95, w - 0.3, 0.8, f'<p class="cap c" style="font-size:30px;color:#2B3648">{sub}</p>',
               "rise", style=f"transition-delay:{i * 0.25 + 0.1:.2f}s")
spec += at(X0, y - 0.62, 2 * w, 0.62, '<div class="brk ok"><span>OK on NRP</span></div>', step=1)
spec += at(X0 + 2 * w, y - 0.62, w, 0.62, '<div class="brk no"><span>Not on NRP</span></div>', step=1)
spec += at(X0, TOP + 2.85, 12.13, 0.4, '<p class="dh l" style="font-size:38px">Good uses</p>', step=2)
spec += at(X0, TOP + 3.3, 12.13, 0.5, '<p style="font-size:36px">model development and training · image analysis · '
           'simulation · teaching · LLMs on non-sensitive text</p>', step=2)
spec += at(X0, TOP + 3.95, 12.13, 0.45, '<p class="cap" style="font-size:32px">Also not for: commercial work, or '
           'services that need guaranteed uptime (it is a shared, best-effort cluster)</p>', step=2)
spec += at(X0, 5.95, 12.13, 0.6, '<p style="font-size:42px;color:#B3261E">NRP is <b>not HIPAA compliant</b>. Keep PHI '
           "in UCLA Health's approved environments.</p>", step=1)
slide("What NRP Is For", spec, steps=2)

section("Getting Access")

ga = at(X0, TOP + 0.15, 6.3, 5.1, '<div class="steps">'
        '<p class="sh">1.&nbsp; Log in at <b>nrp.ai</b></p><p class="sd">Log In → CILogon → choose <b>UCLA</b> → your UCLA login</p>'
        '<p class="sh">2.&nbsp; Get into a namespace</p><p class="sd">Request one at <b>get-started.nrp-nautilus.io</b><br>'
        'Or ask an existing namespace admin to add you</p>'
        '<p class="sh">3.&nbsp; Start working</p><p class="sd">JupyterHub, kubectl, or an LLM token from <b>nrp.ai/llmtoken</b></p>'
        '<p class="sd" style="margin-top:44px"><b>Who can request a namespace:</b> faculty, staff, postdocs and research '
        'scientists. <b>Students:</b> your PI or instructor requests it and adds you.</p></div>', "stagger")
ga += at(7.2, TOP + 0.05, 5.53, 0.3, link("https://get-started.nrp-nautilus.io", size=14, align="right"))
ga += at(7.2, TOP + 0.42, 5.53, 4.8, img(IMG / "namespace_form.png", "framed", fit="contain"), "pop")
slide("Getting Access", ga)

ns = at(X0, TOP + 0.15, 4.75, 5.1, ul([
    "Your group's workspace on the cluster",
    "One per lab, project or course; the PI or instructor is its admin and adds members",
    "Needed for GPU jobs, storage, your own JupyterHub, and **API access** to the hosted LLMs",
    "Not needed to chat with the LLMs in the browser", "What's inside is visible only to its members"], 18))
spaces = [("lab-smith", "Dr. Smith (admin) and 3 students", "GPU jobs · a data volume · LLM tokens", ""),
          ("bio-course", "the instructor (admin) and 40 students", "a course JupyterHub · shared datasets", ""),
          ("another-lab", "their members only", "you can't see their jobs or data", "dim")]
inner = '<div class="cluster big"><p class="dh l">Nautilus cluster</p>'
for i, (name, people, inside, st) in enumerate(spaces):
    inner += (f'<div class="nsb {st}" style="transition-delay:{0.3 + i * 0.3:.1f}s"><code>{name}</code>'
              f'<div><b>{people}</b><span>{inside}</span></div></div>')
inner += "</div>"
ns += at(5.7, TOP + 0.1, 7.03, 5.1, inner, "nsd")
slide("What is a Namespace?", ns)

tc = ""
chain = [("Your laptop", "`kubectl` + `~/.kube/config`"), ("CILogon", "your UCLA login, once"),
         ("Nautilus API", "checks who you are"), ("Your namespace", "jobs, pods, data")]
bw, gp = 2.75, 0.38
for i, (h, sub) in enumerate(chain):
    x = X0 + i * (bw + gp)
    tc += at(x, TOP + 0.15, bw, 0.78, box(h, sub, "active" if i == 0 else ""), "rise",
             style=f"transition-delay:{i * 0.35:.2f}s")
    if i < 3:
        tc += at(x + bw, TOP + 0.52, gp, 0.04, '<div class="arr"></div>', "rise",
                 style=f"transition-delay:{i * 0.35 + 0.2:.2f}s")
tc += at(X0, TOP + 1.35, 5.9, 3.9, '<div class="steps">'
         '<p class="sh">1.&nbsp; Install <b>kubectl</b> and the <b>kubelogin</b> plugin</p>'
         '<p class="sh">2.&nbsp; Download your config from <b>nrp.ai/config</b>, save it as ~/.kube/config</p>'
         '<p class="sh">3.&nbsp; Run any kubectl command: a browser opens for the UCLA login</p>'
         '<p class="sh">4.&nbsp; Work in your namespace</p>'
         '<p class="cap" style="margin-top:30px">On the training JupyterHub this is already set up.</p></div>')
tc += at(6.83, TOP + 1.35, 5.9, 3.55, code("""# one-time setup
mkdir -p ~/.kube
curl -o ~/.kube/config -fSL https://nrp.ai/config

# first command: a browser opens for CILogon
kubectl get pods -n my-lab
No resources found in my-lab namespace.

# make my-lab your default namespace
kubectl config set contexts.nautilus.namespace my-lab""", 12.5, cls="typed"))
tc += at(6.83, TOP + 5.0, 5.9, 0.3, link("https://nrp.ai/documentation/userdocs/start/getting-started/", size=12))
slide("Talking to the Cluster", tc)

section("GPUs")

# the fleet chart, redrawn as HTML bars that grow in, colored by memory per GPU
TIER_COL = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]


def tier(mib):
    return 0 if mib < 17000 else 1 if mib < 25000 else 2 if mib < 50000 else 3


def short(p):
    if "MIG-1g.10gb" in p:
        return "A100 slices (10 GB)"
    for a, b in [("NVIDIA-", ""), ("GeForce-", ""), ("Tesla-", ""), ("-SXM4-80GB", " 80GB SXM"),
                 ("-80GB-PCIe", " 80GB PCIe"), ("-80GB-HBM3", ""), ("-SXM2-", " "), ("-NVL", "")]:
        p = p.replace(a, b)
    return p.replace("-", " ")


top = sorted(FLEET, key=lambda r: -r["gpus"])[:14]
rest = sum(r["gpus"] for r in FLEET if r not in top)
mx = max(r["gpus"] for r in top)
bars = f'<p class="dh l" style="margin-bottom:10px">{GPUS:,} GPUs across {GPU_MODELS} models</p>'
for i, r in enumerate(top + [dict(product=f"{GPU_MODELS - len(top)} other models", gpus=rest, memory_mib=-1)]):
    col = TIER_COL[tier(r["memory_mib"])] if r["memory_mib"] >= 0 else "#c3c2b7"
    bars += (f'<div class="brow"><span class="bn">{escape(short(r["product"]))}</span><span class="bt">'
             f'<i style="--w:{r["gpus"] / mx * 100:.1f}%;background:{col};transition-delay:{i * 0.05:.2f}s"></i>'
             f'<em>{r["gpus"]}</em></span></div>')
bars += '<div class="legend">' + "".join(f'<span><i style="background:{c}"></i>{t}</span>' for c, t in
                                         zip(TIER_COL, ["Up to 16 GB", "20–24 GB", "32–48 GB", "80 GB and up"])) + "</div>"
slide("GPUs on NRP",
      at(X0, TOP + 0.15, 5.0, 5.0, ul([f"{GPUS:,} GPUs in {GPU_MODELS} models, contributed by campuses",
                                       "Most common: A10 and RTX 3090, 24 GB each",
                                       "About 140 A100s with 80 GB, plus H100s and H200s",
                                       "Ask for the GPU memory your job needs, not a brand name",
                                       "What's free right now: **nrp.ai/viz/resources**"], 19), "stagger") +
      at(5.9, TOP + 0.05, 6.83, 5.25, f'<div class="bars">{bars}</div>'))

rows = [["GPU memory", "Examples", "Good for", "How to ask"],
        ["Up to 16 GB", "RTX 2080 Ti, GTX 1080 Ti, A4000, A100 slices", "Teaching, debugging, classic ML, small CNNs",
         "nvidia.com/gpu: 1"],
        ["20–24 GB", "A10, RTX 3090, L4, RTX 4090",
         "Most deep learning; fine-tuning and serving models up to ~8B parameters", "nvidia.com/gpu: 1 + memory or model"],
        ["32–48 GB", "L40, V100 32 GB, RTX A6000, A40", "Bigger models and batches; serving models up to ~30B",
         "nvidia.com/gpu, or rtxa6000 / a40"],
        ["80 GB and up", "A100 80 GB, H100, H200", "Large training runs and large models",
         "A100: access request; H100/H200 reserved"]]
slide("Choosing a GPU",
      at(X0, TOP + 0.1, 12.13, 4.1, table(rows, [1.55, 3.0, 4.0, 3.55], 15), "rows") +
      at(X0, 5.75, 12.13, 0.4, '<p style="font-size:32px">Current PyTorch builds need <b>Turing or newer</b>: on a GTX '
         '1080 Ti or V100, use an older image.</p>') +
      at(X0, 6.25, 12.13, 0.3, link("https://nrp.ai/documentation/userdocs/running/gpu-pods/", size=14)))

# Ways to run work: JupyterHub, a pod, a Deployment, each in turn (earlier ones dim), then a Job: six jobs from a
# sweep are submitted, four start, two wait in Pending and take the first GPUs that free up
rw = ""
for i, (head, items) in enumerate(RUN_WAYS):
    y = TOP + 0.1 + i * 1.65
    rw += at(X0, y, 5.55, 1.6, f'<p class="dh l" style="font-size:38px">{escape(head)}</p>'
             f'<div style="margin-top:14px">{ul(items, 15.5)}</div>', f"lw b{i}", step=i or None)
rw += at(6.55, TOP + 0.1, 6.18, 0.45, '<p class="dh l" style="font-size:38px">Batch: a Job</p>', step=3)
rw += at(6.55, TOP + 0.52, 6.18, 0.75, ul(RUN_JOB, 15.5), step=3)
rw += at(6.55, TOP + 1.3, 6.18, 0.52, code(RUN_CMD, 12, cls="one"), step=3)
UNIT, T0 = 0.55, 1.5                      # seconds per time unit; when the first jobs start
LX, TW, LH, LG = 115, 775, 58, 11         # label column, track width, lane height and gap (px)
g = '<span class="plab">Pending</span>'
for i, (job, gpu, t0, t1) in enumerate(SWEEP):
    g += (f'<span class="pc" style="left:{LX + i * 129}px;--a:{0.5 + i * 0.08:.2f}s;--b:{T0 + t0 * UNIT:.2f}s">'
          f'{job}</span>')
for k in range(4):
    g += f'<span class="glab" style="top:{70 + k * (LH + LG)}px">GPU {k + 1}</span>'
    g += f'<span class="trk" style="top:{70 + k * (LH + LG)}px"></span>'
for job, gpu, t0, t1 in SWEEP:
    bw = (t1 - t0) / SWEEP_T * TW - 6
    st = f"left:{LX + t0 / SWEEP_T * TW + 3:.0f}px;top:{70 + gpu * (LH + LG) + 4}px;"
    tm = f"--t0:{T0 + t0 * UNIT:.2f}s;--t1:{T0 + t1 * UNIT:.2f}s;--du:{(t1 - t0) * UNIT:.2f}s"
    g += (f'<span class="gb" style="{st}--w:{bw:.0f}px;{tm}"></span>'
          f'<span class="gl" style="{st}--w:{bw:.0f}px;{tm}">{job}</span>')
g += f'<span class="nowl" style="--t0:{T0:.2f}s;--du:{SWEEP_T * UNIT:.2f}s"></span>'
g += f'<span class="tax" style="top:{70 + 4 * (LH + LG) - 4}px"></span><span class="tlab" style="top:{70 + 4 * (LH + LG)}px">time</span>'
rw += at(6.55, TOP + 1.95, 6.18, 2.95, f'<div class="gantt">{g}</div>', step=3)
rw += at(6.55, TOP + 4.85, 6.18, 0.55, f'<p class="cap" style="font-size:27px">{escape(RUN_CAPTION)}</p>', step=3)
# steps 0-2: what each way looks like (right, top), and what happens to its GPU or node over time (right, bottom)
LCT = 3.6                                 # seconds for a timeline to play


def lifecycle(k, lane, segs, marks):
    """A timeline that draws itself on step k: segs (start, end, kind, text) and marks (pos, text, kind, place, align)
    in fractions of the track."""
    h = f'<span class="lcl">{lane}</span><span class="trk" style="top:40px"></span>'
    for t0, t1, kind, text in segs:
        w = (t1 - t0) * TW - 4
        h += (f'<span class="sg {kind}" style="left:{LX + t0 * TW + 2:.0f}px;--w:{w:.0f}px;--t0:{0.5 + t0 * LCT:.2f}s;'
              f'--du:{(t1 - t0) * LCT:.2f}s">{escape(text)}</span>')
    for pos, text, kind, place, align in marks:
        x = LX + pos * TW
        tx = {"start": f"left:{x - 2:.0f}px", "center": f"left:{x - 300:.0f}px;width:600px;text-align:center",
              "end": f"right:{890 - x - 2:.0f}px;text-align:right"}[align]
        h += (f'<span class="mk {kind}" style="left:{x - 1.5:.0f}px;--t:{0.5 + pos * LCT:.2f}s"></span>'
              f'<span class="mt {kind}" style="{tx};top:{0 if place == "above" else 110}px;--t:{0.5 + pos * LCT:.2f}s">'
              f'{escape(text)}</span>')
    return at(6.55, TOP + 3.35, 6.18, 1.9, f'<div class="lc lc{k}">{h}</div>', only=str(k))


SPAWNER = IMG / "jhub_spawner.png"         # the hub's server options page, where you pick the GPU
if SPAWNER.exists():                      # side by side: pick a GPU, then the notebook running on it
    rw += at(6.55, TOP + 0.05, 2.95, 0.4, '<p class="dh l" style="font-size:26px">1. Pick a GPU</p>', only="0")
    rw += at(6.55, TOP + 0.45, 2.95, 2.65, img(SPAWNER, "framed"), only="0")
    rw += at(9.6, TOP + 0.05, 3.13, 0.4, '<p class="dh l" style="font-size:26px">2. Your notebook runs on it</p>',
             only="0")
    rw += at(9.6, TOP + 0.45, 3.13, 2.65, img(IMG / "jupyterlab_gpu.png", "framed"), only="0")
else:
    rw += at(6.55, TOP + 0.1, 6.18, 3.0, img(IMG / "jupyterlab_gpu.png", "framed"), only="0")
rw += lifecycle(0, "GPU", [(0, .55, "run", "you work in notebooks"), (.55, .8, "idle", "idle")],
                [(.55, "you close the browser", "neutral", "above", "center"),
                 (.8, "1 h later: server stops, GPU back to the pool", "ok", "below", "end")])
pod_term = ["$ kubectl apply -f pod.yaml", "pod/dev-pod created", "$ kubectl exec -it dev-pod -- bash",
            "root@dev-pod:/# nvidia-smi -L", "GPU 0: NVIDIA A10 (UUID: GPU-…)", "root@dev-pod:/# python test.py"]
rw += at(6.55, TOP + 0.3, 6.18, 2.3, '<div class="code kterm podterm" style="font-size:25px"><pre>'
         + "".join(f'<span class="ln{" cmd" if l.startswith(("$ ", "root@")) else ""}" style="--i:{i}">{escape(l)}</span>'
                   for i, l in enumerate(pod_term)) + "</pre></div>", only="1")
rw += lifecycle(1, "GPU", [(0, .8, "run", "dev-pod: a shell, tests, debugging")],
                [(.8, "6 h: the pod is deleted", "bad", "below", "end")])
dep = ('<div class="depbox"><p class="dh l" style="font-size:28px">Deployment <code>web-app</code> · 2 replicas</p>'
       '<div class="dpods"><div class="dpod"><code>web-app-5d59d-x2kqp</code><b>Running</b></div>'
       '<div class="dpod swapper"><span class="p1"><code>web-app-5d59d-m4q9d</code><b>Running</b></span>'
       '<span class="p2"><code>web-app-5d59d-m4q9d</code><b>crashed</b></span>'
       '<span class="p3"><code>web-app-5d59d-c8w3n</code><b>Running</b></span></div></div>'
       '<p class="cap" style="font-size:26px;margin-top:18px">Kubernetes keeps two copies running; when one crashes, it '
       'starts a replacement</p></div>')
rw += at(6.55, TOP + 0.3, 6.18, 2.45, dep, only="2")
rw += lifecycle(2, "Node", [(0, .42, "run", "web-app"), (.45, .92, "run", "web-app (replacement)")],
                [(.435, "crash: restarted for you", "bad", "above", "center"),
                 (.92, "2 weeks: removed, unless admins grant an exception", "neutral", "below", "end")])
slide("Ways to Run Work", rw, steps=3, cls="runways")

# the GPU job: each part of the YAML lights up with its explanation
yaml = """apiVersion: batch/v1
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
              - {key: nvidia.com/gpu.compute.major, operator: Gt, values: ["7"]}"""
groups = {3: 1, 10: 2, 11: 2, 12: 3, 13: 3, 14: 3, 15: 4, 16: 4, 17: 4, 18: 4, 19: 4, 20: 4, 21: 4}
yh = code(yaml, 12)
for ln_no in range(len(yaml.split("\n")), 0, -1):         # tag lines with their group, from the end
    pass
parts = yh.split('<span class="ln">')
yh = parts[0] + "".join(f'<span class="ln g{groups.get(i, 0)}">' + p for i, p in enumerate(parts[1:], 1))
call = ""
for k, (h, b) in enumerate([("Where:", "your namespace"), ("What:", "a container image, and the command to run"),
                            ("Resources:", "2 CPUs, 6 GB of memory, one GPU"),
                            ("Which GPU:", "more than 20 GB, Ampere or newer; or name exact models")], 1):
    call += f'<p class="co c{k}">({k}) <b>{h}</b> {b}</p>'
slide("A GPU Job", at(X0, TOP + 0.1, 8.25, 5.2, yh, "yaml") + at(9.1, TOP + 0.2, 3.63, 5.0, call, "calls"),
      steps=4, cls="gpujob")

out = "".join(f'<span class="ol" style="--d:{i}">{escape(l) or " "}</span>' for i, l in enumerate(DEMO_OUT))
slide("Running the Job",
      at(X0, TOP + 0.1, 6.3, 3.0, code("""# submit
kubectl apply -f gpu-job.yaml

# watch: Pending → Running → Completed
kubectl get pods -l job-name=gpu-train-daniel

# read the output
kubectl logs -f job/gpu-train-daniel

# clean up
kubectl delete job gpu-train-daniel""", 14)) +
      at(X0, TOP + 3.3, 6.3, 1.9, '<p style="font-size:34px">Stuck in <b>Pending</b>? <code>kubectl describe pod</code> '
         'says why, usually that no matching GPU is free.</p><p style="font-size:34px;margin-top:20px">Our test: under '
         '30 s from submit to done on an A10 that had the image; several minutes in Pending when the cluster was '
         'full.</p>') +
      at(7.15, TOP + 0.1, 5.58, 3.55, f'<div class="code term" style="font-size:25px"><div class="ct">Output, 9 Nov '
         f'2026</div><pre>{out}</pre></div>', step=1), steps=1, cls="runjob")

slide("Using GPUs Fairly",
      at(X0, TOP + 0.1, 5.9, 0.45, '<p class="dh l" style="font-size:42px">Do</p>') +
      at(X0, TOP + 0.6, 5.9, 4.6, ul(["Run batch work as a **Job** that exits",
                                      "Request what you'll use; keep limits within 20% of requests",
                                      "Keep data on a persistent volume or in S3", "Run a sweep as many one-GPU jobs",
                                      "Borrow idle A100/H100s with `priorityClassName: opportunistic`, and checkpoint"],
                                     19), "stagger") +
      at(6.83, TOP + 0.1, 5.9, 0.45, '<p class="dh l" style="font-size:42px">Don\'t</p>', step=1) +
      at(6.83, TOP + 0.6, 5.9, 4.6, ul(["Leave a notebook holding a GPU overnight",
                                        "Put `sleep` in a Job to keep a GPU (bannable)",
                                        "Ask for 4 GPUs \"just in case\": use must stay above 40%",
                                        "Keep results on the pod's own disk; it vanishes with the pod"], 19), step=1) +
      at(X0, 6.3, 9.0, 0.3, link("https://nrp.ai/documentation/userdocs/start/policies/", size=14)), steps=1)

section("AI Services")

rows = [["Model", "Good for"], ["qwen3, qwen3-small", "Hard reasoning, long documents, images"],
        ["gpt-oss", "General chat, reproducible research"], ["glm-5, kimi, minimax", "Agentic coding"],
        ["deepseek-v4-flash", "Whole codebases, very long documents"],
        ["gemma, gemma-small", "Images, video, audio transcription"], ["qwen3-embedding", "Search and RAG (embeddings)"]]
slide("Hosted LLMs",
      at(X0, TOP + 0.15, 5.3, 5.0, ul(["Open-weight models on NRP GPUs, behind one OpenAI-compatible endpoint:",
                                       ("ellm.nrp-nautilus.io/v1", 1),
                                       "Free for non-commercial research and education",
                                       "Prompts are processed on NRP hardware, not sent to a commercial provider",
                                       "Still not for PHI", "About 7.1 billion tokens a day (September 2026)"], 18),
         "stagger") +
      at(6.3, TOP + 0.2, 6.43, 4.2, table(rows, [2.5, 3.93], 14.5, mono=(0,)), "rows") +
      at(6.3, TOP + 4.55, 6.43, 0.3, link("https://nrp.ai/documentation/userdocs/ai/llm-managed/models/", size=13)) +
      at(6.3, TOP + 4.9, 6.43, 0.3, '<p class="cap" style="font-size:24px">Uses from the models page, 26 Oct 2026. '
         'The catalog rotates.</p>'))

shots = [(f, c) for f, c in [("claude_code_nrp.png", "Claude Code on NRP's gpt-oss, asked about the demo's GPU job"),
                             ("opencode_nrp.png", "opencode on NRP's qwen3, same question")] if (IMG / f).exists()]
ll = at(X0, TOP + 0.15, 3.85, 5.1, ul(["**In the browser:** Open WebUI", ("nrp-openwebui.nrp-nautilus.io", 1),
                                       "**From code:** the standard OpenAI library; token from nrp.ai/llmtoken",
                                       "**In JupyterHub:** Jupyter AI (in the demo)",
                                       "**Coding agents:** Claude Code, opencode, VS Code and others",
                                       ("tested configurations in the NRP docs", 1)], 17))
for i, (f, c) in enumerate(shots):
    ll += at(4.7, TOP + 0.1, 8.03, 0.35, f'<p class="dh l" style="font-size:28px">{escape(c)}</p>', only=str(i))
    ll += at(4.7, TOP + 0.5, 8.03, 4.75, img(IMG / f, "framed dark"), "pop", only=str(i))
slide("Using the LLMs", ll, steps=max(0, len(shots) - 1))

slide("Jupyter AI",
      at(X0, TOP + 0.1, 2.6, 5.15, img(IMG / "jupyter-ai.png", "framed")) +
      at(X0 + 2.8, TOP + 0.1, 1.85, 5.15, img(IMG / "jupyter-ai2.png", "framed")) +
      at(5.75, TOP + 0.15, 6.98, 3.1, ul(["Already pointed at NRP's models on the training hub, and on any course hub "
                                          "you run", "**Chat panel:** ask about code, an error or a concept",
                                          "**/fix:** select a cell that crashed; it explains and proposes a fix",
                                          "**%%ai magics:** {variables} in a prompt become their live values, so the "
                                          "model sees your data"], 17), "stagger") +
      at(5.75, TOP + 3.55, 6.98, 1.7, code("""%%ai openai-chat:gpt-oss
Here is a summary of my dataset: {summary}
Which columns would you check first, and why?""", 13, cls="typed")))

slide("Running Your Own Models",
      at(X0, TOP + 0.15, 12.13, 4.3, ul([
          "**Serve your own model:** vLLM or SGLang on a GPU in your namespace, your weights or your fine-tune behind "
          "the same OpenAI API; ask the admins before running one as a long-lived service",
          "**Train and fine-tune:** PyTorch and Hugging Face in GPU jobs, from one GPU to eight on a node",
          "**Search your documents (RAG):** qwen3-embedding and NRP's managed Milvus vector database",
          "**Inference accelerators:** Qualcomm Cloud AI 100 cards, requested in a job like a GPU"], 20), "stagger") +
      at(X0, 5.45, 12.13, 0.4, '<p style="font-size:34px">Worked examples: the PEARC26 tutorial (serving, RAG), and a '
         'physics neural network trained in GPU jobs (CMS HATS)</p>') +
      at(X0, 5.9, 12.13, 0.35, link("https://training.nrp-nautilus.io", size=16)))

section("Labs and Classes")

rows = [["Your class needs", "A hub on NRP gives it"],
        ["The same environment for every student", "A container image you choose"],
        ["No laptop setup on day one", "JupyterLab in the browser, with campus login"],
        ["GPUs for a neural-network unit", "GPU options on the start menu, with limits"],
        ["An AI assistant, without per-seat fees", "Jupyter AI and the hosted LLMs, preconfigured"],
        ["Shared datasets and notebooks", "One shared volume in every server"]]
slide("JupyterHub for Classes",
      at(X0, TOP + 0.15, 7.6, 4.4, table(rows, [3.65, 3.95], 15), "rows") +
      at(8.6, TOP + 0.2, 4.13, 5.0, ul(["**Instructors:** contact us; we'll help you set up a hub for your lab or course",
                                        "It's one configuration file in a namespace you own",
                                        "**Students:** if your course needs GPUs, ask your professor to get in touch"],
                                       18), "stagger"))

slide("Getting Started",
      at(X0, TOP + 0.2, 7.4, 5.1, '<div class="steps big">'
         '<p class="sh">1.&nbsp; Log in: <b>nrp.ai</b> (CILogon → UCLA)</p>'
         '<p class="sh">2.&nbsp; Request a namespace: <b>get-started.nrp-nautilus.io</b></p>'
         '<p class="sd cap">PIs, faculty, staff, postdocs; students ask their PI</p>'
         '<p class="sh">3.&nbsp; Try the LLMs: <b>nrp-openwebui.nrp-nautilus.io</b></p>'
         '<p class="sh">4.&nbsp; Run your first GPU job:<br><b>training.nrp-nautilus.io/ucla-health</b></p></div>',
         "stagger") +
      at(8.4, TOP + 0.2, 4.33, 0.5, '<p class="dh l" style="font-size:44px">Help</p>') +
      at(8.4, TOP + 0.75, 4.33, 4.6, ul(["Documentation: nrp.ai/documentation", "Support chat and email: nrp.ai/contact",
                                         "Labs, courses or a UCLA campus group: d4diaz@ucsd.edu"], 19)))

section("Live Demo")

slide("Acknowledgments",
      at(X0, TOP + 0.15, 12.13, 5.0, ul([
          "NRP is supported by NSF awards OAC-1541349, OAC-1826967, OAC-2030508, OAC-1841530, OAC-2005369, OAC-2112167, "
          "CISE-1713149, CISE-2100237 and CISE-2120019",
          "Networks: CENIC, Pacific Wave, Internet2, MREN, GPN, NYSERNet, FLR, NEREN, Sun Corridor, OARnet, SCLR and the "
          "Albuquerque GigaPoP",
          "The NRP operations teams at SDSC, the University of Nebraska–Lincoln and MGHPCC, and the campuses that host and "
          "share their hardware, UCLA among them",
          "Clifford and UCLA Health IT's Research Tech Talks, for hosting"], 18)))

q = ""
for i, (lab, url) in enumerate([("Today's materials", "training.nrp-nautilus.io/ucla-health"), ("Portal and login", "nrp.ai"),
                                ("Request a namespace", "get-started.nrp-nautilus.io"),
                                ("Chat with the LLMs", "nrp-openwebui.nrp-nautilus.io"), ("LLM token", "nrp.ai/llmtoken"),
                                ("GPUs free right now", "nrp.ai/viz/resources"),
                                ("GPU jobs, docs", "nrp.ai/documentation/userdocs/running/gpu-pods"),
                                ("Support", "nrp.ai/contact")]):
    q += (f'<div class="qrow"><span>{lab}</span><a href="https://{url}" target="_blank" rel="noopener">{url}</a>'
          f'</div>')
slide("Questions?", at(X0, 1.7, 9.5, 4.6, q, "stagger") +
      at(X0, 6.25, 12.1, 0.45, '<p style="font-size:38px;color:#fff;font-weight:700">Daniel Diaz · d4diaz@ucsd.edu</p>'),
      kind="reverse")


# ═════════════════════════════════════════════════════════════════════════════════════
# PAGE
# ═════════════════════════════════════════════════════════════════════════════════════
WORDMARK = uri(TPL / "wordmark.png")
TITLE_BG = uri(TPL / "title.jpg")

CSS = """
:root { --navy:#182B49; --blue:#00629B; --gold:#FFCD00; --orange:#EB6834; --card:#EEF3F8; --card2:#DDE8F2; --body:#2B3648;
  --muted:#5C6778; --light:#C9D4E3; --bar:#747678; --dim:#F3F4F6; --dimt:#A3ABB6;
  --f-title:'Teko','Arial Narrow',sans-serif; --f-body:'Source Sans 3','Source Sans Pro','Helvetica Neue',Arial,sans-serif;
  --f-mono:'Source Code Pro',Menlo,Consolas,monospace; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 100%; height: 100%; background: #0b0f17; overflow: hidden; font-family: var(--f-body); color: var(--body); }
#deckStage { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; }
.slide { position: absolute; inset: 0; background: #fff; opacity: 0; visibility: hidden; transition: opacity .35s; overflow: hidden; }
.slide.active { opacity: 1; visibility: visible; }
.slide .ttl { position: absolute; left: 72px; top: 30px; width: 1776px; font: 600 80px/1.15 var(--f-title); color: var(--blue); letter-spacing: .01em; }
.bar { position: absolute; left: 0; right: 0; bottom: 0; height: 79px; background: var(--bar); }
.bar img { position: absolute; left: 26px; top: 16px; height: 46px; }
.bar .num { position: absolute; right: 300px; top: 24px; color: #fff; font: 600 22px var(--f-body); }
.a { position: absolute; }
.a > p, .a p { line-height: 1.25; }
.notes { display: none; }
b { font-weight: 700; color: inherit; }
code { font-family: var(--f-mono); font-size: .9em; }
/* bullets */
ul.bl { list-style: none; }
ul.bl li { position: relative; line-height: 1.22; }
ul.bl li.l0 { padding-left: 1.05em; margin-top: .55em; }
ul.bl li.l0:first-child { margin-top: 0; }
ul.bl li.l0::before { content: "•"; position: absolute; left: .15em; color: var(--navy); }
ul.bl li.l1 { padding-left: 2.1em; font-size: .85em; margin-top: .2em; }
ul.bl li.l1::before { content: "•"; position: absolute; left: 1.2em; color: var(--navy); }
/* text bits */
.dh { font: 700 34px/1.2 var(--f-body); color: var(--navy); text-align: center; }
.dh.l { text-align: left; }
.cap { font-size: 26px; color: var(--muted); }
.cap.c { text-align: center; }
.lk { display: block; color: var(--blue); text-decoration: underline; font-style: italic; }
.steps .sh { font-size: 40px; margin-top: 30px; } .steps .sh:first-child { margin-top: 0; }
.steps .sd { font-size: 34px; margin-top: 6px; }
.steps.big .sh { font-size: 44px; margin-top: 40px; }
/* boxes and arrows */
.bx { width: 100%; height: 100%; border-radius: 14px; background: var(--card); border: 2px solid #C9D4E3; display: flex;
  flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 6px 12px;
  transition: background .45s, color .45s, border-color .45s; }
.bx .bh { font-weight: 700; font-size: 30px; color: var(--navy); line-height: 1.1; transition: color .45s; }
.bx .bs { font-size: 23px; color: var(--body); line-height: 1.15; margin-top: 2px; transition: color .45s; }
.bx.active { background: var(--navy); border-color: var(--navy); } .bx.active .bh { color: #fff; } .bx.active .bs { color: var(--light); }
.arr { width: 100%; height: 100%; position: relative; }
.arr::before { content: ""; position: absolute; left: 0; right: 10px; top: 50%; height: 3px; margin-top: -1.5px; background: var(--muted); transition: background .45s; }
.arr::after { content: ""; position: absolute; right: 0; top: 50%; margin-top: -8px; border-left: 14px solid var(--muted); border-top: 8px solid transparent; border-bottom: 8px solid transparent; transition: border-color .45s; }
.you { width: 100%; height: 100%; background: var(--navy); border-radius: 14px; color: #fff; font: 700 36px var(--f-body); display: flex; align-items: center; justify-content: center; }
/* images, code, tables */
.im { display: block; max-width: 100%; max-height: 100%; width: auto; height: auto; }
.framed { border: 2px solid #DDE8F2; } .framed.dark { border-color: #3a3a3a; }
.code { width: 100%; height: 100%; background: var(--navy); border-radius: 8px; padding: 22px 26px; color: #fff; overflow: hidden; }
.code pre { font-family: var(--f-mono); line-height: 1.32; white-space: pre; }
.code .ln { display: block; transition: background .4s, opacity .4s; }
.code .cm { color: #9FB3CC; } .code .st { color: var(--gold); }
.code .ct { color: var(--gold); font: 600 .95em var(--f-body); margin-bottom: 8px; }
table.tb { width: 100%; border-collapse: collapse; }
table.tb th { background: var(--navy); color: #fff; text-align: left; padding: 14px 16px; font-weight: 700; }
table.tb td { padding: 14px 16px; vertical-align: middle; line-height: 1.2; }
table.tb td:first-child { font-weight: 700; }
table.tb tbody tr:nth-child(odd) td { background: var(--card); }
table.tb td.mono { font-family: var(--f-mono); font-weight: 400; font-size: .92em; }
/* section, title and reverse slides */
.slide.section { background: var(--navy); }
.slide.section .ttl { top: 400px; left: 131px; font-size: 150px; color: #fff; }
.slide.reverse { background: var(--navy); } .slide.reverse .ttl { color: #fff; }
.qrow { display: flex; gap: 40px; font-size: 34px; color: var(--light); line-height: 2.05; }
.qrow span { width: 446px; } .qrow a { color: var(--gold); font: 700 30px var(--f-mono); text-decoration: none; }
.slide.title { background: #0d1a2e center/cover no-repeat; }
.slide.title .shade { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(24,43,73,.92) 0%, rgba(24,43,73,.78) 55%, rgba(24,43,73,.35) 100%); }
.slide.title .tt { position: absolute; left: 96px; top: 150px; width: 1700px; color: #fff; font: 600 96px/0.95 var(--f-title); }
.slide.title .tg { position: absolute; left: 96px; top: 560px; color: var(--gold); font: 900 64px var(--f-body); }
.slide.title .tn { position: absolute; left: 96px; top: 680px; color: #fff; font-size: 42px; }
.slide.title .te { position: absolute; left: 96px; top: 745px; color: #E7E6E6; font-size: 34px; }
/* build steps: hidden until the slide reaches their step; data-only shows on listed steps only */
[data-s], [data-only] { transition: opacity .5s ease, transform .5s ease; }
[data-s] { opacity: 0; transform: translateY(14px); }
[data-s].on { opacity: 1; transform: none; }
[data-only] { opacity: 0; pointer-events: none; }
[data-only].on { opacity: 1; pointer-events: auto; }
.slide [data-only]:not(.on) { opacity: 0 !important; }  /* steps win over the open-slide fade-in */
.slide [data-s]:not(.on) { opacity: 0 !important; }
/* blocks that ease in when a slide opens */
.stagger li, .stagger .sh, .stagger .sd, .stagger .qrow, .rows tbody tr, .pop, .rise { opacity: 0; transform: translateY(12px); transition: opacity .5s ease, transform .5s ease; }
.slide.active .stagger li, .slide.active .stagger .sh, .slide.active .stagger .sd, .slide.active .stagger .qrow,
.slide.active .rows tbody tr, .slide.active .pop, .slide.active .rise { opacity: 1; transform: none; }
""" + "".join(f".slide.active .stagger li:nth-child({i}), .slide.active .stagger .qrow:nth-child({i}), "
              f".slide.active .rows tbody tr:nth-child({i}) {{ transition-delay: {0.1 + i * 0.12:.2f}s; }}\n"
              for i in range(1, 12)) + """
.slide.active .pop { transition-delay: .35s; }
/* Kubernetes intro */
.k8sintro .layer.on { transform: none; }
.cluster { width: 100%; height: 100%; border: 2px solid #B9C7D8; border-radius: 10px; padding: 18px 28px; }
.cluster .node { background: #fff; border: 2px solid #C9D4E3; border-radius: 10px; height: 144px; margin-top: 28px; padding: 22px; display: flex; flex-direction: column; justify-content: center; }
.cluster .node b { font-size: 28px; color: var(--navy); } .cluster .node span { font-size: 24px; }
.chip { width: 100%; height: 100%; background: #FDEBE3; color: var(--navy); border: 4px solid var(--orange); border-radius: 14px; font: 700 22px/1 var(--f-body); display: flex; align-items: center; justify-content: center; text-align: center; padding: 6px; box-shadow: 0 6px 18px rgba(0,0,0,.2); }
.imgbox { width: 100%; height: 100%; overflow: visible; }
.imgbox rect { fill: none; stroke: var(--orange); stroke-width: 5; stroke-dasharray: 1; stroke-dashoffset: 1; transition: stroke-dashoffset 1s ease .1s; }
.k8sintro [data-s].on .imgbox rect { stroke-dashoffset: 0; }
.k8sintro .mover { transition: left 1.1s cubic-bezier(.5,0,.2,1), top 1.1s cubic-bezier(.5,0,.2,1), width 1.1s cubic-bezier(.5,0,.2,1), height 1.1s cubic-bezier(.5,0,.2,1), opacity .3s, transform .3s; }
.k8sintro[data-cur="4"] .mover { left: 1625px !important; top: 539px !important; width: 151px !important; height: 86px !important; }
/* site map: pins drop in */
.usmap { display: block; overflow: visible; }
.usmap .land { fill: #E6ECF3; stroke: #fff; stroke-width: 1.2; stroke-linejoin: round; }
.usmap .pin { opacity: 0; transform: translateY(-70px); transition: transform .55s cubic-bezier(.3,1.45,.55,1), opacity .2s; }
.usmap .pin use { stroke: #fff; stroke-width: 1.2; } .usmap .pin circle { fill: #fff; }
.usmap .k-other use { fill: var(--blue); } .usmap .k-ops use { fill: var(--navy); }
.usmap .k-ucla use { fill: var(--gold); stroke: var(--navy); } .usmap .k-ucla circle { fill: var(--navy); }
.usmap .pl { font: 700 LABELpx var(--f-body); fill: var(--navy); paint-order: stroke; stroke: #fff; stroke-width: 7px; stroke-linejoin: round; opacity: 0; transition: opacity .4s; }
.slide.active .usmap .k-ops, .whatnrp:not([data-cur="0"]) .usmap .k-ucla, .whatnrp[data-cur="2"] .usmap .k-other,
.whatnrp[data-cur="3"] .usmap .k-other { opacity: 1; transform: none; transition-delay: var(--d); }
/* access methods: one lane lights up per step, the others dim */
.access[data-cur="1"] .lane:not(.l-llm) .bx, .access[data-cur="2"] .lane:not(.l-jh) .bx,
.access[data-cur="3"] .lane:not(.l-k8s) .bx, .access[data-cur="4"] .lane:not(.l-k8s) .bx { background: var(--dim); border-color: #E3E6EA; }
.access[data-cur="1"] .lane:not(.l-llm) .bh, .access[data-cur="2"] .lane:not(.l-jh) .bh, .access[data-cur="3"] .lane:not(.l-k8s) .bh,
.access[data-cur="4"] .lane:not(.l-k8s) .bh, .access[data-cur="1"] .lane:not(.l-llm) .bs, .access[data-cur="2"] .lane:not(.l-jh) .bs,
.access[data-cur="3"] .lane:not(.l-k8s) .bs, .access[data-cur="4"] .lane:not(.l-k8s) .bs { color: var(--dimt); }
.access[data-cur="1"] .l-llm .bx, .access[data-cur="2"] .l-jh .bx, .access[data-cur="3"] .l-k8s .bx, .access[data-cur="4"] .l-k8s .bx { background: var(--navy); border-color: var(--navy); }
.access[data-cur="1"] .l-llm .bh, .access[data-cur="2"] .l-jh .bh, .access[data-cur="3"] .l-k8s .bh, .access[data-cur="4"] .l-k8s .bh { color: #fff; }
.access[data-cur="1"] .l-llm .bs, .access[data-cur="2"] .l-jh .bs, .access[data-cur="3"] .l-k8s .bs, .access[data-cur="4"] .l-k8s .bs { color: var(--light); }
.access[data-cur="1"] .lane:not(.l-llm) .arr::before, .access[data-cur="2"] .lane:not(.l-jh) .arr::before, .access[data-cur="3"] .lane:not(.l-k8s) .arr::before, .access[data-cur="4"] .lane:not(.l-k8s) .arr::before { background: #D5DAE0; }
.access[data-cur="1"] .lane:not(.l-llm) .arr::after, .access[data-cur="2"] .lane:not(.l-jh) .arr::after, .access[data-cur="3"] .lane:not(.l-k8s) .arr::after, .access[data-cur="4"] .lane:not(.l-k8s) .arr::after { border-left-color: #D5DAE0; }
.access[data-cur="1"] .l-llm .arr::before, .access[data-cur="2"] .l-jh .arr::before, .access[data-cur="3"] .l-k8s .arr::before, .access[data-cur="4"] .l-k8s .arr::before { background: var(--blue); height: 5px; margin-top: -2.5px; }
.access[data-cur="1"] .l-llm .arr::after, .access[data-cur="2"] .l-jh .arr::after, .access[data-cur="3"] .l-k8s .arr::after, .access[data-cur="4"] .l-k8s .arr::after { border-left-color: var(--blue); }
.sweep { position: absolute; inset: 0; }
.kterm { padding: 18px 24px; } .kterm .ln { color: #C9D4E3; } .kterm .ln.cmd { color: #fff; }
.kterm .swap { display: block; position: relative; } .kterm .v3, .kterm .v4 { display: block; transition: opacity .45s; }
.kterm .v4 { position: absolute; left: 0; top: 0; opacity: 0; }
.access[data-cur="4"] .kterm .v3 { opacity: 0; } .access[data-cur="4"] .kterm .v4 { opacity: 1; }
.gnode { width: 100%; height: 100%; background: #fff; border: 2px solid #B9C7D8; border-radius: 10px; padding: 10px 16px; }
.slots { display: flex; gap: 12px; margin-top: 14px; }
.slot { width: 84px; height: 137px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font: 700 19px var(--f-body); position: relative; text-align: center; }
.slot.busy { background: #DDE1E6; color: #6B7480; } .slot.mine { background: var(--navy); color: #fff; }
.slot.s0 i { position: absolute; font-style: normal; transition: opacity .5s, transform .5s; }
.slot.s0 .a2 { opacity: 0; transform: translateY(-20px); }
.access[data-cur="4"] .slot.s0 .a1 { opacity: 0; transform: translateY(20px); }
.access[data-cur="4"] .slot.s0 .a2 { opacity: 1; transform: none; }
.access[data-cur="4"] .slot.s0 { animation: flash 1s ease; }
@keyframes flash { 0% { background: var(--gold); color: var(--navy); } 100% { background: var(--navy); } }
/* data spectrum */
.seg { width: 100%; height: 100%; border-radius: 10px; display: flex; align-items: center; justify-content: center; font: 700 36px var(--f-body); color: var(--navy); text-align: center; }
.brk { width: 100%; height: 100%; position: relative; text-align: center; font: 700 34px var(--f-body); }
.brk::after { content: ""; position: absolute; left: 8px; right: 8px; bottom: 18px; height: 5px; border-radius: 3px; }
.brk.ok { color: #1B7F55; } .brk.ok::after { background: #1B7F55; } .brk.no { color: #B3261E; } .brk.no::after { background: #B3261E; }
/* namespaces */
.cluster.big { padding: 18px 28px; } .nsb { display: flex; align-items: center; gap: 30px; height: 183px; margin-top: 28px; padding: 0 28px; background: var(--card); border: 2px solid #C9D4E3; border-radius: 12px; opacity: 0; transform: translateY(12px); transition: opacity .5s, transform .5s; }
.nsb code { font-size: 32px; font-weight: 600; color: var(--navy); width: 255px; flex: none; }
.nsb b { display: block; font-size: 30px; color: var(--navy); } .nsb span { font-size: 28px; }
.nsb.dim { background: var(--dim); border-color: #E3E6EA; } .nsb.dim code, .nsb.dim b, .nsb.dim span { color: var(--dimt); }
.slide.active .nsb { opacity: 1; transform: none; }
/* GPU bars */
.bars { width: 100%; height: 100%; }
.brow { display: flex; align-items: center; height: 39px; font-size: 22px; }
.brow .bn { width: 270px; text-align: right; padding-right: 14px; color: #52514e; white-space: nowrap; }
.brow .bt { flex: 1; display: flex; align-items: center; gap: 10px; }
.brow .bt i { display: block; height: 26px; width: 0; transition: width .9s cubic-bezier(.3,.7,.2,1); border-radius: 2px; }
.slide.active .brow .bt i { width: var(--w); }
.brow em { font-style: normal; color: #52514e; font-size: 20px; }
.legend { display: flex; gap: 22px; margin: 12px 0 0 284px; font-size: 20px; color: #52514e; }
.legend i { display: inline-block; width: 22px; height: 14px; margin-right: 6px; }
/* GPU job: highlight one part of the YAML per step */
.gpujob .calls .co { font-size: 34px; line-height: 1.25; margin-bottom: 28px; transition: opacity .4s, color .4s; }
""" + "".join(f".gpujob[data-cur=\"{k}\"] .ln.g{k} {{ background: rgba(255,205,0,.22); }}\n"
              f".gpujob[data-cur=\"{k}\"] .co:not(.c{k}) {{ opacity: .35; }}\n"
              f".gpujob[data-cur=\"{k}\"] .co.c{k} {{ color: var(--navy); }}\n" for k in range(1, 5)) + """
/* ways to run work: earlier blocks dim; the sweep plays out on four GPUs */
.runways .lw { transition: opacity .5s, transform .5s; }
.runways[data-cur="1"] .b0, .runways[data-cur="2"] .b0, .runways[data-cur="2"] .b1, .runways[data-cur="3"] .lw { opacity: .4 !important; }
.code.one { padding: 12px 22px; display: flex; align-items: center; }
.gantt { position: absolute; inset: 0; font-family: var(--f-mono); }
.gantt .plab, .gantt .glab, .gantt .tlab { position: absolute; left: 0; font: 700 24px var(--f-body); color: var(--navy); line-height: 58px; }
.gantt .plab { top: 0; line-height: 46px; color: #C27C0E; }
.gantt .tlab { left: auto; right: 0; font: 400 22px var(--f-body); color: var(--muted); line-height: 30px; }
.gantt .pc { position: absolute; top: 0; width: 120px; height: 46px; line-height: 42px; text-align: center; font-size: 19px; color: var(--navy); background: #FFF4DE; border: 2px solid #E9B55C; border-radius: 10px; opacity: 0; }
.gantt .trk { position: absolute; left: 115px; width: 775px; height: 58px; background: var(--dim); border-radius: 12px; }
.gantt .gb, .gantt .gl { position: absolute; height: 50px; border-radius: 10px; }
.gantt .gb { background: var(--blue); width: 0; }
.gantt .gl { width: 0; overflow: hidden; white-space: nowrap; line-height: 50px; text-align: left; padding-left: 16px; font-size: 20px; font-weight: 600; color: #fff; opacity: 0; }
.gantt .nowl { position: absolute; top: 62px; height: 284px; width: 3px; left: 115px; background: var(--gold); opacity: 0; }
.gantt .tax { position: absolute; left: 115px; width: 775px; height: 2px; background: var(--muted); }
.runways[data-cur="3"] .gantt .pc { animation: show .3s ease var(--a) forwards, leave .4s ease var(--b) forwards; }
.runways[data-cur="3"] .gantt .gb { animation: grow var(--du) linear var(--t0) both, done .4s ease var(--t1) forwards; }
.runways[data-cur="3"] .gantt .gl { animation: grow var(--du) linear var(--t0) both, show .25s linear calc(var(--t0) + .3s) forwards, darkt .4s ease var(--t1) forwards; }
.runways[data-cur="3"] .gantt .nowl { animation: sweepnow var(--du) linear var(--t0) forwards; }
@keyframes show { to { opacity: 1; } }
@keyframes leave { from { opacity: 1; } to { opacity: 0; transform: translateY(40px); } }
@keyframes grow { from { width: 0; } to { width: var(--w); } }
@keyframes done { to { background: #8FB0CF; } }
@keyframes darkt { to { color: var(--navy); } }
@keyframes sweepnow { 0% { left: 115px; opacity: 1; } 96% { opacity: 1; } 100% { left: 890px; opacity: 0; } }
/* ways to run work, steps 0-2: a timeline per way, the pod terminal, the deployment replacing a crashed pod */
.lc { position: absolute; inset: 0; }
.lc .lcl { position: absolute; left: 0; top: 40px; line-height: 58px; font: 700 24px var(--f-body); color: var(--navy); }
.lc .trk { position: absolute; left: 115px; width: 775px; height: 58px; background: var(--dim); border-radius: 12px; }
.lc .sg { position: absolute; top: 44px; height: 50px; width: 0; border-radius: 10px; overflow: hidden; white-space: nowrap; line-height: 50px; text-indent: 16px; font: 600 22px var(--f-body); color: #fff; }
.lc .sg.run { background: var(--blue); }
.lc .sg.idle { background: repeating-linear-gradient(45deg, #F2C46D 0 10px, #F8DDA6 10px 20px); color: var(--navy); }
.lc .mk { position: absolute; top: 30px; width: 3px; height: 78px; opacity: 0; }
.lc .mt { position: absolute; font: 600 24px var(--f-body); line-height: 30px; white-space: nowrap; opacity: 0; }
.lc .mk.neutral { background: var(--muted); } .lc .mt.neutral { color: var(--body); }
.lc .mk.ok { background: #1B7F55; } .lc .mt.ok { color: #1B7F55; }
.lc .mk.bad { background: #B3261E; } .lc .mt.bad { color: #B3261E; }
.runways[data-cur="0"] .lc0 .sg { animation: grow var(--du) linear var(--t0) both; }
.runways[data-cur="0"] .lc0 .mk, .runways[data-cur="0"] .lc0 .mt { animation: show .3s ease var(--t) forwards; }
.runways[data-cur="1"] .lc1 .sg { animation: grow var(--du) linear var(--t0) both; }
.runways[data-cur="1"] .lc1 .mk, .runways[data-cur="1"] .lc1 .mt { animation: show .3s ease var(--t) forwards; }
.runways[data-cur="2"] .lc2 .sg { animation: grow var(--du) linear var(--t0) both; }
.runways[data-cur="2"] .lc2 .mk, .runways[data-cur="2"] .lc2 .mt { animation: show .3s ease var(--t) forwards; }
.podterm .ln { opacity: 0; }
.runways[data-cur="1"] .podterm .ln { animation: show .01s linear calc(.3s + var(--i) * .4s) forwards; }
.depbox { width: 100%; height: 100%; border: 3px dashed #B9C7D8; border-radius: 14px; padding: 22px 26px; }
.dpods { display: flex; gap: 20px; margin-top: 22px; }
.dpod { flex: 1; height: 110px; border-radius: 12px; background: var(--card); border: 2px solid #C9D4E3; display: flex; flex-direction: column; justify-content: center; padding: 0 18px; position: relative; }
.dpod code, .dpod span code { font-size: 21px; color: var(--navy); } .dpod b { font-size: 24px; color: #1B7F55; margin-top: 6px; }
.dpod.swapper span { position: absolute; left: 18px; right: 18px; top: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; }
.dpod .p2, .dpod .p3 { opacity: 0; } .dpod .p2 b { color: #B3261E; }
.runways[data-cur="2"] .dpod .p1 { animation: hide .2s linear 1.95s forwards; }
.runways[data-cur="2"] .dpod .p2 { animation: show .2s linear 1.95s forwards, hide .3s linear 2.6s forwards; }
.runways[data-cur="2"] .dpod .p3 { animation: show .4s ease 2.6s forwards; }
.runways[data-cur="2"] .dpod.swapper { animation: crashbg .9s ease 1.95s; }
@keyframes hide { from { opacity: 1; } to { opacity: 0; } }
@keyframes crashbg { 0%, 100% { background: var(--card); } 25%, 75% { background: #F6D6D3; border-color: #B3261E; } }
/* job output types in, line by line */
.runjob .ol { display: block; opacity: 0; }
.runjob[data-cur="1"] .ol { animation: typein .01s forwards; animation-delay: calc(var(--d) * .45s + .3s); }
@keyframes typein { to { opacity: 1; } }
.code.typed .ln { opacity: 0; }
.slide.active .code.typed .ln { animation: typein .01s forwards; }
""" + "".join(f".slide.active .code.typed .ln:nth-child({i}) {{ animation-delay: {0.4 + i * 0.22:.2f}s; }}\n"
              for i in range(1, 14)) + """
/* notes overlay and pager */
#notes { position: fixed; left: 0; right: 0; bottom: 0; max-height: 40%; overflow: auto; background: rgba(10,15,25,.94); color: #f2f2f2; font: 18px/1.5 var(--f-body); padding: 18px 28px; display: none; white-space: pre-wrap; z-index: 10; }
body.show-notes #notes { display: block; }
#help { position: fixed; right: 12px; bottom: 10px; color: rgba(255,255,255,.75); background: rgba(0,0,0,.45); padding: 4px 8px; border-radius: 4px; font: 13px var(--f-body); z-index: 5; animation: helpfade 1s 6s forwards; }
@keyframes helpfade { to { opacity: 0; } }
/* print: every slide on its own page, in its final state */
body.print { overflow: visible; background: #fff; }
body.print #deckStage { position: static; transform: none !important; width: auto; height: auto; }
body.print .slide { position: relative; opacity: 1; visibility: visible; width: 1920px; height: 1080px; page-break-after: always; }
body.print [data-s], body.print .stagger li, body.print .pop, body.print .rise, body.print .nsb, body.print .rows tbody tr { opacity: 1 !important; transform: none !important; }
body.print #help { display: none; }
body.print .gantt * { animation: none !important; } body.print .gantt .gb { width: var(--w) !important; background: #8FB0CF; }
body.print .gantt .gl { opacity: 1; color: var(--navy); width: var(--w); } body.print .usmap .pin, body.print .usmap .pl { opacity: 1; transform: none; }
body.print .runways .lw { opacity: 1 !important; } body.print .gantt .pc, body.print .gantt .nowl { display: none; }
@page { size: 1920px 1080px; margin: 0; }
"""
CSS = CSS.replace("LABELpx", f"{LABEL_PX}px")

JS = r"""
(function () {
  const slides = Array.from(document.querySelectorAll('.slide'));
  const stage = document.getElementById('deckStage');
  const notes = document.getElementById('notes');
  const print = new URLSearchParams(location.search).has('print');
  let cur = 0, step = 0;
  function fit() {
    if (print) return;
    const f = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `translate(${(innerWidth - 1920 * f) / 2}px, ${(innerHeight - 1080 * f) / 2}px) scale(${f})`;
  }
  function apply(s, k) {
    s.dataset.cur = k;
    s.querySelectorAll('[data-s]').forEach(e => e.classList.toggle('on', +e.dataset.s <= k));
    s.querySelectorAll('[data-only]').forEach(e => e.classList.toggle('on', e.dataset.only.split(' ').includes(String(k))));
  }
  function show(i, atEnd) {
    cur = Math.max(0, Math.min(i, slides.length - 1));
    const s = slides[cur];
    step = atEnd ? +s.dataset.steps : 0;
    slides.forEach((x, k) => x.classList.toggle('active', k === cur));
    apply(s, step);
    notes.textContent = (s.querySelector('.notes') || {}).textContent || '';
    history.replaceState(null, '', '#' + (cur + 1));
  }
  function next() { const s = slides[cur]; if (step < +s.dataset.steps) { step++; apply(s, step); } else if (cur < slides.length - 1) show(cur + 1); }
  function prev() { const s = slides[cur]; if (step > 0) { step--; apply(s, step); } else if (cur > 0) show(cur - 1, true); }
  if (print) {
    document.body.classList.add('print');
    slides.forEach(s => { s.classList.add('active'); apply(s, +s.dataset.steps); });
    return;
  }
  document.addEventListener('keydown', e => {
    if (['ArrowRight', 'ArrowDown', ' ', 'PageDown', 'Enter'].includes(e.key)) { e.preventDefault(); next(); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(e.key)) { e.preventDefault(); prev(); }
    else if (e.key === 'Home') show(0); else if (e.key === 'End') show(slides.length - 1);
    else if (e.key === 'n' || e.key === 'N') document.body.classList.toggle('show-notes');
    else if (e.key === 'f' || e.key === 'F') { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen().catch(() => {}); }
  });
  document.addEventListener('click', e => { if (e.target.closest('a')) return; (e.clientX < innerWidth / 4 ? prev : next)(); });
  let x0 = null;
  document.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
  document.addEventListener('touchend', e => { if (x0 === null) return; const dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 50) (dx < 0 ? next : prev)(); x0 = null; });
  window.addEventListener('resize', fit); fit();
  function fromHash() {                       // #12 is slide 12; #12.3 is slide 12 at step 3
    const m = (location.hash || '').match(/^#(\d+)(?:\.(\d+))?/);
    if (!m) return show(0);
    if (+m[1] - 1 !== cur || !m[2]) show(+m[1] - 1);
    if (m[2]) { step = Math.min(+m[2], +slides[cur].dataset.steps); apply(slides[cur], step); }
  }
  window.addEventListener('hashchange', fromHash);
  fromHash();
})();
"""


def render(sd, with_notes):
    num = f'<span class="num">{sd["n"]}</span>'
    bar = f'<footer class="bar"><img src="{WORDMARK}" alt="San Diego Supercomputer Center">{num}</footer>'
    notes = f'<div class="notes">{escape(sd["notes"])}</div>' if with_notes else ""
    if sd["kind"] == "title":
        return (f'<section class="slide title" data-steps="0" style="background-image:url({TITLE_BG})">'
                '<div class="shade"></div><div class="tt">The National Research Platform<br>for AI-Enabled Research</div>'
                '<div class="tg">GPUs and AI for research and education</div>'
                '<div class="tn"><b>Daniel Diaz</b> · San Diego Supercomputer Center, UC San Diego</div>'
                f'<div class="te">UCLA Health IT Research Tech Talk · 10 November 2026</div>{notes}</section>')
    cls = {"section": "section", "reverse": "reverse"}.get(sd["kind"], "")
    return (f'<section class="slide {cls} {sd["cls"]}" data-steps="{sd["steps"]}"><h1 class="ttl">{escape(sd["title"])}'
            f'</h1>{sd["body"]}{bar}{notes}</section>')


def page(with_notes):
    help_ = "→ next · ← back · N notes · F full screen" if with_notes else "→ next · ← back · F full screen"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>GPUs and AI on the National Research Platform</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Teko:wght@500;600&family=Source+Sans+3:wght@400;600;700;900&family=Source+Code+Pro:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body><div id="deckStage">{"".join(render(s, with_notes) for s in SLIDES)}</div>
<div id="notes"></div><div id="help">{help_}</div>
<script>{JS if with_notes else JS.replace("document.body.classList.toggle('show-notes')", "0")}</script></body></html>
"""


OUT.write_text(page(False))                  # the published deck: no speaker notes
PRESENTER_OUT.write_text(page(True))         # for presenting: N shows the notes; not committed
print(f"{OUT}  ({len(SLIDES)} slides, {OUT.stat().st_size / 1e6:.1f} MB), notes copy: {PRESENTER_OUT}")
missing = [s["title"] for s in SLIDES if not s["notes"]]
if missing:
    print("  no notes for:", ", ".join(missing))
