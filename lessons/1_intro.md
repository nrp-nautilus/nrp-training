---
title: Welcome, Kubernetes & NRP Architecture
teaching: 40
exercises: 0
---

::: callout Launch the workspace in JupyterHub
**[▶ Launch the workspace in JupyterHub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fpearc26&targetpath=pearc26&urlpath=lab%2Ftree%2Fpearc26%2Fworkspace)** — signs you in at jh-training.nrp-nautilus.io, pulls the tutorial workspace, and opens JupyterLab on the training GPU nodes.
:::

**Morning session · 9:00 – 9:40 AM**

Welcome to **Kubernetes for AI-Enabled Scientific Research Computing, and Education** at PEARC26. This full-day tutorial takes you from the concept of batch-oriented HPC to the practical use of service-oriented, Kubernetes-managed resources on the **National Research Platform (NRP)** — interactive AI notebooks, LLM services, GPU workloads, and course-scale JupyterHub deployments.

Run all commands from a JupyterHub terminal unless noted otherwise. Command blocks are formatted for copy/paste into that terminal.

## Schedule — full day at a glance

| Time | Session |
| --- | --- |
| 9:00 – 9:10 | Introduction and welcome |
| 9:10 – 9:40 | Kubernetes introduction & architecture (this episode) |
| 9:40 – 10:50 | Basic Docker and Kubernetes hands-on |
| 10:50 – 11:05 | *Break* |
| 11:05 – 11:55 | AI & computational science applications |
| 11:55 – 12:00 | Q&A / discussion |
| 12:00 – 12:15 | *Break* |
| 12:15 – 12:45 | Persistent storage & I/O for AI/scientific workloads |
| 12:45 – 1:25 | JupyterHub on NRP |
| 1:25 – 1:40 | *Break* |
| 1:40 – 2:50 | Advanced topics: custom JupyterHub & building images in NRP GitLab |
| 2:50 – 3:15 | Wrap-up and Q&A |

## The National Research Platform

The National Research Platform (NRP) is a partnership of 50+ institutions providing an open, nationally distributed cyberinfrastructure built on a Kubernetes cluster named **Nautilus** — 500+ nodes, 1500+ GPUs (NVIDIA A10/A100/H100, Qualcomm Cloud AI 100 Ultra), 50+ FPGAs, in continuous operation for over six years. Researchers and educators access it via Kubernetes namespaces, with persistent storage on Ceph and shared services for JupyterHub, GitLab, Coder, and S3.

The core mental model:

1. **CILogon** authenticates users through institutional identity providers.
2. **JupyterHub** gives each participant a browser-based JupyterLab workspace and terminal.
3. **Kubernetes namespaces** isolate class or project workloads.
4. **YAML manifests** describe the compute resources a workload needs.
5. **Device plugins** expose accelerators such as NVIDIA GPUs (`nvidia.com/gpu`) and Qualcomm Cloud AI 100 SoCs (`qualcomm.com/qaic`) to Kubernetes.

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
  <img src="images/kcluster.png" alt="Nautilus Kubernetes cluster map">
</div>

### Capabilities and scale

- **Storage:** CephFS, RBD block storage, CVMFS, S3
- **Monitoring:** Prometheus, Grafana, PerfSONAR
- **Compute and data tools:** JupyterHub, GitLab, Coder, WebODM, Nextcloud, Overleaf
- **AI services:** managed LLM inference (OpenAI-compatible), Milvus vector database
- **Scale:** 500+ nodes · 1500+ GPUs · 50+ FPGAs

Useful links for the live session:

- [Launch the workspace](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fpearc26&targetpath=pearc26&urlpath=lab%2Ftree%2Fpearc26%2Fworkspace)
- [NRP live resource view](https://nrp.ai/viz/resources/)
- [NRP namespaces view](https://nrp.ai/viz/namespaces/)
- [NRP documentation](https://nrp.ai/documentation/)
- [NRP support and Matrix chat](https://nrp.ai/contact/)

## How users interact with NRP

![Top uses of NRP](images/TopUse.png)

The majority of NRP users interact with the cluster in three ways:

- **Kubernetes** — directly submit and manage containerized workloads (services and batch jobs) using `kubectl` and the Kubernetes APIs.
- **JupyterHub** — start a JupyterLab notebook server on the cluster for interactive analysis, prototyping, and teaching workflows.
- **Coder** — launch a browser-based VS Code environment connected to cluster resources.

Today you will use **JupyterHub as the front door** and drive **Kubernetes from its terminal**.

## Kubernetes basics (quick intro)

Kubernetes is a system for running applications on a cluster by managing **workloads** (things you want to run) and keeping them in the desired state.

Most interactions with Kubernetes involve creating and updating **resources** (objects) described in **YAML**.

- A YAML "manifest" declares the *desired state* (what you want running).
- Kubernetes works continuously to make the cluster match that desired state.

Typical workflow:

1. Write or edit a YAML manifest.
2. Apply it to the cluster (`kubectl apply -f ...`).
3. Check status and troubleshoot (pods, logs, events).

### Kubernetes workloads

- **Pod**: the basic unit where your application runs (one or more containers together).
- **Job**: runs work to completion (batch or one-off tasks).
- **Deployment**: manages long-running services and keeps them available (including rolling updates).

Rule of thumb:

- Use a **Job** when the work should finish.
- Use a **Deployment** when the work should keep running.

### Hardware acceleration

Kubernetes requires specialized extensions to manage and assign non-CPU hardware.

- **GPUs in Kubernetes**: workloads explicitly request NVIDIA GPUs (e.g. `nvidia.com/gpu`) via resource limits in their manifests.
- **Device plugins**: software components that advertise specialized hardware to the Kubernetes scheduler. Qualcomm Cloud AI devices are exposed natively as `qualcomm.com/qaic`.

### Keep in mind

- Pods are **ephemeral**. Once a pod is terminated all data is deleted.
- **PersistentVolumeClaims** (PVCs) are used to claim long-term storage.
- Users don't log into cluster nodes. Workloads are defined in YAML and submitted with `kubectl` from any machine that has it — your laptop or a JupyterHub terminal.

## Docker and containers

Docker is a tool for building and running **containers**. A container image packages your application code, its libraries and dependencies, and enough operating-system files to run consistently — the same image runs on your laptop, a VM, or a Kubernetes cluster.

**Why Docker matters for Kubernetes:** Kubernetes runs container images; it does not build them. You build an image (with Docker or CI/CD), a registry stores it, and Kubernetes pulls and runs it.

**Container registries** store and distribute images. Docker Hub is the public example; NRP GitLab provides a registry for your own images (public or private), and you can build images directly in GitLab CI/CD — the afternoon session does exactly that.

## Getting a terminal with kubectl

::: callout Zero install — use the training JupyterHub
The tutorial hub at [jh-training.nrp-nautilus.io](https://jh-training.nrp-nautilus.io) is pre-configured: every spawned JupyterLab pod has `kubectl` and `helm` installed with a kubeconfig wired to the tutorial namespace. Open **File → New → Terminal** in JupyterLab and start running `kubectl` immediately.
:::

Verify your access:

```bash
kubectl auth whoami
kubectl get pods -n nrp-training-k8s
```

<details>
<summary>Expected output</summary>

```text
Username:   system:serviceaccount:nrp-training:jupyterhub-sa
```

The pod listing may be empty or show other participants' pods — both are fine.
</details>

## Gatekeeper: why every example sets requests and limits

Nautilus runs a cluster-wide Gatekeeper policy that **rejects pods that omit CPU or memory requests/limits, and rejects pods where the limit/request ratio exceeds 1.2×**. Every YAML in this tutorial sets `requests == limits` so you never trip it. If you copy-paste a manifest from upstream Kubernetes docs and it gets rejected, this is almost always why.

## Being a good citizen

NRP is a **shared resource**. Aim for pod utilization of GPU > 40%, CPU 20–200%, RAM 20–150% of the requested amount, and delete what you're not using. Live dashboards are on [Grafana](https://grafana.nrp-nautilus.io/dashboards); the acceptable-use policy is at [nrp.ai/documentation/userdocs/start/policies](https://nrp.ai/documentation/userdocs/start/policies/).

Next up: hands-on Kubernetes — pods, storage, deployments, jobs, services, and your first GPU pod.
