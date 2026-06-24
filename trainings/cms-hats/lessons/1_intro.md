---
title: Introduction
teaching: 10
exercises: 0
---

**Time:** 00:00-00:25

This section introduces NRP as a resource for US-CMS researchers. We will cover how to gain access and the basics of how to interact with the cluster. 

## What NRP is
NRP is a shared national cyberinfrastructure built on the Nautilus Kubernetes
cluster. It provides hundreds of GPU nodes, shared storage, and managed
services such as JupyterHub, S3, a vector database (Milvus), and an
OpenAI-compatible **managed LLM endpoint** — all free for U.S. academic
research, teaching, and outreach.

- **Scale**
   - **500+ nodes**
   - **1400+ GPUs**
   - **30+ FPGAs**

<details>
  <summary>Click to reveal more</summary>

![NRP](images/dash-full.png)
</details>


## A quick mental model:

1. **CILogon** signs you in through your institution's identity provider.
2. **JupyterHub** gives you a browser-based JupyterLab workspace and terminal.
3. **Kubernetes namespaces** isolate each class or project's workloads.
4. **Managed services** (LLM, Milvus, …) mean you call an API instead of running and paying for your own servers.


## Interacting with NRP
![Top Uses](images/TopUse.png)

The majority of NRP users interact with the cluster using the following three methods.
- via **Kubernetes**: Directly submit and manage containerized workloads (services and batch jobs) using Kubernetes APIs and tools like `kubectl`.
- via the **Coder** service: Launch a browser-based VS Code environment connected to cluster resources for interactive development and execution.
- via NRP deployed **Jupyterhub**: Start a JupyterLab notebook server on the cluster for interactive analysis, prototyping, and teaching workflows.

Today, we will be using two of these services. We will launch a jupyterhub server. From the jupyterhub server, we will interact with kubernetes directly using the hub's terminal.

## Demo slides

::: slides CMS HATS slide demo
@include slides/cms-nrp-hats.pdf
:::

