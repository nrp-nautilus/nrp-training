---
title: Inference on NRP
teaching: 30
exercises: 0
---

::: callout Open this notebook in JupyterHub
**[▶ Open this notebook in JupyterHub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fai-unlocked-tutorial&branch=main&urlpath=lab%2Ftree%2Fai-unlocked-tutorial%2F2_inference.ipynb)** — opens `2_inference.ipynb` live on jh-training.nrp-nautilus.io.
:::

This notebook is the hands-on portion of the AI Unlocked workshop. Everything
runs **inside this JupyterHub session** — there are no separate pods to launch
and no YAML to apply. (We keep the YAML equivalents around as collapsible
reveals so you can see what the same workflow would look like as a Kubernetes
manifest, but you never have to run them.)

A one-line vocabulary primer, in case these are new:

- **LLM** — a large language model (the thing that answers prompts).
- **Inference** — running a prompt through a model to get an answer.
- **RAG** — *retrieval-augmented generation*: look up relevant text first,
  then ask the model to answer **using only that text**. It's how you get an
  LLM to answer questions about your own docs instead of guessing.

**What you'll do**

1. Verify the session has the env vars, `kubectl`, and (optionally) a GPU.
2. Call the **NRP managed LLM** (`https://ellm.nrp-nautilus.io/v1`) from Python.
3. Run a **local LLM** (Ollama + `mistral`) on the JupyterHub session's GPU
   and ask the same prompt — managed vs local, side by side.
4. Build a **RAG pipeline** over a real page of the NRP documentation, using
   NRP's **managed embedding model** (no vector database, no local models),
   and answer through both the managed and local backends.

**How to run a notebook (skip if you've used Jupyter before)**

- A notebook is a list of **cells**. Grey cells are code; this one is text.
- Click a cell and press **Shift + Enter** to run it and move to the next one
  (or click the ▶ button in the toolbar). Run the cells **top to bottom, in
  order** — later cells reuse variables defined earlier.
- A `[*]` next to a cell means it's still running; a number like `[7]` means
  it finished. If something gets stuck, use **Kernel → Restart Kernel** and
  re-run from the top.
- Cells that print `Skipping — no GPU` are doing the right thing on a
  CPU-only session; just keep going.

**Prerequisites**

- Spawn this session with **1 × NVIDIA-A10 GPU, ~4 CPU cores, and ~16 GB RAM**
  (the spawn form defaults to 1 core / 8 GB — too low; the local `mistral`
  load alone needs ~4 GB and the defaults risk running out of memory).
  A GPU is only needed for the
  local-Ollama half of section 3. The managed-LLM and both RAG
  sections work fine on a CPU-only session — the GPU is only needed to run
  `mistral` locally for the side-by-side comparison.
- Use the `NRP Deep Learning & Data Science Full, PyTorch` image (default).
- The session pod already exports `OPENAI_API_BASE` and `OPENAI_API_KEY` and
  has `kubectl` wired to the `nrp-training-k8s` namespace.


## 1. Setup check

Confirm the session has everything we'll need: the managed-LLM env vars,
`kubectl` against `nrp-training-k8s`, and `nvidia-smi` if you spawned with a
GPU. The Ollama sections will skip themselves gracefully if there's no GPU.


```python
import os, shutil, subprocess

print("OPENAI_API_BASE =", os.environ.get("OPENAI_API_BASE", "NOT SET"))
# Print the actual token. This is a shared workshop key — fine to show here;
# treat your own personal token as a secret.
key = os.environ.get("OPENAI_API_KEY", "")
print("OPENAI_API_KEY  =", key if key else "NOT SET")

kubectl = shutil.which("kubectl") or "/opt/conda/bin/kubectl"
print("kubectl path    =", kubectl)
print("kubectl version =", subprocess.run([kubectl, "version", "--client", "-o", "json"],
                                          capture_output=True, text=True).stdout[:120], "...")

print("can list pods in nrp-training-k8s:",
      subprocess.run([kubectl, "auth", "can-i", "list", "pods", "-n", "nrp-training-k8s"],
                     capture_output=True, text=True).stdout.strip())

```

```python
# GPU detection. Section 3 (local Ollama) need this; others are fine without.
import subprocess

HAS_GPU = False
try:
    out = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, check=True).stdout.strip()
    print("GPU(s) detected:")
    print(out)
    HAS_GPU = True
except (FileNotFoundError, subprocess.CalledProcessError):
    print("No GPU in this session pod.")
    print("Section 3 (local Ollama) will skip the local-LLM half.")
    print("To run the full comparison, respawn with 1 x NVIDIA-A10 from the JupyterHub launcher.")

```

## 2. Option A — Use NRP's managed LLMs

There are **two ways to get an LLM in this notebook**, and they use the *same*
Python code:

- **Option A (this section): NRP's managed LLMs.** NRP runs a catalog of
  open-weights models for you behind one OpenAI-compatible URL. You don't run
  a pod and no GPU is billed to you — you just send HTTP requests.
- **Option B (section 3): run your own LLM locally** with Ollama, on the GPU
  attached to this JupyterHub session.

### What the NRP managed LLM service is

NRP hosts a **rotating catalog of open-weights LLMs**, reachable two ways:

- a **browser chat UI** (no setup, ChatGPT-like) at
  [`https://nrp-openwebui.nrp-nautilus.io`](https://nrp-openwebui.nrp-nautilus.io), and
- an **OpenAI-compatible API** at `https://ellm.nrp-nautilus.io/v1` — the one
  we use here.

You authenticate with a **bearer token**. Anyone in an LLM-enabled group can
mint one at [`https://nrp.ai/llmtoken`](https://nrp.ai/llmtoken); on this
training session it's already exported for you as `OPENAI_API_KEY`.

**The catalog rotates** as the open-source frontier moves. Roughly, today:

| Model | Size | Good for |
|---|---|---|
| `qwen3` | 397B | frontier reasoning, largest context |
| `gpt-oss` | 120B | agentic tool-calling / code |
| `gemma` | 31B | general chat, multimodal |
| `kimi`, `glm-5`, `minimax-m2` | 230B–1T | coding (under evaluation) |
| `qwen3-embedding` | 8B | embeddings only (not chat) |

> Some of these (`qwen3`, `minimax-m2`, `gpt-oss`, …) are **reasoning models** —
> they "think" before answering. We'll see what that means in code below.

### Why this matters: one API, many backends

The same `openai` Python SDK code targets:

- the **NRP managed endpoint** (this section),
- a **local Ollama / vLLM server** (section 3),
- or the OpenAI cloud — **just by changing `base_url`**.

That portability is the entire point of OpenAI-compatible APIs.

**NRP LLM docs:**
[overview](https://nrp.ai/documentation/userdocs/ai/llm-managed/) ·
[models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/) ·
[chat interfaces](https://nrp.ai/documentation/userdocs/ai/llm-managed/chat-interfaces/) ·
[API access](https://nrp.ai/documentation/userdocs/ai/llm-managed/api-access/) ·
[client configs](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/)


### What the next five cells do

Each one does a single small thing, so you can see every moving part:

1. **List the catalog** — ask the endpoint which models it's serving right now.
2. **Define a `chat()` helper** — a tiny wrapper so every later call is one line.
3. **Ask one question** — a single request and response.
4. **Stream** — the same call, but printing tokens as they're generated.
5. **Swap the model** — identical code, just a different `model=` name.

Notice that the only NRP-specific thing is the `base_url`. Everything else is
the standard `openai` library you'd use against OpenAI itself.


```python
# List the models currently served by the NRP managed endpoint.
import os, json
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"])
models = client.models.list()
print(f"{len(models.data)} models available right now:\n")
for m in sorted(models.data, key=lambda x: x.id):
    print(f"  {m.id}")

```

```python
# A tiny helper we'll reuse across this notebook. The default model is
# `minimax-m2` (fast on NRP, and a good default). It's a *reasoning* model: it
# streams a private chain-of-thought into a separate `reasoning` field and only
# fills `content` once it concludes — so we default `max_tokens` high enough
# (1200) to leave room for both the thinking and the final answer. If a call
# still runs out of tokens mid-thought, we surface that reasoning rather than
# returning nothing.
def chat(prompt, model="minimax-m2", system=None, max_tokens=1200, llm=None):
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    resp = (llm or client).chat.completions.create(
        model=model, messages=msgs, max_tokens=max_tokens, temperature=0.2,
    )
    msg = resp.choices[0].message
    if msg.content:
        return msg.content
    reasoning = getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None)
    if reasoning:
        return f"(no final answer within max_tokens={max_tokens}; reasoning so far:)\n{reasoning}"
    return "(model produced no content — try raising max_tokens or another model)"
```

```python
# Single chat completion.
print(chat(
    "What is the National Research Platform?",
    system="Answer in one sentence.",
))

```

```python
# Streaming — tokens arrive live, one at a time, instead of all at once.
# minimax-m2 is a reasoning model: it streams its private "thinking" first (the
# `reasoning` field), then the final answer (`content`). We print BOTH, labeled,
# so you can watch the tokens flow and see what "reasoning" means. (A loop that
# printed only `content` — like a haiku-only loop — would show nothing until the
# thinking finished, and with a small max_tokens it may never finish.)
stream = client.chat.completions.create(
    model="minimax-m2",
    messages=[{"role": "user", "content": "Write a haiku about GPUs."}],
    stream=True,
    max_tokens=600,
)

section = None
for chunk in stream:
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta
    think = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
    if think:
        if section != "think":
            print("[thinking]"); section = "think"
        print(think, end="", flush=True)
    if delta.content:
        if section != "answer":
            print("\n\n[answer]"); section = "answer"
        print(delta.content, end="", flush=True)
print()
```

### Standard vs. reasoning models

Most models answer immediately. **Reasoning models** (`qwen3`, `minimax-m2`,
`gpt-oss`, …) first write a private chain-of-thought into a separate
`reasoning` field, then put the final answer in `content`. The practical
catch: that thinking spends tokens, so you must give them a **larger
`max_tokens`** or they'll hit the limit before producing any `content` — which
is exactly the empty-answer case the `chat()` helper guards against.


```python
# Switch to a smaller model — same code, just change the `model` arg.
print(chat("Explain Kubernetes namespaces in two sentences.", model="gemma-small"))

# Now a reasoning model. We give it room (max_tokens=800) so it finishes
# thinking AND produces a final answer — with too few tokens the whole budget
# is spent reasoning and `content` comes back empty (what the helper guards).
print("\n--- minimax-m2 (a reasoning model) ---")
print(chat("In one sentence, name a strength of this model.", model="minimax-m2", max_tokens=800))

# Try the others yourself — e.g. model="gpt-oss" (fast) or model="qwen3"
# (the 397B flagship; highest quality but slowest to respond).

```

<details>
<summary><b>What this would look like as a Kubernetes pod (click to expand)</b></summary>

If you wanted to run your *own* LLM server on NRP instead of using the managed
endpoint, you'd request a GPU pod that boots an OpenAI-compatible server like
vLLM or HuggingFace TGI. The pod below would expose `/v1/chat/completions` on
the same port, so the Python code above works against it unchanged — only the
`base_url` changes (e.g., to `http://127.0.0.1:8080/v1` after a port-forward).

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tutorial-<username>-tgi
  namespace: nrp-training-k8s
spec:
  containers:
  - name: tgi
    image: ghcr.io/huggingface/text-generation-inference:2.1.1
    args: ["--model-id", "HuggingFaceH4/zephyr-7b-beta"]
    resources:
      requests: { cpu: "4", memory: 16Gi, nvidia.com/gpu: 1 }
      limits:   { cpu: "4", memory: 16Gi, nvidia.com/gpu: 1 }
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - { key: nvidia.com/gpu.product, operator: In, values: [NVIDIA-A10] }
  tolerations:
  - { key: nautilus.io/reservation, operator: Equal, value: nrp, effect: NoSchedule }
```

Compared to the managed endpoint:

| | Managed (`ellm.nrp-nautilus.io`) | Self-hosted pod (YAML above) |
|---|---|---|
| Setup | none — just an API call | `kubectl apply` + wait for pull + port-forward |
| Cost | shared, no GPU billed to you | a GPU on the workshop reservation |
| Control | pick from the catalog | pick *any* HF model, quantization, runtime flags |
| Use when | classroom demos, prototypes | research that needs a specific model or config |

</details>


## 3. Option B — Run your own LLM locally (Ollama on the session GPU)

Same OpenAI-compatible API, but now the model runs on **your** GPU inside this
JupyterHub session instead of on NRP's shared endpoint. We install Ollama,
pull `mistral` (7B Q4, ~4 GB), and hit it at `http://localhost:11434/v1` — then
ask the same prompt against NRP's managed `minimax-m2` and our local `mistral` side
by side. **Only `base_url` changes between the two.**

> These cells skip themselves if `HAS_GPU` is `False`. Respawn with
> **1 × NVIDIA-A10** to run the local half.

> **Heads-up on speed:** Ollama and its models install to fast local `/tmp`
> (re-downloaded each session, ~10 s) so the GPU is detected reliably. The
> first `mistral` call **pulls ~4 GB**, which takes a minute or two; after that
> it's loaded on the A10 and responds in a second or two.


```python
# Install Ollama onto the session's FAST local disk (/tmp), NOT the home
# directory. Ollama ships ~3.5 GB of CUDA libraries; the home volume is
# networked storage (Ceph), and reading 3.5 GB from it is too slow for Ollama's
# GPU probe — it times out and silently falls back to CPU. /tmp is node-local
# and fast, so the A10 is detected in under a second. (/tmp is wiped when the
# session stops, so this re-downloads each session — it only takes ~10 s.)
import os, shutil, subprocess

OLLAMA_DIR = f"/tmp/ollama-{os.getuid()}"  # per-user dir we own (avoids shared-path clashes)
OLLAMA_BIN = f"{OLLAMA_DIR}/bin/ollama"
OLLAMA_VERSION = "v0.24.0"  # pinned to a known-good release

if not HAS_GPU:
    print("Skipping Ollama install — no GPU in this session.")
elif os.path.exists(OLLAMA_BIN):
    print("Ollama already installed at", OLLAMA_BIN)
else:
    print(f"Downloading Ollama {OLLAMA_VERSION} to {OLLAMA_DIR} (~10 s)...")
    os.makedirs(OLLAMA_DIR, exist_ok=True)
    url = f"https://github.com/ollama/ollama/releases/download/{OLLAMA_VERSION}/ollama-linux-amd64.tar.zst"
    subprocess.run(
        f"curl -fsSL {url} | tar --use-compress-program=unzstd -xf - -C {OLLAMA_DIR}",
        shell=True, check=True,
    )
if HAS_GPU:
    os.environ["PATH"] = f"{OLLAMA_DIR}/bin" + os.pathsep + os.environ["PATH"]
    print("ollama binary at:", shutil.which("ollama"))

```

```python
# Start `ollama serve` in the background and wait until it answers.
#   - Everything (binary, CUDA libs, models) lives under /tmp/ol on fast local
#     disk, so the GPU probe finds the A10 in well under a second.
#   - OLLAMA_LLM_LIBRARY + LD_LIBRARY_PATH point at the bundled CUDA libraries.
#   - OLLAMA_MODELS keeps pulled models on /tmp too, so they load fast.
import os, socket, subprocess, time, urllib.request, urllib.error

def ollama_alive():
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        return True
    except (urllib.error.URLError, ConnectionResetError, OSError, socket.timeout, TimeoutError):
        return False

LIB = f"{OLLAMA_DIR}/lib/ollama"
SERVE_LOG = f"{OLLAMA_DIR}/serve.log"  # we created OLLAMA_DIR, so this is always writable

if not HAS_GPU:
    print("Skipping Ollama serve — no GPU in this session.")
elif ollama_alive():
    print("Ollama already running.")
else:
    print("Starting `ollama serve` in the background...")
    ollama_env = {
        **os.environ,
        "HOME": OLLAMA_DIR,  # keep ollama's identity key + data on the fast local dir we own
        "OLLAMA_HOST": "0.0.0.0:11434",
        "OLLAMA_LOAD_TIMEOUT": "15m",
        "OLLAMA_MODELS": f"{OLLAMA_DIR}/models",
        "OLLAMA_LIBRARY_PATH": LIB,
        "OLLAMA_LLM_LIBRARY": "cuda_v12",
        "LD_LIBRARY_PATH": ":".join([
            LIB, LIB + "/cuda_v12", "/usr/lib/x86_64-linux-gnu",
            os.environ.get("LD_LIBRARY_PATH", ""),
        ]),
    }
    subprocess.Popen(f"nohup {OLLAMA_BIN} serve > {SERVE_LOG} 2>&1 &", shell=True, env=ollama_env)
    t0 = time.time(); deadline = t0 + 120
    while time.time() < deadline:
        time.sleep(2)
        if ollama_alive():
            print(f"Ollama up after ~{int(time.time() - t0)}s.")
            break
    else:
        print(f"Ollama did not come up within 120s. Check {SERVE_LOG}")

# Report which device Ollama is using.
if HAS_GPU and ollama_alive():
    log = subprocess.run(f"grep -iE 'inference compute' {SERVE_LOG} | tail -1",
                         shell=True, capture_output=True, text=True).stdout.lower()
    if "library=cuda" in log:
        print("Device: GPU (CUDA) — the A10 was detected. \U0001f389")
    elif "id=cpu" in log:
        print(f"Device: CPU — GPU probe fell back to CPU; check {SERVE_LOG}")
    else:
        print(f"Device: unknown — see {SERVE_LOG}")

```

```python
# Pull the mistral 7B model (~4 GB). First time only.
import subprocess, time, json, urllib.request

def already_pulled(name="mistral"):
    try:
        r = json.load(urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2))
        return any(name in m["name"] for m in r.get("models", []))
    except Exception:
        return False

if not HAS_GPU:
    print("Skipping — no GPU.")
elif already_pulled("mistral"):
    print("mistral already pulled.")
else:
    print("Pulling mistral... (~4 GB, 2-4 minutes the first time)")
    # Drive the pull via the HTTP API instead of `ollama pull`, because the CLI
    # writes \r-based progress bars that buffer indefinitely under nbconvert.
    body = json.dumps({"name": "mistral", "stream": True}).encode()
    req  = urllib.request.Request("http://localhost:11434/api/pull", data=body,
                                  headers={"Content-Type": "application/json"})
    t0 = time.time()
    last_status = None
    with urllib.request.urlopen(req) as resp:
        for raw in resp:
            try:
                evt = json.loads(raw.decode())
            except Exception:
                continue
            status = evt.get("status", "")
            # Only print on status transitions (not every kilobyte) to keep output tidy
            if status and status != last_status:
                print(f"  [{int(time.time()-t0):3d}s] {status}")
                last_status = status
            if evt.get("error"):
                raise RuntimeError(evt["error"])
    print(f"Done in {int(time.time()-t0)}s.")

```

```python
# Hello-world against the local model. Same OpenAI client, different base_url.
# Heads up: the first call after `ollama serve` started will be slow (~30-120s
# while llama.cpp loads the 4 GB of weights into VRAM). Subsequent calls in
# this notebook reuse the loaded model and respond in 1-2 seconds.
from openai import OpenAI

if HAS_GPU:
    local = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1",
                   timeout=900)  # generous timeout for the cold load
    print(chat(
        "Say hi from the GPU in this JupyterHub session.",
        model="mistral", llm=local, max_tokens=80,
    ))
else:
    print("Skipping — no GPU.")

```

```python
# Side-by-side: same prompt, managed minimax-m2 vs local mistral.
prompt = "Explain in two sentences why a research cluster might use Kubernetes namespaces."

print("=" * 78)
print("NRP MANAGED (minimax-m2)")
print("=" * 78)
print(chat(prompt, model="minimax-m2"))

if HAS_GPU:
    print()
    print("=" * 78)
    print("LOCAL (mistral, on this pod's GPU)")
    print("=" * 78)
    print(chat(prompt, model="mistral", llm=local))
else:
    print("\n(Local half skipped — no GPU.)")

```

**What to notice.** The Python code is byte-for-byte identical — same SDK,
same `chat.completions.create`, same messages. Only `base_url` differs.
Latency, answer style, and request privacy will differ:

| | Managed `minimax-m2` | Local `mistral` (this pod) |
|---|---|---|
| Where it runs | NRP GPUs you don't see | the A10 attached to this pod |
| Latency to first answer | thinks first, then streams | ~6 s (warm) |
| GPU billed | none | yours, while pod runs |
| Privacy | request leaves your namespace | never leaves your pod |
| Catalog | the NRP model list | anything `ollama pull` supports |

<details>
<summary><b>What the Ollama equivalent looks like as a YAML pod (click to expand)</b></summary>

If you ran Ollama in its own dedicated pod instead of inside the JupyterHub
session (e.g., to share one Ollama server across multiple notebook sessions,
or to keep model weights on a separate PVC), it would look like this:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tutorial-<username>-ollama
  namespace: nrp-training-k8s
spec:
  containers:
  - name: ollama
    image: ollama/ollama:0.2.8
    resources:
      requests: { cpu: "4", memory: 16Gi, nvidia.com/gpu: 1 }
      limits:   { cpu: "4", memory: 16Gi, nvidia.com/gpu: 1 }
    ports:
    - { containerPort: 11434 }
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - { key: nvidia.com/gpu.product, operator: In, values: [NVIDIA-A10] }
  tolerations:
  - { key: nautilus.io/reservation, operator: Equal, value: nrp, effect: NoSchedule }
```

You'd then `kubectl port-forward pod/tutorial-<username>-ollama 11434:11434`
and point your notebook at `http://localhost:11434/v1` — same code, same
result. The in-notebook path you just ran is the same thing, minus the YAML.

</details>


## 4. RAG — answer from NRP's own docs (no extra infrastructure)

**RAG** ("retrieval-augmented generation") makes an LLM answer from *your*
text instead of guessing: (1) split your docs into chunks and **embed** each
into a vector, (2) embed the question and find the closest chunks, (3) put
those chunks in the prompt with "answer only from this context."

The nice part on NRP: the **embedding model is managed too**. The same endpoint
that serves the chat models also serves `qwen3-embedding`, so we don't install
or download anything. And for a small corpus, a handful of vectors in NumPy is
all the "vector database" we need.

We'll pull **one real page of the NRP documentation** and answer questions from it.


```python
# Pull one real NRP documentation page (the cluster policies page) and clean it.
import requests, re

PAGE = "https://nrp.ai/documentation/userdocs/start/policies/"
RAW  = ("https://gitlab.nrp-nautilus.io/prp/nrp-site/-/raw/main/"
        "src/content/docs/Documentation/userdocs/start/policies.mdx")

md = requests.get(RAW, timeout=30).text
md = re.sub(r"^---.*?---\s*", "", md, flags=re.S)        # drop frontmatter
md = re.sub(r"^import .*$", "", md, flags=re.M)          # drop MDX imports
md = re.sub(r":::\w+(\[[^\]]*\])?|:::", "", md)          # drop admonition markers
md = re.sub(r"<[^>]+>", "", md)                          # drop stray HTML/JSX
md = re.sub(r"\n{3,}", "\n\n", md).strip()

# Split into ~700-char chunks. (A real corpus would chunk every page; one is plenty here.)
chunks = [md[i:i+700] for i in range(0, len(md), 550)]
print(f"Pulled {len(md)} chars from {PAGE}")
print(f"Split into {len(chunks)} chunks.")

```

```python
# Embed with NRP's MANAGED embedding model — no local model, nothing to download.
# Same `client`, same endpoint as the chat models; just a different call.
import numpy as np

def embed(texts):
    resp = client.embeddings.create(model="qwen3-embedding", input=texts)
    vecs = np.array([d.embedding for d in resp.data])
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)   # normalize for cosine

chunk_vecs = embed(chunks)          # one API call embeds the whole page
print(f"Embedded {len(chunks)} chunks into vectors of dim {chunk_vecs.shape[1]} (via qwen3-embedding).")

def retrieve(question, k=3):
    qv = embed([question])[0]
    scores = chunk_vecs @ qv         # cosine similarity (everything is normalized)
    top = scores.argsort()[-k:][::-1]
    return [(chunks[i], float(scores[i])) for i in top]

```

```python
# Answer a question by RAG. Swap model/llm to answer with the local GPU model instead.
SYSTEM = ("Answer the question using ONLY the provided context. "
          "If the context doesn't contain the answer, say so. Be concise.")

def ask(question, model="minimax-m2", llm=None):
    context = "\n\n".join(text for text, _ in retrieve(question))
    return chat(f"Context:\n{context}\n\nQuestion: {question}", system=SYSTEM, model=model, llm=llm)

QUESTION = "Is it okay to run `sleep infinity` in a Job on NRP?"
print("Retrieved chunks:")
for text, score in retrieve(QUESTION):
    print(f"  score={score:.3f}  {text[:70].strip()}...")
print("\n--- Answer (NRP managed minimax-m2) ---")
print(ask(QUESTION))

```

```python
# The exact same RAG pipeline, answered by the local model on this session's GPU.
# Only the model + client change — retrieval and embeddings are identical.
if HAS_GPU:
    print("--- Answer (local mistral on the GPU) ---")
    print(ask(QUESTION, model="mistral", llm=local))
else:
    print("(Skipped — no GPU. The managed answer above used the same pipeline.)")

```

**What to notice.**

- **Everything came from NRP's managed endpoint** — the chat model *and* the
  `qwen3-embedding` embedding model. No models were installed or downloaded.
- Retrieval was ~5 lines of NumPy. That's all a vector database does under the
  hood; for one page it's overkill. For a **large, persistent corpus** you'd swap
  the NumPy array for NRP's managed **Milvus** vector database — same three steps
  (embed, search, prompt), just scalable across many documents and users.
- Managed vs local was one argument: the same `ask()` answered through NRP's
  `minimax-m2` and the local `mistral`, with identical retrieval and embeddings.


## 5. Cleanup

Stopping the local Ollama process frees the GPU memory. (The RAG step used only
NRP's managed services and in-memory NumPy, so there's nothing else to tear down.)


```python
# Stop the local Ollama daemon (frees GPU memory).
import subprocess
subprocess.run(["pkill", "-x", "ollama"], check=False)
print("Ollama stopped.")

```

## Takeaways

- The same OpenAI-compatible Python code targeted three different inference
  backends: NRP's managed `ellm.nrp-nautilus.io`, a local Ollama on this
  session's GPU, and (via the collapsible YAML reveals) self-hosted TGI/vLLM
  pods. Only `base_url` changed.
- Managed LLMs are the lowest-friction path for classrooms — no token
  handoff, no GPU billed to students. Self-hosted pods make sense when you
  need a specific model, quantization, or runtime control.
- RAG is "embed your docs, retrieve the closest chunks, prompt the LLM with
  'answer from context only.'" Here the **embedding model (`qwen3-embedding`)
  and the LLM both came from NRP's managed endpoint** — no local models — and a
  few NumPy lines replaced a vector database for a one-page corpus.
- Whatever you do in this notebook, the YAML equivalent is one
  `kubectl apply` away — useful when you outgrow the JupyterHub session.

**Next:** [3_agentic.md](3_agentic.md) — point an agentic coding CLI (`opencode`)
at the NRP managed LLM and have it write a chess game.

