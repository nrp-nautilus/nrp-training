"""'Using It Yourself', the demo, acknowledgments and questions.

Part of the SCinet deck: slides.py imports the section files in order. Shared constants and
helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
"""
from common import *  # noqa: F401,F403

# ═════════════════════════════════════════════════════════════════════════════════════
# USE IT
# ═════════════════════════════════════════════════════════════════════════════════════
section("Using It Yourself", "[0:31] You can use all of this. Here's how.")

ways = [("JupyterHub", "notebooks with a GPU, in the browser", "jupyterhub-west.nrp-nautilus.io"),
        ("Coder", "VS Code in the browser, in your namespace", "coder.nrp-nautilus.io"),
        ("kubectl", "jobs, services and storage in a namespace", "nrp.ai/config"),
        ("GitLab", "repos, CI in Kata VMs, a registry", "gitlab.nrp-nautilus.io"),
        ("LLM API", "OpenAI- and Anthropic-compatible", "ellm.nrp-nautilus.io/v1"),
        ("Open WebUI", "chat with every model", "nrp-openwebui.nrp-nautilus.io")]
we = []
for i, (h, b, u) in enumerate(ways):
    x, y = X0 + (i % 3) * 4.1, TOP + 0.2 + (i // 3) * 2.2
    we += [Box(x, y, 3.9, 1.95, h, b, head_size=22, sub_size=15, cls="rise", style=f"transition-delay:{i * 0.12:.2f}s"),
           Text(x, y + 1.35, 3.9, 0.4, T(u, size=13, color=BLUE, font=MONO, align="c"), cls="rise",
                style=f"transition-delay:{i * 0.12:.2f}s")]
we.append(Text(X0, 5.85, W, 0.5, T("Who uses them today: research groups, each in a namespace; courses, each with "
                                    "its own JupyterHub; and collaborations through OSG.", size=16, color=MUTED)))
add("Ways In", we, notes="""
[0:31] Six ways in, depending on how much infrastructure you want to touch. JupyterHub and Coder in the browser; kubectl for anything Kubernetes can run; GitLab for code and CI, the same one from earlier; the LLM API, the endpoint from the AI part; and Open WebUI to just chat with the models. Today that's research groups, courses that each get their own hub, and big collaborations through OSG.
""")

add("Getting Access", [
    Text(X0, TOP + 0.15, 6.3, 5.1, [
        T("1.  Log in at **nrp.ai**", size=20),
        T("Log In → CILogon → your institution", size=17, before=3),
        T("2.  Get into a namespace", size=20, before=16),
        T("Request one at **get-started.nrp-nautilus.io**", size=17, before=3),
        T("Or ask an existing namespace admin to add you", size=17, before=3),
        T("3.  Start working", size=20, before=16),
        T("JupyterHub, kubectl, GitLab, or an LLM token from **nrp.ai/llmtoken**", size=17, before=3),
        T("**Who can request a namespace:** faculty, staff, postdocs and research scientists; students through "
          "their PI.", size=16, before=20)], cls="stagger"),
    Link(7.2, TOP + 0.05, 5.53, 0.3, "https://get-started.nrp-nautilus.io", size=14, align="r"),
    Image(7.2, TOP + 0.42, 5.53, 4.8, IMG / "namespace_form.png", border="DDE8F2", align="r", valign="t", cls="pop"),
], notes="""
[0:32] Access is three steps. Log in at nrp.ai through CILogon with your institution. Get into a namespace: if you're faculty, staff, a postdoc or a research scientist you can request one with this form; a person reviews it. Then start working. For the LLMs, you get a token from nrp.ai/llmtoken.
""")


# What is a Namespace? (from the UCLA deck)
NS_CSS = """<style>
.nsd .kcl { width: 100%; height: 100%; border: 2px solid #B9C7D8; border-radius: 10px; padding: 18px 28px; }
.nsd .nsb { display: flex; align-items: center; gap: 30px; height: 183px; margin-top: 28px; padding: 0 28px;
  background: var(--card); border: 2px solid #C9D4E3; border-radius: 12px; opacity: 0; transform: translateY(12px);
  transition: opacity .5s, transform .5s; }
.nsd .nsb code { font-size: 32px; font-weight: 600; color: var(--navy); width: 255px; flex: none; }
.nsd .nsb b { display: block; font-size: 30px; color: var(--navy); } .nsd .nsb span { font-size: 28px; }
.nsd .nsb.dim { background: var(--dim); border-color: #E3E6EA; }
.nsd .nsb.dim code, .nsd .nsb.dim b, .nsd .nsb.dim span { color: var(--dimt); }
.slide.active .nsd .nsb { opacity: 1; transform: none; }
</style>"""
SPACES = [("netlab", "a PI (admin) and three students", "GPU jobs · a Ceph volume · a web app", ""),
          ("cse-course", "the instructor (admin) and 40 students", "a course JupyterHub · shared datasets", ""),
          ("another-lab", "their members only", "you can't see their pods or data", "dim")]
nsi = '<div class="kcl"><p class="dh l" style="font-size:30px">Nautilus cluster</p>' + "".join(
    f'<div class="nsb {st}" style="transition-delay:{0.3 + i * 0.3:.1f}s"><code>{name}</code><div><b>{who}</b>'
    f'<span>{inside}</span></div></div>' for i, (name, who, inside, st) in enumerate(SPACES)) + "</div>"


def ns_draw(s, k):
    Frame(5.7, TOP + 0.1, 7.03, 5.1, label="Nautilus cluster", line="B9C7D8").pptx(s, k)
    for i, (name, who, inside, st) in enumerate(SPACES):
        y = TOP + 0.6 + i * 1.47
        Box(5.9, y, 6.63, 1.27, name, f"{who} · {inside}", state="dim" if st else "normal", head_size=16,
            sub_size=13, align="l").pptx(s, k)


add("What is a Namespace?", [
    Bullets(X0, TOP + 0.15, 4.75, 5.1, [
        "Your group's space on the cluster: one per lab, project, course or service",
        "The PI or instructor is its admin and adds members",
        "Everything you run lives in it: pods, Jobs, volumes, Services, Ingresses",
        "Members see their own namespaces, not anyone else's",
        f"{S['namespaces']:,} of them today"], size=18, gap=10),
    Raw(0, 0, 0.1, 0.1, NS_CSS, pptx=False),
    Raw(5.7, TOP + 0.1, 7.03, 5.1, nsi, cls="nsd", draw=ns_draw),
], secs=40, notes=f"""
Back to the namespace from the Kubernetes slide, now that you have access. A namespace is your group's space: one per lab, project, course or service, with the PI or instructor as its admin, who adds the members. Everything you run lives in it: pods and Jobs, storage volumes, the Services and Ingresses from the traffic slide. Members see their own namespaces and nobody else's. There are {S['namespaces']:,} of them today.
""")

# Ways to run work: ported from the UCLA deck (JupyterHub, a pod, a Deployment, then a sweep of Jobs)
def runways():
    h = ""

    def at(x, y, w, hh, inner, cls="", step=None, only=None, style=""):
        a = f' data-s="{step}"' if step is not None else ""
        a += f' data-only="{only}"' if only is not None else ""
        return f'<div class="sb {cls}"{a} style="{pos(x, y, w, hh)}{style}">{inner}</div>'

    def ul(items, size):
        return (f'<ul class="bl" style="font-size:{size * 2}px;--gap:16px">'
                + "".join(f'<li class="l0">{md(t)}</li>' for t in items) + "</ul>")

    for i, (head, items) in enumerate(RUN_WAYS):
        y = TOP + 0.1 + i * 1.65
        h += at(X0, y, 5.55, 1.6, f'<p class="dh l" style="font-size:38px">{escape(head)}</p>'
                f'<div style="margin-top:14px">{ul(items, 15.5)}</div>', f"lw b{i}", step=i or None)
    h += at(6.55, TOP + 0.1, 6.18, 0.45, '<p class="dh l" style="font-size:38px">Batch: a Job</p>', step=3)
    h += at(6.55, TOP + 0.52, 6.18, 0.75, ul(RUN_JOB, 15.5), step=3)
    h += at(6.55, TOP + 1.3, 6.18, 0.52, f'<div class="code one" style="font-size:24px"><pre>{escape(RUN_CMD)}</pre></div>',
            step=3)
    UNIT, T0 = 0.55, 1.5
    LX, TW, LH, LG = 115, 775, 58, 11
    g = '<span class="plab">Pending</span>'
    for i, (job, gpu, t0, t1) in enumerate(SWEEP):
        g += (f'<span class="pc" style="left:{LX + i * 129}px;--a:{0.5 + i * 0.08:.2f}s;--b:{T0 + t0 * UNIT:.2f}s">'
              f'{job}</span>')
    for k in range(4):
        g += f'<span class="glab" style="top:{70 + k * (LH + LG)}px">GPU {k + 1}</span>'
        g += f'<span class="trk" style="top:{70 + k * (LH + LG)}px"></span>'
    for job, gpu, t0, t1 in SWEEP:
        bw_ = (t1 - t0) / SWEEP_T * TW - 6
        st = f"left:{LX + t0 / SWEEP_T * TW + 3:.0f}px;top:{70 + gpu * (LH + LG) + 4}px;"
        tm_ = f"--t0:{T0 + t0 * UNIT:.2f}s;--t1:{T0 + t1 * UNIT:.2f}s;--du:{(t1 - t0) * UNIT:.2f}s"
        g += (f'<span class="gb" style="{st}--w:{bw_:.0f}px;{tm_}"></span>'
              f'<span class="gl" style="{st}--w:{bw_:.0f}px;{tm_}">{job}</span>')
    g += f'<span class="nowl" style="--t0:{T0:.2f}s;--du:{SWEEP_T * UNIT:.2f}s"></span>'
    g += (f'<span class="tax" style="top:{70 + 4 * (LH + LG) - 4}px"></span><span class="tlab" style="top:'
          f'{70 + 4 * (LH + LG)}px">time</span>')
    h += at(6.55, TOP + 1.95, 6.18, 2.95, f'<div class="gantt">{g}</div>', step=3)
    h += at(6.55, TOP + 4.85, 6.18, 0.55, f'<p class="cap" style="font-size:27px">{escape(RUN_CAPTION)}</p>', step=3)
    LCT = 3.6

    def lifecycle(k, lane, segs, marks):
        hh = f'<span class="lcl">{lane}</span><span class="trk" style="top:40px"></span>'
        for t0, t1, kind, text in segs:
            w = (t1 - t0) * TW - 4
            hh += (f'<span class="sg {kind}" style="left:{LX + t0 * TW + 2:.0f}px;--w:{w:.0f}px;--t0:{0.5 + t0 * LCT:.2f}s;'
                   f'--du:{(t1 - t0) * LCT:.2f}s">{escape(text)}</span>')
        for p_, text, kind, place, align in marks:
            x = LX + p_ * TW
            tx = {"start": f"left:{x - 2:.0f}px", "center": f"left:{x - 300:.0f}px;width:600px;text-align:center",
                  "end": f"right:{890 - x - 2:.0f}px;text-align:right"}[align]
            hh += (f'<span class="mk {kind}" style="left:{x - 1.5:.0f}px;--t:{0.5 + p_ * LCT:.2f}s"></span>'
                   f'<span class="mt {kind}" style="{tx};top:{0 if place == "above" else 110}px;--t:{0.5 + p_ * LCT:.2f}s">'
                   f'{escape(text)}</span>')
        return at(6.55, TOP + 3.35, 6.18, 1.9, f'<div class="lc lc{k}">{hh}</div>', only=str(k))

    from elements import uri
    h += at(6.55, TOP + 0.05, 2.95, 0.4, '<p class="dh l" style="font-size:26px">1. Pick a GPU</p>', only="0")
    h += at(6.55, TOP + 0.45, 2.95, 2.65, f'<img class="im framed" src="{uri(IMG / "jhub_spawner.png")}" alt="">',
            only="0")
    h += at(9.6, TOP + 0.05, 3.13, 0.4, '<p class="dh l" style="font-size:26px">2. Your notebook runs on it</p>',
            only="0")
    h += at(9.6, TOP + 0.45, 3.13, 2.65, f'<img class="im framed" src="{uri(IMG / "jupyterlab_gpu.png")}" alt="">',
            only="0")
    h += lifecycle(0, "GPU", [(0, .55, "run", "you work in notebooks"), (.55, .8, "idle", "idle")],
                   [(.55, "you close the browser", "neutral", "above", "center"),
                    (.8, "1 h later: server stops, GPU back to the pool", "ok", "below", "end")])
    pod_term = ["$ kubectl apply -f pod.yaml", "pod/dev-pod created", "$ kubectl exec -it dev-pod -- bash",
                "root@dev-pod:/# nvidia-smi -L", "GPU 0: NVIDIA A10 (UUID: GPU-…)", "root@dev-pod:/# python test.py"]
    h += at(6.55, TOP + 0.3, 6.18, 2.3, '<div class="code kterm podterm" style="font-size:25px"><pre>'
            + "".join(f'<span class="ln{" cmd" if l.startswith(("$ ", "root@")) else ""}" style="--i:{i}">{escape(l)}'
                      f'</span>' for i, l in enumerate(pod_term)) + "</pre></div>", only="1")
    h += lifecycle(1, "GPU", [(0, .8, "run", "dev-pod: a shell, tests, debugging")],
                   [(.8, "6 h: the pod is deleted", "bad", "below", "end")])
    dep = ('<div class="depbox"><p class="dh l" style="font-size:28px">Deployment <code>web-app</code> · 2 replicas</p>'
           '<div class="dpods"><div class="dpod"><code>web-app-5d59d-x2kqp</code><b>Running</b></div>'
           '<div class="dpod swapper"><span class="p1"><code>web-app-5d59d-m4q9d</code><b>Running</b></span>'
           '<span class="p2"><code>web-app-5d59d-m4q9d</code><b>crashed</b></span>'
           '<span class="p3"><code>web-app-5d59d-c8w3n</code><b>Running</b></span></div></div>'
           '<p class="cap" style="font-size:26px;margin-top:18px">Kubernetes keeps two copies running; when one '
           'crashes, it starts a replacement</p></div>')
    h += at(6.55, TOP + 0.3, 6.18, 2.45, dep, only="2")
    h += lifecycle(2, "Node", [(0, .42, "run", "web-app"), (.45, .92, "run", "web-app (replacement)")],
                   [(.435, "crash: restarted for you", "bad", "above", "center"),
                    (.92, "2 weeks: removed, unless admins grant an exception", "neutral", "below", "end")])
    return h


def runways_draw(s, k):
    from deckkit import CODE_BG
    for i, (head, items) in enumerate(RUN_WAYS):
        y = TOP + 0.1 + i * 1.65
        s.text(X0, y, 5.55, 0.45, P(head, size=19, bold=True, color=NAVY))
        s.text(X0, y + 0.42, 5.55, 1.15, [P(t, size=15.5, color=BODY, bullet=True, accent=NAVY, before=4 if j else 0)
                                           for j, t in enumerate(items)])
    s.text(6.55, TOP + 0.1, 6.18, 0.45, P("Batch: a Job", size=19, bold=True, color=NAVY))
    s.text(6.55, TOP + 0.52, 6.18, 0.8, [P(t, size=15.5, color=BODY, bullet=True, accent=NAVY, before=4 if j else 0)
                                          for j, t in enumerate(RUN_JOB)])
    s.code(6.55, TOP + 1.3, 6.18, 0.62, RUN_CMD, size=12)
    GX, GW, LY, LHH, LGG = 7.35, 5.38, TOP + 2.45, 0.4, 0.08
    for g in range(4):
        y = LY + g * (LHH + LGG)
        s.text(6.55, y, 0.75, LHH, P(f"GPU {g + 1}", size=12, bold=True, color=NAVY), anchor="m")
        s.rect(GX, y, GW, LHH, fill="F3F4F6", radius=0.12)
    for job, g, t0, t1 in SWEEP:
        y = LY + g * (LHH + LGG)
        x, w = GX + t0 / SWEEP_T * GW, (t1 - t0) / SWEEP_T * GW
        s.rect(x + 0.02, y + 0.03, w - 0.04, LHH - 0.06, fill="8FB0CF", radius=0.18)
        s.text(x, y, w, LHH, P(job, size=11, bold=True, color=NAVY, align="c", font=MONO), anchor="m")
    ay = LY + 4 * (LHH + LGG) - 0.02
    s.line(GX, ay, GX + GW, ay, color=MUTED, width=1.25)
    s.text(6.55, ay + 0.32, 6.18, 0.6, P(RUN_CAPTION, size=13.5, color=MUTED, line=1.0))


add("Ways to Run Work", [Raw(0, 0, 13.333, 7.5, runways(), draw=runways_draw)], steps=3, cls="runways", notes="""
[0:32] And the ways to run work, which map onto Kubernetes objects. JupyterHub: pick a GPU, work in a notebook; idle servers stop, an hour after you close the browser on our hub. [click] A bare pod with a shell: deleted after six hours, at most two GPUs. [click] A Deployment for a service that stays up and gets restarted when it crashes; removed after two weeks unless we grant an exception. [click] And Jobs for real work: submit six, four start, two wait in Pending and take the first GPUs that free up, and when they finish the GPUs go back to the pool.
""")

YAML = """apiVersion: batch/v1
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
calls = [("Where:", "your namespace"), ("What:", "a container image, and the command to run"),
         ("Resources:", "2 CPUs, 6 GB of memory, one GPU"),
         ("Which GPU:", "more than 20 GB, Ampere or newer; or name exact models")]
add("A GPU Job", [
    Code(X0, TOP + 0.1, 8.25, 5.2, YAML, size=12, lang="yaml", lines_hl={k: [v] for k, v in groups.items()}),
    *[Text(9.1, TOP + 0.2 + i * 1.25, 3.63, 1.2, T(f"({i + 1}) **{h}** {b}", size=17), hl=[i + 1], cls="co")
      for i, (h, b) in enumerate(calls)],
], steps=4, cls="gpujob", optional=True, notes="""
[0:33] For completeness, a GPU job. Four parts: where it runs, your namespace; what it runs, an image and a command; what it needs, two CPUs, six gigs, one GPU; and which GPU, by memory and generation rather than by brand. The demo submits exactly this.
""")

add("Where to Start", [
    Text(X0, TOP + 0.1, 5.9, 0.45, T("Use it", size=21, bold=True, color=NAVY)),
    Bullets(X0, TOP + 0.6, 5.9, 4.5, [
        "**The LLM API in your automation:** config review, log triage, a docs assistant; task names keep working "
        "as the catalog changes",
        "**Your tools in a namespace:** web apps, Postgres and ClickHouse from the operators, S3 for data",
        "**GitLab CI** to build and ship them",
        "**GPUs for AI and ML:** a notebook to start, Jobs when it's real"], size=17, gap=10),
    Text(6.83, TOP + 0.1, 5.9, 0.45, T("Connect to it", size=21, bold=True, color=NAVY)),
    Bullets(6.83, TOP + 0.6, 5.9, 4.5, [
        "**Contribute nodes**, the way a node joins: you keep priority, NRP runs them",
        "**InterLink:** a Slurm cluster appears as a virtual node",
        "**Federation** with another Kubernetes cluster",
        "**FABRIC and SENSE** testbeds, with Multus for extra NICs",
        "**perfSONAR:** a testpoint on your node joins the mesh"], size=17, gap=10),
    Link(X0, 6.0, W, 0.3, "https://nrp.ai/documentation/admindocs/participating/new-contributor-guide/", size=13),
], notes="""
[0:34] Where to start, two ways. Use it: the LLM API in your own automation, where the task names save you from chasing model names; your tools in a namespace; GitLab CI to build them; GPUs for ML. Or connect to it: contribute nodes, the way you saw a node join; attach a Slurm cluster through InterLink; federate a Kubernetes cluster; the FABRIC and SENSE testbed integrations; or just put a perfSONAR testpoint in the mesh.
""")

section("Live Demo", """About fifteen minutes, on jh-training.nrp-nautilus.io: workspace/notebooks/demo.ipynb (Bash kernel) for parts 1–3 and 5, agent.ipynb (Python 3) for part 4. Run sheet: deck/README.md.

1. The cluster (2 min): kubectl get nodes with -L and -l: nodes per region, GPU nodes per model.
2. The LLM gateway (4 min): curl | jq for the model list and one qwen3 answer; curl -si | grep for the rate-limit headers; then the task name coding and which model answered.
3. A GPU job (2 min): set ME, submit, kubectl get pods. Leave it starting.
4. Your own agent (5 min): three read-only tools, their schemas, the loop; ask whether three nrp-nautilus.io names share an address and answer on 443, then ask about the GPU job.
5. Back to the job (2 min): logs -f, delete. If it's Pending, describe, then show the warm-up job.""", secs=900)

add("Acknowledgments", [
    Bullets(X0, TOP + 0.15, W, 5.0, [
        "NRP is supported by NSF awards OAC-1541349, OAC-1826967, OAC-2030508, OAC-1841530, OAC-2005369, "
        "OAC-2112167, CISE-1713149, CISE-2100237 and CISE-2120019",
        "Networks: CENIC, Pacific Wave, Internet2, MREN, GPN, NYSERNet, FLR, NEREN, Sun Corridor, OARnet, SCLR and "
        "the Albuquerque GigaPoP",
        "The NRP operations teams at SDSC, the University of Nebraska–Lincoln and MGHPCC, and the campuses that "
        "host and share their hardware",
        "SCinet, for having us during the NOC move"], size=18, gap=14),
], notes="[0:47] Thanks to NSF, the networks, the operations teams and the campuses, and to SCinet for having me.")

links = [("Today's materials", "training.nrp-nautilus.io/scinet-sc26"), ("Portal and login", "nrp.ai"),
         ("Request a namespace", "get-started.nrp-nautilus.io"), ("LLM endpoint", "ellm.nrp-nautilus.io/v1"),
         ("LLM token", "nrp.ai/llmtoken"), ("perfSONAR", "perfsonar.nrp-nautilus.io"),
         ("Admin guide", "nrp.ai/documentation/admindocs"), ("Support chat and email", "nrp.ai/contact")]
q = "".join(f'<div class="qrow"><span>{lab}</span><a href="https://{u}" target="_blank" rel="noopener">{u}</a></div>'
            for lab, u in links)


def q_draw(s, k):
    for i, (lab, u) in enumerate(links):
        y = 1.70 + i * 0.56
        s.text(X0, y, 3.1, 0.5, P(lab, size=17, color=LIGHT), anchor="m")
        s.text(X0 + 3.15, y, 6.6, 0.5, P(u, size=15, bold=True, color=GOLD, font=MONO), anchor="m")


add("Questions?", [
    Raw(X0, 1.7, 9.5, 4.6, q, draw=q_draw, cls="stagger"),
    Text(X0, 6.25, 12.1, 0.45, T("Daniel Diaz  ·  d4diaz@ucsd.edu", size=19, bold=True, color=WHITE)),
], kind="reverse", notes="[0:48] Questions. All the links are on the slide.")
