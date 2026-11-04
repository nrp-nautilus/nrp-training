---
title: JupyterHub for a Lab or Class
teaching: 7
exercises: 0
questions:
  - Can I run a JupyterHub for my own lab or course on NRP?
  - What does that involve?
objectives:
  - Describe what a hub of your own gives you.
  - Know where the full walkthrough lives.
keypoints:
  - A hub of your own is one Helm chart and one values file, deployed into a namespace you administer.
  - It gives every member a browser-based workspace — a free alternative to Colab for people with limited hardware.
  - A production hub uses CILogon, which is registered with an outside service and takes days.
---

**Time:** 00:40–00:47

A brief look — not a deep dive — at what comes next once you are comfortable on
NRP: running a **JupyterHub of your own** for a lab, a course, or a workshop.

## Why have one

A hub in your own namespace gives every member a browser-based JupyterLab with
the environment you choose, no laptop setup, and — for a class or a group with
modest hardware — a **free alternative to Google Colab**, backed by NRP's CPUs
and GPUs. You control:

- **Who can sign in** — campus credentials through CILogon, narrowed to your roster.
- **The environment** — a container image, identical for everyone.
- **The sizes on offer** — a spawn menu of CPU and GPU profiles with limits.
- **Shared storage** — one volume of datasets and notebooks mounted for the whole group.

![JupyterHub profile menu](images/jhub-2.png)

## What it takes

A hub is **one Helm chart plus one values file**, deployed into a namespace you
are admin of — one hub per namespace. The values file is your whole deployment:
version-control it and you can rebuild the hub anywhere. Adding an image, a GPU
profile or a shared folder is a small change to that file and a `helm upgrade`.

::: important Plan the login early
A real hub signs people in with **CILogon**, which means registering your own
OAuth client with CILogon — an independent service, not run by NRP. They review
registrations by hand, so **budget a few days, sometimes more than a week**.
:::

## Go deeper

The full, step-by-step deployment — Helm, the values file, profiles, shared
storage, authentication — is the subject of NRP's classroom webinar, with a
runnable notebook:

- [Deploy a JupyterHub classroom — NAIRR webinar
  materials](https://training.nrp-nautilus.io/nairr-classroom/)
- [NRP docs: Deploy JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/)

::: callout Questions?
Open Q&A — your own project, GPU and allocation policy, getting a group
started. You can also reach NRP afterwards by email or on the NRP Slack
workspace.
:::
