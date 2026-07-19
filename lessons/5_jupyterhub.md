---
title: JupyterHub on NRP
teaching: 30
exercises: 10
---

::: callout Launch the workspace in JupyterHub
**[▶ Launch the workspace in JupyterHub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fpearc26&targetpath=pearc26&urlpath=lab%2Ftree%2Fpearc26%2Fworkspace)** — you have been using the thing this episode explains all day.
:::

**Afternoon session · 12:45 – 1:25 PM**

You've spent the morning *inside* a JupyterHub. This episode opens the hood: what JupyterHub actually is, how it runs on Kubernetes, why it has become the standard for reproducible classroom and research computing, and the features you'd lean on when running your own course — before the final episode, where you deploy one yourself.

> 📘 **Docs:** [JupyterHub service](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub-service/) · [Deploy JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/) · [Scientific images](https://nrp.ai/documentation/userdocs/running/sci-img/) · [Z2JH (upstream)](https://z2jh.jupyter.org)

## What JupyterHub is

JupyterHub is a multi-user gateway to single-user Jupyter servers: users authenticate, the hub **spawns** an isolated JupyterLab server per user, and a proxy routes each browser to the right server. On Kubernetes ("Zero to JupyterHub", z2jh), those pieces map to:

- **hub pod** — authentication, user database, and the *spawner* that creates user pods.
- **proxy pod** — routes incoming traffic to the hub or to the correct user server.
- **user pods** — one JupyterLab server per active user, created on demand, culled when idle.
- **PVCs** — one home volume per user (plus one for the hub database).

<div class="image-row">
  <img src="images/jhub-1.png" alt="JupyterHub spawner profile page">
  <img src="images/jhub-2.png" alt="JupyterLab session on NRP">
</div>

Because each user server is just a **pod**, everything from this morning applies: images define the software stack, resource requests define CPU/RAM/GPU, tolerations and affinity steer students onto reserved nodes, PVCs make home directories persistent.

## Why this matters for education and research

- **Reproducibility** — every student gets the identical container image; "works on my machine" disappears.
- **Zero install** — a laptop with a browser is the only prerequisite (today's tutorial required nothing else).
- **Institutional login** — CILogon/OIDC means students use campus credentials; no account provisioning.
- **Fair sharing** — per-user CPU/RAM/GPU limits and idle culling keep one user from starving a class.
- **Scale on national CI** — the same hub that serves 5 researchers serves a 300-student course; NRP supplies the nodes.

## The hosted NRP JupyterHubs

NRP operates hosted hubs you can use without deploying anything — e.g. [jupyterhub-west.nrp-nautilus.io](https://jupyterhub-west.nrp-nautilus.io) with CILogon institutional login. After signing in you pick a **profile** (CPU/GPU size and image) and land in JupyterLab. Home directories are persistent PVCs (5 GB default); idle servers are culled about an hour after your browser disconnects.

The tutorial hub you're on ([jh-training.nrp-nautilus.io](https://jh-training.nrp-nautilus.io)) is the same architecture, plus tutorial extras: `kubectl`/`helm` preinstalled, the LLM token injected, and every spawn steered to the reserved A10 pool.

## Hands-on: features you'd use in a course

**1. The spawner profile list.** Go to the hub control panel (**File → Hub Control Panel**), stop your server, and look at the spawn page: each entry is a `profileList` item mapping a display name to an image and resource set. You'll write one of these yourself in the next episode.

**2. Query the NRP LLM from Jupyter AI.** As in the morning: the chat panel and `%%ai` magics are wired to the managed LLM per spawn — a course-wide AI assistant with no per-student API keys. In a notebook:

```python
%load_ext jupyter_ai_magics
```

```text
%%ai openai-chat:minimax-m2
Give me three exam-style questions about Kubernetes pods.
```

**3. Distribute materials with nbgitpuller.** The "Launch the workspace" button on every page of this site is an [nbgitpuller](https://jupyterhub.github.io/nbgitpuller/) link: it signs the student in, clones/updates a git repo into their home directory **without ever overwriting their edits**, and opens a target path. Build your own links with the [nbgitpuller link generator](https://nbgitpuller.readthedocs.io/en/latest/link.html) — this is the standard way to hand out assignments.

**4. Real-time collaboration.** JupyterLab's collaborative mode (shared documents, live cursors) can be enabled per hub — useful for pair exercises and office hours.

## Sizing a hub for a course

Rules of thumb the NRP team uses when provisioning class hubs:

- **Concurrency, not enrollment** — a 100-student course rarely exceeds ~40 simultaneous servers outside deadline nights.
- **Right-size the default profile** — most coursework fits in 1–2 CPU / 4–8 GB; make GPU profiles a deliberate choice, not the default.
- **Idle culling is non-negotiable** — `cull.timeout` of 1 hour reclaims forgotten servers (that's why we set it on every hub).
- **Storage** — home PVC size × enrollment is your Ceph footprint; keep homes small and put datasets on a shared RWX volume.

Requesting a hub without running one yourself: NRP can host custom hubs for courses — [contact the team](https://nrp.ai/contact/). Or run your own, which is exactly what's next.
