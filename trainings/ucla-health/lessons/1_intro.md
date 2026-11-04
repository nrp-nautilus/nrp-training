---
title: What NRP Offers
teaching: 15
exercises: 0
questions:
  - What is the National Research Platform, and who can use it?
  - What hardware and services does it offer a research group?
  - How do researchers actually reach those resources?
objectives:
  - Describe what NRP provides and how the contributed-resource model works.
  - Name the three ways of reaching the cluster and pick the right one.
  - Know what NRP is not suited for, including protected health data.
keypoints:
  - NRP is shared national cyberinfrastructure built on the Nautilus Kubernetes cluster, free for U.S.-based researchers and educators.
  - JupyterHub is the lowest-barrier way in; `kubectl` and Coder are there when you outgrow it.
  - NRP is **not HIPAA compliant** — do not put protected health data on it.
---

**Time:** 00:00–00:15

Welcome, and thanks to UCLA Health IT's Research Tech Talks for hosting. This
session has one goal: introduce NRP as a computing resource you can use for
**AI-enabled research and education** — what it is, how to get in, and what you
can do once you are there — with a live demo along the way.

::: objectives
By the end you will know what NRP offers, how a research group gets access, how
to call a hosted LLM from a notebook, and where JupyterHub fits for a lab or a
class.
:::

## Schedule

| Time | Topic | What you walk away with |
|---|---|---|
| 00:00–00:15 | **What NRP offers** | The platform, the hardware, the ways in |
| 00:15–00:25 | **[Live demo: getting access](2_onboarding.html)** | Account, namespace, and admin roles |
| 00:25–00:40 | **[AI-enabled research](3_ai.html)** | An LLM call from a notebook, and an assistant that fixes code |
| 00:40–00:47 | **[JupyterHub for a lab or class](4_jupyterhub.html)** | What running your own hub involves |
| 00:47–01:00 | **Q&A** | Your questions |

Questions in the Zoom chat are welcome at any point.

## What NRP is

The National Research Platform is shared national cyberinfrastructure built on
the **Nautilus** Kubernetes cluster: hundreds of nodes, many NVIDIA GPU types,
shared storage, and hosted services — JupyterHub, GitLab, S3, a managed vector
database, and a managed LLM inference endpoint.

It runs on a **"potluck" model**: more than **70 institutions** contribute nodes,
and everyone benefits from the pooled capacity. **UCLA contributes nodes to the
cluster.** It is **free to use for U.S.-based researchers and educators**,
funded by the National Science Foundation and sustained by the community that
contributes to it.

![Anatomy of a Kubernetes cluster](images/kcluster2.png)

### Scale

- **~500 nodes**
- **~1400 GPUs**
- **~30 FPGAs**

<style>
.image-row {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: nowrap;
}

.image-row img {
  width: calc(50% - 8px);
  max-width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
}

@media (max-width: 768px) {
  .image-row { flex-wrap: wrap; }
  .image-row img { width: 100%; }
}
</style>

<div class="image-row">
  <img src="images/dash.png" alt="NRP dashboard">
</div>
<details>
  <summary>Click to reveal more</summary>

![NRP](images/dash-full.png)
</details>

### Capabilities

- **Storage:** CephFS, CVMFS, S3
- **Compute and data tools:** JupyterHub, GitLab, Nextcloud, Overleaf, WebODM
- **Monitoring:** a pre-configured Grafana/Prometheus stack, PerfSONAR
- **AI services:** hosted open-source LLMs, a managed Milvus vector database

::: important NRP is not HIPAA compliant
NRP is a good fit for research that does **not** involve protected health
information — public and de-identified datasets, simulation, model development,
code, teaching. It is **not** a place for PHI, and nothing here changes that. If
your data is covered by HIPAA, keep it in your institution's approved
environment, and treat anything you send to a hosted LLM as non-confidential.
:::

## The hardware you can ask for

NRP is deliberately heterogeneous. Ask for the class of device that matches the
work, not the biggest one available.

**CPUs.** The default. Most analysis — pandas, scikit-learn, bioinformatics
pipelines — never needs anything else, and CPU-only pods schedule fastest because
there is the most of that capacity.

**NVIDIA GPUs.** Many models across the cluster, from older training-friendly
cards to current datacenter parts. They are **not interchangeable**: ask for a
class that matches the job.

<div style="display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap;">
  <img src="images/GPU-pie.png" alt="GPU distribution" style="width:45%; min-width:280px; max-width:520px;">
  <img src="images/GPUModels.png" alt="GPU model list" style="width:45%; min-width:280px; max-width:520px;">
</div>

### Seeing what is actually available

Before requesting anything, look at what the cluster has right now — GPU models
and counts, regions, node labels, and current utilization.

![NRP resource view](images/resourcePage.png)

- [NRP live resource view](https://nrp.ai/viz/resources/)
- [NRP namespaces view](https://nrp.ai/viz/namespaces/)

## Ways to reach the cluster

![Top Uses](images/TopUse.png)

Almost everyone reaches the cluster one of three ways. They differ in how much
Kubernetes you have to know:

| Route | What it is | Barrier | Best for |
|---|---|---|---|
| **JupyterHub** | A browser-based JupyterLab server, sized from a spawn menu | Lowest — a login and a dropdown | Newcomers, exploration, notebooks, teaching. **Roughly 90% of users start here.** |
| **Kubernetes** (`kubectl`) | Submit pods, jobs, and services directly with YAML | Highest — you write manifests | Batch work, training runs, services, deploying a hub |
| **Coder** | A browser-based VS Code connected to cluster resources | Low | Development that outgrows a notebook |

**If you are new, start with JupyterHub.** Today's demos run entirely in the
browser.

There is also a second sense of the word "request", and mixing them up is a
common source of confusion:

1. **A portal or allocation request** — asking NRP for access, namespace
   membership, quotas, or a policy exception.
2. **A Kubernetes workload request** — asking the scheduler for CPU, memory,
   and accelerator devices inside a YAML manifest.

Workload requests are declarative. Over-requesting does not make anything
faster; it just makes you wait longer for a slot.

::: callout Next
Next, a live demo of how a research group gets in: [Live demo: getting
access](2_onboarding.html).
:::
