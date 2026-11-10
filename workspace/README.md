# Workspace — The National Research Platform (UCLA Health)

Files for the live demo.

| Path | What it is |
|---|---|
| `notebooks/1_ai.ipynb` | Part 1: call NRP's hosted LLMs from Python, then Jupyter AI: `/fix`, `%%ai` with a summary of a public dataset, `%ai error` |
| `notebooks/2_gpu.ipynb` | Part 2: the GPUs on the cluster, a GPU in your session, then the same work as a batch job |
| `yamls/gpu-job.yaml` | The GPU Job: one GPU with more than 20 GB, Ampere or newer; trains a small CNN on MNIST |
| `check.sh` | Checks your setup: `bash check.sh <1-2>` |

The notebooks use the **Python** kernel on the training JupyterHub, where
`OPENAI_API_BASE` and `OPENAI_API_KEY` are exported and `kubectl` points at the
`nrp-training-k8s` namespace. **Do not put protected health information in any
prompt**: NRP is not HIPAA compliant.

## Checking your setup

```bash
bash check.sh 1   # AI: token, endpoint, a real chat/completions call, openai SDK
bash check.sh 2   # GPUs: kubectl, permission to create jobs, a GPU in this session
```
