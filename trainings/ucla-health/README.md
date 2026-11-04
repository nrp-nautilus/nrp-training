# The National Research Platform -- AI-Enabled Scientific Research Computing, and Education

UCLA Health IT Research Tech Talk · 10 November 2026 · 12:00–1:00 pm PT · Zoom

NRP pools GPUs, petabyte-scale storage, and hosted open-weight AI models across more than 70 institutions; it is free, funded by the NSF, and sustained by the community that contributes to it. This talk introduces NRP to UCLA Health researchers: what the platform offers,
how a group gets access (with a live namespace-admin onboarding), hosted LLMs in
Jupyter notebooks, and a brief look at JupyterHub for a lab or class. Slides
followed by a live demo; target 40–50 minutes with time held at both ends.

[Event page](https://it.uclahealth.org/events/using-the-national-research-platform-nrp-for-ai-enabled) ·
[Published materials](https://training.nrp-nautilus.io/ucla-health/)

## Lessons

| # | Lesson | Time | Covers |
|---|---|---|---|
| 1 | [What NRP Offers](lessons/1_intro.md) | 15 min | Platform, potluck model, hardware, three ways in, HIPAA caveat |
| 2 | [Live Demo: Getting Access](lessons/2_onboarding.md) | 10 min | CILogon, namespaces, admin roles, live onboarding |
| 3 | [AI-Enabled Research](lessons/3_ai.md) | 15 min | Managed LLM endpoint from Python, Jupyter AI, `%%ai` magics |
| 4 | [JupyterHub for a Lab or Class](lessons/4_jupyterhub.md) | 7 min | What a hub of your own involves |
| — | Q&A | 13 min | |

## Layout

- `config.yml` — title, landing-page metadata, and lesson order.
- `lessons/` — the lesson Markdown files.
- `workspace/` — the AI notebook and `check.sh`.
- `images/` — screenshots and diagrams used by the lessons.

## Hands-on requirements

None required. Attendees who want to follow the AI demo use the training
JupyterHub at `jh-training.nrp-nautilus.io`, where the LLM token is preconfigured.
