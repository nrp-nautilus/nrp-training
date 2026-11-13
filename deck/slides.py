"""Every slide of the NAIRR Classroom webinar deck (NJEdge, 13 Nov 2026), defined once;
build_html.py and build_deck.py render it.

The slides live in section files, imported here in deck order:

    s1_open.py     title, agenda, what NRP is, containers and Kubernetes
    s2_access.py   getting in: access, NAIRR Classroom, namespaces, ways in
    s2b_course.py  what a course can use: GPUs, sharing, storage, ways to run work, fair use
    s3_jhub.py     JupyterHub for your class: what the instructor controls
    s3b_ai.py      AI in the classroom: Jupyter AI, the API, task names
    s4_close.py    the demo, where to start, questions, backup

Numbers come from data/snapshot.json (snapshot.py, read-only queries against the cluster) and the
site list in data/nrp_sites.json (the NRP dashboard's API).
"""
import re

from common import SECONDS, SLIDES, TOP, X0, W, X1  # noqa: F401
import s1_open  # noqa: F401  (each import appends its slides to SLIDES)
import s2_access  # noqa: F401
import s2b_course  # noqa: F401
import s3_jhub  # noqa: F401
import s3b_ai  # noqa: F401
import s4_close  # noqa: F401
from s1_open import DECK_TITLE, EVENT, SPEAKER, TAGLINE, TITLE  # noqa: F401

SECONDS.setdefault("Prototype National Research Platform Classroom", 75)      # the host's introduction, then yours


def retime(slides, default=55, section=10):
    """Start each speaker note with "[h:mm]", from the per-slide durations. Backup slides get none."""
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
