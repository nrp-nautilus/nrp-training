"""'JupyterHub for Your Class': what an instructor controls when running a hub for a course.

Part of the NAIRR Classroom webinar deck: slides.py imports the section files in order. Shared constants
and helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
"""
from common import *  # noqa: F401,F403

HUBS = 152          # pods labeled component=hub on the cluster, 12 Nov 2026
SERVERS = 111       # pods labeled component=singleuser-server at the same time

section("JupyterHub for Your Class", "Most of today: what you get to decide when you run a hub for a course.")

# ── Two ways to give students Jupyter ──────────────────────────────────────────────────────────────────
two = [Frame(X0, TOP + 0.1, 5.95, 4.5, fill=CARD, line=None, radius=0.05),
       Text(X0 + 0.3, TOP + 0.3, 5.4, 0.9, [T("NRP's JupyterHub", size=22, bold=True, color=NAVY),
                                             T("jupyterhub-west.nrp-nautilus.io", size=14, color=BLUE, font=MONO,
                                               before=2)]),
       Bullets(X0 + 0.3, TOP + 1.3, 5.4, 3.2, [
           "Nothing to run: share the link",
           "Students choose CPUs, memory and a GPU from a menu",
           "NRP's images, the same rules for everyone",
           "Good for trying things, small classes and research"], size=17, gap=8),
       Frame(6.78, TOP + 0.1, 5.95, 4.5, fill="FFF4CC", line="E9B55C", radius=0.05, step=1),
       Text(7.08, TOP + 0.3, 5.4, 0.9, [T("Your own hub, in your namespace", size=22, bold=True, color=NAVY),
                                        T("jhub-yourcourse.nrp-nautilus.io", size=14, color=BLUE, font=MONO,
                                          before=2)], step=1),
       Bullets(7.08, TOP + 1.3, 5.4, 3.2, [
           "Your image menu, built for the syllabus",
           "Your login rules: only your students",
           "Your limits, storage and course files",
           "One Helm chart and one settings file: the rest of this section"], size=17, gap=8, step=1),
       Text(X0, TOP + 4.85, W, 0.5, T(f"{HUBS} JupyterHubs were running on NRP on 12 Nov, with {SERVERS} servers "
                                      "open at that moment.", size=16, color=MUTED))]
add("Two Ways to Give Students Jupyter", two, steps=1, secs=60, notes=f"""
There are two ways to give students Jupyter on NRP. The first is NRP's own JupyterHub: there's nothing to run, you share a link, and students pick CPUs, memory and a GPU from a menu. It's NRP's images and the same rules for everyone, which is great for trying things, small classes and research.

[click] The second is your own hub, in your course's namespace. Then the image menu is yours, built for your syllabus; only your students get in; and you decide limits, storage and how course files arrive. It's one Helm chart and one settings file, and that's the rest of this section. You're in good company: {HUBS} JupyterHubs were running on the cluster yesterday.
""")

# ── How a class hub works (animated) ───────────────────────────────────────────────────────────────────
STU_X, STU_W = X0, 1.55
stu_y = [TOP + 0.25, TOP + 1.1, TOP + 1.95]
HUB_X, HUB_W, HUB_Y, HUB_H = 2.6, 1.95, TOP + 1.1, 1.0
CIL_Y = TOP + 0.05
CL_X, CL_Y, CL_W, CL_H = 5.15, TOP + 0.05, 7.58, 2.7
NA_X, NB_X, N_Y, N_W, N_H = 5.35, 9.05, TOP + 0.5, 3.48, 2.05
pods = [("alex", "Python · 2 CPUs", NA_X + 0.15), ("bea", "R · 2 CPUs", NA_X + 1.78), ("chen", "PyTorch · 1 GPU",
                                                                                         NB_X + 0.15)]
POD_Y, POD_W, POD_H = N_Y + 0.5, 1.55, 0.7
hw = [Box(STU_X, y, STU_W, 0.7, "Student", "a browser", state="white", head_size=14, sub_size=11, hl=[1] if i == 0
          else None) for i, y in enumerate(stu_y)]
hw += [Arrow(STU_X + STU_W, y + 0.35, HUB_X, HUB_Y + 0.5, color="C9D4E3") for y in stu_y]
hw += [Box(HUB_X, CIL_Y, HUB_W, 0.75, "CILogon", "campus login", state="white", head_size=14, sub_size=11, hl=[1]),
       Arrow(HUB_X + HUB_W / 2, HUB_Y, HUB_X + HUB_W / 2, CIL_Y + 0.75, dashed=True, head=False, hl=[1]),
       Box(HUB_X, HUB_Y, HUB_W, HUB_H, "Your hub", "login, menu, servers", head_size=16, sub_size=11.5, hl=[1, 2]),
       Frame(CL_X, CL_Y, CL_W, CL_H, label="Your namespace on Nautilus", line="B9C7D8", label_size=13),
       Frame(NA_X, N_Y, N_W, N_H, label="Node · 64 CPUs", line="C9D4E3", label_size=12, fill="F7F9FC"),
       Frame(NB_X, N_Y, N_W, N_H, label="Node · 4 GPUs", line="C9D4E3", label_size=12, fill="F7F9FC"),
       Arrow(HUB_X + HUB_W, HUB_Y + 0.5, CL_X, HUB_Y + 0.5, step=2, hl=[2])]
for i, (who, what, x) in enumerate(pods):
    hw += [Box(x, POD_Y, POD_W, POD_H, f"{who}'s server", what, state="orange", head_size=13, sub_size=10.5, step=2,
               cls=f"pod p{i}", style=f"transition-delay:{0.2 + i * 0.3:.1f}s"),
           Box(x + 0.25, POD_Y + 0.82, POD_W - 0.5, 0.42, f"{who}'s home", None, state="gold", head_size=11, step=3,
               style=f"transition-delay:{0.2 + i * 0.25:.1f}s")]
hw += [Box(CL_X + 0.2, CL_Y + CL_H + 0.1, CL_W - 0.4, 0.42, "shared course folder: read-only for students", None,
           state="green", head_size=12.5, step=3, style="transition-delay:.9s"),
       Raw(NB_X + 0.15, POD_Y, POD_W, POD_H, '<div class="idle-x">idle 1 h: stopped<br>GPU back to the pool</div>',
           only=[4], pptx=False),
       packet("hubwork", {1: [(STU_X + STU_W, stu_y[0] + 0.35), (HUB_X, HUB_Y + 0.5), (HUB_X + HUB_W / 2, HUB_Y),
                              (HUB_X + HUB_W / 2, CIL_Y + 0.75), (HUB_X + HUB_W / 2, HUB_Y),
                              (HUB_X + HUB_W / 2, HUB_Y + HUB_H / 2)],
                          2: [(HUB_X + HUB_W, HUB_Y + 0.5), (CL_X, HUB_Y + 0.5), (pods[0][2] + 0.1, POD_Y + 0.35)]},
              speed=3.0),
       Raw(0, 0, 0.1, 0.1, '<style>.hubwork .idle-x { width: 100%; height: 100%; border-radius: 12px; '
           'background: rgba(243,244,246,.94); border: 2px dashed #A3ABB6; color: var(--body); font: 600 19px/1.2 '
           'var(--f-body); display: flex; align-items: center; justify-content: center; text-align: center; }'
           '.hubwork[data-cur="4"] .pod.p2 .bx { opacity: .25; transition: opacity .8s .3s; }</style>', pptx=False)]
HCAPS = {0: ("A class hub, step by step", "One URL for the whole class. Behind it: your hub, in your namespace, "
             "and the cluster's nodes."),
         1: ("1. Students log in", "With their campus account, through CILogon. The hub lets in only the people you "
             "allow."),
         2: ("2. Each student gets a server", "The hub starts a container for each student, with the image, CPUs, "
             "memory or GPU of the option they picked."),
         3: ("3. Their files are there", "Each server mounts the student's own home folder, plus a shared course "
             "folder everyone reads from."),
         4: ("4. Idle servers stop", "After an hour with no activity the server shuts down and its GPU goes back to "
             "the pool. The home folder stays for next time.")}
for k, (h, b) in HCAPS.items():
    hw.append(Text(X0, TOP + 3.55, W, 1.5, [T(h, size=21, bold=True, color=NAVY), T(b, size=18, color=BODY,
                                                                                    before=5)], only=[k]))
add("How a Class Hub Works", hw, steps=4, cls="hubwork", builds=True, secs=110, notes="""
How a class hub works. Your students get one URL. Behind it is your hub, running in your namespace, and the cluster's nodes.

[click] A student opens the URL and logs in with their campus account, through CILogon. The hub checks that they're someone you allowed.

[click] The hub starts a server for that student: a container on one of the nodes, with the image and the CPUs, memory or GPU of the option they picked. Thirty students, thirty servers, spread across the cluster.

[click] Each server mounts that student's own home folder, so their work is there next time, plus a shared course folder that everyone reads from.

[click] And when a student walks away, after an hour of no activity the server stops, and if it had a GPU, the GPU goes back to the pool for someone else. The home folder stays.
""")

# ── Who can log in ─────────────────────────────────────────────────────────────────────────────────────
LG_Y = TOP + 0.55
login = [Bullets(X0, TOP + 0.15, 5.7, 5.2, [
    "**Campus login through CILogon:** you never hand out or reset passwords",
    "**Your class list:** allow your students by name or email, or a whole campus domain",
    "**Admins:** you and your TAs; an admin can open a student's server to help",
    "For a workshop or a demo, a shared password works too: today's demo uses one"], size=18, gap=11),
    Box(6.75, LG_Y, 1.75, 0.95, "Sign in", "at your hub's URL", state="white", head_size=15, sub_size=11.5),
    Box(8.85, LG_Y, 1.85, 0.95, "CILogon", "pick your campus", state="white", head_size=15, sub_size=11.5),
    Box(11.05, LG_Y, 1.68, 0.95, "On the list?", "your hub checks", head_size=15, sub_size=11.5),
    Arrow(8.5, LG_Y + 0.47, 8.85, LG_Y + 0.47), Arrow(10.7, LG_Y + 0.47, 11.05, LG_Y + 0.47),
    Box(9.3, LG_Y + 1.75, 1.6, 0.75, "In", "a server starts", state="green", head_size=15, sub_size=11),
    Box(11.13, LG_Y + 1.75, 1.6, 0.75, "Not on it", "turned away", state="red", head_size=15, sub_size=11),
    Arrow(11.4, LG_Y + 0.95, 10.4, LG_Y + 1.75), Arrow(11.93, LG_Y + 0.95, 11.93, LG_Y + 1.75),
    packet("login", {0: [(7.62, LG_Y + 0.47), (9.78, LG_Y + 0.47), (11.6, LG_Y + 0.47), (10.6, LG_Y + 1.6)]},
           speed=2.2, loop=True, color="var(--green)", size=22),
    packet("login", {0: [(7.62, LG_Y + 0.75), (9.78, LG_Y + 0.75), (11.93, LG_Y + 0.75), (11.93, LG_Y + 1.6)]},
           speed=2.0, loop=True, color="var(--red)", size=22),
    Text(6.75, LG_Y + 2.85, 5.98, 1.2, T("CILogon connects your hub to your institution's own sign-in, the same "
                                         "one students use for email.", size=15, color=MUTED))]
add("Who Can Log In", login, secs=55, notes="""
Who can log in is your call. In a real course you use CILogon: students sign in with their campus account, so you never hand out or reset passwords. Then you say who's allowed: your class list by name or email, or everyone at your campus. And you name the admins, you and your TAs. An admin can open a student's server to help them debug, which is the office-hours superpower. For a one-off workshop, a shared password is fine, and that's what today's demo uses.
""")

# ── Setting up campus login ────────────────────────────────────────────────────────────────────────────
LOGIN_YAML = """hub:
  config:
    JupyterHub:
      authenticator_class: cilogon
    CILogonOAuthenticator:
      client_id: <from CILogon>        # and its client secret
      oauth_callback_url: https://jhub-bio210.nrp-nautilus.io/hub/oauth_callback
      allowed_idps:
        https://idp.campus.edu/idp/shibboleth:     # your campus's entity ID
          username_derivation: {username_claim: email}
      admin_users: [you@campus.edu, ta@campus.edu]
      allowed_users: [student1@campus.edu, student2@campus.edu]"""
ls_hl = {6: [1], 7: [1], 8: [2], 9: [2], 10: [2], 11: [3], 12: [3]}
SETUP = [("1. Ask CILogon for a client", "for your hub's address; it's issued by hand, so ask early"),
         ("2. Look up your campus", "its entity ID, in the CILogon IdP list"),
         ("3. Name who gets in", "admins, and your class list or your whole campus domain"),
         ("4. helm upgrade", "students who drop lose access at the next upgrade")]
cs = [Code(X0, TOP + 0.1, 7.3, 4.4, LOGIN_YAML, size=11.5, lang="yaml", lines_hl=ls_hl,
           title="The login part of values.yaml")]
for i, (h, b) in enumerate(SETUP):
    cs.append(Box(8.2, TOP + 0.15 + i * 1.1, 4.53, 0.95, h, b, state="white", head_size=15, sub_size=12, align="l",
                  hl=[i + 1]))
cs.append(Text(X0, TOP + 4.7, W, 0.6, T("Allow rules add up: `allowed_domains` admits a whole campus, `allowed_users` "
                                        "named people; `blocked_users` wins over both.", size=15, color=MUTED)))
add("Setting Up Campus Login", cs, steps=4, builds=True, secs=75, notes="""
Setting up campus login is four steps, and the first one is the only slow one. [click] Ask CILogon for a client for your hub's address: a client ID and secret. They're issued by hand, so ask a couple of weeks before the term. [click] Look up your campus's entity ID in the CILogon list and paste it exactly; a key CILogon doesn't recognize never matches, and nobody gets in. [click] Name who gets in: your admins, and either your class list or your whole campus domain. [click] Then helm upgrade. Students who drop the course lose access the next time you upgrade. The allow rules add up, and blocked users always win.
""")

# ── The image menu ─────────────────────────────────────────────────────────────────────────────────────
MENU = [("Python for data science", "2 CPUs · 8 GB"), ("R with the tidyverse", "2 CPUs · 8 GB"),
        ("PyTorch with a GPU", "4 CPUs · 16 GB · 1 GPU"), ("BIO 210 course image", "your packages, preinstalled")]
menu = ('<style>.imenu { width: 100%; height: 100%; background: #fff; border: 2px solid #DDE8F2; border-radius: 12px; '
        'padding: 22px 28px; box-shadow: 0 6px 18px rgba(0,0,0,.08); } .imenu h3 { font: 700 34px var(--f-body); '
        'color: var(--navy); margin-bottom: 18px; } .imenu .opt { display: flex; align-items: center; gap: 18px; '
        'padding: 16px 18px; margin-top: 12px; border: 2px solid #E3E6EA; border-radius: 10px; transition: background '
        '.4s, border-color .4s; } .imenu .opt i { width: 26px; height: 26px; border-radius: 50%; border: 3px solid '
        '#A3ABB6; flex: none; transition: background .4s, border-color .4s; } .imenu .opt b { display: block; '
        'font-size: 27px; color: var(--navy); } .imenu .opt span { font-size: 22px; color: var(--muted); } '
        '.imenu .btn { margin-top: 22px; display: inline-block; background: var(--blue); color: #fff; font: 700 24px '
        'var(--f-body); padding: 10px 26px; border-radius: 8px; }'
        + "".join(f'.imagemenu[data-cur="{k + 1}"] .opt.o{k} {{ background: #FFF4CC; border-color: #E9B55C; }} '
                  f'.imagemenu[data-cur="{k + 1}"] .opt.o{k} i {{ background: var(--blue); border-color: var(--blue); }}'
                  for k in range(4))
        + '</style><div class="imenu"><h3>Server Options</h3>'
        + "".join(f'<div class="opt o{k}"><i></i><div><b>{escape(h)}</b><span>{escape(s_)}</span></div></div>'
                  for k, (h, s_) in enumerate(MENU))
        + '<span class="btn">Start</span></div>')


def menu_draw(s, k):
    Frame(X0, TOP + 0.1, 5.7, 5.2, fill="FFFFFF", line="DDE8F2", radius=0.04).pptx(s, k)
    s.text(X0 + 0.2, TOP + 0.2, 5.3, 0.45, P("Server Options", size=17, bold=True, color=NAVY))
    for i, (h, s_) in enumerate(MENU):
        Box(X0 + 0.2, TOP + 0.8 + i * 0.95, 5.3, 0.8, h, s_, state="gold" if i == k - 1 else "white", head_size=14,
            sub_size=11.5, align="l").pptx(s, k)


im = [Raw(X0, TOP + 0.1, 5.7, 5.2, menu, draw=menu_draw),
      Text(6.83, TOP + 0.1, 5.9, 5.2, [
          T("What students see when they start a server: a menu **you** write.", size=18, color=BODY),
          T("**Ready-made images** for Python, R, Julia and Spark, from the Jupyter Docker Stacks", size=17,
            before=16, step=1),
          T("**Each option sets the CPUs and memory** a student gets", size=17, before=12, step=2),
          T("**GPUs only where the work needs them**, and you choose the kind", size=17, before=12, step=3),
          T("**Your own course image:** exactly your packages (next slide)", size=17,
            before=12, step=4),
          T("Every student runs the same environment: no more “it works on my laptop”.", size=17, color=BLUE,
            bold=True, before=20, step=4)])]
add("Your Image Menu", im, steps=4, cls="imagemenu", builds=True, secs=80, notes="""
When a student starts a server, they see a menu, and you write it.

[click] Options can be ready-made images: Python, R, Julia, Spark, from the Jupyter Docker Stacks.

[click] Each option sets how many CPUs and how much memory the student gets.

[click] GPUs only go on the options that need them, for example a deep-learning unit, and you choose what kind.

[click] Or you build one image for the course with exactly your packages, from a Dockerfile in NRP's GitLab. The payoff: every student runs the same environment, and the first week isn't spent fixing installs.
""")

# ── Your course image ──────────────────────────────────────────────────────────────────────────────────
DOCKERFILE = """FROM quay.io/jupyter/scipy-notebook:2024-04-22

# what BIO 210 needs, installed once for everyone
RUN pip install --no-cache-dir \\
      biopython scanpy seaborn statsmodels"""
CY = TOP + 3.0
steps_ = [("Dockerfile", "in your course repo", X0, 2.25), ("GitLab CI", "builds it on every push", 3.2, 2.35),
          ("Registry", "gitlab-registry.nrp-nautilus.io", 5.9, 2.75), ("Your menu", "an option points at it", 9.0, 1.95),
          ("Students", "start it from the menu", 11.3, 1.43)]
ci = [Code(X0, TOP + 0.1, 7.2, 2.4, DOCKERFILE, size=14, title="Dockerfile", typed=True),
      Bullets(8.2, TOP + 0.15, 4.53, 2.6, [
          "Start from a ready-made image; add only what your course needs",
          "NRP's GitLab builds it for you: no Docker on your laptop",
          "Pull it in class from the cluster's own registry: fast"], size=16, gap=8)]
for i, (h, b, x, w) in enumerate(steps_):
    ci.append(Box(x, CY, w, 1.0, h, b, head_size=15, sub_size=11, state="white", hl=[i + 1] if i < 4 else [4]))
    if i:
        px = steps_[i - 1][2] + steps_[i - 1][3]
        ci.append(Arrow(px, CY + 0.5, x, CY + 0.5, hl=[i]))
ci += [packet("courseimg", {k: [(steps_[k - 1][2] + steps_[k - 1][3] / 2, CY + 0.5),
                                (steps_[k][2] + steps_[k][3] / 2, CY + 0.5)] for k in range(1, 5)}, speed=2.5),
       Text(X0, CY + 1.3, W, 0.8, T("Change a package, push, and next week's servers start with it.", size=17,
                                    color=BODY), step=4)]
add("Your Course Image", ci, steps=4, cls="courseimg", builds=True, secs=65, notes="""
If the ready-made images aren't enough, build one course image. A Dockerfile is a few lines: start from a ready-made Jupyter image and add what your course needs.

[click] Put it in a repository on NRP's GitLab, and GitLab's CI builds it on every push, so you never need Docker on your laptop.

[click] The image lands in NRP's own registry, inside the cluster, so forty students starting it at once pull it quickly.

[click] Your menu option points at it.

[click] And students start it. Change a package, push, and next week's servers start with the new version.
""")

# ── Files and course material ──────────────────────────────────────────────────────────────────────────
files = [("Home folders", "One per student, kept between sessions. You set the size; the demo uses 5 GB.",
          "white"),
         ("Course material by link", "One link pulls your course's git repository into each student's folder "
          "(nbgitpuller). This webinar's launch links work the same way.", "gold"),
         ("Shared data", "One shared volume in every server: read-only for students, writable for you. Big "
          "datasets live once, not 40 times.", "green")]
fl = []
for i, (h, b, st) in enumerate(files):
    x = X0 + i * 4.1
    fl += [Box(x, TOP + 0.3, 3.9, 0.85, h, None, state=st, head_size=21, step=i,
               style=f"transition-delay:{0.1 * i:.1f}s"),
           Text(x + 0.1, TOP + 1.35, 3.7, 2.3, T(b, size=17, color=BODY), step=i)]
fl += [Code(X0, TOP + 3.6, W, 0.75, "https://jhub-bio210.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https://"
                                    "github.com/you/bio210&urlpath=lab/tree/bio210/week3.ipynb", size=13, step=1),
       Text(X0, TOP + 4.45, W, 0.6, T("A student clicks it and lands in week 3's notebook; their own edits are kept "
                                      "when the repository updates.", size=15, color=MUTED), step=1)]
add("Files and Course Material", fl, steps=2, secs=60, notes="""
Files. Every student has a home folder that's kept between sessions; you set the size.

[click] Course material arrives by link. One link pulls your course's git repository into each student's folder and opens the right notebook; that's a tool called nbgitpuller, and it's exactly how this webinar's launch links work. When you update the repository, students get the changes, and their own edits are kept.

[click] And shared data: one shared volume mounted in every server, read-only for students and writable for you, so a big dataset lives once, not forty times.
""")

# ── A student's first day ──────────────────────────────────────────────────────────────────────────────
DAY = [("1. Click the link", "from the syllabus or the LMS"), ("2. Campus login", "CILogon, nothing new to remember"),
       ("3. Pick from the menu", "the options you wrote"), ("4. JupyterLab opens", "week 1's notebook, ready to run")]
fd = []
for i, (h, b) in enumerate(DAY):
    x = X0 + i * 3.08
    fd.append(Box(x, TOP + 0.15, 2.9, 0.95, h, b, head_size=17, sub_size=12.5, step=i, hl=[i]))
    if i:
        fd.append(Arrow(x - 0.16, TOP + 0.62, x - 0.02, TOP + 0.62, step=i))
fd += [Image(X0 + 2 * 3.08, TOP + 1.35, 2.9, 3.2, IMG / "jhub_spawner.png", border="DDE8F2", align="c", valign="t",
             step=2),
       Image(X0 + 3 * 3.08, TOP + 1.35, 2.9, 3.2, IMG / "jupyterlab_gpu.png", border="DDE8F2", align="c", valign="t",
             step=3),
       Text(X0, TOP + 1.4, 5.9, 3.0, [T("From the student's side, the first day is four clicks. No installs, no "
                                        "“which Python?”, and the same environment as everyone else.", size=18,
                                        color=BODY),
                                      T("Screenshots: NRP's own hub. Your hub's menu shows your options.", size=13,
                                        color=MUTED, before=16)], step=1)]
add("A Student's First Day", fd, steps=3, builds=True, secs=60, notes="""
What the first day looks like for a student. They click the link in your syllabus or your LMS. [click] They sign in with their campus account. [click] They pick an option from your menu; the screenshot is NRP's own hub, and yours shows your options. [click] And JupyterLab opens on week one's notebook, ready to run. No installs, no "which Python do I have", and everyone has the same environment.
""")

# ── Sizing a class: what the scheduler sets aside ───────────────────────────────────────────────────────
SZ = [(40, "students on the Python option", "2 CPUs · 8 GB each", "80 CPUs · 320 GB"),
      (10, "students in the GPU lab", "1 GPU (24 GB) each", "10 GPUs"),
      (20, "servers idle after class", "stopped after an hour", "resources back to the pool")]
sz = [Bullets(X0, TOP + 0.15, 5.5, 5.2, [
    "Each server asks for the CPUs, memory and GPU of its menu option; the scheduler sets exactly that aside",
    ("So set options to what a student really uses, not the most you can get", 0, 1),
    ("GPU options for the units that need them; the rest of the term on CPUs", 0, 2),
    ("Idle servers stop, so a class only holds resources while it works", 0, 3),
    ("Tell the NRP team your class size and your lab times", 0, 3)], size=17, gap=10)]
sz.append(Raw(0, 0, 0.1, 0.1, '<style>.sizing .grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 8px; '
              'width: 100%; } .sizing .grid i { height: 40px; border-radius: 6px; background: #DDE1E6; transition: '
              'background .4s; } .sizing:not([data-cur="0"]) .grid i { background: var(--blue); } '
              '.sizing[data-cur="2"] .grid i.g, .sizing[data-cur="3"] .grid i.g { background: var(--orange); } '
              '.sizing[data-cur="3"] .grid i.idle { background: #DDE1E6; }</style>', pptx=False))
cells = "".join(f'<i class="{"g" if j < 10 else ""} {"idle" if j >= 20 else ""}" style="transition-delay:{j * 0.02:.2f}s">'
                f'</i>' for j in range(40))
sz.append(Raw(6.6, TOP + 0.2, 6.13, 2.3, f'<div class="grid">{cells}</div>',
              draw=lambda s, k: [s.rect(6.6 + (j % 10) * 0.61, TOP + 0.2 + (j // 10) * 0.55, 0.53, 0.45,
                                        fill=("EB6834" if j < 10 and k >= 2 else "DDE1E6" if (j >= 20 and k >= 3) or k == 0
                                              else BLUE), radius=0.08)
                                 for j in range(40)]))
for i, (n, who, each, total) in enumerate(SZ):
    sz.append(Text(6.6, TOP + 2.6 + i * 0.85, 6.13, 0.8, [T(f"**{n}** {who}: {each}", size=16, color=BODY),
                                                         T(f"= {total}", size=16, bold=True, color=NAVY)],
                   step=i + 1))
add("Sizing a Class", sz, steps=3, cls="sizing", builds=True, secs=70, notes="""
A word on sizing, because it's the question I get most. Each server asks for the CPUs, memory and GPU of its menu option, and the scheduler sets exactly that aside, whether the student uses it or not.

[click] Forty students on a Python option with two CPUs and eight gigs is eighty CPUs and 320 gigs held while they're working. So set the options to what a student really uses.

[click] Put GPUs on the options for the units that need them, here ten students in a GPU lab, ten GPUs, and keep the rest of the term on CPUs.

[click] And idle servers stop on their own, so after class those resources go back. If you tell the NRP team your class size and lab times, they can make sure the capacity is there.
""")

# ── Running the class ──────────────────────────────────────────────────────────────────────────────────
ADMIN = [("alex@campus.edu", "Python", "running", "ok"), ("bea@campus.edu", "R", "running", "ok"),
         ("chen@campus.edu", "PyTorch · GPU", "stopped (idle)", "idle"), ("dana@campus.edu", "Python", "running",
                                                                         "ok")]
adm = ('<style>.admin { width: 100%; height: 100%; background: #fff; border: 2px solid #DDE8F2; border-radius: 12px; '
       'padding: 20px 24px; box-shadow: 0 6px 18px rgba(0,0,0,.08); } .admin h3 { font: 700 30px var(--f-body); '
       'color: var(--navy); margin-bottom: 12px; } .admin table { width: 100%; border-collapse: collapse; '
       'font-size: 22px; } .admin th { text-align: left; color: var(--muted); font-weight: 600; padding: 8px 6px; '
       'border-bottom: 2px solid #E3E6EA; } .admin td { padding: 12px 6px; border-bottom: 1px solid #EEF1F4; } '
       '.admin .ok { color: #1B7F55; font-weight: 700; } .admin .idle { color: var(--muted); } .admin .b { display: '
       'inline-block; font-size: 18px; padding: 4px 10px; border-radius: 6px; margin-right: 6px; border: 2px solid '
       '#B9C7D8; color: var(--navy); } .runclass[data-cur="1"] .admin .acc { background: #FFF4CC; border-color: '
       '#E9B55C; }</style><div class="admin"><h3>Admin · BIO 210 hub</h3><table><tr><th>Student</th><th>Option</th>'
       '<th>Server</th><th></th></tr>'
       + "".join(f'<tr><td>{u}</td><td>{o}</td><td class="{c}">{st}</td><td><span class="b">stop</span>'
                 f'<span class="b acc">open</span></td></tr>' for u, o, st, c in ADMIN)
       + "</table></div>")


def adm_draw(s, k):
    rows = [["Student", "Option", "Server"]] + [[u, o, st] for u, o, st, _ in ADMIN]
    s.text(X0, TOP + 0.1, 6.3, 0.4, P("Admin · BIO 210 hub", size=16, bold=True, color=NAVY))
    s.table(X0, TOP + 0.55, 6.3, [2.6, 1.9, 1.8], rows, size=13, head_size=13, row_h=0.45, mono_cols=(),
            bold_first=False)


rc = [Raw(X0, TOP + 0.1, 6.3, 3.4, adm, draw=adm_draw),
      Bullets(7.25, TOP + 0.15, 5.48, 5.2, [
          ("The admin page lists every student's server: stop it, or **open it** to help", 0, None),
          ("Idle servers stop on their own: an hour by default, or what you set", 0, None),
          ("A big lab session? Ask the NRP team to set nodes aside for it", 0, 2),
          ("End of term: students download their work, then you remove the hub", 0, 2)], size=17, gap=11),
      Text(X0, TOP + 3.75, 6.3, 1.2, T("“Open” drops you into the student's own JupyterLab, with their files, "
                                       "so you can see exactly what they see.", size=15, color=MUTED), step=1)]
add("Running the Class", rc, steps=2, cls="runclass", secs=55, notes="""
Day to day, the admin page is where you live. It lists every student's server, and you can stop one or open it. Idle servers stop on their own, after an hour by default.

[click] Open is the useful one: it drops you into that student's own JupyterLab, with their files, so you see exactly what they see. It turns "it doesn't work" emails into a thirty-second fix.

[click] For a big lab session, ask the NRP team ahead of time to set some nodes aside for that hour. And at the end of the term, students download their work, and you remove the hub with one command.
""")

# ── A hub is one file ──────────────────────────────────────────────────────────────────────────────────
HUBFILE = """hub:
  config:
    JupyterHub:
      authenticator_class: cilogon          # campus login
      admin_users: [you@campus.edu, ta@campus.edu]
    CILogonOAuthenticator:
      allowed_idps:
        https://idp.campus.edu/idp/shibboleth:
          allowed_domains: [campus.edu]
singleuser:
  profileList:                              # the image menu
  - display_name: Python for data science
    kubespawner_override:
      image_spec: quay.io/jupyter/scipy-notebook:2024-04-22
  - display_name: PyTorch with a GPU
    kubespawner_override:
      image_spec: quay.io/jupyter/pytorch-notebook:cuda12-2024-04-22
      extra_resource_limits: {nvidia.com/gpu: "1"}
  storage:
    capacity: 5Gi                           # each student's home folder
cull:
  timeout: 3600                             # stop idle servers after an hour
ingress:
  hosts: [jhub-bio210.nrp-nautilus.io]      # your class's URL"""
hf_hl = {**{i: [1] for i in range(1, 10)}, **{i: [2] for i in range(10, 19)}, 19: [3], 20: [3], 21: [4], 22: [4],
         23: [5], 24: [5]}
HCAP = [("Who logs in", "campus login, your admins, your campus"), ("The image menu", "an image and resources per option"),
        ("Home folders", "the size of each student's folder"), ("Idle servers", "stop after an hour"),
        ("The address", "the URL you give the class")]
one = [Code(X0, TOP + 0.05, 7.4, 5.0, HUBFILE, size=11.5, lang="yaml", lines_hl=hf_hl, title="values.yaml (shortened)")]
for i, (h, b) in enumerate(HCAP):
    one.append(Box(8.3, TOP + 0.1 + i * 0.85, 4.43, 0.72, h, b, state="white", head_size=15, sub_size=11.5,
                   align="l", hl=[i + 1]))
one.append(Code(8.3, TOP + 4.3, 4.43, 0.85, "helm install bio210 \\\n    jupyterhub/jupyterhub -f values.yaml",
                size=11, step=5))
add("A Hub Is One File", one, steps=5, cls="hubfile", builds=True, secs=90, notes="""
Everything I just described is one settings file for a standard Helm chart, the community's JupyterHub chart. Shortened, it looks like this.

[click] Who logs in: campus login through CILogon, your admins, and which campus.

[click] The image menu: each option is an image, and here the second one asks for a GPU.

[click] The size of each student's home folder.

[click] When idle servers stop.

[click] And your class's address. Then one command, helm install, and a few minutes later you have a hub. That's what I'll do live in a moment.
""")

# ── Changing the hub mid-term: overlays ────────────────────────────────────────────────────────────────
TERM = [("Week 1", "values.yaml", "the hub you agreed to run"),
        ("Week 6", "+ gpu-unit.yaml", "a GPU option for the deep-learning unit"),
        ("Week 9", "+ dataset.yaml", "this term's dataset, shared"),
        ("Finals", "+ finals.yaml", "a longer idle timeout"), ("After", "helm uninstall", "students keep their work")]
mt = []
for i, (w, f, what) in enumerate(TERM):
    x = X0 + i * 2.48
    mt += [Box(x, TOP + 0.2, 2.3, 1.45, w, None, state="active" if i == 0 else "white", head_size=18, step=i),
           Text(x, TOP + 1.05, 2.3, 0.4, T(f, size=13, font=MONO, color=GOLD if i == 0 else BLUE, align="c"), step=i),
           Text(x, TOP + 1.8, 2.3, 1.0, T(what, size=15, color=BODY, align="c"), step=i)]
mt += [Code(X0, TOP + 3.05, W, 0.95, "helm upgrade bio210 jupyterhub/jupyterhub \\\n    -f values.yaml -f gpu-unit.yaml",
            size=14, step=1),
       Text(X0, TOP + 4.2, W, 1.2, [T("Each change is a small file on top of the one you started with. Remove the file "
                                      "and upgrade again, and the change is gone; the base file never changes.",
                                      size=17, color=BODY)], step=1)]
add("Changing the Hub Mid-Term", mt, steps=4, builds=True, secs=70, notes="""
Courses change during the term, and so can the hub. You start with the values file you agreed to run. [click] In week six, the deep-learning unit: a small extra file adds a GPU option, and helm upgrade applies it on top. [click] In week nine, this term's dataset, mounted for everyone. [click] During finals, a longer idle timeout so nobody loses a server mid-exam. Each change is its own small file; remove it and upgrade again, and it's gone. [click] And after the term, students download their work and one command removes the hub. A tip from the lesson page: the files merge, except lists like the menu, which a later file replaces whole.
""")

# ── From request to first lecture ──────────────────────────────────────────────────────────────────────
PLAN = [("Ask", "email the NRP team, or a NAIRR Classroom request"), ("Namespace ready", "you and your TAs as admins"),
        ("Write the file", "start from this webinar's values file"), ("helm install", "minutes to a running hub"),
        ("Test, then share", "with your TAs first, then the class URL")]
pl = []
bw, gap = 2.2, 0.28
for i, (h, b) in enumerate(PLAN):
    x = X0 + i * (bw + gap)
    pl.append(Box(x, TOP + 0.3, bw, 1.45, f"{i + 1}. {h}", b, head_size=15.5, sub_size=12.5, step=i, hl=[i]))
    if i:
        pl.append(Arrow(x - gap + 0.02, TOP + 1.02, x - 0.02, TOP + 1.02, step=i))
pl += [Text(X0, TOP + 2.25, W, 1.2, [T("Before the term: a week or two is plenty. The NRP team helps at every step, "
                                       "in office hours and on chat.", size=19, color=BODY)], step=4),
       Text(X0, TOP + 3.3, W, 1.2, [T("After the term: students download their work; `helm uninstall` removes the "
                                      "hub.", size=19, color=MUTED)], step=4),
       Link(X0, TOP + 4.6, W, 0.3, "https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/", size=14, step=4)]
add("From Request to First Lecture", pl, steps=4, secs=50, notes="""
Putting it together, from request to first lecture. Ask: email the NRP team, or put in a NAIRR Classroom request. [click] Your namespace is ready, with you and your TAs as admins. [click] Write the file, starting from the one in this webinar's materials. [click] helm install, and minutes later you have a hub. [click] Test it with your TAs, then share the URL with the class. A week or two before the term is plenty, and the NRP team helps at every step. After the term, students download their work and one command removes the hub.
""")

# ── This webinar runs on one ───────────────────────────────────────────────────────────────────────────
add("This Webinar Runs on One", [
    Bullets(X0, TOP + 0.15, 6.3, 5.2, [
        "**jh-training.nrp-nautilus.io**: a JupyterHub on NRP for workshops like this one",
        "Every attendee's server comes with `kubectl` and `helm` set up, and an LLM token",
        "Jupyter AI is in the image, pointed at NRP's models",
        "A pool of 100 namespaces, **nrp-training-000** to **099**: each person claims one for the session",
        "Sized for about 200 people at once; idle servers stop on their own"], size=18, gap=11),
    Frame(7.2, TOP + 0.2, 5.53, 4.3, fill=CARD, line=None, radius=0.05),
    Text(7.5, TOP + 0.45, 4.93, 3.9, [T("Workshop hub vs. course hub", size=18, bold=True, color=NAVY),
                                      T("Same chart, same kind of values file", size=16, before=12),
                                      T("A workshop: short-lived, a shared login, tools preinstalled", size=16,
                                        before=8),
                                      T("A course: a term long, campus login, your class list, home folders that "
                                        "last", size=16, before=8),
                                      T("If you follow the demo, you're using it right now.", size=16, bold=True,
                                        color=BLUE, before=16)]),
], secs=50, notes="""
One more example, and you're looking at it. If you follow along today, you're on jh-training, a JupyterHub on NRP for workshops. Every attendee's server comes with kubectl and helm set up and an LLM token, Jupyter AI is in the image, and there's a pool of a hundred namespaces, one per person for the session. It's the same chart and the same kind of values file as a course hub; the differences are lifetime, login and storage.
""")
