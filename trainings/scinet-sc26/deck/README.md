# Deck and run sheet: Inside the National Research Platform (SCinet, SC26)

Builds the animated deck (`../slides/scinet-nrp.html`) and its PowerPoint fallback
(`../slides/scinet-nrp.pptx`) from one set of slide definitions, and holds the run sheet.

## Rebuild

```bash
cd trainings/scinet-sc26
python3 deck/snapshot.py      # optional: today's numbers from the cluster (read-only; needs kubectl with admin read)
python3 deck/metrics.py       # optional: 7 days of CPU/memory/GPU use from Thanos, and the MaDDash grid
python3 deck/make_map.py      # the map images for the PowerPoint
python3 deck/build_html.py    # -> slides/scinet-nrp.html, and deck/presenter/scinet-nrp.html with notes
python3 deck/build_deck.py    # -> slides/scinet-nrp.pptx, and deck/presenter/scinet-nrp.pptx with notes
soffice --headless --convert-to pdf --outdir slides slides/scinet-nrp.pptx
```

Needs Python 3 with `python-pptx`, `Pillow`, `lxml` and `matplotlib`. `DECK_OUT=<dir>` before either
build writes a test copy there instead of `slides/` and `presenter/`.

| File | Role |
|---|---|
| `slides.py` | The deck: imports the section files in order, and computes the timing tags |
| `s1_open.py` … `s6_backup.py` | The slides, one file per section (opening, built, run, AI, use, backup): each slide's build steps and speaker notes, defined once |
| `common.py` | Shared numbers and helpers, including `packet()` and `flow()` for moving dots |
| `reference.md` | For the presenter: answers to review questions, and a glossary of every term on the slides |
| `elements.py` | The pieces a slide is made of (bullets, boxes, arrows, code, tables, stats), each rendered as HTML and as PowerPoint shapes |
| `build_html.py` | The animated deck: CSS, the step engine, and the animations (map pins, packets, the perfSONAR mesh, the GPU sharing) |
| `build_deck.py` | The PowerPoint: each slide in its final state; "What is NRP?", "Git Is the Source of Truth" and "A Request, Step by Step" as one copy per step |
| `deckkit.py` | PowerPoint layout helpers (from the UCLA and HPC-CI decks) |
| `metrics.py` | Read-only: Thanos time series for the Grafana panels, and the MaDDash grid → `data/metrics.json` |
| `snapshot.py` | Read-only cluster queries → `data/snapshot.json`: nodes, GPUs, cores, regions, Ceph, Argo CD apps, DaemonSets, AI gateway routes, model servers and where they run |
| `make_map.py` | The site maps: real dashboard coordinates; Fresno State and Internet2 Ann Arbor (not on the dashboard) placed by city |
| `sweep.py` | Text and schedule for "Ways to Run Work" (from the UCLA deck) |
| `data/nrp_sites.json` | Sites from dash.nrp-nautilus.io/api/nodes, 10 Nov 2026 |

The `.pptx` is overwritten on every build. Once you edit it in PowerPoint, treat it as the source.

## Slide order

Each idea has one home, and no slide leans on something a later slide introduces. Later slides
refer back ("the Kata runtime from the hardware slide", "the Envoy Gateway from the ingress slide",
"the opportunistic priority from the sharing slide"). That's why "How a Node Joins" closes the
operations section: by then NetBox, Prometheus, perfSONAR, the topology labels, the Calico policy
and owner priority have all been shown, so each step is a callback. For the same reason the ops bot
closes the AI section, and the full Argo CD table is a backup slide. If you move a slide, check
its notes and bullets for "from the ... slide" references.

## Timing and what to cut

About 39 minutes of slides with everything shown, a 15-minute demo, and about 6 minutes of questions.
The `[h:mm]` at the start of each speaker note is computed from per-slide durations
(`secs=` on each `add(...)`, defaults at the end of `slides.py`), so the times stay right when slides move or go. These are
marked `optional=True`, roughly in the order I'd cut them (about 5 minutes in all):

1. Routine Care
2. Around the Models
3. Multi-Node Serving
4. A GPU Job
5. Build and Deploy Your Own
6. More Than GPUs (CI still explains Kata on its own)
7. From PRP to NRP

To drop one, delete its `add(...)` block in its section file and rebuild, or hide the slide in PowerPoint.

## What the numbers are, and what's illustrative

- **From the cluster** (`data/snapshot.json`, 10 Nov 2026): nodes, GPUs, cores, regions, zones,
  Ceph capacity, namespaces, Ingress and HTTPRoute counts, DaemonSet sizes (NetBox agent,
  perfSONAR testpoint, node exporter, HAProxy), Argo CD applications, runtime classes, the
  gateway's routes and fallback order, model servers, their GPUs and their sites.
- **Copied from the cluster:** the runner config (CI slide), the NetBox agent config and loop,
  the BackendTrafficPolicy (shortened), the qwen3 StatefulSet (shortened).
- **From the NRP docs:** network requirements and ports, the contributor steps, the Kaniko pipeline,
  the security tools, the gateway's request path and the multi-node DeepSeek setup.
- **From the nrp-ops-bot README:** its tools, guardrails and status.
- **From Thanos** (`data/metrics.json`, `metrics.py`): the CPU, memory and GPU-use curves on "Watching
  the Cluster", hourly, 4–11 Nov.
- **From MaDDash** (perfsonar.nrp-nautilus.io/maddash, public): the packet-loss grid on "Measuring the
  Network", 11 Nov.
- **From the runner config maps:** "Runner Flavors" (backup).
- **From the demo run on 10 Nov:** the rate-limit headers.
- **"7.1 billion tokens a day":** the September 2026 average, from the HPC-CI webinar (as in the UCLA deck).
- **Illustrative:** the queue depths and KV-cache numbers on "A Request, Step by Step" (labeled
  "example values"), the "8-GPU node" on "Sharing GPUs Fairly", and the three campuses on "The
  Network Underneath".

## Demo run sheet

**The day before**

1. Review, then commit and push this training to `main`, so `materials/scinet-sc26` exists. The launch link pulls from that branch.
2. Restart the site so training.nrp-nautilus.io picks it up:

   ```bash
   kubectl rollout restart deployment/training-site -n nrp-training
   ```

3. Optional: `python3 deck/snapshot.py`, then rebuild, for that day's numbers.

**About an hour before**

GPUs can be scarce: on 11 Nov the test job waited more than 10 minutes, with every A10 on the
training nodes (`nrp-training=true`) in use. Either ask the admins to reserve some training nodes
for the session, or submit a warm-up job now so you have a finished run to show. On the hub, in a
terminal:

```bash
cd ~/scinet-sc26/workspace/yamls
sed "s/<username>/warmup/" gpu-job.yaml | kubectl apply -f -
kubectl get pods -l job-name=gpu-train-warmup
```

**About 15 minutes before**

1. Log in at jh-training.nrp-nautilus.io (a CPU server is enough) and open the demo through the launch link. On the hub, `kubectl` already points at `nrp-training-k8s` and `OPENAI_API_KEY` is set.
2. Run part 2 once so the gateway is warm, and check that a call answers in a few seconds.
4. Open browser tabs: https://nrp.ai/llm-status/, https://perfsonar.nrp-nautilus.io/, https://argocd.nrp-nautilus.io/ and https://grafana.nrp-nautilus.io/ (signed in, for the optional tour).

**The demo (about 15 minutes)**

1. **The cluster (2 min), in `demo.ipynb`:** nodes per region and GPU nodes per model, from the node labels. (Any NRP user can list nodes: the `nautilus-user` group has read-only list access.)
2. **The LLM gateway (4 min):** the model list (point out the task names); one `qwen3` call with the token counts; the `x-ratelimit` headers; then `coding`, and which model answered. Compare its command with the region count from part 1.
3. **A GPU job (2 min):** set `ME`, submit, `kubectl get pods`. Leave it starting.
4. **Your own agent (5 min), in `agent.ipynb` (Python 3 kernel):** the three tools, the schemas, the loop; then the DNS-and-443 question (about 10 s with `gpt-oss`; all three names land on the same ingress node) and the job-status question.
5. **Back to the job (2 min):** `kubectl logs -f`, then delete. If it's still Pending, run the `describe` cell and show the warm-up job: `kubectl logs job/gpu-train-warmup`.
6. **If time:** the Argo CD app list, a Grafana dashboard, the MaDDash grid, in a browser.

**Fallbacks**

- Gateway slow or down: check https://nrp.ai/llm-status/; switch `qwen3` to `qwen3-small` or `gpt-oss`. The expected output is on the demo page.
- The hub's LLM token fails (it returned 403 on 10 Nov): run part 2 from your laptop with your own token in `OPENAI_API_KEY`.
- Cluster busy: show the warm-up job's output.
- Animation trouble: present `slides/scinet-nrp.pptx` or the PDF.

## The animated HTML version

`slides/scinet-nrp.html` is one self-contained file (images embedded; fonts from Google Fonts).
Present from a browser or from the site's presentation page. The published copy has no notes;
`deck/presenter/scinet-nrp.html` (git-ignored) has them, toggled with **N**.

| Key | Does |
| --- | --- |
| → ↓ Space PgDn (a presenter clicker sends PgDn) | next step, then next slide |
| ← ↑ PgUp | back |
| N | speaker notes (presenter copy only) |
| F | full screen |

Mouse clicks don't change slides, so you can point at and select text. On a touch screen, swipe.

`#12` in the URL jumps to slide 12 and `#12.3` to its third step; `?print` shows every slide in
its final state, for printing to PDF from Chrome.
