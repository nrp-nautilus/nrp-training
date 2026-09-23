---
title: AI for the Classroom
teaching: 10
exercises: 10
questions:
  - How does a class call an LLM without anyone handling an API key?
  - What does an AI assistant inside JupyterLab actually change for a student?
objectives:
  - Call NRP's managed LLM from a notebook using the token the hub already provides.
  - Use Jupyter AI to explain the last error and reason about live variables.
keypoints:
  - One OpenAI-compatible endpoint serves notebooks, assistants, agents and scripts.
  - Only `base_url` changes between NRP, your own GPU pod, and a commercial API.
  - The hub exports the token, so no student ever handles a credential.
  - The Jupyter AI chat panel cannot see your kernel; the `%%ai` magics can.
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

## 2. What models are on offer

One endpoint fronts the whole catalog — chat models large and small, a code
model, and an embeddings model:

```python
from openai import OpenAI

client = OpenAI(base_url=os.environ["OPENAI_API_BASE"])

for m in client.models.list().data:
    print(m.id)
```

<details>
<summary>Expected output (the catalog rotates)</summary>

```text
glm-5
qwen3
qwen3-embedding
qwen3-small
gemma-small-e4b
gpt-oss
gemma
kimi
minimax-m2
deepseek-v4-flash
gemma-small
gemma4-small
gemma4-12b
```
</details>

Models come and go as the team rotates capacity, so check the
[models page](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/)
before pinning a name into a syllabus — and prefer a small model for classwork,
since it answers faster and leaves the big ones free.

::: callout What `/models` does and does not prove
On the NRP gateway the model list answers **without authentication**, so a
successful listing proves only that the endpoint is reachable. The first call
that actually checks your token is a chat completion — that is the real smoke
test, and it is the next cell.
:::

## 3. Ask it something

Picking one of those names is the only change needed; the `openai` SDK talks to
NRP unchanged, because only `base_url` differs from the commercial API:

```python
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

**That is the whole trick.** Those few lines work against a commercial API,
against NRP, or against a vLLM server you run yourself on a GPU pod — you change
`base_url` and nothing else. Teach the OpenAI-compatible API once and the skill
outlives whatever model is fashionable this year.

## 4. Jupyter AI

The hub ships [Jupyter AI](https://jupyter-ai.readthedocs.io/) already pointed
at the NRP endpoint — no install, no key to paste. Click the **chat icon** in
the left sidebar and ask it something.

::: important The chat panel cannot see your notebook
It has no access to the kernel, your variables, or your cell outputs. Ask it
*"why is 86.333 the average?"* and it will quite reasonably ask what you are
talking about, because nothing in the conversation says. `/learn` does not help
either — it indexes **files on disk**, not the running kernel.

Section 5 shows the way around that.
:::

### Now break something on purpose

The notebook has three cells that are broken on purpose. Each names the bug it
carries rather than a position, because Jupyter AI will happily rewrite a cell
in place **or** drop a corrected copy underneath it — so "the third cell" stops
meaning anything the moment you accept a fix.

| Broken cell | What happens | What it demonstrates |
|---|---|---|
| `temperature conversion` | `NameError` — a misspelled function name | The instant win: the assistant reads the traceback and points at the typo |
| `class average` | `TypeError` — iterating a dict yields *keys*, not values | A real conceptual bug, not a slip |
| `sensor average` | **No error at all** — and the answer is wrong | The interesting one |

Run them, then select a cell and ask the chat panel what went wrong.

::: callout `/fix` only works on cells that crashed
Jupyter AI's `/fix` command requires a selected cell **with error output** —
otherwise it answers *"`/fix` requires an active code cell with error output."*

So the first two cells get the one-click treatment and `sensor average` does
not. The assistant's whole error-shaped affordance disappears at exactly the
moment the bug goes quiet, which is the real argument for teaching the third
case: a student who only knows how to react to red text has no move here.
:::

```python
# 🐞 BROKEN — temperature conversion   (this one crashes)
temperatures_c = [18, 21, 25, 30, 12]

def to_fahrenheit(c):
    return c * 9 / 5 + 32

for t in temperatures_c:
    print(t, "C =", to_farenheit(t), "F")
```

```python
# 🐞 BROKEN — class average   (this one crashes)
student_scores = {"ana": 88, "ben": 92, "cleo": 79}

total = 0
for name in student_scores:
    total += name

print("class average:", total / len(student_scores))
```

```python
# 🐞 BROKEN — sensor average   (no crash; the answer is just wrong)
readings = [3, 7, 2, 9, 4, 8]

# intended: the average of every reading after the first
average = sum(readings[1:]) / len(readings)

print("average of readings 2..6 =", average)
print("expected:", (7 + 2 + 9 + 4 + 8) / 5)
```

**The `sensor average` cell is the one worth dwelling on in front of a class.**
It runs, prints a number, and the number is wrong — it divides by 6 when it
should divide by 5. There is no traceback to paste, so the assistant has to
reason about what the code was *meant* to do. That is the failure mode that
quietly survives into a student's homework.

## 5. The `%%ai` magic

The chat panel is one way in. The other is a **magic** — a notebook command
that is not Python, which here gets you an assistant that *can* see the kernel.

```python
%load_ext jupyter_ai_magics
```

### First, a confusing bit

```python
%ai list
```

That prints a long table of providers and models — `openai-chat:gpt-4o`,
`ai21:j2-jumbo`, and so on.

::: callout Those are not NRP models
That table is a catalog **hardcoded inside Jupyter AI**, listing what each
*provider* offers in general. The `✅` beside `OPENAI_API_KEY` only means the
variable is set, not that those models exist here. Ask NRP for `gpt-4o` and it
will tell you there is no such model.

So how does anything reach NRP? Jupyter AI does **not** check the model name
against that table — it passes the name straight to LangChain, which reads
`OPENAI_API_BASE` from your environment. That variable points at NRP, so
whatever you type after the provider goes to NRP.

| Spelling | Why |
|---|---|
| `openai-chat:gpt-oss` | Works by pass-through; the name is never validated |
| `openai-chat-custom:gpt-oss` | The provider *meant* for "non-OpenAI models behind the OpenAI API" — its model list is literally `*` |

Either way, **the model name must be one from
[section 2](#2-what-models-are-on-offer)** — `gpt-oss`, `minimax-m2`, `qwen3`,
`gemma`, and the rest. The names in `%ai list` are a distraction.
:::

```text
%%ai openai-chat:minimax-m2
What is the National Research Platform in two sentences?
```

### Two things the chat panel cannot do

**1. Explain the last error.** `%ai error` reaches into the kernel for the most
recent traceback — nothing to copy or paste. The exception hook is installed by
`%load_ext`, so it only records errors raised *after* that ran; re-run a broken
cell first.

```python
%ai error openai-chat:minimax-m2
```

**2. Ask about your actual values.** Anything in `{curly braces}` inside a
`%%ai` prompt is replaced with the *live value* of that variable from the
kernel. This is the fix for "why is this number what it is?" — you hand it the
number.

Re-run it so `readings` and `average` are live in the kernel — and still
wrong — right where the next prompt needs them:

```python
# 🐞 BROKEN — sensor average, again   (re-run so the wrong values are live below)
readings = [3, 7, 2, 9, 4, 8]

# intended: the average of every reading after the first
average = sum(readings[1:]) / len(readings)

print("average of readings 2..6 =", average)
print("expected:", (7 + 2 + 9 + 4 + 8) / 5)
```

```text
%%ai openai-chat:minimax-m2
Here are some sensor readings: {readings}

My code computed an average of {average}, but what I wanted was the average of
every reading *after the first one*. Is {average} the right answer? Show the
arithmetic either way.
```

That prompt reaches the model with the real list and the real number already
substituted in, which is why it can answer instead of asking for context.

> **What to expect during the demo.** Asked to fix a cell, Jupyter AI often
> offers more than one correction — a loop and a one-liner, say — and both will
> be right. That is worth naming rather than glossing over: the assistant
> proposes, and the student still has to read the proposal and choose.

## What to take away

- The endpoint is **OpenAI-compatible**, so anything speaking that API —
  notebooks, Jupyter AI, agents, your own scripts — works against NRP with a
  `base_url` change.
- On a hub you run, the token is an environment variable *you* set once, so no
  student ever handles a credential.
- An assistant sitting inside JupyterLab changes what a stuck student does at
  2am — but only the `%%ai` magics can see their variables; the chat panel
  cannot.

::: callout Next
Next we deploy a JupyterHub of your own — the image menu, resource limits and
shared storage a course needs: [Deploy a Custom
JupyterHub](3_custom_jupyterhub.html).
:::
