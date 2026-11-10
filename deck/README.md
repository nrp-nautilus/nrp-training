# Deck and run sheet — UCLA Health Research Tech Talk

Builds `../slides/ucla-health-nrp.pptx` (SDSC template, speaker notes with planned
times on every slide) and holds the presenter's run sheet for the demo.

## Rebuild the deck

```bash
cd trainings/ucla-health
python3 deck/snapshot_fleet.py   # optional: refresh GPU counts from the cluster (needs kubectl)
python3 deck/make_figures.py     # data/gpu_fleet.csv -> figures/fleet_by_memory.png
python3 deck/make_map.py         # data/nrp_sites.json -> figures/map_0..2.png (add --refresh for today's sites)
python3 deck/build_deck.py       # -> slides/ucla-health-nrp.pptx
python3 deck/build_html.py       # -> slides/ucla-health-nrp.html (animated; run after build_deck.py)
python3 deck/build_deck.py alts /tmp/alts.pptx   # optional: the A/B/C versions of slides 4 and 17
```

Style: short topic titles, no subtitles, plain bullets, one real visual per slide, and the
template's own section headers. `V4` and `V17` at the top of `build_deck.py` pick the version
of "What is NRP?" and the policy slide.

Needs Python 3 with `python-pptx`, `Pillow`, `lxml` and `matplotlib`. Then export
`slides/ucla-health-nrp.pdf` (PowerPoint: File → Export → PDF, or
`soffice --headless --convert-to pdf`); the site offers it as a download. The presentation
page itself shows the animated HTML deck, embedded with an iframe in `lessons/1_presentation.md`.

`build_deck.py` overwrites the `.pptx`. Once you edit the deck in PowerPoint,
treat the `.pptx` as the source.

| File | Role |
|---|---|
| `build_deck.py` | Every slide and its speaker notes |
| `build_html.py` | The animated HTML version (`slides/ucla-health-nrp.html`), same slides with step animations; notes come from the pptx |
| `deckkit.py` | Layout helpers (cards, icons, code panels, tables), from the HPC-CI webinar deck |
| `snapshot_fleet.py` | GPUs per model from the cluster's node labels → `data/gpu_fleet.csv` |
| `make_figures.py` | The fleet chart, colored by GPU memory |
| `make_map.py` | The site map on "What is NRP?": the PowerPoint frames, and the geometry the HTML map uses |
| `sweep.py` | Text both builders share: the kubectl output on "Access Methods" and the sweep on "Ways to Run Work" |
| `data/nrp_sites.json` | Site names and coordinates from the NRP dashboard's API (dash.nrp-nautilus.io/api/nodes), 10 Nov 2026 |
| `data/us-states-10m.json` | US state outlines (US Census boundaries, from the us-atlas package) |
| `data/demo_job_output.txt` | Real output of `workspace/yamls/gpu-job.yaml`, shown on the "Running the Job" slide |
| `assets/` | The SDSC template (and its wordmark and title photo for the HTML version), screenshots |

Numbers on the slides: GPUs, models and nodes come from the snapshot (date in
`data/SNAPSHOT`); "7.1 B tokens a day" is the September 2026 average from the
HPC-CI webinar; model uses come from the NRP models page (26 Oct 2026).

## Timing

About 30 minutes of slides, a 12-minute demo, and 15 minutes of questions. Slide 0:00 is
after Clifford's introduction. Two slides are fake animations, copies of one slide paged
through in the PDF: "What is NRP?" (four copies: the three operator sites, then UCLA, then
every site, then the last bullet) and "Access Methods" (overview, then the LLM, JupyterHub
and Kubernetes paths highlighted). Slide numbers are plain text, so the copies share a
number; if you insert slides in PowerPoint, the numbers after them won't update by themselves.

## Demo run sheet

**Morning of the talk**

1. Merge and push this training to `main`, so `materials/ucla-health` has the new
   notebooks. The launch links pull from that branch.
2. Open https://training.nrp-nautilus.io/ucla-health/ and check the slides and both launch links.
3. Optional: `python3 deck/snapshot_fleet.py` and rebuild if you want today's GPU counts.

**About 15 minutes before (11:45)**

1. Log in at jh-training.nrp-nautilus.io and start a server **with a GPU**. Open
   `1_ai.ipynb` and `2_gpu.ipynb`; open the Jupyter AI chat panel once so it's warm.
2. Run `1_ai.ipynb` top to bottom once (the `%%ai` cells take 5–15 s each), then
   **Kernel → Restart and clear outputs**.
3. Submit a warm-up job, so a node has the image and you have a finished run to
   show if the live one waits for a GPU:

   ```bash
   cd ~/ucla-health/workspace/yamls
   sed "s/<username>/warmup/" gpu-job.yaml | kubectl apply -f -
   kubectl get pods -n nrp-training-k8s -l job-name=gpu-train-warmup -w
   ```

4. Open https://nrp.ai/viz/resources/ in a browser tab.

**Part 1 — AI (about 6 min), `1_ai.ipynb`**

1. Sections 1–3: token, model list, one `gpt-oss` call (about 2 s).
2. Chat panel: run `temperature conversion`, select it, `/fix`. Then point at
   `sensor average`: no traceback, so no `/fix`.
3. `%load_ext`, then **Give it your data**: run the summary cell, the `%%ai` cell
   (about 15 s), then the `df.corr()` check. Point out anything the model got
   wrong or left out; in testing it called `s3` predictive without saying the
   correlation is negative.
4. If time: the silent bug with `{readings}` and `{average}`.

**Part 2 — GPUs (about 6 min), `2_gpu.ipynb`**

1. Show nrp.ai/viz/resources, then section 1 (GPU counts from node labels).
2. Section 2: `nvidia-smi` and the CPU vs GPU matrix multiply.
3. Section 3: print the YAML, submit, run the watch cell. Narrate Pending →
   Running. If it stays Pending for more than a minute, run the `describe` cell
   (reasons such as `Insufficient nvidia.com/gpu`), then show the warm-up job:
   `kubectl logs job/gpu-train-warmup -n nrp-training-k8s`.
4. Clean up both jobs.

**Fallbacks**

- LLM slow or down: check https://nrp.ai/llm-status/; switch the `%%ai` model to
  another name from the model list (e.g. `qwen3-small`) and give it a larger budget,
  or show the expected output on the training site.
- No GPU in the session: skip section 2 of Part 2; the batch job doesn't need one.
- Cluster busy: the expected job output is on the slide "Running the Job"
  and on the demo page.

**Tested 9 Nov 2026:** the job ran on an A10 (image cached) in under 30 s from
submit, and waited about 5 minutes for a GPU when the cluster was full. On a node
without the image, the 3 GB pull took from 2 to more than 10 minutes depending on
the site. On a V100 the same image fails with "no kernel image is available",
which is why the job requires Ampere or newer.

**If you want to remove the pull delay entirely:** ask for the training nodes
(`nrp-training=true`) to be reserved for the session, or pre-pull
`pytorch/pytorch:2.9.0-cuda13.0-cudnn9-runtime` onto them with the
`tutorial-image-prepuller` DaemonSet in the `nrp-training` namespace.

## The animated HTML version

`slides/ucla-health-nrp.html` is one self-contained file (images embedded; fonts from Google
Fonts). Open it in a browser, or on the training site's presentation page.

| Key | Does |
| --- | --- |
| → ↓ Space PgDn, or a click | next step, then next slide |
| ← ↑ PgUp, or a click on the left quarter | back |
| N | speaker notes |
| F | full screen |

`#12` in the URL jumps to slide 12 and `#12.3` to its third step. `?print` shows every slide in
its final state; with the site served locally, a PDF of it:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer \
  --virtual-time-budget=8000 --print-to-pdf=animated.pdf "http://localhost:8000/ucla-health/slides/ucla-health-nrp.html?print"
```

Animated steps: What is NRP? (the operators' sites, then UCLA, then every site drops onto the map,
west to east); Kubernetes and Containers (layers stack, an orange box draws around them with "built
once, from a Dockerfile", the cluster appears, an orange container lifts off and lands on a GPU node);
Access Methods (each door lights up; on the Kubernetes door, kubectl apply and get pods, then the
first job completes and the pending one takes its GPU); What NRP Is For; Ways to Run Work (JupyterHub,
a pod, a Deployment, then a Job: six jobs submitted, four start, two wait in Pending and take the first
GPUs that free up); A GPU Job (each part of the YAML lights up with its explanation); Running the Job
(the output types in); Using the LLMs (Claude Code, then opencode). If anything misbehaves, present the
PDF or PowerPoint instead.

## Agent screenshots

The Claude Code and opencode pictures on "Using the LLMs" are real sessions, run on 10 Nov 2026
from `workspace/yamls` against NRP's models (Claude Code on `gpt-oss` through
`https://ellm.nrp-nautilus.io/anthropic`, opencode on `qwen3`), each asked to explain
`gpu-job.yaml`. The final terminal screen was captured with a pseudo-terminal and drawn in Menlo.
