---
title: Agentic Workflows — opencode & IDE Integration
teaching: 30
exercises: 20
questions:
  - What is an agentic coding tool and how is it different from chat?
  - How do I configure opencode to use NRP's managed LLMs?
  - How can I use NRP models inside VS Code, Claude Code, or other tools?
objectives:
  - Install opencode and write an NRP provider config.
  - Use opencode to complete a real coding task with an NRP-hosted model.
  - Connect VS Code Copilot Chat to NRP's managed LLM endpoint.
  - Know which other agentic tools support a custom OpenAI-compatible base URL.
keypoints:
  - Any tool that accepts a custom OpenAI-compatible `base_url` works against NRP.
  - opencode is a terminal agentic coding CLI — plan, edit, run, iterate.
  - VS Code connects to NRP via Chat→Manage Language Models→Custom Endpoint.
  - The NRP endpoint, token, and model list are the same regardless of which client you use.
---

In Part 2 you **called** NRP's managed LLMs from Python. Now you will point an
**agentic coding tool** at the same endpoint and have it plan, write, and run code
autonomously on your behalf.

The key teaching point is **portability**: anything that speaks an OpenAI-compatible
`base_url` works against NRP, so the agentic workflow you already use locally
runs unchanged against NRP's managed inference — no API key handoff theater, no
per-user billing.

::: callout Where to run these exercises
You can work from either:
- A **JupyterHub terminal** on [jupyterhub-west.nrp-nautilus.io](https://jupyterhub-west.nrp-nautilus.io) (open a terminal from the Launcher)
- Your **local machine** (macOS or Linux)

All commands are the same either way.
:::

---

## Part 1: opencode

[`opencode`](https://opencode.ai) is an open-source terminal UI agentic coding
assistant — similar in spirit to Claude Code or Cursor's CLI. It reads your
project files, plans changes, edits code, and iterates.

### Install

```bash
curl -fsSL https://opencode.ai/install | bash
export PATH="$HOME/.opencode/bin:$PATH"
opencode --version
```

Add the `export` to your `~/.bashrc` or `~/.bash_profile` to make it permanent.

### Configure NRP as the provider

Write the config file that tells opencode to use NRP's endpoint:

```bash
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
        "minimax-m2":      { "name": "MiniMax M2"        },
        "gpt-oss":         { "name": "GPT-OSS"           },
        "qwen3":           { "name": "Qwen3 397B"        },
        "gemma-small-e4b": { "name": "Gemma 3n E4B"      },
        "gemma":           { "name": "Gemma 31B"         }
      }
    }
  },
  "model": "nrp/gpt-oss"
}
JSON
```

`{env:OPENAI_API_KEY}` tells opencode to read the token from your environment
at runtime — the shared workshop token is already exported on the JupyterHub, and
on your local machine you can export your personal token from
[https://nrp.ai/llmtoken](https://nrp.ai/llmtoken).

::: callout Switching models
Inside opencode, press **Ctrl+P** and select *Switch models* to change the active
model mid-session. Try the same task with `gpt-oss` (strong at code) vs `qwen3`
(largest context, good for understanding large codebases).
:::

### Exercise: Build a CMS analysis helper

Create a fresh project directory and launch opencode:

```bash
mkdir -p ~/cms-llm-exercise && cd ~/cms-llm-exercise
opencode
```

Inside the opencode TUI, press `/` to open the prompt. Paste the following task:

```text
Write a Python script cms_nano_summary.py that uses the uproot library to open
a CMS NanoAOD ROOT file (path given as a command-line argument) and prints a
summary table of all the TTree branches under the "Events" tree, grouped by
collection (e.g., all "Muon_*" branches together, all "Jet_*" branches
together). For each group print the branch name, type, and a one-line
description if available. At the end print the total number of events. Add a
proper argparse interface and a top-level docstring. Also add a
requirements.txt pinning uproot>=5 and tabulate.
```

opencode will plan the implementation, write the files, and tell you how to run
them. Install and test:

```bash
pip install -r requirements.txt
# For the exercise, point to any NanoAOD file you have access to, or use:
python cms_nano_summary.py --help
```

::: important
If opencode generates a file named `uproot.py`, rename it — it would shadow the
`uproot` package on import.
:::

**Things to try:**
- Once the script is written, ask opencode to add a `--filter` argument that
  limits output to a specific collection (e.g., `--filter Muon`).
- Switch to `qwen3` and ask it to add unit tests with `pytest`.

---

## Part 2: VS Code Integration

VS Code can use NRP-managed LLMs directly inside **Copilot Chat** via a custom
endpoint, with no Copilot subscription needed for NRP models.

::: important
You need VS Code with the **GitHub Copilot** extension installed. The extension
itself is free to install; you are substituting the NRP endpoint for the default
Copilot backend.
:::

### Setup

1. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
2. Run **Chat: Manage Language Models**.
3. Click **Add Models**.
4. Choose **Custom Endpoint**.
5. Enter the endpoint URL: `https://ellm.nrp-nautilus.io/v1/chat/completions`
6. You will be prompted for your API token (stored securely by VS Code).

VS Code will generate a configuration similar to:

```json
{
  "name": "NRP",
  "vendor": "customendpoint",
  "apiKey": "${input:chat.lm.secret.NRP}",
  "apiType": "chat-completions",
  "models": [
    {
      "id": "qwen3",
      "name": "qwen3",
      "url": "https://ellm.nrp-nautilus.io/v1/chat/completions",
      "toolCalling": true,
      "vision": true,
      "maxInputTokens": 1010000,
      "maxOutputTokens": 100000
    },
    {
      "id": "gpt-oss",
      "name": "gpt-oss",
      "url": "https://ellm.nrp-nautilus.io/v1/chat/completions",
      "toolCalling": true,
      "vision": false,
      "maxInputTokens": 524288,
      "maxOutputTokens": 100000
    },
    {
      "id": "minimax-m2",
      "name": "minimax-m2",
      "url": "https://ellm.nrp-nautilus.io/v1/chat/completions",
      "toolCalling": true,
      "vision": false,
      "maxInputTokens": 204800,
      "maxOutputTokens": 100000
    }
  ]
}
```

Full setup guide: [NRP client configs — VS Code](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/#vs-code).

### Exercise

Open the `cms-llm-exercise` directory you created in Part 1 in VS Code. In the
Copilot Chat panel, select an NRP model and ask:

```text
Review cms_nano_summary.py. Are there any edge cases not handled for NanoAOD
files with empty collections or jagged arrays? Suggest improvements.
```

---

## Part 3: Other Agentic Tools

The same NRP endpoint works with any tool that supports a custom OpenAI-compatible URL. Here is a quick reference:

| Tool | How to point at NRP |
|---|---|
| **opencode** | `"baseURL": "https://ellm.nrp-nautilus.io/v1"` in `~/.config/opencode/opencode.json` |
| **VS Code Copilot Chat** | Chat: Manage Language Models → Custom Endpoint (see Part 2) |
| **Claude Code** | `export ANTHROPIC_BASE_URL=https://ellm.nrp-nautilus.io/v1` (OpenAI-compat mode) |
| **Continue** (VS Code/JetBrains) | Set `apiBase` in `~/.continue/config.json` |
| **Cursor** | Settings → Models → Add Custom Provider |
| **LangChain / LlamaIndex** | Pass `base_url` to `ChatOpenAI` or `OpenAI` constructor |
| **any `curl` / `httpx` script** | Replace `api.openai.com/v1` with `ellm.nrp-nautilus.io/v1` |

::: callout CMS-specific example: Claude Code with NRP
If you use Claude Code for CMS analysis work, you can configure it to route
requests through NRP's open-weights models instead of Anthropic's API:

```bash
export ANTHROPIC_BASE_URL=https://ellm.nrp-nautilus.io/v1
export ANTHROPIC_API_KEY=$OPENAI_API_KEY
claude --model gpt-oss
```

Note: NRP models are OpenAI-compatible, not Anthropic-compatible — some
Claude-specific features (extended thinking, tool-use schemas) may behave
differently. Test your workflow and fall back to the default endpoint when needed.
:::

---

## Discussion

Key takeaways from this session:

- **Portability is the point.** The same NRP endpoint powers your notebook, your
  terminal agent, your IDE, and your analysis scripts. You bring the workflow;
  NRP supplies the inference.
- **No per-user billing.** NRP's managed LLM is a community resource. Members of
  the `us-cms` namespace access it with a personal token — no usage metering
  against your grant.
- **Models live close to your data.** NRP GPUs are co-located with CMS data
  stores at US sites. For latency-sensitive agentic loops processing large files,
  running on NRP can be faster than routing through a commercial cloud.
- **Agents work in controlled directories.** An agent edits files in the project
  directory you open it in — it does not touch production systems. You review
  diffs before committing.

**Coming soon:** a worked CMS example using opencode to look up a CMS publication,
extract the relevant formula, and generate analysis code that implements it. Stay
tuned.

---

## References

- [NRP managed LLM documentation](https://nrp.ai/documentation/userdocs/ai/llm-managed/)
- [Available models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/)
- [Client configs (opencode, VS Code, Claude Code, …)](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/)
- [Get your LLM token](https://nrp.ai/llmtoken)
- [opencode documentation](https://opencode.ai)
