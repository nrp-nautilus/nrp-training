"""'Getting In': access, NAIRR Classroom, namespaces, and what a course can use.

Part of the NAIRR Classroom webinar deck: slides.py imports the section files in order. Shared constants
and helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
"""
from common import *  # noqa: F401,F403

TRAIN = HERE.parent / "images"          # the training's own screenshots (nairr-classroom/images)

section("Getting In", "How you and your students get onto NRP.")

# ── Getting Access ──────────────────────────────────────────────────────────────────────────────────────
add("Getting Access", [
    Text(X0, TOP + 0.15, 6.3, 5.1, [
        T("1.  Log in at **nrp.ai**", size=20),
        T("Log In → CILogon → your institution's own login", size=17, before=3),
        T("2.  Get a namespace for your course", size=20, before=16),
        T("Request one at **get-started.nrp-nautilus.io**, or email the NRP team the course, the number of "
          "students and the start date", size=17, before=3),
        T("3.  Bring your students", size=20, before=16),
        T("They log in the same way, with their campus account: no new passwords, nothing to install", size=17,
          before=3),
        T("**Who can request a namespace:** faculty, staff, postdocs and research scientists. Free for US "
          "nonprofit institutions.", size=16, before=20)], cls="stagger"),
    Link(7.2, TOP + 0.05, 5.53, 0.3, "https://get-started.nrp-nautilus.io", size=14, align="r"),
    Image(7.2, TOP + 0.42, 5.53, 4.8, IMG / "namespace_form.png", border="DDE8F2", align="r", valign="t", cls="pop"),
], secs=60, notes="""
Getting in is three steps. You log in at nrp.ai through CILogon, which means your own institution's login: no new account, no new password. You get a namespace for your course: request one with this form, or just email the NRP team with the course, roughly how many students and when it starts, and they'll have it ready before the first lecture. Then your students log in the same way, with their campus accounts.
""")

# ── NAIRR Classroom: the formal route ──────────────────────────────────────────────────────────────────
nc = [Bullets(X0, TOP + 0.15, 5.6, 5.2, [
    "The **NAIRR Pilot** takes **Classroom** requests from US educators",
    "Your course, and what it needs, in **up to three pages**",
    "Courses that teach AI, in **any discipline**, for US-based students",
    "Reviewed as they arrive; **a decision within a month**",
    "Tick **Prototype NRP (PNRP) Classroom**: a Jupyter platform, CPUs, GPUs, storage and hosted AI models, run "
    "by the NRP team",
    "Not required to use NRP, but it gives your course priority"], size=17, gap=9, cls="stagger"),
    Image(6.35, TOP + 0.1, 6.38, 3.4, TRAIN / "NAIRR_Classroom_2.png", border="DDE8F2", align="r", valign="t",
          cls="pop"),
    Text(6.35, TOP + 3.6, 6.38, 0.6, T("The NAIRR Classroom request form: NRP's option, among the other providers",
                                       size=13, color=MUTED, align="r")),
    Link(6.35, TOP + 4.15, 6.38, 0.3, "https://nairrpilot.org", size=14, align="r")]
add("NAIRR Classroom", nc, secs=50, notes="""
There's also a formal route, through the NAIRR Pilot. NAIRR Classroom takes requests from US educators: up to three pages on your course and what it needs. It's for courses that teach AI, in any discipline, with US-based students, and you hear back within a month. NRP is one of the classroom providers, as the Prototype NRP Classroom. You don't need to go through NAIRR to use NRP, but an allocation gives your course priority.
""")

# ── What is a Namespace? (from the UCLA and SCinet decks, course flavored) ───────────────────────────────
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
SPACES = [("bio-210", "the instructor (admin), 2 TAs, 40 students", "the course JupyterHub · shared datasets", ""),
          ("ml-lab", "a PI (admin) and three students", "GPU jobs · a data volume · a web app", ""),
          ("another-course", "their members only", "you can't see their servers or files", "dim")]
nsi = '<div class="kcl"><p class="dh l" style="font-size:30px">Nautilus cluster</p>' + "".join(
    f'<div class="nsb {st}" style="transition-delay:{0.3 + i * 0.3:.1f}s"><code>{name}</code><div><b>{who}</b>'
    f'<span>{inside}</span></div></div>' for i, (name, who, inside, st) in enumerate(SPACES)) + "</div>"


def ns_draw(s, k):
    Frame(5.7, TOP + 0.1, 7.03, 5.1, label="Nautilus cluster", line="B9C7D8").pptx(s, k)
    for i, (name, who, inside, st) in enumerate(SPACES):
        Box(5.9, TOP + 0.6 + i * 1.47, 6.63, 1.27, name, f"{who} · {inside}", state="dim" if st else "normal",
            head_size=16, sub_size=13, align="l").pptx(s, k)


add("What is a Namespace?", [
    Bullets(X0, TOP + 0.15, 4.75, 5.1, [
        "Your course's space on the cluster: one per course, lab or project",
        "You're its admin, and you add your TAs",
        "Your course hub, its storage and anything else you run lives in it",
        "Members see their own namespaces, not anyone else's",
        f"{S['namespaces']:,} of them today"], size=18, gap=10),
    Raw(0, 0, 0.1, 0.1, NS_CSS, pptx=False),
    Raw(5.7, TOP + 0.1, 7.03, 5.1, nsi, cls="nsd", draw=ns_draw),
], secs=40, notes=f"""
A namespace is your course's space on the cluster: one per course, lab or project. You're its admin, and you can add your TAs. Your course's JupyterHub and its storage live in it, and nobody outside sees inside. There are {S['namespaces']:,} namespaces today.
""")

# ── Ways In ─────────────────────────────────────────────────────────────────────────────────────────────
ways = [("JupyterHub", "notebooks in the browser; NRP's, or your course's own", "jupyterhub-west.nrp-nautilus.io"),
        ("Coder", "VS Code in the browser, for programming courses", "coder.nrp-nautilus.io"),
        ("kubectl", "jobs, services and storage in your namespace", "nrp.ai/config"),
        ("GitLab", "course repositories, and builds of course images", "gitlab.nrp-nautilus.io"),
        ("LLM API", "hosted models for notebooks and apps", "ellm.nrp-nautilus.io/v1"),
        ("Chat", "talk to the hosted models in a browser", "nrp-openwebui.nrp-nautilus.io")]
we = []
for i, (h, b, u) in enumerate(ways):
    x, y = X0 + (i % 3) * 4.1, TOP + 0.2 + (i // 3) * 2.2
    we += [Box(x, y, 3.9, 1.95, h, b, head_size=22, sub_size=15, state="active" if i == 0 else "normal", cls="rise",
               style=f"transition-delay:{i * 0.12:.2f}s"),
           Text(x, y + 1.35, 3.9, 0.4, T(u, size=13, color=GOLD if i == 0 else BLUE, font=MONO, align="c"),
                cls="rise", style=f"transition-delay:{i * 0.12:.2f}s")]
we.append(Text(X0, 5.85, W, 0.5, T("Most students only ever see the first one. The rest are there when a course "
                                    "outgrows notebooks.", size=16, color=MUTED)))
add("Ways In", we, secs=45, notes="""
Once you're in, there are several ways to use NRP. JupyterHub, notebooks in the browser, either NRP's own hub or your course's. Coder, which is VS Code in the browser and great for programming courses. kubectl, for anything Kubernetes can run, which is how you'll deploy a hub. GitLab, for course repositories and for building course images. The LLM API, and a chat interface for the hosted models. Most students only ever see the first one, and that's the point of today.
""")
