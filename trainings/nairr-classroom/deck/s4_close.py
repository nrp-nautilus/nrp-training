"""The demo, where to start, acknowledgments and questions; then backup slides.

Part of the NAIRR Classroom webinar deck: slides.py imports the section files in order. Shared constants
and helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
"""
from common import *  # noqa: F401,F403

section("Live Demo", """About fifteen minutes, on jh-training.nrp-nautilus.io, in workspace/notebooks/2_custom_jupyterhub.ipynb (Bash kernel). Run sheet: deck/README.md. Each step is marked ▶ on the demo page.

1. Get a namespace (1 min): NS=$(curl -s ".../claim?user=$JUPYTERHUB_USER").
2. One file holds every decision (3 min): the grep of the six deciding lines in jhub-values.yaml: who logs in, admins, home folder size, the image menu, the idle timeout, the address.
3. Install it (3 min): helm repo add/update, then sed the namespace into the file and helm install jhub ... --wait. About two minutes; talk through the values while it runs. Then kubectl get pods,pvc,ingress.
4. Log in like a student (4 min): https://jhub-$NS.nrp-nautilus.io, log in as admin, start Scipy (a first start on a node pulls the image, a minute or two), show the admin page.
5. Change it (2 min): helm upgrade with course-menu.yaml; the menu drops to three entries, one with a GPU. The running server survives.
6. Clean up (1 min): helm uninstall, delete the leftover pods and volumes, release the namespace.""", secs=900)

add("Getting Help", [
    Bullets(X0, TOP + 0.15, 6.3, 5.0, [
        "**Office hours** with the NRP team, every two weeks",
        "**Chat** with the team and other instructors, for quick questions",
        "**Docs** for every step in today's talk, at nrp.ai/documentation",
        "**Recorded trainings** on Docker, Kubernetes and JupyterHub, at nrp.ai/training",
        "**Today's materials**: the slides, the demo notebook and the values files"], size=18, gap=12),
    Frame(7.2, TOP + 0.2, 5.53, 3.4, fill=CARD, line=None, radius=0.05),
    Text(7.5, TOP + 0.45, 4.93, 3.0, [T("Bringing a course?", size=18, bold=True, color=NAVY),
                                      T("Email the NRP team with the course, the number of students and the start "
                                        "date, and they'll have your namespace ready before the first lecture.",
                                        size=16, before=10)]),
    Link(7.2, TOP + 3.75, 5.53, 0.3, "https://nrp.ai/contact/", size=14, align="r"),
], secs=40, notes="""
You won't be on your own. There are office hours with the NRP team every two weeks, a chat where instructors help each other, docs for every step I showed, and recorded trainings on Docker, Kubernetes and JupyterHub. And if you're bringing a course, email the team with the course, how many students and when it starts.
""")

add("Where to Start", [
    Text(X0, TOP + 0.1, 5.9, 0.45, T("This term", size=21, bold=True, color=NAVY)),
    Bullets(X0, TOP + 0.6, 5.9, 4.5, [
        "Log in at **nrp.ai** and try NRP's JupyterHub",
        "Email the NRP team about your course: what it is, how many students, when it starts",
        "For priority, a **NAIRR Classroom** request",
        "Come to office hours: every two weeks, with the NRP team"], size=17, gap=10),
    Text(6.83, TOP + 0.1, 5.9, 0.45, T("Your own hub", size=21, bold=True, color=NAVY)),
    Bullets(6.83, TOP + 0.6, 5.9, 4.5, [
        "Start from today's values file: it's in the materials",
        "Add CILogon and your class list before students arrive",
        "Build a course image when the default menu isn't enough",
        "Follow along later: every step of today's demo is on the training page"], size=17, gap=10),
    Link(X0, 6.0, W, 0.3, "https://nrp.ai/education/", size=14),
], secs=45, notes="""
Where to start. This term: log in and try NRP's JupyterHub, email the NRP team about your course, and if you want priority, put in a NAIRR Classroom request. Office hours run every two weeks. For your own hub: start from today's values file, add CILogon and your class list, and build a course image when the default menu isn't enough. Every step of the demo is on the training page.
""")

add("Acknowledgments", [
    Bullets(X0, TOP + 0.15, W, 5.0, [
        "NRP is supported by NSF awards OAC-1541349, OAC-1826967, OAC-2030508, OAC-1841530, OAC-2005369, "
        "OAC-2112167, CISE-1713149, CISE-2100237 and CISE-2120019",
        "Networks: CENIC, Pacific Wave, Internet2, MREN, GPN, NYSERNet, FLR, NEREN, Sun Corridor, OARnet, SCLR and "
        "the Albuquerque GigaPoP",
        "The NRP operations teams at SDSC, the University of Nebraska–Lincoln and MGHPCC, and the campuses that "
        "host and share their hardware",
        "Forough Ghahramani and Edge, for hosting this webinar series"], size=18, gap=14),
], secs=20, notes="Thanks to NSF, the networks, the operations teams and the campuses, and to Forough and Edge for hosting.")

links = [("Today's materials", "training.nrp-nautilus.io/nairr-classroom"), ("Portal and login", "nrp.ai"),
         ("Teaching with NRP", "nrp.ai/education"), ("Request a namespace", "get-started.nrp-nautilus.io"),
         ("NRP's JupyterHub", "jupyterhub-west.nrp-nautilus.io"),
         ("Your own hub (docs)", "nrp.ai/documentation/userdocs/jupyter/jupyterhub"),
         ("LLM token", "nrp.ai/llmtoken"), ("Support chat and email", "nrp.ai/contact")]
q = "".join(f'<div class="qrow"><span>{lab}</span><a href="https://{u}" target="_blank" rel="noopener">{u}</a></div>'
            for lab, u in links)


def q_draw(s, k):
    for i, (lab, u) in enumerate(links):
        y = 1.70 + i * 0.56
        s.text(X0, y, 3.1, 0.5, P(lab, size=17, color=LIGHT), anchor="m")
        s.text(X0 + 3.15, y, 8.0, 0.5, P(u, size=15, bold=True, color=GOLD, font=MONO), anchor="m")


add("Questions?", [
    Raw(X0, 1.7, 11.0, 4.6, q, draw=q_draw, cls="stagger"),
    Text(X0, 6.25, 12.1, 0.45, T("Daniel Diaz  ·  d4diaz@ucsd.edu", size=19, bold=True, color=WHITE)),
], kind="reverse", secs=600, notes="Questions. All the links are on the slide and on the training page.")

# ═════════════════════════════════════════════════════════════════════════════════════
# BACKUP
# ═════════════════════════════════════════════════════════════════════════════════════
section("Backup", "Backup slides for questions.")

cmp_rows = [["", "NRP's JupyterHub", "Your own hub"], ["Setup", "none: share the link", "one values file, helm install"],
            ["Who logs in", "anyone with an NRP login", "your class list, through CILogon"],
            ["Images", "NRP's menu", "your menu, or your course image"],
            ["Resources", "students choose from the menu", "you set them per option"],
            ["Course files", "students copy them in", "a link, and a shared folder"],
            ["Help", "NRP's support chat", "you open a student's server"]]
add("NRP's Hub or Your Own?", [
    Table(X0, TOP + 0.15, W, 4.4, cmp_rows, [2.4, 4.85, 4.85], size=16, row_h=0.6, cls="rows"),
], notes="Backup: the two ways side by side.")
