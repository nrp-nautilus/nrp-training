---
title: Introduction, Access & Resource Requests
teaching: 15
exercises: 0
questions:
  - What is the National Research Platform, and what does it offer a classroom?
  - How do students and instructors get access?
  - How do I request the resources a course needs?
objectives:
  - Describe what NRP provides and where JupyterHub fits.
  - Sign in through CILogon and reach a working terminal.
  - Know how to request a namespace and an allocation for a course.
keypoints:
  - NRP is shared national cyberinfrastructure built on the Nautilus Kubernetes cluster.
  - CILogon means students sign in with existing campus credentials — no new passwords.
  - Compute lives in a **namespace** tied to a project or course.
  - A classroom hub is one Helm release plus one values file you keep in version control.
---

::: callout Launch the workspace in JupyterHub
**[▶ Launch the workspace in JupyterHub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fnairr-webinar&targetpath=nairr-webinar&urlpath=lab%2Ftree%2Fnairr-webinar%2Fworkspace)** — signs you in at jh-training.nrp-nautilus.io, pulls the materials, and opens JupyterLab in the workspace directory.
:::

**Time:** 00:00–00:15

Welcome to the NAIRR AI Education Webinar Series. This hour has one concrete
goal: show you what it takes to run **your own JupyterHub classroom** on the
National Research Platform — and then actually deploy one.

This first segment covers what NRP is, how you and your students get in, and
how to ask for the resources a course needs. The rest of the hour is the
hands-on part.

::: callout Following along
You can watch this one or run it yourself. To run it you need an NRP account
and a namespace — see [Getting your own access](#getting-your-own-access) at
the end of this page. If you're joining without access today, everything here
stays online and every command is reproducible later.
:::

## Questions & polls

Drop questions here at any point during the hour — we'll work through them as
we go and in the Q&A at the end.

<iframe src="https://app.sli.do/event/8FY6gX1uNxrVyYpeSyWPA3" height="100%" width="100%" frameBorder="0" style="min-height: 560px;" allow="clipboard-write" title="Slido"></iframe>

Not loading? Open it directly at
[app.sli.do/event/8FY6gX1uNxrVyYpeSyWPA3](https://app.sli.do/event/8FY6gX1uNxrVyYpeSyWPA3).

## What NRP provides

The National Research Platform is shared national cyberinfrastructure built on
the **Nautilus** Kubernetes cluster: hundreds of nodes, many NVIDIA GPU types,
Qualcomm Cloud AI 100 accelerators, shared storage, and hosted services —
JupyterHub, GitLab, S3, and a managed LLM inference endpoint.

The mental model is short:

1. **CILogon** authenticates users through their institutional identity provider.
2. **JupyterHub** gives each participant a browser-based JupyterLab workspace and terminal.
3. **Kubernetes** runs the workloads; users interact with it through `kubectl` and YAML.
4. **Helm** packages a whole application — like a JupyterHub — into one installable chart.

![The Nautilus cluster](images/kcluster.png)

### Scale

- **~500 nodes**
- **~1400 GPUs**
- **~30 FPGAs**

### Capabilities

- **Storage:** CephFS, CVMFS, S3
- **Compute and data tools:** JupyterHub, GitLab, Nextcloud, Overleaf, WebODM
- **Monitoring:** Prometheus, PerfSONAR
- **AI services:** managed LLM inference on NRP GPUs

## NRP as a NAIRR Classroom provider

For teaching, NRP acts as a **classroom provider**: you get a Jupyter platform
for your course plus access to NRP resources — CPU, GPUs, storage, and LLM
services — without running any infrastructure yourself.

![NAIRR Classroom](images/NAIRR_Classroom_1.png)

![NAIRR Classroom](images/NAIRR_Classroom_2.png)

What that means in practice for an instructor:

| You want | NRP gives you |
|---|---|
| Every student in the same environment | A container image you control, identical for the whole class |
| No laptop setup on day one | Browser-based JupyterLab, campus login |
| GPUs for a deep-learning unit | GPU profiles on the spawn menu, with per-profile limits |
| Shared datasets and notebooks | One RWX volume mounted into every student's server |
| No passwords to distribute | CILogon institutional login |

## Access with CILogon

NRP authenticates through **CILogon**, so users sign in with an existing
campus account — there is no separate NRP password to issue or reset. For a
course, this is the single biggest operational win: enrollment is an allowlist,
not a credential-distribution problem.

![JupyterHub sign-in](images/jhub-1.png)

Once you're in, JupyterLab gives you the file browser, notebooks, and a
terminal with `kubectl` and `helm` already configured.

![JupyterLab workspace](images/jhub-2.png)

If you're following along in the training hub, confirm your terminal is wired
up:

```bash
kubectl version --client
kubectl auth whoami
kubectl config current-context
```

## Namespaces: where a course lives

Compute on NRP lives in a **namespace** — a Kubernetes grouping that scopes
resources and membership. For teaching, the namespace *is* the course:

- **Admins** (you, the instructor) add and remove members and create resources.
- **Users** (your students) work inside it.
- Admins are also responsible for members following cluster policy.

A JupyterHub can be deployed **once per namespace**, so one namespace maps
naturally to one course hub.

## Seeing what's available

Before requesting anything, look at what the cluster actually has. The live
resource view shows GPU models and counts, regions, node labels, and current
utilization.

![NRP resource view](images/resourcePage.png)

- [NRP live resource view](https://nrp.ai/viz/resources/)
- [NRP namespaces view](https://nrp.ai/viz/namespaces/)

Two things worth knowing when you size a course:

- **GPU types are not interchangeable.** Ask for a class of GPU that matches
  the work; a teaching exercise rarely needs the largest card available.
- **Requests are declarative.** A pod asks for CPU, memory, and optionally
  `nvidia.com/gpu`, and the scheduler places it. Over-requesting doesn't make
  anything faster — it just makes your students wait for a slot.

## Getting your own access

Three steps, and none of them need to happen live:

**1. Register your identity.** Go to
**[portal.nrp.ai](https://portal.nrp.ai)** and sign in with CILogon (pick your
institution), then complete
[Getting started](https://nrp.ai/documentation/userdocs/start/getting-started/).

**2. Get into a namespace.**

- **Joining an existing project?** Ask its admin to add you — send them the
  identity shown in the portal.
- **Starting a course?** Request a namespace and allocation through
  **[nrp.ai/contact](https://nrp.ai/contact/)**, which is also the Matrix
  channel used for live help. Say what you're teaching and roughly what you
  need — number of students, whether the course needs GPUs, and when the term
  starts.

**3. Point `kubectl` at NRP.** Grab your kubeconfig from the portal
([get-config](https://nrp.ai/documentation/userdocs/start/get-config/)), drop
it at `~/.kube/config`, and verify:

```bash
kubectl config get-contexts
kubectl get pods -n <your-namespace>
```

::: callout Next
With access and a namespace, everything in the next section works against your
own course. [Deploy a Custom JupyterHub &
Build Images in NRP GitLab](2_custom_jupyterhub.html) is the deployment itself.
:::
