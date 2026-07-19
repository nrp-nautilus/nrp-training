# PEARC26 tutorial workspace

Hands-on files for **Kubernetes for AI-Enabled Scientific Research Computing, and
Education** (PEARC26). This folder is pulled into your JupyterHub home directory by
the launch buttons at [training.nrp-nautilus.io](https://training.nrp-nautilus.io/).

- `notebooks/` — **one runnable notebook per episode** (Bash kernel). Open the
  episode's notebook, run the ⚙️ setup cell (sets `$NRP_USER` and renders
  personalized manifests into `my-yamls/`), then Shift+Enter through the day.
  Cells share one persistent shell, so exports and `cd` carry between cells.
  Steps marked **🖥️ Terminal step** are interactive — run those in a JupyterLab
  terminal (**File → New → Terminal**) instead.
- `yamls/` — every Kubernetes manifest used in the episodes (pods, PVCs,
  deployments, jobs, ingress, GPU pods, TGI, Milvus RAG, JupyterHub helm values),
  plus `nrp_docs_rag.py` for the RAG exercise. Templates with `<username>`
  placeholders — the notebooks' setup cell renders filled-in copies to `my-yamls/`.
- `check.sh` — **check your work**: `bash check.sh <episode 1-6>` verifies your
  resources on the live cluster (✅/⚪/❌ with a hint for anything broken).
  Uses `$NRP_USER` (and `$NRP_NAMESPACE` for episode 6).

New to JupyterLab? **Help → PEARC26 Tutorial Tour** in the hub gives a one-minute
guided walkthrough, and each notebook carries its own mini-tour — click the
**📌 pin icon** in the notebook toolbar. Executed cells also show a run-time
stamp, so you can tell a slow step from a stuck one.

Conventions: namespace `nrp-training-k8s`; replace `<username>` in every manifest
with your own short name (the notebooks do this for you). Reserved GPU pool:
label `nrp-training=true`, taint `nautilus.io/reservation=nrp:NoSchedule`.
