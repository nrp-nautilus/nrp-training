---
title: Managed LLM & RAG
teaching: 25
exercises: 0
---

::: callout Open this notebook in JupyterHub
**[▶ Open this notebook in JupyterHub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Frcsi&targetpath=rcsi&urlpath=lab%2Ftree%2Frcsi%2Fworkspace%2F2_inference.ipynb)** — opens `workspace/2_inference.ipynb` live on jh-training.nrp-nautilus.io.
:::

The hands-on portion: call NRP's **managed LLMs** from Python, watch them do some
fun tricks, and build a **RAG** pipeline — all in this session, **no GPU needed**.

| Step | Section |
|---|---|
| ① Check the session | 1 |
| ② Talk to NRP's **managed LLMs** | 2 |
| ③ 🎭 Personas via system prompts | 3 |
| ④ 💬 Interactive chat | 4 |
| ⑤ 🔢 Explore the **embedding model** | 5 |
| ⑥ 🖼️ **Multimodal** — send an image | 6 |
| ⑦ 📚 **RAG** over NRP's own docs | 7 |

**Running cells:** click a grey cell, press **Shift + Enter**, top to bottom.
`[*]` = running, `[7]` = done. Kernel is **Python 3** (top-right).

**Prereqs:** a CPU-only session is plenty. `OPENAI_API_BASE`/`OPENAI_API_KEY` and
`kubectl` are already wired up.

## 1. Setup check

Confirm the managed-LLM env vars and `kubectl` are present.

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

## 2. Talk to NRP's managed LLMs

NRP serves a rotating catalog of open-weights LLMs behind one OpenAI-compatible
URL (`https://ellm.nrp-nautilus.io/v1`) — no pod, no GPU billed to you. The
**same `openai` SDK** works; only `base_url` changes.

> Reasoning models (`minimax-m2`, `qwen3`, `gpt-oss`) think privately before
> answering, so they need a bigger `max_tokens` — the `chat()` helper handles it.

📘 [models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/) ·
[API access](https://nrp.ai/documentation/userdocs/ai/llm-managed/api-access/) ·
[chat UI](https://nrp-openwebui.nrp-nautilus.io)

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
# `gemma-small-e4b` (Gemma 3n E4B — fast on NRP and multimodal). The helper also
# handles *reasoning* models like `minimax-m2` (you'll try one below): they
# stream a private chain-of-thought into a separate `reasoning` field and only
# fill `content` once they conclude — so we default `max_tokens` high enough
# (1200) to leave room for both the thinking and the final answer. If a call
# still runs out of tokens mid-thought, we surface that reasoning rather than
# returning nothing.
def chat(prompt, model="gemma-small-e4b", system=None, max_tokens=1200, llm=None):
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

## 3. 🎭 Same question, different *roles*

The **system prompt** sets how the model behaves — its role, tone, and focus.
Here's the same question answered as a **guiding teaching assistant**, a
**technical coder**, a **concise expert**, and a **research assistant**. Swap in
roles useful for your own course and run again.

```python
# The system prompt sets the model's ROLE. Same question, four useful roles:
QUESTION = ("How do I compute the average and standard deviation of a list of "
            "student grades in Python?")

ROLES = {
    "Teaching assistant": (
        "You are a supportive teaching assistant. Explain clearly and build "
        "intuition with a short example, guiding the learner toward the answer "
        "rather than just dumping it."),
    "Technical coder": (
        "You are an expert software engineer. Write clean, correct, "
        "well-commented Python, then briefly explain it and note any edge cases."),
    "Concise expert": (
        "You are a domain expert. Give a precise, rigorous answer in a few "
        "sentences for a graduate-level audience. No filler."),
    "Research assistant": (
        "You are a meticulous research assistant. Give a structured answer, "
        "separate established facts from uncertainty, and point to where to "
        "learn more."),
}
for role, system in ROLES.items():
    print(f"=== {role} ===")
    print(chat(QUESTION, system=system, model="gemma-small-e4b"), "\n")
```

## 4. 💬 Have a conversation

Set a **role** and **model**, run the cell, then chat in the prompt that appears
(type `quit` to stop, `reset` to clear). It remembers context, like office hours.
Change `ROLE`/`MODEL` and re-run to try another.

```python
# A simple interactive chat — works in ANY session (no widget extension needed).
# Set ROLE + MODEL, run the cell, then chat. Type 'quit' to stop, 'reset' to clear.
SYSTEMS = {
    "Teaching assistant": "You are a supportive teaching assistant. Explain clearly, "
        "build intuition with short examples, and guide the learner toward the answer.",
    "Technical coder": "You are an expert software engineer. Write clean, correct, "
        "well-commented code and briefly explain it.",
    "Concise expert": "You are a domain expert. Answer precisely in a few sentences, "
        "graduate level, no filler.",
    "Research assistant": "You are a meticulous research assistant. Give structured "
        "answers, flag uncertainty, and suggest where to learn more.",
}
ROLE  = "Teaching assistant"   # <- change to any key above
MODEL = "gemma-small-e4b"          # <- or minimax-m2, gpt-oss, qwen3, gemma

history = []
print(f"Chatting as: {ROLE} ({MODEL}).  Type 'quit' to stop, 'reset' to clear.\n")
while True:
    try:
        msg = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n(ended)"); break
    if msg.lower() in ("quit", "exit", "q", ""):
        print("Bye!"); break
    if msg.lower() == "reset":
        history.clear(); print("(conversation cleared)\n"); continue
    history.append({"role": "user", "content": msg})
    r = client.chat.completions.create(
        model=MODEL, max_tokens=1000, temperature=0.5,
        messages=[{"role": "system", "content": SYSTEMS[ROLE]}] + history)
    m = r.choices[0].message
    reply = m.content or getattr(m, "reasoning", None) or "(no reply)"
    history.append({"role": "assistant", "content": reply})
    print(f"AI: {reply}\n")
```

## 5. 🔢 Peek at the embedding model

`qwen3-embedding` turns text into vectors where **similar meanings sit closer
together**. Below: rank sentences against a query (semantic search), then a
similarity heatmap.

```python
import numpy as np, matplotlib.pyplot as plt

def embed(texts):
    r = client.embeddings.create(model="qwen3-embedding", input=texts)
    v = np.array([d.embedding for d in r.data])
    return v / np.linalg.norm(v, axis=1, keepdims=True)

docs = [
    "A GPU accelerates deep-learning training.",
    "Kubernetes schedules containers across a cluster.",
    "Helm is a package manager for Kubernetes.",
    "The recipe needs two cups of flour.",
    "Cats like to nap in the sun.",
]
D = embed(docs)
query = "How do I run AI workloads on a compute cluster?"
sims = D @ embed([query])[0]
print(f"Query: {query}\n")
for i in sims.argsort()[::-1]:
    print(f"  {sims[i]:.3f}  {docs[i]}")

M = D @ D.T
fig, ax = plt.subplots(figsize=(5, 4))
im = ax.imshow(M, cmap="viridis", vmin=0, vmax=1)
lab = [d[:20] + "..." for d in docs]
ax.set_xticks(range(len(docs))); ax.set_xticklabels(lab, rotation=45, ha="right", fontsize=7)
ax.set_yticks(range(len(docs))); ax.set_yticklabels(lab, fontsize=7)
fig.colorbar(im, label="cosine similarity")
ax.set_title("Sentence similarity (qwen3-embedding)")
plt.tight_layout(); plt.show()
```

## 6. 🖼️ Multimodal — send an image

Vision models (`gemma-small-e4b`, `gemma`, `qwen3`) accept images. We show one inline and ask
`gemma-small-e4b` to describe it. Swap `IMG_URL` for any image.

```python
import base64, requests
from IPython.display import Image, display

IMG_URL = "https://picsum.photos/id/237/420/280"     # any image URL works
raw = requests.get(IMG_URL, timeout=20).content
display(Image(data=raw))                              # show it inline

b64 = base64.b64encode(raw).decode()
r = client.chat.completions.create(model="gemma-small-e4b", max_tokens=200, messages=[
    {"role": "user", "content": [
        {"type": "text", "text": "Describe this image — what's in it, and the mood?"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
    ]}])
print("gemma-small-e4b sees:\n", r.choices[0].message.content)
```

## 7. 📚 RAG — answer from NRP's own docs

**RAG** = retrieve relevant text, then ask the LLM to answer **only from it**.
Both the embedder (`qwen3-embedding`) and the LLM are NRP-managed — nothing to
install. We pull one real NRP docs page and answer from it.

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
# Answer a question by RAG, using NRP's managed LLM.
SYSTEM = ("Answer the question using ONLY the provided context. "
          "If the context doesn't contain the answer, say so. Be concise.")

def ask(question, model="minimax-m2"):
    context = "\n\n".join(text for text, _ in retrieve(question))
    return chat(f"Context:\n{context}\n\nQuestion: {question}", system=SYSTEM, model=model)

QUESTION = "Is it okay to run `sleep infinity` in a Job on NRP?"
print("Retrieved chunks:")
for text, score in retrieve(QUESTION):
    print(f"  score={score:.3f}  {text[:70].strip()}...")

print("\n--- Answer (NRP managed minimax-m2) ---")
print(ask(QUESTION))
```

**What to notice.** Everything — chat, embeddings, vision, RAG — came from
NRP's managed endpoint with the same `openai` client. No GPU, no model downloads.
In **Part 3** you'll point an agentic coding CLI at this same managed endpoint.

## Takeaways

- One OpenAI-compatible endpoint gave you **chat, personas, embeddings, vision,
  and RAG** — only `base_url` changed.
- Managed LLMs are the lowest-friction path for classrooms: no GPU, no model ops.
- RAG = embed your docs, retrieve the closest chunks, answer from context.

**Next:** [Agentic Workflows](3_agentic.html) — point an agentic coding CLI at
NRP's managed LLM and have it build a program from scratch.
