---
title: "Presentation: NRP for Your Classroom"
teaching: 37
exercises: 0
questions:
  - What is the National Research Platform, and what can a course use on it?
  - How do instructors and students get access?
  - What does an instructor control when running a JupyterHub for a class?
objectives:
  - Get onto NRP with a campus login, and get a namespace for a course.
  - Know the NAIRR Classroom route and what the Prototype NRP Classroom offers.
  - Know what a course hub lets you decide: who logs in, the image menu, files, resources, idle servers, AI models.
keypoints:
  - NRP is one Kubernetes cluster on hardware from 70+ institutions, free for US nonprofit institutions, community colleges included.
  - Students and instructors log in with their campus account through CILogon. A course lives in a namespace.
  - NRP's own JupyterHub needs no setup; your own hub, in your namespace, is one values file and `helm install`.
  - As the instructor you choose who logs in, the image menu and its resources, home folders, shared data, and when idle servers stop.
---

**Time:** about 37 minutes, then the [live demo](2_custom_jupyterhub.html).

Click the slides, then use the arrow keys or Space to step through. **F** goes full screen. [Open the slides in their own tab](slides/nairr-classroom.html).

<div style="position:relative;width:100%;aspect-ratio:16/9;margin:0.5rem 0 0.75rem;">
  <iframe src="slides/nairr-classroom.html" title="Slides: Prototype National Research Platform Classroom" allowfullscreen
          style="position:absolute;inset:0;width:100%;height:100%;border:0;border-radius:6px;"></iframe>
</div>

Download: [PowerPoint](slides/nairr-classroom.pptx) · [PDF](slides/nairr-classroom.pdf)

The cluster numbers on the slides come from a read-only snapshot taken on 10 November 2026: 534 nodes, 1,460 GPUs in 33 models, about 35,000 CPUs (hardware threads), and 2,334 namespaces. On 12 November, 152 JupyterHubs were running on the cluster.

## Get access

| Step | Where | Who |
|---|---|---|
| Log in | [nrp.ai](https://nrp.ai/): **Log In** → CILogon → your institution | Everyone, students included |
| Get a namespace for your course | [get-started.nrp-nautilus.io](https://get-started.nrp-nautilus.io/), or email the NRP team with the course, the number of students and the start date | Faculty, staff, postdocs and research scientists |
| Ask for priority (optional) | A **NAIRR Classroom** request at [nairrpilot.org](https://nairrpilot.org/), choosing **Prototype National Research Platform (PNRP) Classroom** | US educators teaching AI in any discipline |
| Get help | [Office hours and chat](https://nrp.ai/contact/), every two weeks | Everyone |

## What an instructor's hub lets you decide

| You want | What you set |
|---|---|
| Only your students get in | CILogon login, with your class list or your campus domain; you and your TAs as admins |
| The same environment for everyone | The image menu: ready-made Jupyter images, or one course image built in NRP's GitLab |
| GPUs for a deep-learning unit | GPUs only on the menu options that need them, with CPUs and memory per option |
| Students' work kept between sessions | A home folder per student; you choose the size |
| Course material without copy-and-paste | nbgitpuller links that pull your course repository into each student's folder |
| One copy of a big dataset | A shared volume in every server, read-only for students |
| GPUs back in the pool when students leave | Idle servers stop after an hour, or what you set |
| An AI assistant students can use | NRP's hosted models through an OpenAI-compatible API, with a token from [nrp.ai/llmtoken](https://nrp.ai/llmtoken) |

## Where each topic is documented

| Topic | Docs |
|---|---|
| Teaching with NRP | [nrp.ai/education](https://nrp.ai/education/) |
| NRP's hosted JupyterHub | [JupyterHub service](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub-service/) |
| Your own JupyterHub | [Deploy JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/) |
| Building images in GitLab | [Building in GitLab](https://nrp.ai/documentation/userdocs/development/gitlab/) |
| GPUs | [GPU pods](https://nrp.ai/documentation/userdocs/running/gpu-pods/) · [live resource view](https://nrp.ai/viz/resources/) |
| Hosted AI models | [LLM service](https://nrp.ai/documentation/userdocs/ai/llm-managed/) |
| Cluster policies | [Policies](https://nrp.ai/documentation/userdocs/start/policies/) |
