# Workspace — The National Research Platform (UCLA Health)

Files attendees can open during the talk.

| Path | What it is |
|---|---|
| `notebooks/3_ai.ipynb` | Runnable notebook for [AI-Enabled Research](https://training.nrp-nautilus.io/ucla-health/3_ai.html) — the managed LLM endpoint from Python, notebook magics, and Jupyter AI |
| `check.sh` | Verifies your setup: `bash check.sh <1-2>` |

The notebook uses the **Python** kernel on the training JupyterHub, where
`OPENAI_API_BASE` and `OPENAI_API_KEY` are already exported. **Do not put
protected health information in any prompt** — NRP is not HIPAA compliant.

## Checking your setup

```bash
bash check.sh 1   # access: kubectl, cluster auth, helm
bash check.sh 2   # AI: token, endpoint, a real chat/completions call, openai SDK
```
