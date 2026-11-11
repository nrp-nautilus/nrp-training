"""Every slide of the SCinet deck, defined once; build_html.py and build_deck.py render it.

The slides live in section files, imported here in deck order:

    s1_open.py     title, agenda, what NRP is
    s2_built.py    how it's built
    s3_run.py      how we run it
    s4_ai.py       AI on NRP
    s5_use.py      using it yourself, demo, questions
    s6_backup.py   backup slides

Numbers come from data/snapshot.json (snapshot.py, read-only queries against the cluster) and the
site list in data/nrp_sites.json (the NRP dashboard's API). Slides marked optional=True are the
first to cut if the talk runs long; deck/README.md lists them.
"""
from common import SECONDS, SLIDES, TOP, X0, W, X1  # noqa: F401
import s1_open  # noqa: F401  (each import appends its slides to SLIDES)
import s2_built  # noqa: F401
import s3_run  # noqa: F401
import s4_ai  # noqa: F401
import s5_use  # noqa: F401
import s6_backup  # noqa: F401
from s1_open import EVENT, SPEAKER, TAGLINE, TITLE  # noqa: F401

# ═════════════════════════════════════════════════════════════════════════════════════
# TIMING: the "[h:mm]" that starts each speaker note, computed from these durations (seconds),
# so reordering or cutting slides keeps the times right. Backup slides get none.
# ═════════════════════════════════════════════════════════════════════════════════════
_DEFAULTS = {"Inside the National Research Platform": 60, "Agenda": 45, "What is NRP?": 90, "From PRP to NRP": 50,
           "NRP in Numbers": 40, "The Network Underneath": 75, "Policy Lives in the Cluster": 60,
           "One Cluster, Many Sites": 45, "Storage": 50, "More Than GPUs": 50, "Getting Traffic In": 60,
           "Git Is the Source of Truth": 70, "CI in a VM per Job": 60, "Build and Deploy Your Own": 40,
           "NetBox Knows Every Node": 75, "The Agent, Up Close": 40, "Watching the Cluster": 50,
           "Measuring the Network": 60, "Security": 60, "Routine Care": 30, "Sharing GPUs Fairly": 60,
           "How a Node Joins": 60, "The LLM Service": 50, "Where the Models Run": 40, "A Request, Step by Step": 100,
           "Gateway Policies": 60, "Ask for a Task, Not a Model": 50, "Serving with vLLM": 60,
           "Borrowing Idle GPUs": 50, "Around the Models": 30,
           "An LLM on Call: nrp-ops-bot": 75, "Ways In": 40, "Getting Access": 45, "Ways to Run Work": 70,
           "A GPU Job": 40, "Where to Start": 50, "Live Demo": 720, "Acknowledgments": 20}
for _k, _v in _DEFAULTS.items():
    SECONDS.setdefault(_k, _v)


def retime(slides, default=55, section=10):
    import re
    t, backup = 0, False
    for sd in slides:
        backup = backup or sd.title == "Backup"
        tag = re.compile(r"^\[\d+:\d\d\]\s*")
        if backup:
            sd.notes = tag.sub("", sd.notes)
            continue
        if sd.notes:
            sd.notes = f"[{t // 3600}:{t // 60 % 60:02d}] " + tag.sub("", sd.notes)
        t += SECONDS.get(sd.title, section if sd.kind == "section" else default)
    return t


TOTAL = retime(SLIDES)
