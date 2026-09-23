# Workspace — NRP: Cyberinfrastructure for Research and Education (HI-DSI)

Files attendees open or run during the workshop.

| Path | What it is |
|---|---|
| `notebooks/2_ai_classroom.ipynb` | Runnable notebook for [AI for the Classroom](https://training.nrp-nautilus.io/hidsi/2_ai_classroom.html) — the managed LLM endpoint from Python, and Jupyter AI |
| `notebooks/3_custom_jupyterhub.ipynb` | Runnable notebook for [Deploy a Custom JupyterHub](https://training.nrp-nautilus.io/hidsi/3_custom_jupyterhub.html) — Helm, ingress, profiles, GitLab CI images |
| `check.sh` | Verifies your work against the live cluster: `bash check.sh <1-3>` |
| `yamls/jhub-values.yaml` | The Helm values file the JupyterHub deploy uses |
| `yamls/cilogon-jupyterhub-config.yaml` | Production CILogon/OIDC authentication block |
| `yamls/qaic-vllm-server.yaml` | vLLM on a Qualcomm Cloud AI 100 card — same OpenAI API, different silicon |

Both notebooks use the **Bash** kernel: every cell is a shell command, and cells
share one persistent shell, so `export` and `cd` carry from cell to cell.

## The `my-yamls/` convention

The setup cell in notebook 3 renders every file in `yamls/` into `my-yamls/`
with `<username>` replaced by your short name, so no manifest needs hand-editing
during the session. `my-yamls/` is generated — re-running the setup cell
overwrites it.

## Checking your work

```bash
bash check.sh 1   # access: kubectl, cluster auth, helm
bash check.sh 2   # AI: token, endpoint, a real chat/completions call, openai SDK
bash check.sh 3   # JupyterHub: helm release, hub/proxy pods, PVC, ingress
```

Section 3 needs `$NRP_NAMESPACE`, which the notebook's setup cell exports.
Resources you already cleaned up show as "not found" — that is expected.
