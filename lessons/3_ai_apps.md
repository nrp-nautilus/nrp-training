---
title: AI & Computational Science Applications
teaching: 15
exercises: 35
---

::: callout Launch the workspace in JupyterHub
**[▶ Open the runnable notebook for this episode](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fpearc26&targetpath=pearc26&urlpath=lab%2Ftree%2Fpearc26%2Fworkspace%2Fnotebooks%2F3_ai_apps.ipynb)** — every command below is a Shift+Enter cell; manifests are in the workspace's `yamls/` folder.
:::

**Morning session · 11:05 – 11:55 AM**

NRP runs hundreds of NVIDIA GPUs (and Qualcomm Cloud AI 100 cards) across the country. A subset of those GPUs power a community-shared, **OpenAI-compatible LLM inference endpoint** at `https://ellm.nrp-nautilus.io/v1`. This episode walks the full path: talk to the managed LLM from Jupyter AI, `curl`, and Python; then bring up your own GPU pod for training, self-hosted inference, and a RAG pipeline against NRP's managed [Milvus](https://milvus.io) vector database.

> 📘 **Docs:** [Managed LLMs](https://nrp.ai/documentation/userdocs/ai/llm-managed/) · [Available models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/) · [LLM API access](https://nrp.ai/documentation/userdocs/ai/llm-managed/api-access/) · [Vector DB (Milvus)](https://nrp.ai/documentation/userdocs/vector-database/) · [LLM token](https://nrp.ai/llmtoken) · [GPU pods](https://nrp.ai/documentation/userdocs/running/gpu-pods/)

## 1. NRP GPUs power a managed LLM service

NRP exposes GPUs in two complementary ways:

1. **Bring-your-own pod** — request `nvidia.com/gpu` (or model-specific keys) in your container's resources, as in Episode 2. Full control over weights, runtime, and versions.
2. **Managed LLM service** — a rotating catalog of open-weights LLMs hosted on those same GPUs behind the OpenAI-compatible URL `https://ellm.nrp-nautilus.io/v1`. No pod to run, no GPU time to hold; just HTTP requests with a bearer token from [nrp.ai/llmtoken](https://nrp.ai/llmtoken).

See the [models page](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/) for the live catalog — large mixture-of-experts chat models, code models, vision-language models, and an embeddings model, all behind one endpoint.

**Browser entry points** (no token needed; sign in with your NRP account):

- [nrp-openwebui.nrp-nautilus.io](https://nrp-openwebui.nrp-nautilus.io) — Open WebUI
- [librechat.nrp-nautilus.io](https://librechat.nrp-nautilus.io) — LibreChat

::: callout Tutorial token & endpoint
Inside the tutorial JupyterHub, `OPENAI_API_BASE` and `OPENAI_API_KEY` are **already exported** in every terminal and notebook, and injected into pods that mount the `nrp-llm-token` Secret in `nrp-training-k8s`. The examples below use those variables verbatim. After the tutorial, mint your own token at [nrp.ai/llmtoken](https://nrp.ai/llmtoken).
:::

## 2. Talk to the LLM from Jupyter AI

The tutorial hub ships with [Jupyter AI](https://jupyter-ai.readthedocs.io/) **pre-configured for the NRP managed LLM** — nothing to install.

**Try it now — chat panel.** Click the **chat (robot) icon** in the JupyterLab left sidebar, type a question, and send. Replies stream back from a model running on NRP GPUs.

**Or use the cell magic** in a Python 3 notebook:

```python
%load_ext jupyter_ai_magics
```

```text
%%ai openai-chat:minimax-m2
What is the National Research Platform in two sentences?
```

Switch model per cell — the first line of the magic is `%%ai <provider>:<model>`. `%ai list` shows every registered provider.

**What you learn.** Jupyter AI is the lowest-friction way to demo the managed LLM during a class — students log in, no token handoff, no `pip install`.

## 3. Talk to the LLM with `curl`

The endpoint is OpenAI-compatible — anything that speaks OpenAI's REST API speaks NRP. Open a JupyterLab terminal.

**List models:**

```bash
curl -s -H "Authorization: Bearer $OPENAI_API_KEY" \
     "$OPENAI_API_BASE/models" | python3 -m json.tool | head -30
```

**Send a chat completion:**

```bash
curl -s -X POST "$OPENAI_API_BASE/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimax-m2",
    "messages": [
      {"role": "system", "content": "Answer in one sentence."},
      {"role": "user",   "content": "What is the National Research Platform?"}
    ]
  }' | python3 -c 'import json,sys; print(json.load(sys.stdin)["choices"][0]["message"]["content"])'
```

**Stream tokens** (add `"stream": true` and watch SSE chunks arrive):

```bash
curl -sN -X POST "$OPENAI_API_BASE/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"minimax-m2","stream":true,"messages":[{"role":"user","content":"Count 1 to 5 with a brief reason for each."}]}'
```

**What you learn.** `curl` is the universal smoke test — if it works here, anything OpenAI-compatible (LangChain, openai-python, your own app) works.

## 4. Talk to the LLM with Python (`openai` SDK)

The client is pre-installed on hub spawns (`pip install openai` elsewhere):

```python
import os
from openai import OpenAI

client = OpenAI()   # reads OPENAI_API_KEY / OPENAI_API_BASE from the environment

resp = client.chat.completions.create(
    model="minimax-m2",
    messages=[
        {"role": "system", "content": "You are a concise teaching assistant."},
        {"role": "user",   "content": "Explain Kubernetes namespaces in two sentences."},
    ],
)
print(resp.choices[0].message.content)
```

**Streaming:**

```python
stream = client.chat.completions.create(
    model="minimax-m2",
    messages=[{"role": "user", "content": "Write a haiku about GPUs."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

**What you learn.** The exact same code targets the OpenAI cloud, NRP's managed LLM, or any vLLM/TGI server you bring up yourself — only `base_url` changes. This portability is the entire point of the OpenAI-compatible API.

## 5. Bring your own GPU pod

The managed LLM is convenient but constrained: you don't pick the weights, version, quantization, or runtime. When you need that control — or want to run training — request a GPU yourself. Every manifest below already includes the tutorial reservation pattern from Episode 2 (toleration + A10 affinity).

### 5.1 PyTorch GPU sanity check + 1-epoch MNIST

`yamls/pytorch-training.yaml` requests **1 NVIDIA A10**, runs `nvidia-smi`, then trains MNIST for one epoch. Apply (replace `<username>`):

```bash
kubectl apply -n nrp-training-k8s -f yamls/pytorch-training.yaml
kubectl get pod -n nrp-training-k8s tutorial-<username>-gp3 -w
```

Once `Completed`:

```bash
kubectl logs -n nrp-training-k8s tutorial-<username>-gp3 | tail -25
```

<details>
<summary>Expected output (truncated)</summary>

```text
|   0  NVIDIA A10                  ...    |  ...                 |   0%      Default    |

Train Epoch: 1 [0/60000 (0%)]    Loss: 2.305199
...
Test set: Average loss: 0.0501, Accuracy: 9849/10000 (98%)
PyTorch MNIST completed successfully.
```
</details>

Cleanup:

```bash
kubectl delete -n nrp-training-k8s -f yamls/pytorch-training.yaml
```

### 5.2 Run your own LLM with TGI

Same pattern with HuggingFace's [Text Generation Inference](https://github.com/huggingface/text-generation-inference) serving `HuggingFaceH4/zephyr-7b-beta` on a single A10:

```bash
kubectl apply -n nrp-training-k8s -f yamls/tgi-inference.yaml
kubectl get pod -n nrp-training-k8s tutorial-<username>-tgi -w
```

Wait 1–3 minutes for the model download, then port-forward and query it:

```bash
kubectl port-forward -n nrp-training-k8s tutorial-<username>-tgi 8080:80
# second terminal:
curl -s http://127.0.0.1:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"inputs":"Why are penguins black and white?","parameters":{"max_new_tokens":60}}'
```

And the punchline — TGI exposes an OpenAI-compatible `/v1`, so the §4 code works against **your own GPU** by changing only the base URL:

```python
from openai import OpenAI
client = OpenAI(api_key="not-needed", base_url="http://127.0.0.1:8080/v1")
print(client.chat.completions.create(
    model="tgi",
    messages=[{"role":"user","content":"Hi from my own GPU."}],
).choices[0].message.content)
```

Cleanup:

```bash
kubectl delete -n nrp-training-k8s -f yamls/tgi-inference.yaml
```

### 5.3 RAG over the NRP docs with Milvus

The densest exercise of the morning: a managed vector database, the managed LLM, and a retrieval pipeline wired together. A pod (a) clones the public NRP docs, (b) chunks and embeds every page with `sentence-transformers/all-MiniLM-L6-v2`, (c) writes vectors to the managed **Milvus** cluster at `milvus.nrp-nautilus.io:50051`, and (d) answers questions by retrieving the top-4 chunks and sending them to the LLM with the system prompt *"answer only from this context — if it isn't there, say so."*

The pod mounts two pre-loaded Secrets from `nrp-training-k8s`:

| Secret | Keys | Source |
|---|---|---|
| `nrp-training-milvus-credentials` | `host`, `port`, `username`, `password`, `secure`, `database` | [nrp.ai/milvus](https://nrp.ai/milvus) |
| `nrp-llm-token` | `OPENAI_API_BASE`, `OPENAI_API_KEY` | [nrp.ai/llmtoken](https://nrp.ai/llmtoken) |

**Stage 1 — bring up the RAG pod** (bootstrap takes 3–5 min after `Running`):

```bash
kubectl apply  -n nrp-training-k8s -f yamls/milvus-rag.yaml
kubectl get pod -n nrp-training-k8s tutorial-<username>-vectordb -w
```

**Stage 2 — build the index** (the workspace ships `yamls/nrp_docs_rag.py`, one ~290-line script — read it; nothing magic):

```bash
kubectl cp yamls/nrp_docs_rag.py nrp-training-k8s/tutorial-<username>-vectordb:/scratch/
kubectl exec -it -n nrp-training-k8s tutorial-<username>-vectordb -- bash
cd /scratch
python3 nrp_docs_rag.py --reindex
```

Chunking is instant, embedding ~960 chunks takes ~25 s on the A10, and the collection **persists in Milvus across runs** — later invocations answer in seconds.

**Stage 3 — ask questions:**

```bash
python3 nrp_docs_rag.py --only-ask \
  --ask "How do I get a Milvus database password on NRP, and what is the connection endpoint?"
```

<details>
<summary>Expected output</summary>

```text
Q: How do I get a Milvus database password on NRP, and what is the connection endpoint?
------------------------------------------------------------------------------
To get your Milvus database password, navigate to the Milvus password page
(/milvus) and click the "Get milvus password" button; a link to a secure page
containing your password will be sent to your email.

The Milvus GRPC endpoint is **milvus.nrp-nautilus.io:50051**.

Source: https://nrp.ai/documentation/userdocs/ai/vector-database
```
</details>

Also try a question whose answer is **not** in the docs — a well-grounded pipeline should decline rather than confabulate:

```bash
python3 nrp_docs_rag.py --only-ask \
  --ask "What does the cluster do if a pod has no CPU or memory limits?"
```

**What you learn.** Same code, same retriever, same prompt — the inference backend is swappable (managed endpoint, your own TGI pod, a local Ollama). Pick per deployment context: cost, latency, privacy.

Cleanup:

```bash
kubectl delete -n nrp-training-k8s -f yamls/milvus-rag.yaml
```

The Milvus collection survives the pod — the next RAG pod reuses it without re-indexing.

## 6. End-of-morning cleanup

```bash
kubectl delete -n nrp-training-k8s -f yamls/pytorch-training.yaml --ignore-not-found
kubectl delete -n nrp-training-k8s -f yamls/tgi-inference.yaml    --ignore-not-found
kubectl delete -n nrp-training-k8s -f yamls/milvus-rag.yaml       --ignore-not-found
```

Stop any `kubectl port-forward` processes, then verify with `bash check.sh 3`.

::: quiz Quick check — before lunch
1. Your notebook code talks to the NRP managed LLM. What changes to point the same code at the TGI server on your own GPU pod?
- [x] Only the base URL (and the token, which your own server doesn't need)
- [ ] Rewrite the code against a different SDK
- [ ] Nothing — the managed endpoint proxies to your pod automatically
> That is the value of the OpenAI-compatible API: managed endpoint, your own TGI/vLLM pod, or OpenAI cloud — same code, different `base_url`.

2. When do you need your **own** GPU pod instead of the managed endpoint?
- [ ] Whenever you use Python instead of curl
- [x] When you need control over the weights, version, quantization, or want to train
- [ ] When you need streaming responses
> The managed service is zero-ops but its catalog rotates and you don't pick the runtime. Training, custom weights, or pinned versions ⇒ bring your own pod (with the reservation pattern from Episode 2).

3. In the RAG exercise, the pipeline refused to answer a question. Why is that the *desired* behavior?
- [ ] The Milvus collection was still indexing
- [x] The answer wasn't in the retrieved context, and a grounded pipeline should decline rather than make something up
- [ ] The model was too small to know the answer
> The system prompt says "answer only from this context." Declining on out-of-context questions is evidence the grounding works — the opposite of confabulation.
:::
