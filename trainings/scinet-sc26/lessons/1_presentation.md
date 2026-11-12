---
title: "Presentation: Inside the National Research Platform"
teaching: 39
exercises: 0
questions:
  - How is a Kubernetes cluster spread over a hundred sites built, on the network and in software?
  - How does a small team run it: GitOps, CI, inventory, monitoring, security?
  - How does NRP serve open-weight LLMs on GPUs that campuses contributed?
  - How can I use it?
objectives:
  - Know NRP's network model (Science DMZ, jumbo frames, a Calico overlay, policy in the cluster) and how a node joins.
  - Know the operations stack (GitLab, Argo CD, CI in Kata VMs, NetBox fed by LLDP, Prometheus and Thanos, perfSONAR).
  - Follow one LLM request through Envoy AI Gateway, an InferencePool's endpoint picker and vLLM.
  - Know the ways in, and how to get an account and a namespace.
keypoints:
  - NRP is one Kubernetes cluster on hardware from 70+ institutions, in campus Science DMZs on research and education networks. Contributors keep priority on their nodes.
  - Git is the source of truth; Argo CD syncs and self-heals. CI jobs run in their own Kata VMs.
  - Every node reports to NetBox (with LLDP neighbors), Prometheus and a perfSONAR mesh.
  - One OpenAI-compatible endpoint serves open-weight models from GPUs at nine sites; task names like `coding` fall back across models.
  - Log in at nrp.ai, request a namespace, and use JupyterHub, Coder, kubectl, GitLab or the LLM API.
---

**Time:** about 39 minutes, then the [live demo](2_demo.html).

Click the slides, then use the arrow keys or Space to step through. **F** goes full screen. [Open the slides in their own tab](slides/scinet-nrp.html).

<div style="position:relative;width:100%;aspect-ratio:16/9;margin:0.5rem 0 0.75rem;">
  <iframe src="slides/scinet-nrp.html" title="Slides: Inside the National Research Platform" allowfullscreen
          style="position:absolute;inset:0;width:100%;height:100%;border:0;border-radius:6px;"></iframe>
</div>

Download: [PowerPoint](slides/scinet-nrp.pptx) · [PDF](slides/scinet-nrp.pdf)

The numbers on the slides come from a read-only snapshot of the cluster taken on 10 November 2026: 534 nodes, 1,460 GPUs in 33 models, about 35,000 CPUs (hardware threads), 14.9 PB of raw Ceph in 9 clusters, and 2,334 namespaces.

## Get access

| Step | Where | Who |
|---|---|---|
| Log in | [nrp.ai](https://nrp.ai/): **Log In** → CILogon → your institution | Everyone |
| Request a namespace | [get-started.nrp-nautilus.io](https://get-started.nrp-nautilus.io/) | Faculty, staff, postdocs and research scientists; students through their PI |
| kubectl and your kubeconfig | [Getting started](https://nrp.ai/documentation/userdocs/start/getting-started/) | Namespace members |
| Chat with the hosted LLMs | [nrp-openwebui.nrp-nautilus.io](https://nrp-openwebui.nrp-nautilus.io/) | Anyone with an NRP login |
| An LLM API token | [nrp.ai/llmtoken](https://nrp.ai/llmtoken) | Members of a group with LLM access |
| GitLab, CI and a registry | [gitlab.nrp-nautilus.io](https://gitlab.nrp-nautilus.io/) | Anyone with an NRP login |

## Where each part of the talk is documented

| Topic | Documentation |
|---|---|
| Network requirements, ports, Calico policy | [Networking](https://nrp.ai/documentation/admindocs/participating/network/) |
| Contributing a node | [Contributing a node](https://nrp.ai/documentation/admindocs/participating/new-contributor-guide/) |
| Exposing services: Ingress and Gateway API | [Exposing HTTP](https://nrp.ai/documentation/userdocs/running/ingress/) · [Gateway API](https://nrp.ai/documentation/userdocs/running/gateway/) · [Load-balancer VIPs](https://nrp.ai/documentation/userdocs/networks/loadbalancer-vips/) |
| Storage: Ceph, Linstor, CVMFS | [Storage options](https://nrp.ai/documentation/userdocs/storage/intro/) |
| Building in GitLab CI | [Building in GitLab](https://nrp.ai/documentation/userdocs/development/gitlab/) · [GitLab runners (admin)](https://nrp.ai/documentation/admindocs/cluster/gitlab/) |
| perfSONAR and the all-to-all mesh | [A2A MaDDash](https://nrp.ai/documentation/admindocs/perfsonar/a2a/) · [perfsonar.nrp-nautilus.io](https://perfsonar.nrp-nautilus.io/) |
| Security tools | [Security tools](https://nrp.ai/documentation/admindocs/cluster/security-tools/) |
| The LLM gateway and model servers | [Managing AI models (admin)](https://nrp.ai/documentation/admindocs/ai/managing_models/) · [API access](https://nrp.ai/documentation/userdocs/ai/llm-managed/api-access/) · [Models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/) |
| The ops bot | [github.com/djw8605/nrp-ops-bot](https://github.com/djw8605/nrp-ops-bot) |
| Policies | [Cluster policies](https://nrp.ai/documentation/userdocs/start/policies/) |

## Help

- Documentation: [nrp.ai/documentation](https://nrp.ai/documentation/), including the [admin guide](https://nrp.ai/documentation/admindocs/)
- Support chat and email: [nrp.ai/contact](https://nrp.ai/contact/)
- Daniel Diaz, [d4diaz@ucsd.edu](mailto:d4diaz@ucsd.edu)

::: callout Next
[Live demo: NRP from a terminal](2_demo.html)
:::
