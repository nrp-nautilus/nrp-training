# PEARC26 tutorial workspace

Hands-on files for **Kubernetes for AI-Enabled Scientific Research Computing, and
Education** (PEARC26). This folder is pulled into your JupyterHub home directory by
the "Launch the workspace" buttons at
[training.nrp-nautilus.io](https://training.nrp-nautilus.io/).

- `yamls/` — every Kubernetes manifest used in the episodes (pods, PVCs,
  deployments, jobs, ingress, GPU pods, TGI, Milvus RAG, JupyterHub helm values),
  plus `nrp_docs_rag.py` for the RAG exercise.

Conventions: namespace `nrp-training-k8s`; replace `<username>` in every manifest
with your own short name. Reserved GPU pool: label `nrp-training=true`, taint
`nautilus.io/reservation=nrp:NoSchedule`.
