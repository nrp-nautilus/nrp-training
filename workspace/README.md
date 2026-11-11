# Workspace: Inside the National Research Platform (SCinet)

Files for the live demo.

| Path | What it is |
|---|---|
| `notebooks/demo.ipynb` | The demo, on the **Bash** kernel: nodes and GPUs with `kubectl get nodes`, the LLM gateway with `curl` and `jq`, a GPU Job |
| `yamls/gpu-job.yaml` | The GPU Job: one GPU with more than 20 GB, Ampere or newer; trains a small CNN on MNIST |

On the training JupyterHub, `kubectl` already points at the `nrp-training-k8s` namespace and
`OPENAI_API_KEY` holds an LLM token, so the commands need no `-n` and no setup. Elsewhere, use your
own kubeconfig and namespace (add `-n <namespace>`, and change `namespace:` in the job), and put a
token from [nrp.ai/llmtoken](https://nrp.ai/llmtoken) in `OPENAI_API_KEY`.
