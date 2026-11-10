---
title: "Live Demo: AI and GPUs"
teaching: 12
exercises: 0
questions:
  - How do I call NRP's hosted LLMs from a notebook, and let an assistant see my data?
  - How do I run a training job on a GPU, and watch it?
objectives:
  - Call a hosted model from Python, and use Jupyter AI to fix code and ask about a dataset.
  - Use a GPU in a JupyterHub session, then submit the same kind of work as a Kubernetes Job.
keypoints:
  - Only `base_url` changes between NRP, a model you serve yourself, and a commercial API.
  - "`%%ai` magics put live variables, such as a summary of your data, into the prompt. Check what comes back."
  - A GPU Job states what it needs (one GPU, enough memory, a recent generation), runs, and releases the GPU.
  - "`Pending` means waiting for a matching GPU; `kubectl describe pod` says why."
---

**Time:** 00:30–00:42 · Part 1 about 6 minutes, Part 2 about 6 minutes.

Both parts run on NRP's training JupyterHub, where the LLM token is already set and `kubectl` is connected to the `nrp-training-k8s` namespace. To follow along, open a notebook below; when the hub asks what server to start, **pick a GPU** if you want to try section 2 of Part 2.

::: callout Open the notebooks
**[▶ Part 1: AI on NRP](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fucla-health&targetpath=ucla-health&urlpath=lab%2Ftree%2Fucla-health%2Fworkspace%2Fnotebooks%2F1_ai.ipynb)** · **[▶ Part 2: GPUs on NRP](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fucla-health&targetpath=ucla-health&urlpath=lab%2Ftree%2Fucla-health%2Fworkspace%2Fnotebooks%2F2_gpu.ipynb)**

Each link signs you in at jh-training.nrp-nautilus.io, copies this training's files into your server, and opens the notebook.
:::

::: important Public and de-identified data only
NRP is not HIPAA compliant. Treat every prompt as non-confidential: no PHI, no identifiable patient data.
:::

## Part 1 — AI in a notebook

### 1. Call a model from Python

The hub exports `OPENAI_API_BASE` and `OPENAI_API_KEY`, so the standard `openai` package works as is. Elsewhere, get a token at [nrp.ai/llmtoken](https://nrp.ai/llmtoken).

```python
import os
from openai import OpenAI

client = OpenAI(base_url=os.environ["OPENAI_API_BASE"])

for m in client.models.list().data:      # what's on offer today
    print(m.id)

resp = client.chat.completions.create(
    model="gpt-oss",
    messages=[{"role": "user", "content": "In two sentences, what is the National Research Platform?"}],
)
print(resp.choices[0].message.content)
```

The same code works against a model you serve yourself or a commercial API: only `base_url` changes.

### 2. Jupyter AI: fix broken code

Open the **chat icon** in the left sidebar. The notebook has three cells broken on purpose:

| Cell | What happens | What it shows |
|---|---|---|
| `temperature conversion` | `NameError`: a misspelled function | `/fix` reads the traceback and points at the typo |
| `class average` | `TypeError`: looping over a dict gives keys | A real conceptual bug |
| `sensor average` | **No error**, and the answer is wrong | The assistant can't react to red text; you have to say what you meant |

`/fix` only works on a selected cell that crashed. The chat panel can't see your variables, which is what the magics are for.

### 3. `%%ai` with your data

Anything in `{curly braces}` in a `%%ai` prompt is replaced by the variable's live value. The notebook summarizes scikit-learn's bundled diabetes dataset (public, de-identified, 442 patients) and asks about it:

```python
%load_ext jupyter_ai_magics

from sklearn.datasets import load_diabetes
df = load_diabetes(as_frame=True, scaled=False).frame
summary = df.describe().round(1).to_string()
```

```text
%%ai openai-chat:gpt-oss
Here is a summary of a public, de-identified dataset (one row per patient; "target" is
disease progression one year later):

{summary}

Which three columns would you look at first to predict the target, and what would you
check before trusting this data? Keep it short.
```

Then **check the answer** with one line of pandas. When we tested this, the model suggested `s3` as strongly predictive; it is, but *negatively* (−0.39), which the answer didn't say.

```python
df.corr()["target"].drop("target").sort_values(key=abs, ascending=False).round(2)
```

The notebook also shows `%ai error`, which explains the most recent traceback, and the silent sensor bug with its live values.

## Part 2 — A GPU job

### 1. What GPUs are there?

The live view is [nrp.ai/viz/resources](https://nrp.ai/viz/resources/). From a terminal, the GPU model and memory are labels on each node:

```bash
kubectl get nodes -L nvidia.com/gpu.product,nvidia.com/gpu.memory
```

### 2. A GPU in your session

If you started your server with a GPU:

```bash
nvidia-smi
```

The notebook then times the same 4096 × 4096 matrix multiply on the CPU and on the GPU.

### 3. The same work as a batch job

[`workspace/yamls/gpu-job.yaml`](https://github.com/nrp-nautilus/nrp-training/blob/materials/ucla-health/workspace/yamls/gpu-job.yaml) asks for one GPU and trains a small convolutional network on MNIST (handwritten digits). The part that matters:

```yaml
spec:
  template:
    spec:
      restartPolicy: Never
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - {key: nvidia.com/gpu.memory, operator: Gt, values: ["20000"]}   # more than 20 GB
              - {key: nvidia.com/gpu.compute.major, operator: Gt, values: ["7"]} # Ampere or newer
      containers:
      - name: train
        image: pytorch/pytorch:2.9.0-cuda13.0-cudnn9-runtime
        resources:
          requests: {cpu: "2", memory: 6Gi, nvidia.com/gpu: 1}
          limits:   {cpu: "2", memory: 6Gi, nvidia.com/gpu: 1}
```

The second rule matters: current PyTorch builds no longer run on older cards such as the V100 or GTX 1080 Ti. We found that out by testing this job.

Submit, watch, read, clean up (from a JupyterHub terminal, replace `yourname`):

```bash
cd ~/ucla-health/workspace/yamls
sed "s/<username>/yourname/" gpu-job.yaml | kubectl apply -f -
kubectl get pods -n nrp-training-k8s -l job-name=gpu-train-yourname -w
kubectl logs -f job/gpu-train-yourname -n nrp-training-k8s
kubectl delete job gpu-train-yourname -n nrp-training-k8s
```

<details>
<summary>Expected output</summary>

```text
Running on: NVIDIA A10
Matrix multiply, 4096 x 4096:
  CPU (2 cores)  0.09 TFLOP/s
  GPU            14.0 TFLOP/s  (154x)
Training on 60,000 images, testing on 10,000
epoch 1: loss 0.090, accuracy 98.4%, 1.6 s
epoch 2: loss 0.009, accuracy 98.7%, 1.0 s
epoch 3: loss 0.033, accuracy 98.7%, 1.1 s
Done: the job exits and frees the GPU.
```
</details>

**Stuck in `Pending`?** The scheduler is waiting for a free GPU that matches. `kubectl describe pod -n nrp-training-k8s -l job-name=gpu-train-yourname` lists the reasons, such as `Insufficient nvidia.com/gpu`. The first run on a node also downloads the container image, which can take a few minutes.

## Run it in your own namespace

1. Get a namespace: PIs, faculty, staff and postdocs request one at [get-started.nrp-nautilus.io](https://get-started.nrp-nautilus.io/); students are added by their PI.
2. Install `kubectl` and your NRP kubeconfig: [Getting started](https://nrp.ai/documentation/userdocs/start/getting-started/).
3. In `gpu-job.yaml`, change `namespace:` and delete the workshop-only `preferredDuringScheduling…` block. Then `kubectl apply -f gpu-job.yaml`.

**Going further:** keep data on a persistent volume, run a sweep as many one-GPU jobs, and see the [CMS HATS training](https://training.nrp-nautilus.io/cms-hats/) for a physics neural network trained in GPU jobs with storage and experiment tracking. Serving your own model and RAG are in the [PEARC26 tutorial](https://training.nrp-nautilus.io/pearc26/).

::: callout Questions?
Open Q&A. You can also reach NRP afterwards at [nrp.ai/contact](https://nrp.ai/contact/), or Daniel Diaz at [d4diaz@ucsd.edu](mailto:d4diaz@ucsd.edu).
:::
