# The National Research Platform -- AI-Enabled Scientific Research Computing, and Education

UCLA Health IT Research Tech Talk · 10 November 2026 · 12:00–1:00 pm PT · Zoom

What NRP offers UCLA researchers, students and instructors for **GPU computing
and AI**: the platform, how to get access (and what a namespace is), the GPU
fleet and how to run a GPU job, the hosted open-weight LLMs, and a brief word on
JupyterHub for labs and classes. About 30 minutes of slides, a 12-minute live
demo, then questions.

[Event page](https://it.uclahealth.org/events/using-the-national-research-platform-nrp-for-ai-enabled) ·
[Published materials](https://training.nrp-nautilus.io/ucla-health/)

## Schedule

| # | Page | Time | Covers |
|---|---|---|---|
| 1 | [Presentation](lessons/1_presentation.md) | 30 min | The slide deck, plus access steps, a GPU table and links |
| 2 | [Live demo](lessons/2_demo.md) | 12 min | Hosted LLMs and Jupyter AI in a notebook; a GPU in JupyterHub and a GPU Job |
| — | Questions | 15 min | |

## Layout

- `config.yml` — title, landing-page metadata, and page order.
- `lessons/` — the two pages.
- `slides/` — the deck as `.pptx` (with speaker notes) and `.pdf`, plus the page images the site shows.
- `workspace/` — the demo notebooks, the GPU job, and `check.sh`.
- `deck/` — the script that builds the deck from the SDSC template, and the presenter run sheet ([deck/README.md](deck/README.md)).
- `images/` — older screenshots kept from the first version of this training.

## Hands-on requirements

None. Attendees who want to follow the demo use the training JupyterHub at
`jh-training.nrp-nautilus.io`, where the LLM token is preset and `kubectl` is
connected to the `nrp-training-k8s` namespace.
