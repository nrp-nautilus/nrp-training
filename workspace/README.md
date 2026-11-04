# Workspace — NAIRR Prototype NRP Classroom

Files used during the one-hour webinar. See the lessons at
<https://training.nrp-nautilus.io/nairr-classroom/>.

| Path | What it is |
|---|---|
| `notebooks/2_custom_jupyterhub.ipynb` | Runnable notebook for [Deploy a JupyterHub Classroom](https://training.nrp-nautilus.io/nairr-classroom/2_custom_jupyterhub.html) — Helm, ingress, profiles, shared storage |
| `check.sh` | Verifies your work against the live cluster: `bash check.sh <1-2>` |
| `yamls/jhub-values.yaml` | The Helm values file the JupyterHub deploy uses |
| `yamls/cilogon-jupyterhub-config.yaml` | Production CILogon/OIDC authentication block |

The notebook uses the **Bash** kernel: every cell is a shell command, and cells
share one persistent shell, so `export` and `cd` carry from cell to cell.

## The `my-yamls/` convention

The setup cell renders every file in `yamls/` into `my-yamls/` with `<username>`
replaced by your short name, so no manifest needs hand-editing. `my-yamls/` is
generated — re-running the setup cell overwrites it.

## Checking your work

```bash
bash check.sh 1   # access: kubectl, cluster auth, helm
bash check.sh 2   # JupyterHub: helm release, hub/proxy pods, PVC, ingress
```

Section 2 needs `$NRP_NAMESPACE`, which the notebook's setup cell exports.
Resources you already cleaned up show as "not found" — that is expected.
