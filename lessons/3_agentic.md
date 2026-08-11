---
title: Agentic Workflows — opencode & IDE Integration
teaching: 30
exercises: 50
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

::: callout Open the notebook in JupyterHub
**[▶ Open notebook in JupyterHub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats-llm&targetpath=cms-hats-llm&urlpath=lab%2Ftree%2Fcms-hats-llm%2Fworkspace%2Fnotebooks%2F3_agentic.ipynb)** — clones the training repo and opens `workspace/notebooks/3_agentic.ipynb` on uscms-af.nrp-nautilus.io. Uses a **bash kernel**, same as the Kubernetes-focused trainings — every command below is a Shift+Enter cell.
:::

This episode is partly terminal- and IDE-driven — the install/config/setup steps
run as ordinary notebook cells, but launching `opencode` itself opens an
interactive terminal UI, and the VS Code steps happen in an IDE, so neither fits
inside a notebook cell. Those are called out individually below. You can work
from either:
- The **notebook**, for the runnable parts, plus a JupyterHub terminal (**File
  → New → Terminal**) for the interactive `opencode` steps
- Your **local machine** (macOS or Linux), running the same commands directly

All commands are the same either way.

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

Terminals in JupyterLab are **separate processes** from a notebook's own shell
— `export`s in one don't reach the other. The most common failure mode from
this: opencode returns `Forbidden` because the terminal's shell never saw
`OPENAI_API_KEY`. Persist the endpoint, your token, and opencode's `PATH` into
your shell startup files once, so **every new terminal** picks them up
automatically:

```bash
: "${OPENAI_API_BASE:=https://ellm.nrp-nautilus.io/v1}"
: "${OPENAI_API_KEY:=<paste-your-token-here>}"

for RC in ~/.bashrc ~/.bash_profile; do
    touch "$RC"
    grep -v -E 'OPENAI_API_BASE=|OPENAI_API_KEY=|\.opencode/bin|NRP managed LLM \(cms-hats-llm training\)' "$RC" > "$RC.tmp" && mv "$RC.tmp" "$RC"
    cat >> "$RC" <<EOF

# --- NRP managed LLM (cms-hats-llm training) ---
export OPENAI_API_BASE="$OPENAI_API_BASE"
export OPENAI_API_KEY="$OPENAI_API_KEY"
export PATH="\$HOME/.opencode/bin:\$PATH"
EOF
done
```

A terminal that's already open needs `source ~/.bashrc` — or just close it and
open a fresh one.

### Configure NRP as the provider

Write the config file that tells opencode to use NRP's endpoint. (See the
[full client-config reference](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/)
for opencode, VS Code, Claude Code, and more.)

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
        "minimax-m2":  { "name": "MiniMax M2"  },
        "gpt-oss":     { "name": "GPT-OSS"     },
        "qwen3":       { "name": "Qwen3 397B"  },
        "gemma-small": { "name": "Gemma 4 12B" },
        "gemma":       { "name": "Gemma 31B"   }
      }
    }
  },
  "model": "nrp/gpt-oss"
}
JSON
```

`{env:OPENAI_API_KEY}` tells opencode to read the token from your environment
at runtime. The persistence step above makes sure any terminal you open has
it — edit the placeholder in that step to your own personal token from
[https://nrp.ai/llmtoken](https://nrp.ai/llmtoken) first, on the Analysis Hub
or your own machine.

::: callout Switching models
Inside opencode, press **Ctrl+P** and select *Switch models* to change the active
model mid-session. Try the same task with `gpt-oss` (strong at code) vs `qwen3`
(largest context, good for understanding large codebases).
:::

### Exercise: Build a CMS analysis helper

opencode scopes file writes to the nearest `.git` directory, not simply your
shell's current directory — without one, it can fall back to a much wider
default and write generated files somewhere you don't expect (a
[known opencode behavior](https://github.com/anomalyco/opencode/issues/15192),
not something specific to this training). `git init` the project directory
first so it's scoped correctly, then launch opencode:

```bash
mkdir -p ~/opencode-exercise && cd ~/opencode-exercise
git init -q
export PATH="$HOME/.opencode/bin:$PATH"
opencode
```

Getting `Forbidden` responses once inside opencode? That means this shell
doesn't have `OPENAI_API_KEY` — go back and rerun the persistence step above,
then open a new terminal.

The prompt is active as soon as opencode opens — just type your task and press
Enter. (`/` opens the slash-command menu for things like `/models` or
`/clear`, not the prompt itself.) Paste the following task:

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
      "maxInputTokens": 131072,
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

Open the `opencode-exercise` directory you created in Part 1 in VS Code. In the
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
| **Claude Code** | `"ANTHROPIC_BASE_URL": "https://ellm.nrp-nautilus.io/anthropic"` in `~/.claude/settings.json` |
| **Continue** (VS Code/JetBrains) | Set `apiBase` in `~/.continue/config.json` |
| **Cursor** | Settings → Models → Add Custom Provider |
| **LangChain / LlamaIndex** | Pass `base_url` to `ChatOpenAI` or `OpenAI` constructor |
| **any `curl` / `httpx` script** | Replace `api.openai.com/v1` with `ellm.nrp-nautilus.io/v1` |

::: callout CMS-specific example: Claude Code with NRP
Claude Code speaks the Anthropic API, not the OpenAI one — so it uses NRP's
separate **Anthropic-compatible** endpoint at `/anthropic` (not `/v1`), and
reads its configuration from `~/.claude/settings.json` rather than plain
environment variables:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://ellm.nrp-nautilus.io/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "<your-llm-token>",
    "ANTHROPIC_MODEL": "qwen3"
  }
}
```

Note that not all NRP models route cleanly through the Anthropic-compatible
endpoint, and Anthropic-specific features (notably the built-in web-search
tool) cannot be produced by open-weights models. [Agentic Physics
Analysis](5_analysis.html) uses exactly this setup to run a full analysis
framework on NRP.
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

**Next:** [Build a Simple Agent](4_agent.html) — open the hood and build the
tool-calling loop that powers these tools yourself, in ~30 lines of Python.

---

## References

- [NRP managed LLM documentation](https://nrp.ai/documentation/userdocs/ai/llm-managed/)
- [Available models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/)
- [Client configs (opencode, VS Code, Claude Code, …)](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/)
- [Get your LLM token](https://nrp.ai/llmtoken)
- [opencode documentation](https://opencode.ai)
