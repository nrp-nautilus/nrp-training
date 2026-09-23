# The National Research Platform: Cyberinfrastructure for Research and Education

HI-DSI Workshop Series · 23 September 2026 · 1:00–2:30 pm HST · Zoom

Workshop materials for the University of Hawai‘i Data Science Institute. The
session is geared toward **educational use of NRP**, but the tools covered —
Jupyter notebooks, LLM-as-a-service, AI assistants in JupyterLab — are
of equal relevance to research.

[Event page](https://datascience.hawaii.edu/event/the-national-research-platform-cyberinfrastructure-for-research-and-education/) ·
[Published materials](https://training.nrp-nautilus.io/hidsi/)

## Lessons

| # | Lesson | Time | Covers |
|---|---|---|---|
| 1 | [NRP, Access & Requesting Resources](lessons/1_intro.md) | 20 min | What NRP is, CILogon access, namespaces, CPUs and GPUs, the three ways to request resources |
| 2 | [AI for the Classroom](lessons/2_ai_classroom.md) | 20 min | The managed LLM endpoint from Python, notebook magics, and Jupyter AI fixing broken code |
| 3 | [Deploy a Custom JupyterHub](lessons/3_custom_jupyterhub.md) | 40 min | Helm deploy, ingress, profiles and resource limits, shared class storage, CILogon, custom images in NRP GitLab CI |

## Layout

- `config.yml` — title, landing-page metadata, and lesson order.
- `lessons/` — the lesson Markdown files.
- `workspace/` — notebooks, `check.sh`, and the YAML manifests attendees run.
- `images/` — screenshots and diagrams used by the lessons.

## Hands-on requirements

Attendees work on the training JupyterHub at `jh-training.nrp-nautilus.io`,
where `kubectl`, `helm`, and the LLM token are preconfigured. Lesson 3 needs
each attendee to claim a namespace from the `nrp-training-000`–`099` pool via
the in-cluster claim service.
