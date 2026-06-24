# RCSI Tutorial — Hands-on AI on the National Research Platform

A hands-on tour of running AI on [NRP](https://nrp.ai): calling the managed
LLM and building a RAG pipeline over the NRP documentation with NRP's managed
embedding model, reusing the RAG pattern to query the JupyterHub docs, and agentic workflows with NRP. 

## Quick Start

Open the workspace in the pre-authenticated JupyterLab environment on NRP:

**[Launch RCSI Tutorial Workspace](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Frcsi&targetpath=rcsi&urlpath=lab%2Ftree%2Frcsi%2Fworkspace)**


## 📋 Pre-training survey — please take 2 minutes before we start

<a href="images/pre-training-survey-qr.png"><img src="../images/pre-training-survey-qr.png" alt="Pre-training survey QR code" width="180" align="right"></a>

Scan the QR on the right (or open [`https://ucsantacruz.co1.qualtrics.com/jfe/form/SV_3wQP0UrsPXy3nMO?Q_CHL=qr`](https://ucsantacruz.co1.qualtrics.com/jfe/form/SV_3wQP0UrsPXy3nMO?Q_CHL=qr)) to take the **pre-training survey** — a quick set of questions about your prior Kubernetes / NRP / AI experience. Comparing pre- and post-training responses is how we decide what to keep, cut, or rework for future cohorts.

<br clear="right">

## Helpful links

**NRP — start here**
- [NRP home](https://nrp.ai) · [Documentation](https://nrp.ai/documentation)
- [Getting started](https://nrp.ai/documentation/userdocs/start/getting-started/) · [New-user introduction](https://nrp.ai/documentation/userdocs/tutorial/introduction) · [Using Nautilus](https://nrp.ai/documentation/userdocs/start/using-nautilus/)
- [Cluster policies](https://nrp.ai/documentation/userdocs/start/policies/) · [FAQ](https://nrp.ai/documentation/userdocs/start/faq/)

**AI & managed LLMs** (what this tutorial uses)
- [Managed LLM overview](https://nrp.ai/documentation/userdocs/ai/llm-managed/) · [Available models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/)
- [API access](https://nrp.ai/documentation/userdocs/ai/llm-managed/api-access/) · [Client configs](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/) · [LLMs in JupyterHub](https://nrp.ai/documentation/userdocs/ai/llm-jupyterhub/)
- [Browser chat UI (Open WebUI)](https://nrp-openwebui.nrp-nautilus.io) · [Get an LLM token](https://nrp.ai/llmtoken) · API endpoint: `https://ellm.nrp-nautilus.io/v1`

**Storage**
- [Storage overview](https://nrp.ai/documentation/userdocs/storage/intro/) · [S3 (Ceph)](https://nrp.ai/documentation/userdocs/storage/ceph-s3/) · [Moving data](https://nrp.ai/documentation/userdocs/storage/move-data/)

**Dashboards & status**
- [Nautilus portal / dashboard](https://dash.nrp-nautilus.io) · [Cluster resources](https://nrp.ai/viz/resources) · [Usage & accounting (Grafana)](https://grafana.nrp-nautilus.io)

**Support & community**
- [Support](https://nrp.ai/documentation/userdocs/start/support/) · [Contact](https://nrp.ai/contact) · [Matrix / Element chat](https://element.nrp-nautilus.io/)

**JupyterHub on NRP** (Part 3)
- [Deploy JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/) · [JupyterHub service](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub-service/) · [Persistent storage](https://nrp.ai/documentation/userdocs/storage/ceph/)
- [Zero-to-JupyterHub docs](https://z2jh.jupyter.org/en/stable/) · [Helm](https://helm.sh/) · [7NRP custom-hub guide](https://github.com/nrp-nautilus/7nrp/tree/main/3_custom_jupyterhubs_classroom_research)
