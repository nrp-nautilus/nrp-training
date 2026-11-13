# Deck and run sheet: Prototype National Research Platform Classroom (NJEdge, 13 Nov 2026)

Builds the animated deck (`../slides/nairr-classroom.html`) and its PowerPoint fallback
(`../slides/nairr-classroom.pptx`) from one set of slide definitions, and holds the run sheet.
The machinery is the SCinet deck's (`trainings/scinet-sc26/deck`).

## Rebuild

```bash
cd trainings/nairr-classroom
python3 deck/snapshot.py      # optional: today's cluster numbers (read-only; needs kubectl with admin read)
python3 deck/make_map.py      # the map images for the PowerPoint
python3 deck/build_html.py    # -> slides/nairr-classroom.html, and deck/presenter/nairr-classroom.html with notes
python3 deck/build_deck.py    # -> slides/nairr-classroom.pptx, and deck/presenter/nairr-classroom.pptx with notes
soffice --headless --convert-to pdf --outdir slides slides/nairr-classroom.pptx
```

Needs Python 3 with `python-pptx`, `Pillow`, `lxml` and `matplotlib`. `DECK_OUT=<dir>` before either
build writes a test copy there instead.

| File | Role |
|---|---|
| `slides.py` | The deck: imports the section files in order, and computes the timing tags |
| `s1_open.py` | Title, agenda (with the nautilus), what NRP is (NJEdge's pin highlighted), containers and Kubernetes |
| `s2_access.py` | Getting in: access, NAIRR Classroom, namespaces, ways in |
| `s2b_course.py` | Resources for your course: what a course can use, choosing GPUs, sharing GPUs, regions and storage, ways to run work, a GPU job, fair use |
| `s3_jhub.py` | JupyterHub for your class: two ways, how a class hub works, login and its setup, the image menu, a course image, files, a student's first day, sizing, running the class, the values file, mid-term changes, request to first lecture, the training hub |
| `s3b_ai.py` | AI in the classroom: Jupyter AI and the API, task names |
| `s4_close.py` | The demo section, getting help, where to start, acknowledgments, questions, backup |
| `common.py`, `elements.py`, `deckkit.py`, `build_*.py` | Shared machinery from the SCinet deck |
| `data/` | The 10 Nov cluster snapshot and the dashboard's site list |

The `.pptx` is overwritten on every build. Once you edit it in PowerPoint, treat it as the source.

## What it covers, and what it leaves to Frank

Frank's talk in the same series (EDUCAUSE, 20 Aug 2026) covered why: learning by doing, Jupyter in
large classes, AI tutors, the NDP Education Hub, UC San Diego's numbers, NRP's map and usage. This
deck refers back to it twice (the map, and the Berkeley class with an AI chat panel) and spends its
time on how: access, what a course can use, and what an instructor controls in a course hub.

## Timing

About 37 minutes of slides (35 before the demo, 2 after), a 20-minute demo, and only a few minutes of questions. To make room, skip the optional slides (From PRP to NRP, A GPU Job) or shorten demo step 5 to 5.1. Start: 12:00 pm Eastern (the Zoom invite). Two slides are optional (From PRP to NRP, A GPU Job) if you run long. The `[h:mm]`
at the start of each speaker note comes from `secs=` on each `add(...)`.

## Numbers

- **From the cluster** (`data/snapshot.json`, 10 Nov 2026): nodes, GPUs and models, CPUs (hardware
  threads, physical nodes only), namespaces.
- **Counted on 12 Nov:** 152 JupyterHubs (pods labeled `component=hub`) and 111 open user servers.
- **NAIRR Classroom terms:** the request page (up to three pages, AI subject matter, US-based
  students, a decision within a month).
- **Illustrative:** the course names (BIO 210), students and menu options on the JupyterHub slides.

## Run sheet

**The day before**

1. Review, then commit and push to `main`, so `materials/nairr-classroom` has the demo files.
2. Restart the site so training.nrp-nautilus.io shows it: `kubectl rollout restart deployment/training-site -n nrp-training`.

**Before the day**

- `nrp-training-000` still holds a `jhub-ddiaz` release from 24 Sep. The claim service hands out `000`
  first, so either uninstall it (`helm uninstall jhub-ddiaz -n nrp-training-000`) or expect the first
  claimer to land next to it.
- Check that the pool is empty: the claim service's status shows how many of the 100 are taken.

**About an hour before**

Do one full rehearsal of the live path in your own claimed namespace, then clean up. The first server
start on a node pulls the scipy image (about a minute); a rehearsal warms only the node it lands on.

**About 15 minutes before**

1. Log in at jh-training.nrp-nautilus.io and open the demo notebook through the launch link on the demo page (Bash kernel).
2. Open the presenter copy of the deck (`deck/presenter/nairr-classroom.html`, **N** for notes) and keep a browser tab ready for the hub's address.

**The demo (about 20 minutes; each step is marked ▶ on the demo page)**

1. **Get a namespace (1 min):** the claim cell sets `NS`.
2. **One file holds every decision (3 min):** the `grep` of the six deciding lines in `jhub-values.yaml`.
3. **Install it (3 min):** `helm repo add` and `update`, then `sed` the namespace into the file and `helm install jhub ... --wait`. About two minutes in testing; talk through the values while it runs.
4. **Log in like a student (4 min):** `https://jhub-<namespace>.nrp-nautilus.io`, log in as `admin` (the password is under `DummyAuthenticator` in `jhub-values.yaml`), start Scipy, show the admin page.
5. **A closer look (5 min):** Helm in one paragraph and the 13 objects it renders (`helm get manifest jhub -n $NS | grep "^kind:" | sort | uniq -c`), then each block of the values file with `sed -n`. Short on time: keep 5.1, skip the blocks.
6. **Change it (2 min):** `helm upgrade` with `course-menu.yaml`; the menu drops to three entries, one with a GPU. About 80 s; a running server survives it.
7. **Clean up (1 min):** `helm uninstall`, then delete the leftover pods and volumes together (student pods outlive the release and hold their volumes), then release the namespace.

Tested on 12 Nov as the hub's service account (`jupyterhub-sa`) in `nrp-training-001`: install in 129 s,
login and spawn, the menu change, and full cleanup. Not tested from inside the training hub itself, and
the GPU menu entry wasn't started.

**Fallbacks**

- `helm install` slow: keep talking through the values file; the hub usually answers within two minutes.
- Something breaks: the demo page has every command and its expected output.
- Animation trouble: present `slides/nairr-classroom.pptx` or the PDF.

## Presenting

| Key | Does |
| --- | --- |
| → ↓ Space PgDn (a presenter clicker sends PgDn) | next step, then next slide |
| ← ↑ PgUp | back |
| N | speaker notes (presenter copy only) |
| F | full screen |

Mouse clicks don't change slides, so you can point at and select text.
