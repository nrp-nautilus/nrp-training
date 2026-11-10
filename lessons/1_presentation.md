---
title: "Presentation: GPUs and AI on NRP"
teaching: 30
exercises: 0
questions:
  - What can a UCLA researcher, student or instructor do with NRP?
  - How do I get access, and what is a namespace?
  - Which GPUs are there, and how do I run a job on one?
  - What AI services does NRP host?
objectives:
  - Know what NRP offers for GPU computing and AI, and what it is not for.
  - Get an account, and know who requests a namespace.
  - Pick a GPU by the memory a job needs, and know the two ways to use one.
  - Name the ways to reach NRP's hosted language models.
keypoints:
  - NRP is a national Kubernetes cluster, free for non-commercial research and education. It is **not HIPAA compliant**.
  - Log in at nrp.ai with your UCLA account. PIs, faculty, staff and postdocs request a namespace; students are added by their PI.
  - Ask for the GPU memory a job needs, not a brand name. Explore on a GPU in JupyterHub; run real work as a Job, which releases the GPU when it exits.
  - Open-weight LLMs sit behind one OpenAI-compatible endpoint, usable from a browser, Python, Jupyter AI or a coding agent.
---

**Time:** 00:00–00:30, then the [live demo](2_demo.html).

::: slides GPUs and AI on the National Research Platform
@include slides/ucla-health-nrp.pdf
:::

Download: [PowerPoint, with speaker notes](slides/ucla-health-nrp.pptx) · [PDF](slides/ucla-health-nrp.pdf)

### Animated version

The same slides with step-by-step animations. Click the slides, then use the arrow keys; **N** shows the speaker notes and **F** goes full screen.
[Open it in its own tab](slides/ucla-health-nrp.html).

<div style="position:relative;width:100%;aspect-ratio:16/9;margin:0.5rem 0 1.5rem;">
  <iframe src="slides/ucla-health-nrp.html" title="Animated slides" allowfullscreen loading="lazy"
          style="position:absolute;inset:0;width:100%;height:100%;border:0;border-radius:6px;"></iframe>
</div>

## Get access

| Step | Where | Who |
|---|---|---|
| Log in | [nrp.ai](https://nrp.ai/): **Log In** → CILogon → **UCLA** | Everyone |
| Request a namespace | [get-started.nrp-nautilus.io](https://get-started.nrp-nautilus.io/) | Faculty, staff, postdocs and research scientists. **Students:** ask your PI or instructor to request one and add you. |
| Chat with the hosted LLMs | [nrp-openwebui.nrp-nautilus.io](https://nrp-openwebui.nrp-nautilus.io/) | Anyone with an NRP login |
| Get an LLM API token | [nrp.ai/llmtoken](https://nrp.ai/llmtoken) | Members of a group with LLM access |
| Run GPU jobs from your laptop | [Getting started: kubectl and kubeconfig](https://nrp.ai/documentation/userdocs/start/getting-started/) | Namespace members |

A **namespace** is your group's workspace on the cluster: a lab, a project or a course. Its admin, usually the PI or instructor, adds members. GPU jobs, data volumes and a JupyterHub all live in a namespace, and what you create there is visible only to its members. Namespaces can be nested under a campus-level group; UCLA does not have a campus-level admin yet, so if your department or group wants that role, [get in touch](mailto:d4diaz@ucsd.edu).

::: important NRP is not HIPAA compliant
NRP suits public, de-identified and synthetic data, simulation, model development and teaching. It is **not** a place for protected health information, and nothing you send to the hosted LLMs should identify a patient. Keep PHI in UCLA Health's approved environments.
:::

## GPUs at a glance

| GPU memory | Examples | Good for | How to ask |
|---|---|---|---|
| Up to 16 GB | RTX 2080 Ti, GTX 1080 Ti, A4000, A100 slices | Teaching, debugging, classic ML, small CNNs | `nvidia.com/gpu: 1` |
| 20–24 GB | A10, RTX 3090, L4, RTX 4090 | Most deep learning; models up to ~8B parameters | `nvidia.com/gpu: 1`, plus memory or model affinity |
| 32–48 GB | L40, V100 32 GB, RTX A6000, A40 | Bigger models and batches | `nvidia.com/gpu`, or `nvidia.com/rtxa6000` / `nvidia.com/a40` |
| 80 GB and up | A100 80 GB, H100, H200 | Large training runs and large models | A100: [access request](https://nrp.ai/reservations); H100/H200 are reserved |

- **What's free right now:** [nrp.ai/viz/resources](https://nrp.ai/viz/resources/)
- **Resource keys and access rules:** [GPU pods](https://nrp.ai/documentation/userdocs/running/gpu-pods/)
- Current PyTorch builds need a Turing-or-newer GPU. On a GTX 1080 Ti or V100, use an older image.

## AI services

- **Hosted LLMs:** open-weight models behind `https://ellm.nrp-nautilus.io/v1`, an OpenAI-compatible endpoint. The [models page](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/) says which model suits which task; the catalog rotates.
- **Four ways in:** [Open WebUI](https://nrp-openwebui.nrp-nautilus.io/) in the browser; Python or any OpenAI-compatible tool; Jupyter AI in JupyterHub; coding agents, with [tested configurations](https://nrp.ai/documentation/userdocs/ai/llm-managed/).
- **Run your own:** vLLM on a GPU in your namespace, training and fine-tuning in GPU jobs, and RAG with NRP's managed Milvus vector database. Worked examples: [PEARC26 tutorial](https://training.nrp-nautilus.io/pearc26/), and a physics neural network trained in GPU jobs in [CMS HATS](https://training.nrp-nautilus.io/cms-hats/).

## Labs and classes

A JupyterHub of your own gives every student the same environment in the browser, GPUs from a menu, the AI assistant preconfigured, and shared storage. **Instructors:** contact us and we'll help you set it up. **Students:** if your course needs GPUs, ask your professor to get in touch.

## Help

- Documentation: [nrp.ai/documentation](https://nrp.ai/documentation/)
- Support chat and email: [nrp.ai/contact](https://nrp.ai/contact/)
- Labs, courses, or a UCLA campus group: Daniel Diaz, [d4diaz@ucsd.edu](mailto:d4diaz@ucsd.edu)

::: callout Next
[Live demo: AI and GPUs](2_demo.html)
:::
