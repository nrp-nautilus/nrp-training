# NAIRR AI Education Webinar Series: Prototype National Research Platform Classroom

13 November 2026 · 12:00–1:00 pm EST · webinar

Introduces educators and researchers to the National Research Platform (NRP) and
demonstrates a practical workflow for deploying a multi-user JupyterHub for
classroom instruction. Delivered primarily as a live demonstration; following
along is optional and no advance setup is required.

[Published materials](https://training.nrp-nautilus.io/nairr-classroom/)

## Lessons

| # | Lesson | Time | Covers |
|---|---|---|---|
| 1 | [NRP, Access & Resources](lessons/1_intro.md) | 15 min | What NRP is, CILogon access, namespaces, CPUs and GPUs |
| 2 | [Deploy a JupyterHub Classroom](lessons/2_custom_jupyterhub.md) | 35 min | Helm deploy, ingress, image profiles, shared class storage, what changes for a real course |
| — | Q&A | 10 min | |

## Layout

- `config.yml` — title, landing-page metadata, and lesson order.
- `lessons/` — the lesson Markdown files.
- `workspace/` — notebook, `check.sh`, and the YAML manifests attendees run.
- `images/` — screenshots and diagrams used by the lessons.

## Hands-on requirements

None. Anyone following along works on the training JupyterHub at
`jh-training.nrp-nautilus.io`, where `kubectl` and `helm` are preconfigured.
Lesson 2 needs each follower to claim a namespace from the
`nrp-training-000`–`099` pool via the in-cluster claim service.
