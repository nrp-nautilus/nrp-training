---
title: Chat with LLMs — Python, Multimodal, Embeddings & RAG
teaching: 5
exercises: 40
questions:
  - How do I call NRP's managed LLMs from Python?
  - How can I send images or other non-text inputs to a model?
  - What are embeddings and how do I use them for semantic search?
  - How do I build a RAG pipeline over my own documents?
objectives:
  - Define a reusable `chat()` helper using the `openai` Python SDK.
  - Demonstrate multi-turn conversation, system prompts, and persona switching.
  - Send an image to a vision-capable model.
  - Embed text with `qwen3-embedding` and perform semantic similarity search.
  - Build a minimal RAG pipeline over CMS documentation.
keypoints:
  - One `openai.OpenAI` client, one `base_url`, covers chat, embeddings, and vision.
  - System prompts control model behavior without changing the user-facing interface.
  - Embeddings map text to vectors — semantic search is just a dot product.
  - RAG = embed your docs, retrieve closest chunks, answer only from that context.
---

::: callout Open the notebook in JupyterHub
**[▶ Open notebook in JupyterHub](https://jupyterhub-west.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats-llm&targetpath=cms-hats-llm&urlpath=lab%2Ftree%2Fcms-hats-llm%2Fworkspace%2F2_chat.ipynb)** — clones the training repo and opens `workspace/2_chat.ipynb` on jupyterhub-west.nrp-nautilus.io.
:::

Work through the notebook top to bottom (**Shift+Enter** to run each cell). The notebook covers:

| Step | Topic |
|---|---|
| 1 | Setup check — verify env vars and client |
| 2 | Basic chat — single completions and the `chat()` helper |
| 3 | System prompts & personas |
| 4 | Multi-turn interactive chat |
| 5 | Embeddings and semantic similarity |
| 6 | Multimodal — send a detector image |
| 7 | RAG over CMS documentation |

**Prerequisites:** `OPENAI_API_BASE` and `OPENAI_API_KEY` are pre-loaded on the training JupyterHub. A CPU-only session is sufficient for all exercises.

---

<details>
<summary><strong>📓 Notebook preview (click to expand)</strong></summary>

The content below is the notebook rendered as Markdown with example outputs. Run the live notebook on JupyterHub to execute cells and see your own results.

---

## 1. Setup Check

Confirm that the environment variables and Python client are ready.

```python
import os
from openai import OpenAI

print("OPENAI_API_BASE =", os.environ.get("OPENAI_API_BASE", "NOT SET"))
key = os.environ.get("OPENAI_API_KEY", "")
print("OPENAI_API_KEY  =", key[:8] + "..." if key else "NOT SET")

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_API_BASE"],
)
models = client.models.list()
print(f"\n{len(models.data)} models available:")
for m in sorted(models.data, key=lambda x: x.id):
    print(f"  {m.id}")
```

**Example output:**
```
OPENAI_API_BASE = https://ellm.nrp-nautilus.io/v1
OPENAI_API_KEY  = rifgnLi8...

7 models available:
  gemma
  gemma-small-e4b
  gpt-oss
  minimax-m2
  qwen3
  qwen3-embedding
  qwen3-small
```

---

## 2. Basic Chat & the `chat()` Helper

Define a reusable helper that handles reasoning models (which need larger `max_tokens`).

```python
def chat(prompt, model="gemma-small-e4b", system=None, max_tokens=1200):
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=model, messages=msgs, max_tokens=max_tokens, temperature=0.2,
    )
    msg = resp.choices[0].message
    if msg.content:
        return msg.content
    reasoning = getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None)
    if reasoning:
        return f"(reasoning only, increase max_tokens):\n{reasoning}"
    return "(no content returned)"
```

```python
# Ask something CMS-relevant
print(chat(
    "What is the CMS detector and what is it used for?",
    system="Answer in two sentences for an audience of physics graduate students.",
))
```

**Example output:**
```
The CMS (Compact Muon Solenoid) detector is a general-purpose particle physics
detector at CERN's Large Hadron Collider, designed to observe a wide range of
particles and phenomena produced in proton-proton and heavy-ion collisions.
It is used to study the Standard Model, search for the Higgs boson and its
properties, and probe for physics beyond the Standard Model such as
supersymmetry and dark matter candidates.
```

```python
# Try a code-generation task
print(chat(
    "Write a short Python snippet using ROOT's RDataFrame to read a TTree called "
    "'Events' from 'data.root' and print the number of entries.",
    model="gpt-oss",  # strong at code
))
```

---

## 3. System Prompts & Personas

The system prompt defines the model's role. Same question, four roles — swap in whatever fits your use case.

```python
QUESTION = "How do I apply a muon pT > 20 GeV selection in CMS NanoAOD with Python?"

ROLES = {
    "Teaching assistant": (
        "You are a supportive teaching assistant for CMS physicists. Explain "
        "clearly with short examples, guiding the learner toward the answer."),
    "Technical coder": (
        "You are an expert HEP software engineer. Write clean, correct Python "
        "using coffea or uproot, then briefly explain it and note edge cases."),
    "Concise expert": (
        "You are a senior CMS physicist. Answer precisely in a few sentences "
        "for a graduate-level audience. No filler."),
    "Documentation writer": (
        "You are a CMS documentation writer. Structure your answer clearly with "
        "headings, a code block, and a note on common pitfalls."),
}

for role, system in ROLES.items():
    print(f"\n=== {role} ===")
    print(chat(QUESTION, system=system, model="gemma-small-e4b"))
```

---

## 4. Multi-Turn Interactive Chat

Run this cell, then type questions. The model remembers context across turns. Type `quit` to stop, `reset` to clear history.

```python
ROLE  = "Teaching assistant"
MODEL = "gemma-small-e4b"

SYSTEMS = {
    "Teaching assistant": (
        "You are a supportive teaching assistant for CMS physicists. Explain "
        "clearly, build intuition with examples, guide the learner."),
    "CMS expert": (
        "You are an expert CMS physicist. Answer precisely and technically."),
}

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
    reply = r.choices[0].message.content or "(no reply)"
    history.append({"role": "assistant", "content": reply})
    print(f"AI: {reply}\n")
```

---

## 5. Embeddings & Semantic Similarity

`qwen3-embedding` converts text to vectors. Similar meanings land close together — semantic search is just a dot product.

```python
import numpy as np
import matplotlib.pyplot as plt

def embed(texts):
    r = client.embeddings.create(model="qwen3-embedding", input=texts)
    v = np.array([d.embedding for d in r.data])
    return v / np.linalg.norm(v, axis=1, keepdims=True)

# CMS-flavored corpus
docs = [
    "The Higgs boson was discovered by CMS and ATLAS in 2012.",
    "NanoAOD is a compact CMS data format for analysis.",
    "Muon pT is measured by the CMS tracking system and muon chambers.",
    "The missing transverse energy indicates invisible particles like neutrinos.",
    "Machine learning is used in CMS for jet tagging and trigger decisions.",
    "Python and ROOT are the primary tools for CMS data analysis.",
    "Cats like to nap in the sun.",  # unrelated — should rank last
]

D = embed(docs)
query = "How does CMS measure particle momentum?"
sims = D @ embed([query])[0]

print(f"Query: {query}\n")
for i in sims.argsort()[::-1]:
    print(f"  {sims[i]:.3f}  {docs[i]}")
```

**Example output:**
```
Query: How does CMS measure particle momentum?

  0.712  Muon pT is measured by the CMS tracking system and muon chambers.
  0.634  The Higgs boson was discovered by CMS and ATLAS in 2012.
  0.601  Machine learning is used in CMS for jet tagging and trigger decisions.
  0.589  Python and ROOT are the primary tools for CMS data analysis.
  0.571  The missing transverse energy indicates invisible particles like neutrinos.
  0.543  NanoAOD is a compact CMS data format for analysis.
  0.301  Cats like to nap in the sun.
```

```python
# Pairwise similarity heatmap
M = D @ D.T
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(M, cmap="viridis", vmin=0, vmax=1)
labels = [d[:30] + "..." for d in docs]
ax.set_xticks(range(len(docs))); ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
ax.set_yticks(range(len(docs))); ax.set_yticklabels(labels, fontsize=7)
fig.colorbar(im, label="cosine similarity")
ax.set_title("Sentence similarity (qwen3-embedding)")
plt.tight_layout(); plt.show()
```

---

## 6. Multimodal — Send a Detector Image

Vision models (`gemma-small-e4b`, `gemma`, `qwen3`) accept images alongside text. Swap `IMG_URL` for any CMS event display or detector plot.

```python
import base64, requests
from IPython.display import Image, display

# Replace with a CMS event display or detector plot URL
IMG_URL = "https://cms-results.web.cern.ch/cms-results/public-results/publications/HIG/CMS-HIG-19-004/CMS-HIG-19-004_Figure_001-a.png"

raw = requests.get(IMG_URL, timeout=30).content
display(Image(data=raw))

b64 = base64.b64encode(raw).decode()
r = client.chat.completions.create(
    model="gemma-small-e4b",
    max_tokens=300,
    messages=[{"role": "user", "content": [
        {"type": "text",      "text": "This is a figure from a CMS physics paper. Describe what you see and what physics it might be showing."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ]}],
)
print("Model sees:\n", r.choices[0].message.content)
```

---

## 7. RAG — Answer from CMS Documentation

RAG = embed your documents, retrieve the most relevant chunks, ask the LLM to answer **only from that context**. Both the embedding model and the LLM are NRP-managed — nothing to install.

```python
import requests, re

# Pull a CMS public documentation page (TWiki or CMS public docs)
# Here we use the NRP docs as a stand-in; replace with CMS-specific content
PAGE_URL = "https://raw.githubusercontent.com/nrp-nautilus/nrp-training/main/README.md"
md = requests.get(PAGE_URL, timeout=30).text
md = re.sub(r"\n{3,}", "\n\n", md).strip()

# Chunk into ~700-character pieces with 150-char overlap
chunks = [md[i:i+700] for i in range(0, len(md), 550)]
print(f"Loaded {len(md)} chars, split into {len(chunks)} chunks.")
```

```python
# Embed all chunks with qwen3-embedding
chunk_vecs = embed(chunks)
print(f"Embedded {len(chunks)} chunks → vectors of dim {chunk_vecs.shape[1]}.")

def retrieve(question, k=3):
    qv = embed([question])[0]
    scores = chunk_vecs @ qv
    top = scores.argsort()[-k:][::-1]
    return [(chunks[i], float(scores[i])) for i in top]
```

```python
SYSTEM_RAG = (
    "Answer the question using ONLY the provided context. "
    "If the context does not contain the answer, say so explicitly. Be concise."
)

def ask_rag(question, model="minimax-m2"):
    context = "\n\n".join(text for text, _ in retrieve(question))
    return chat(
        f"Context:\n{context}\n\nQuestion: {question}",
        system=SYSTEM_RAG, model=model,
    )

question = "What namespaces are used in the NRP training?"
print("Retrieved chunks:")
for text, score in retrieve(question):
    print(f"  score={score:.3f}  {text[:60].strip()}...")
print("\n--- Answer ---")
print(ask_rag(question))
```

**Key idea:** everything — chat, personas, embeddings, vision, RAG — uses the same `openai` client with NRP's `base_url`. No GPU needed.

---

## Takeaways

- One `OpenAI` client, one `base_url` — chat, embeddings, vision, RAG all go through the same endpoint.
- System prompts let you define reusable roles without changing any code logic.
- Embeddings + cosine similarity = semantic search; no specialized database required for small corpora.
- RAG keeps LLM answers grounded in your documents and prevents hallucination on domain-specific content.

**Next:** [Agentic Workflows](3_agentic.html) — point an agentic coding CLI at NRP's managed LLM and have it write code autonomously.

</details>
