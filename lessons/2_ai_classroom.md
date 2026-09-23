---
title: AI for the Classroom
teaching: 10
exercises: 10
questions:
  - How does a class call an LLM without anyone handling an API key?
  - What does an AI assistant inside JupyterLab actually change for a student?
objectives:
  - Call NRP's managed LLM from a notebook using the token the hub already provides.
  - Use Jupyter AI to explain and repair broken code in place.
keypoints:
  - One OpenAI-compatible endpoint serves notebooks, assistants, agents and scripts.
  - Only `base_url` changes between NRP, your own GPU pod, and a commercial API.
  - The hub exports the token, so no student ever handles a credential.
---

::: callout Open the runnable notebook
**[▶ Open the notebook for this section](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fhidsi&targetpath=hidsi&urlpath=lab%2Ftree%2Fhidsi%2Fworkspace%2Fnotebooks%2F2_ai_classroom.ipynb)** — a short Python notebook; every block below is a Shift+Enter cell.
:::

**Time:** 00:20–00:40

A subset of NRP's GPUs power a community-shared, **OpenAI-compatible LLM
endpoint** at `https://ellm.nrp-nautilus.io/v1`. No pod to run, no GPU to hold,
no per-seat license.

This is a short taste of two things a class gets for free on a hub like this
one: an **LLM you can call from Python**, and an **assistant inside JupyterLab**
that can explain and fix the code a student is stuck on.

> 📘 **Docs:** [Managed LLMs](https://nrp.ai/documentation/userdocs/ai/llm-managed/) · [Available models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/) · [Get your own token](https://nrp.ai/llmtoken)

## 1. The token is already here

On the training hub, `OPENAI_API_BASE` and `OPENAI_API_KEY` are exported into
every server — **students never handle a key**. On a hub you run, you mint one
at [nrp.ai/llmtoken](https://nrp.ai/llmtoken) and set the same two variables
once, for everybody.

```python
import os

print("base:", os.environ.get("OPENAI_API_BASE", "(not set)"))
key = os.environ.get("OPENAI_API_KEY", "")
print("key: ", (key[:8] + "…") if key else "(not set)")
```

## 2. Ask it something

The `openai` SDK talks to NRP unchanged — only `base_url` differs from the
commercial API:

```python
from openai import OpenAI

client = OpenAI(base_url=os.environ["OPENAI_API_BASE"])

resp = client.chat.completions.create(
    model="gpt-oss",
    messages=[
        {"role": "user",
         "content": "In two sentences, what is the National Research Platform?"},
    ],
)

print(resp.choices[0].message.content)
```

> **One wrinkle.** The SDK looks for `OPENAI_BASE_URL`, but NRP exports
> `OPENAI_API_BASE`. Pass it explicitly, as above, or the client quietly calls
> `api.openai.com` instead and fails on your NRP token.

**That is the whole trick.** Those eight lines work against a commercial API,
against NRP, or against a vLLM server you run yourself on a GPU pod — you change
`base_url` and nothing else. Teach the OpenAI-compatible API once and the skill
outlives whatever model is fashionable this year.

Other models are a string away — `qwen3`, `gemma`, `kimi`, `minimax-m2`,
`deepseek-v4-flash` and more:

```python
for m in client.models.list().data:
    print(m.id)
```

## 3. Jupyter AI

The hub ships [Jupyter AI](https://jupyter-ai.readthedocs.io/) already pointed
at the NRP endpoint — no install, no key to paste.

- **Chat panel:** click the **chat icon** in the left sidebar and ask a question.
- **In a cell:** load the magics and prefix a cell with `%%ai`.

```python
%load_ext jupyter_ai_magics
```

```text
%%ai openai-chat:gpt-oss
Explain what a Kubernetes namespace is, for someone who has never used one.
```

### Breaking things on purpose

The notebook ends with three cells that are broken on purpose. Run them, then
hand the error to Jupyter AI — paste the traceback into the chat panel and ask
what went wrong.

| Cell | What happens | What it demonstrates |
|---|---|---|
| 1 | `NameError` — a misspelled function name | The instant win: assistant reads the traceback and points at the typo |
| 2 | `TypeError` — iterating a dict yields *keys*, not values | A real conceptual bug, not a slip |
| 3 | **No error at all** — and the answer is wrong | The interesting one |

That third cell is the one worth dwelling on in front of a class. It runs, it
prints a number, and the number is wrong — an average divided by the wrong
count. Ask Jupyter AI *"why do these two numbers differ?"* and it has to reason
about the code rather than just read a stack trace. That is the failure mode
that quietly survives into a student's homework.

## What to take away

- The endpoint is **OpenAI-compatible**, so anything speaking that API —
  notebooks, Jupyter AI, agents, your own scripts — works against NRP with a
  `base_url` change.
- On a hub you run, the token is an environment variable *you* set once, so no
  student ever handles a credential.
- An assistant sitting inside JupyterLab changes what a stuck student does at
  2am.

::: callout Next
Next we deploy a JupyterHub of your own — the image menu, resource limits and
shared storage a course needs: [Deploy a Custom
JupyterHub](3_custom_jupyterhub.html).
:::
