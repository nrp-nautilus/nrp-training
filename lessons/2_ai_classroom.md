---
title: AI for the Classroom — Chatbots, LLM Service & Agents
teaching: 10
exercises: 20
questions:
  - How do I give a class an AI assistant without buying seats?
  - How do students call an LLM from a notebook or from Python?
  - What does "agentic AI" mean in practice, and can it run on NRP?
objectives:
  - Use NRP's hosted chatbots as a zero-setup classroom tool.
  - Call the managed LLM endpoint from Jupyter AI, curl, and the openai SDK.
  - Point a terminal coding agent at NRP inference and have it write a program.
keypoints:
  - One OpenAI-compatible endpoint serves chatbots, notebooks, scripts, and agents.
  - Hosted chatbots need no token and no install — the lowest-barrier classroom entry point.
  - Only `base_url` changes between NRP, a GPU pod of your own, and a commercial API.
  - Agentic tools are portable: anything speaking OpenAI-compatible HTTP runs against NRP.
---

::: callout Open the runnable notebook
**[▶ Open the notebook for this section](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fhidsi&targetpath=hidsi&urlpath=lab%2Ftree%2Fhidsi%2Fworkspace%2Fnotebooks%2F2_ai_classroom.ipynb)** — every command below is a Shift+Enter cell.
:::

**Time:** 00:20–00:50

A subset of NRP's GPUs power a community-shared, **OpenAI-compatible LLM
inference endpoint** at `https://ellm.nrp-nautilus.io/v1`. No pod to run, no
GPU time to hold, no per-seat license — just HTTP requests with a token.

This section walks the same service from four directions, in increasing order
of what it asks of the user: a **chatbot in a browser**, an **assistant inside
JupyterLab**, **code** in a notebook, and finally an **agent** that writes and
runs code on its own. Pick the rung that matches your class.

> 📘 **Docs:** [Managed LLMs](https://nrp.ai/documentation/userdocs/ai/llm-managed/) · [Available models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/) · [API access](https://nrp.ai/documentation/userdocs/ai/llm-managed/api-access/) · [LLM token](https://nrp.ai/llmtoken)

## 1. AI chatbots for the classroom

The lowest-barrier thing NRP offers is not an API — it is a **chatbot your
students can open in a browser and sign into with their campus account**. No
token, no install, no `pip`, nothing to configure.

- [**nrp-openwebui.nrp-nautilus.io**](https://nrp-openwebui.nrp-nautilus.io) — Open WebUI
- [**librechat.nrp-nautilus.io**](https://librechat.nrp-nautilus.io) — LibreChat

**Try it now.** Open one, pick a model, and ask it something from your own
field. Both front-ends run against the same NRP models, so the choice is mostly
about interface preference.

Why this matters for teaching, concretely:

| Problem with commercial chatbots in a course | What the hosted NRP chatbot does |
|---|---|
| Per-seat cost, or students paying out of pocket | Free at the point of use, on shared national infrastructure |
| Some students have a subscription, some do not | Everyone gets the same models — the playing field is level |
| Student prompts and data leave for a vendor | Requests stay on NRP |
| Account sign-up friction in week one | CILogon — the campus login they already have |

::: callout A teaching note
Open-weights models are good, and they are not frontier commercial models. That
gap is itself worth teaching: have students compare answers and find where the
model is confidently wrong. A course that treats the chatbot as an object of
study rather than an oracle gets more out of it.
:::

## 2. Your token and the endpoint

Everything past the chatbot needs a token. Mint one at
[**nrp.ai/llmtoken**](https://nrp.ai/llmtoken).

::: callout In the training hub today
`OPENAI_API_BASE` and `OPENAI_API_KEY` are **already exported** in every
terminal and notebook on `jh-training.nrp-nautilus.io`. The examples below use
those variables verbatim — nothing to paste. After today, mint your own.
:::

Confirm what you have, and see the live model catalog:

```bash
echo "base: $OPENAI_API_BASE"
echo "key:  ${OPENAI_API_KEY:0:8}..."

curl -s -H "Authorization: Bearer $OPENAI_API_KEY" \
     "$OPENAI_API_BASE/models" | python3 -m json.tool | head -30
```

<details>
<summary>Expected output (the catalog rotates)</summary>

```json
{
    "object": "list",
    "data": [
        { "id": "gemma",      "object": "model", "owned_by": "nrp" },
        { "id": "gpt-oss",    "object": "model", "owned_by": "nrp" },
        { "id": "minimax-m2", "object": "model", "owned_by": "nrp" }
    ]
}
```
</details>

The catalog rotates — large mixture-of-experts chat models, code models,
vision-language models, and an embeddings model, all behind the one endpoint.
Check the [models page](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/)
before pinning a model name into a syllabus.

::: callout What `/models` does and does not prove
On the NRP gateway `/models` answers without authentication, so a successful
listing proves only that the endpoint is reachable. The first call that
actually checks your token is `chat/completions` — that is the real smoke test.
:::

## 3. An assistant inside JupyterLab (Jupyter AI)

The training hub ships [Jupyter AI](https://jupyter-ai.readthedocs.io/)
**pre-configured against the NRP managed LLM** — nothing to install.

**Chat panel.** Click the **chat (robot) icon** in the JupyterLab left sidebar,
type a question, and send. Replies stream back from a model running on NRP GPUs.

**Cell magic**, in a Python notebook:

```python
%load_ext jupyter_ai_magics
```

```text
%%ai openai-chat:minimax-m2
Explain what a Kubernetes namespace is, for a student who has never
seen a cluster. Two sentences.
```

Switch model per cell — the first line is `%%ai <provider>:<model>`, and
`%ai list` shows every registered provider.

**Why this rung matters.** For a class already working in notebooks, Jupyter AI
is the shortest path from "we have an LLM service" to students using it:
they log in, the assistant is there, no token handoff and no `pip install`.

## 4. From code: `curl` and the `openai` SDK

**A chat completion with `curl`** — the universal smoke test:

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

<details>
<summary>Expected output (replies vary)</summary>

```text
The National Research Platform is a distributed, open cyberinfrastructure built on a Kubernetes cluster called Nautilus that gives researchers and educators across 50+ institutions shared access to GPUs, storage, and AI services.
```
</details>

**The same thing from Python.** The `openai` client is pre-installed on hub
spawns (`pip install openai` elsewhere):

```python
import os
from openai import OpenAI

# OPENAI_API_KEY is read from the environment automatically; the base URL must be
# passed explicitly — the SDK's own env var is OPENAI_BASE_URL, but NRP exports it
# as OPENAI_API_BASE, so wire it in by hand (otherwise the client hits api.openai.com).
client = OpenAI(base_url=os.environ["OPENAI_API_BASE"])

resp = client.chat.completions.create(
    model="minimax-m2",
    messages=[
        {"role": "system", "content": "You are a concise teaching assistant."},
        {"role": "user",   "content": "Explain gradient descent to a first-year student."},
    ],
)
print(resp.choices[0].message.content)
```

**Streaming**, so tokens appear as they arrive:

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

<details>
<summary>Expected output (replies vary)</summary>

```text
Silicon cores ignite—
tensors race through parallel light,
night yields to the dawn.
```
</details>

::: keypoints The portability point
That exact code targets the OpenAI cloud, NRP's managed LLM, or a vLLM/TGI
server you bring up yourself on a GPU or a Qualcomm card — **only `base_url`
changes**. Teach the OpenAI-compatible API once and the skill survives every
change of backend, which is the single most useful thing a student can take
away from this hour.
:::

## 5. Building on it: AI workflows

Two steps beyond a single prompt, both of which NRP hosts the pieces for:

**RAG (retrieval-augmented generation)** — ground answers in your own documents
instead of the model's memory. Chunk and embed your corpus, store the vectors in
NRP's managed **[Milvus](https://nrp.ai/documentation/userdocs/vector-database/)**
cluster, retrieve the top matches at question time, and send them to the model
with a system prompt like *"answer only from this context; if it isn't there,
say so."* A syllabus, a lab manual, or a set of course readings is a perfectly
good corpus — and a pipeline that correctly **declines** to answer an
out-of-context question is the demonstration worth showing a class.

**Bring your own model.** When you need control over weights, version,
quantization, or runtime — or you want to *train* rather than serve — request a
GPU pod and run vLLM or TGI yourself. It exposes the same `/v1` API, so §4's
code works against it unchanged. `workspace/yamls/qaic-vllm-server.yaml` does
exactly this on a Qualcomm Cloud AI 100 card.

## 6. Agentic AI development

Chat and RAG are one-shot: prompt in, text out. An **agent** plans, edits files,
runs commands, reads the output, and iterates — the pattern behind AI-assisted
research automation and behind the coding tools your students are already
hearing about.

We point [`opencode`](https://opencode.ai) — a terminal coding agent, similar in
spirit to Claude Code or Cursor's CLI — at NRP's managed LLM. Open a
**Terminal** in JupyterLab:

```bash
curl -fsSL https://opencode.ai/install | bash
export PATH="$HOME/.opencode/bin:$PATH"

mkdir -p ~/.config/opencode
cat > ~/.config/opencode/opencode.json <<'JSON'
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "nrp": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "NRP LLM",
      "options": {
        "baseURL": "https://ellm.nrp-nautilus.io/v1",
        "apiKey": "{env:OPENAI_API_KEY}"
      },
      "models": {
        "minimax-m2": { "name": "MiniMax M2" },
        "gpt-oss":    { "name": "GPT-OSS"    },
        "qwen3":      { "name": "Qwen3 397B" },
        "gemma":      { "name": "Gemma 31B"  }
      }
    }
  },
  "model": "nrp/gpt-oss"
}
JSON
```

The installer drops a binary in `~/.opencode/bin` — no `sudo`. Create a scratch
project and launch the agent:

```bash
mkdir -p ~/agent-demo && cd ~/agent-demo
opencode
```

Inside the TUI, press `/` to open the prompt and give it a small but real task:

```text
Write a single-file Python program board_game.py that lets two humans play chess
in the terminal using the python-chess library. Render the board after each move
with board.unicode(), accept moves in SAN (e.g. "e4", "Nf3"), and print the result
when the game ends. Then add a requirements.txt pinning python-chess to 1.999, and
tell me the exact commands to install and run it.
```

It plans, writes `board_game.py` and `requirements.txt`, and prints the run
commands. Then:

```bash
pip install -r requirements.txt
python board_game.py
```

::: important Two failure modes worth showing the class
**Don't let the model name the file `chess.py`** — it shadows the `python-chess`
package, so `import chess` re-imports the script and `chess.Board()` raises
`AttributeError`. Models also invent plausible-looking versions like
`python-chess==1.10.0` that are not on PyPI; the real current pin is `1.999`,
which is why the prompt pre-pins it.

Both are the same lesson, and it is the one students most need: **give the agent
its constraints up front, and review what it produces before you run it.**
:::

**Switch models mid-session** with `Ctrl+P → Switch models` and re-run the same
prompt against `qwen3` or `minimax-m2`. Same agent, same prompt, different
inference backend — the portability point again. Any OpenAI-compatible agent
(`opencode`, Crush, Continue, Claude Code via `ANTHROPIC_BASE_URL`) works the
same way: you bring the workflow, NRP supplies the inference.

::: quiz Quick check
1. A student asks how to use the NRP LLM with no setup at all. What do you tell them?
- [x] Open `nrp-openwebui.nrp-nautilus.io` or `librechat.nrp-nautilus.io` and sign in with their campus account
- [ ] Mint a token at nrp.ai/llmtoken and install the openai SDK
- [ ] Request a GPU pod and run vLLM
> The hosted chatbots need no token and no install. Tokens and SDKs matter from the moment students write code, not before.

2. Your notebook code talks to the managed endpoint. What must change to point it at a vLLM server you run yourself?
- [x] Only the base URL (and the token, which your own server may not require)
- [ ] Rewrite it against a different SDK
- [ ] Nothing — the managed endpoint proxies to your pod automatically
> That is the whole value of the OpenAI-compatible contract: managed endpoint, your own GPU pod, a Qualcomm card, or a commercial API — same code, different `base_url`.

3. `curl $OPENAI_API_BASE/models` returns a list. What have you proven?
- [x] The endpoint is reachable and the catalog is live — but not yet that your token works
- [ ] Your token is valid
- [ ] The models are loaded into your namespace
> `/models` answers without authentication on the NRP gateway. `chat/completions` is the first call that actually gates on your token.

4. What distinguishes an *agent* from a chatbot?
- [x] It plans, edits files, runs tools, reads the results, and iterates
- [ ] It uses a larger model
- [ ] It runs on a GPU instead of a CPU
> Chat is one-shot text in, text out. The agentic loop — act, observe, revise — is the difference, and it is why reviewing its output matters.
:::

::: callout Next
You have now *used* NRP's AI services. Next you **deploy** something of your
own: [Deploy a Custom JupyterHub & Build Course
Images](3_custom_jupyterhub.html).
:::
