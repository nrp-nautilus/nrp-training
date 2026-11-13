# NAIRR AI Education Webinar Series: Prototype National Research Platform Classroom

An Edge webinar hosted by NJEdge (Forough Ghahramani) · 13 November 2026 · 12:00–1:00 pm Eastern · Zoom webinar

Introduces educators and researchers to the National Research Platform (NRP) and demonstrates a
practical workflow for deploying a multi-user JupyterHub for classroom instruction. Mostly a
presentation, then a live demonstration; following along is optional and no advance setup is
required. It follows Frank Würthwein's talk in the same series, which covered why notebooks, data
and AI belong in the classroom, so this session is about how.

[Published materials](https://training.nrp-nautilus.io/nairr-classroom/)

## Lessons

| # | Lesson | Time | Covers |
|---|---|---|---|
| 1 | [Presentation](lessons/1_presentation.md) | 37 min | What NRP is, getting in (CILogon, namespaces, NAIRR Classroom), what a course can use (GPUs, storage, fair sharing), what you control in a JupyterHub for your class, and AI in the classroom |
| 2 | [Live demo: a class hub from one file](lessons/2_custom_jupyterhub.md) | 15 min | Claim a namespace, `helm install` a JupyterHub, log in, change its menu, remove it |
| — | Questions | about 8 min | |

## Layout

- `config.yml` — title, landing-page metadata, and lesson order.
- `lessons/` — the lesson pages.
- `deck/` — the animated deck's source (one Python file per section) and its run sheet; see `deck/README.md`.
- `slides/` — the built deck: `nairr-classroom.html` (animated), `.pptx` and `.pdf`.
- `workspace/` — the demo notebook and the values files attendees run.
- `images/` — screenshots used by the slides and lessons.

## Hands-on requirements

None. Anyone following along works on the training JupyterHub at `jh-training.nrp-nautilus.io`,
where `kubectl` and `helm` are preconfigured, and claims a namespace from the
`nrp-training-000`–`099` pool through the in-cluster claim service.
