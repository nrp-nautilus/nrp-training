---
title: Introduction — LLMs on NRP
teaching: 25
exercises: 0
questions:
  - What LLM resources does NRP provide for CMS researchers?
  - How do I get access?
  - What can I do with these resources?
objectives:
  - Understand what the NRP managed LLM service is and what models are available.
  - Know how to obtain an API token and reach the endpoint.
  - Identify the browser-based and programmatic entry points.
keypoints:
  - NRP runs an OpenAI-compatible managed LLM endpoint at `https://ellm.nrp-nautilus.io/v1`.
  - Access requires an NRP account and a personal token from `https://nrp.ai/llmtoken`.
  - Browser UIs (Open WebUI, LibreChat) require no token — sign in with your NRP/CERN account.
  - The same `openai` Python SDK works against NRP, commercial providers, and your own GPU pods.
---

## Overview

The National Research Platform (NRP) makes large language models available to the entire US-CMS community through a managed, OpenAI-compatible inference endpoint. You do **not** need to rent cloud credits, install model weights, or request a GPU — you just point any OpenAI-compatible tool at NRP's URL and authenticate with a personal token.

This lesson covers what is available, how to get access, and the different ways you can interact with the models.

---

## What NRP Provides

NRP exposes two complementary AI/LLM resources:

### 1. Managed LLM Service

A rotating catalog of open-weights models hosted on NRP GPUs and served behind a single OpenAI-compatible REST endpoint:

```
https://ellm.nrp-nautilus.io/v1
```

You authenticate with a **bearer token** (see [Getting Access](#getting-access) below). The endpoint speaks the OpenAI API, so any tool that supports a custom `base_url` works out of the box.

**Currently available models** (see [live list](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/)):

| Model | Parameters | Context | Tools | Vision | Notes |
|---|---|---|---|---|---|
| `qwen3` | 397B (17B active MoE) | 262K | ✓ | image, video | Largest context |
| `qwen3-small` | 27B | 262K | ✓ | image, video | |
| `gpt-oss` | 120B | 131K | ✓ | — | Strong at code |
| `gemma` | 31B | 262K | ✓ | image, video | |
| `gemma-small-e4b` | ~4B active | 128K | ✓ | image, video | Fast, good default |
| `minimax-m2` | 230B | 204K | ✓ | — | Strong reasoning |
| `qwen3-embedding` | 8B | — | embeddings only | — | Semantic search/RAG |
| `kimi` | 1T MoE (eval) | 262K | ✓ | image, video | Under evaluation |

::: callout Tip
For most tasks, start with `gemma-small-e4b` (fast) or `minimax-m2` (strong reasoning). Switch to `qwen3` when you need the largest context window.
:::

Models occasionally restart or roll over to a new version — check what's currently up at the [LLM status dashboard](https://nrp.ai/llm-status/).

### 2. Browser UIs — No Token Required

Two browser frontends are available using your NRP/CERN SSO login — no API token needed:

- **Open WebUI**: [https://nrp-openwebui.nrp-nautilus.io](https://nrp-openwebui.nrp-nautilus.io)
- **LibreChat**: [https://librechat.nrp-nautilus.io](https://librechat.nrp-nautilus.io)

These are useful for quick experiments and for sharing demos with collaborators.

### 3. Bring-Your-Own GPU

For workloads requiring full model control — custom weights, fine-tuning, custom quantization, or private inference — you can request your own GPU pod in your namespace and run any inference server (vLLM, TGI, Ollama, etc.). This is covered in other NRP training sessions.

---

## Getting Access

### Step 1: NRP Account

You need an NRP account associated with your institutional credentials (CERN SSO works for CMS members). If you don't have one yet, follow [Getting Started with NRP](https://nrp.ai/documentation/userdocs/start/getting-started/).

For this training, you should be a member of the `us-cms` namespace. Contact the training organizers if you have not been added.

### Step 2: Get an API Token

Go to [https://nrp.ai/llmtoken](https://nrp.ai/llmtoken) and click **Get LLM token**. A personal bearer token will be sent to your email or displayed on the page.

![Getting a personal LLM token from nrp.ai/llmtoken](images/LLM-tokens.png)

::: important
Treat your personal token like a password. Do not commit it to git or share it publicly. In notebooks and scripts, read it from an environment variable (`OPENAI_API_KEY`) rather than hard-coding it.
:::

On the training JupyterHub (`uscms-af.nrp-nautilus.io`), a shared workshop token is already pre-loaded as `OPENAI_API_KEY` and the endpoint URL as `OPENAI_API_BASE` — you don't need to do anything for the exercises. If you're working from your own machine, or want to swap in your personal token after the workshop, export both yourself:

```bash
export OPENAI_API_BASE="https://ellm.nrp-nautilus.io/v1"
export OPENAI_API_KEY="<paste-your-token-here>"
```

### Step 3: Verify Access

From a terminal (JupyterHub terminal or local machine with `curl`), send a real
chat request — this actually exercises the model, not just the endpoint, so
it's a more meaningful check than listing models:

```bash
curl -s -X POST "$OPENAI_API_BASE/chat/completions" \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "minimax-m2", "messages": [{"role": "user", "content": "Where is the CMS experiment located?"}]}'
```

You should get back a JSON response with a real answer buried in it (something
about CERN, near Geneva, on the LHC).

For a cleaner look, pipe it through Python to pull out just the reply text:

```bash
curl -s -X POST "$OPENAI_API_BASE/chat/completions" \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "minimax-m2", "messages": [{"role": "user", "content": "Where is the CMS experiment located?"}]}' \
  | python3 -c 'import json, sys; print(json.load(sys.stdin)["choices"][0]["message"]["content"])'
```

You can also list the full model catalog:

```bash
curl -s -H "Authorization: Bearer $OPENAI_API_KEY" \
     "$OPENAI_API_BASE/models" \
  | python3 -m json.tool | head -20
```

---

## Entry Points at a Glance

| Method | Where | When to Use |
|---|---|---|
| Open WebUI / LibreChat | Browser | Quick questions, no coding |
| Python `openai` SDK | Notebook / script | Programmatic use, RAG, embeddings |
| `curl` | Terminal | Quick smoke tests, scripting |
| Agentic tools (opencode, VS Code, Claude Code) | Terminal / IDE | AI-assisted coding and research |

---

## How to Get Help

- **NRP support chat** (Slack / Matrix): [https://nrp.ai/contact/](https://nrp.ai/contact/)
- **NRP documentation**: [https://nrp.ai/documentation/](https://nrp.ai/documentation/)
- **LLM-specific docs**: [https://nrp.ai/documentation/userdocs/ai/llm-managed/](https://nrp.ai/documentation/userdocs/ai/llm-managed/)

---

## Run the Notebooks

You can run the notebooks for this training either on the NRP US-CMS Analysis
Hub or on your own machine locally — the Analysis Hub is **recommended** since
the packages and a shared workshop token are already set up for you.

::: callout Launch the workspace in JupyterHub
**[▶ Launch the workspace in JupyterHub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats-llm&targetpath=cms-hats-llm&urlpath=lab%2Ftree%2Fcms-hats-llm%2Fworkspace)** — signs you in at uscms-af.nrp-nautilus.io, pulls the tutorial workspace, and opens JupyterLab with the notebooks for this training.
:::
