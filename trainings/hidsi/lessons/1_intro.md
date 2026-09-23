---
title: NRP, Access & Requesting Resources
teaching: 20
exercises: 0
questions:
  - What is the National Research Platform, and what does it offer a classroom?
  - How do students and instructors get access?
  - What accelerators are available, and how do I ask for them?
objectives:
  - Describe what NRP provides and where JupyterHub fits for teaching.
  - Sign in through CILogon and reach a working terminal.
  - Name the three ways of requesting resources and pick the right one for a course.
keypoints:
  - NRP is shared national cyberinfrastructure built on the Nautilus Kubernetes cluster.
  - CILogon means students sign in with existing campus credentials — no new passwords.
  - Compute lives in a **namespace**, which for teaching maps onto a course.
  - JupyterHub is the lowest-barrier way in; `kubectl` and Coder are there when you outgrow it.
---

::: callout Launch the workspace in JupyterHub
**[▶ Launch the workspace in JupyterHub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fhidsi&targetpath=hidsi&urlpath=lab%2Ftree%2Fhidsi%2Fworkspace)** — signs you in at `jh-training.nrp-nautilus.io`, pulls these materials, and opens JupyterLab in the workspace directory. Do this now; the download takes a moment and you will need it in the next section.
:::

**Time:** 00:00–00:20

Welcome. This 90-minute workshop has one concrete goal: show you what it takes
to use the **National Research Platform** in a classroom — get in, use the AI
services, and stand up a hub of your own — and then actually do it.

The material is geared toward **educational use**, but nothing here is
teaching-only. The same token, the same endpoint, and the same Helm chart serve
a research group just as well as a course.

::: objectives
By the end of the workshop you will have talked to a national LLM service from
three different clients, pointed a coding agent at it, and deployed your own
multi-user JupyterHub on national infrastructure.
:::

## Schedule

| Time | Topic | What you walk away with |
|---|---|---|
| 00:00–00:20 | **NRP, access & requesting resources** | An account path, a namespace, and a working terminal |
| 00:20–00:50 | **[AI for the classroom](2_ai_classroom.html)** | Chatbots for students, LLM-as-a-service, and an agentic workflow |
| 00:50–01:30 | **[Your own JupyterHub](3_custom_jupyterhub.html)** | A deployed course hub and a custom image pipeline |

## What NRP is

The National Research Platform is shared national cyberinfrastructure built on
the **Nautilus** Kubernetes cluster: hundreds of nodes, many NVIDIA GPU types,
Qualcomm Cloud AI 100 accelerators, shared storage, and hosted services —
JupyterHub, GitLab, S3, a managed vector database, and a managed LLM inference
endpoint.

The mental model is short:

1. **CILogon** authenticates users through their institutional identity provider.
2. **JupyterHub** gives each participant a browser-based JupyterLab workspace and terminal.
3. **Kubernetes** runs the workloads; users interact with it through `kubectl` and YAML.
4. **Helm** packages a whole application — like a JupyterHub — into one installable chart.

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
- **Monitoring:** Prometheus, PerfSONAR
- **AI services:** managed LLM inference, a managed Milvus vector database

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
| An AI assistant students can actually use | A hosted chatbot and an OpenAI-compatible API, no per-seat billing |
| Shared datasets and notebooks | One RWX volume mounted into every student's server |
| No passwords to distribute | CILogon institutional login |

## The hardware you can ask for

NRP is deliberately heterogeneous. A course should ask for the class of device
that matches the work, not the biggest one available.

**CPUs.** The default. Most teaching workloads — pandas, scikit-learn, the
whole intro-to-data-science curriculum — never need anything else, and CPU-only
pods schedule fastest because there is the most of that capacity.

**NVIDIA GPUs.** Many models across the cluster, from older training-friendly
cards to current datacenter parts. They are **not interchangeable**: ask for a
class that matches the job.

<div style="display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap;">
  <img src="images/GPU-pie.png" alt="GPU distribution" style="width:45%; min-width:280px; max-width:520px;">
  <img src="images/GPUModels.png" alt="GPU model list" style="width:45%; min-width:280px; max-width:520px;">
</div>

**Qualcomm Cloud AI 100 / Cloud AI 100 Ultra.** Inference accelerators, requested
with the `qualcomm.com/qaic` resource key instead of `nvidia.com/gpu`. They are
built for serving models rather than training them, and an Ultra card carries
substantially more on-card memory than the original Cloud AI 100 — enough to
hold a large model resident for a class to query. The point worth teaching:
because a vLLM server on a Qualcomm card exposes the **same OpenAI-compatible
API** as one on an NVIDIA GPU, the accelerator underneath is an implementation
detail your students' code never sees. `workspace/yamls/qaic-vllm-server.yaml`
in this workspace is a complete working example.

::: callout Qualcomm capacity is limited
There are far fewer Qualcomm nodes than GPU nodes, and a full-size vLLM server
on one needs more CPU and memory than the default bare-pod limits allow — so it
needs an [NRP resource exception](https://nrp.ai/documentation/userdocs/start/policies/).
Treat it as something to plan for, not something to grab mid-class.
:::

### Seeing what is actually available

Before requesting anything, look at what the cluster has right now — GPU models
and counts, regions, node labels, and current utilization.

![NRP resource view](images/resourcePage.png)

- [NRP live resource view](https://nrp.ai/viz/resources/)
- [NRP namespaces view](https://nrp.ai/viz/namespaces/)

## Three ways to request resources

![Top Uses](images/TopUse.png)

Almost everyone reaches the cluster one of three ways. They differ in how much
Kubernetes you have to know, which is exactly the axis that matters for a
classroom.

| Route | What it is | Barrier | Best for |
|---|---|---|---|
| **JupyterHub** | A browser-based JupyterLab server, sized from a spawn menu | Lowest — a login and a dropdown | Students, coursework, anyone new to the cluster |
| **Kubernetes** (`kubectl`) | Submit pods, jobs, and services directly with YAML | Highest — you write manifests | Batch work, training runs, services, deploying a hub |
| **Coder** | A browser-based VS Code connected to cluster resources | Low | Development that outgrows a notebook |

Today we use two of them. We start in **JupyterHub**, because that is where a
class starts; and in the last section we drive **Kubernetes** from a hub
terminal to deploy a JupyterHub of our own.

There is also a second sense of the word "request", and mixing them up is a
common source of confusion:

1. **A portal or allocation request** — asking NRP for access, namespace
   membership, quotas, or a policy exception for a class.
2. **A Kubernetes workload request** — asking the scheduler for CPU, memory,
   and accelerator devices inside a YAML manifest.

Workload requests are declarative. Over-requesting does not make anything
faster; it just makes your students wait longer for a slot.

## Access with CILogon

NRP authenticates through **CILogon**, so users sign in with an existing campus
account — there is no separate NRP password to issue or reset. For a course
this is the single biggest operational win: **enrollment is an allowlist, not a
credential-distribution problem.**

If you are following along in the training hub, confirm your terminal is wired
up. Open a **Terminal** in JupyterLab and run:

```bash
kubectl version --client
kubectl auth whoami
kubectl config current-context
```

<details>
<summary>Expected output</summary>

```text
Client Version: v1.30.2
ATTRIBUTE   VALUE
Username    http://cilogon.org/serverA/users/000000
Groups      [system:authenticated]
nautilus
```
</details>

## Namespaces: where a course lives

Compute on NRP lives in a **namespace** — a Kubernetes grouping that scopes
resources and membership. For teaching, the namespace *is* the course:

- **Admins** (you, the instructor) add and remove members and create resources.
- **Users** (your students) work inside it.
- Admins are also responsible for members following cluster policy.

![Namespaces, roles, and resource scope](images/namespaces.png)

Most of what you create — pods, deployments, services, secrets, storage claims —
is **namespace-scoped**: it lives in your course's namespace and is invisible to
everyone else's. A smaller set of things is **cluster-scoped** and shared by the
whole platform: the nodes themselves, StorageClasses, PersistentVolumes. That
split is why a course namespace is a safe sandbox — students can fill it without
touching anyone else's work.

A JupyterHub can be deployed **once per namespace**, so one namespace maps
naturally onto one course hub.

## Getting your own access

Three steps, and none of them need to happen live today:

**1. Register your identity.** Go to
**[portal.nrp.ai](https://portal.nrp.ai)** and sign in with CILogon (pick your
institution), then complete
[Getting started](https://nrp.ai/documentation/userdocs/start/getting-started/).

**2. Get into a namespace.**

- **Joining an existing project?** Ask its admin to add you — send them the
  identity shown in the portal.
- **Starting a course?** Request a namespace and allocation through
  **[nrp.ai/contact](https://nrp.ai/contact/)**, which is also the Matrix
  channel used for live help. Say what you are teaching and roughly what you
  need — number of students, whether the course needs GPUs, and when the term
  starts.

**3. Point `kubectl` at NRP.** Install `kubectl` and the **kubelogin** plugin,
then grab your kubeconfig ([cluster access via
`kubectl`](https://nrp.ai/documentation/userdocs/start/getting-started/#cluster-access-via-kubectl)):

```bash
mkdir -p ~/.kube
curl -o ~/.kube/config -fSL https://nrp.ai/config
kubectl config get-contexts
kubectl get pods -n <your-namespace>
```

::: important Start the CILogon registration early
If you plan to run a **production** hub for a course, the OAuth client you
register with CILogon is the long pole — reviewed by hand, and it can take
several days to more than a week. Section 3 covers this in detail. Nothing on
the NRP side unblocks it, so start it well before the term.
:::

::: callout Next
With access and a namespace, everything in the rest of the workshop works
against your own course. Next: [AI for the
classroom](2_ai_classroom.html).
:::
