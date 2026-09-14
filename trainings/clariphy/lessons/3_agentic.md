---
title: Agentic Workflows — opencode & IDE Integration
teaching: 15
exercises: 30
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
  - A project-level `opencode.json` points opencode at NRP without touching your own opencode setup.
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
**[▶ Open notebook in JupyterHub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fclariphy&targetpath=clariphy&urlpath=lab%2Ftree%2Fclariphy%2Fworkspace%2Fnotebooks%2F3_agentic.ipynb)** — clones the training repo and opens `workspace/notebooks/3_agentic.ipynb` on jh-training.nrp-nautilus.io. Uses a **bash kernel**, same as the Kubernetes-focused trainings — every command below is a Shift+Enter cell.
:::

This episode is partly terminal- and IDE-driven — the install/config/setup steps
run as ordinary notebook cells, but launching `opencode` itself opens an
interactive terminal UI, and the VS Code steps happen in an IDE, so neither fits
inside a notebook cell. Those are called out individually below. You can work
from either:
- The **notebook**, for the runnable parts, plus a JupyterHub terminal (**File
  → New → Terminal**) for the interactive `opencode` steps
- Your **own machine** (macOS, Linux or WSL), running the same commands in a
  terminal. On native Windows, use the training hub — opencode itself recommends
  WSL there.

The commands are bash and work unchanged in both places. They don't edit your
shell startup files or any opencode configuration you already have: everything
the exercise needs lives in a new `~/opencode-exercise` folder, plus one small
file holding your token.

---

## Part 1: opencode

[`opencode`](https://opencode.ai) is an open-source terminal UI agentic coding
assistant — similar in spirit to Claude Code or Cursor's CLI. It reads your
project files, plans changes, edits code, and iterates.

### Install

If you already have opencode (for example from Homebrew), this keeps your copy;
otherwise it runs the official installer, which puts `opencode` in
`~/.opencode/bin`:

```bash
export PATH="$HOME/.opencode/bin:$PATH"
command -v opencode >/dev/null || curl -fsSL https://opencode.ai/install | bash
opencode --version
```

### Create the exercise folder

opencode scopes file writes to the nearest `.git` directory, not simply your
shell's current directory — without one, it can fall back to a much wider
default and write generated files somewhere you don't expect (a
[known opencode behavior](https://github.com/anomalyco/opencode/issues/15192),
not something specific to this training). So the exercise gets its own fresh
folder, turned into a git project:

```bash
mkdir -p ~/opencode-exercise && cd ~/opencode-exercise
git init -q
pwd
```

### Configure NRP as the provider

opencode needs two things: where NRP's endpoint is, and your token.

Terminals are **separate processes** — a token you `export` in one (or in the
notebook) doesn't reach the next, and the usual workaround of adding it to
`~/.bashrc` edits your shell setup. Instead, save the token once to a private
file in your home directory. It sits outside the project, so it never ends up
in the agent's working files or in git:

```bash
# Paste your personal token from https://nrp.ai/llmtoken if OPENAI_API_KEY isn't already set.
: "${OPENAI_API_KEY:=<paste-your-token-here>}"

if [[ "$OPENAI_API_KEY" == "<"* ]]; then
    echo "Replace <paste-your-token-here> with your token, then run this again."
else
    touch ~/.nrp-llm-token && chmod 600 ~/.nrp-llm-token
    printf '%s' "$OPENAI_API_KEY" > ~/.nrp-llm-token
    echo "Token saved to ~/.nrp-llm-token (readable only by you)."
fi
```

Then write the NRP provider as a **project config** — an `opencode.json` inside the
exercise folder. opencode merges it with any global config you have, with the
project taking priority, so your own `~/.config/opencode` settings are left alone
and this only applies inside `~/opencode-exercise`. (See the
[full client-config reference](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/)
for opencode, VS Code, Claude Code, and more.)

```bash
cd ~/opencode-exercise
cat > opencode.json <<'JSON'
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "nrp": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "NRP LLM",
      "options": {
        "baseURL": "https://ellm.nrp-nautilus.io/v1",
        "apiKey": "{file:~/.nrp-llm-token}"
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
cat opencode.json
```

`{file:~/.nrp-llm-token}` tells opencode to read your token from that file when it
starts — so opencode works in **any** terminal, with nothing to export first.

::: callout Switching models
Inside opencode, press **Ctrl+P** and select *Switch models* to change the active
model mid-session. Try the same task with `gpt-oss` (strong at code) vs `qwen3`
(largest context, good for understanding large codebases).
:::

### Exercise: Build a CMS analysis helper

🖥️ `opencode` is an interactive terminal UI — on the training hub, launch it from a
JupyterLab terminal (**File → New → Terminal**), not the notebook:

```bash
cd ~/opencode-exercise
export PATH="$HOME/.opencode/bin:$PATH"
opencode
```

Getting `Forbidden` or `401` responses once inside opencode? It couldn't read a
valid token — re-run the token step above (with the placeholder replaced), then
restart opencode.

The prompt is active as soon as opencode opens — just type your task and press
Enter. (`/` opens the slash-command menu for things like `/models` or
`/clear`, not the prompt itself.) Paste the following task:

```text
Write a Python script cms_nano_summary.py that uses the uproot library to open
a CMS NanoAOD ROOT file and print a summary of its contents.

The input is a real CMS NanoAOD file whose path is given as a command-line
argument. It has an "Events" TTree using the standard NanoAOD flat-branch
convention: collections appear as "<Collection>_<variable>" (Muon_pt,
Muon_eta, Jet_pt, ...), with an "n<Collection>" counter branch giving the
per-event multiplicity of each collection.

The script should:
- Group the branches by collection (all "Muon_*" together, all "Jet_*"
  together, and so on), listing anything that isn't part of a collection
  under "Event-level".
- For each branch print its name, type, and title/description if uproot
  exposes one.
- Print the total number of events at the end.
- Have a proper argparse interface and a top-level docstring.

Also write a requirements.txt pinning uproot>=5 and tabulate.
```

opencode will plan the implementation, write the files, and tell you how to run
them. Install the script's requirements into a **virtual environment** inside the
project — its own private Python, so the install can't clash with (or be refused
by) your system Python. Calling `.venv/bin/python` uses that environment directly,
so there is nothing to activate:

```bash
cd ~/opencode-exercise
python3 -m venv .venv
grep -qsxF '.venv/' .gitignore || echo '.venv/' >> .gitignore   # keep it out of git and the agent's searches
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python cms_nano_summary.py --help
```

### Test it on a real NanoAOD file

`--help` only proves the script parses. To actually exercise it you need a
NanoAOD file, and there are two ways to get one.

**Option A — copy from CERN EOS with `xrdcp`.** This needs `xrdcp` plus a valid
grid proxy, which the NRP training hub image does not ship — it is the path you
would take on a CMS analysis facility, where `grid-cert-import` and
`grid-proxy-init` are available (covered in [CMS Data on
NRP](https://training.nrp-nautilus.io/cms-hats/5_cms_data.html) in the companion
training). `xrdcp` looks for the proxy at `~/.globus/x509up` by default, so
nothing extra to set. **On the training hub, use Option B instead.**

🖥️ **Terminal step** — `xrdcp` needs a real terminal, not a notebook cell:

```bash
cd ~/opencode-exercise
xrdcp -f root://eoscms.cern.ch//eos/cms/store/group/cmst3/group/l1tr/maglowac/AD_HLT_PF/QCD_Bin-Pt-15to7000_TuneCP5_13p6TeV_pythia8/re-emul_Run3Winter25MiniAOD-FEVTOUTPUT_142X_v7-v1/251124_134438/0000/nanoout_1.root nanoout_1.root
```

**Option B — no grid proxy? ← use this one.** The same file is mirrored on NRP
S3 and needs no credentials or extra tooling, so it works everywhere including
the training hub.

```bash
cd ~/opencode-exercise

# Option B: pull the same NanoAOD file from NRP S3 — no proxy, no credentials (~20 MB).
# Skipped if you already copied it with xrdcp above; a failed download is cleaned up.
[ -f nanoout_1.root ] || curl -fL -o nanoout_1.root \
  "https://s3-west.nrp-nautilus.io/transfer-bucket/QCD_Bin-Pt-15to7000_TuneCP5_13p6TeV_pythia8_nano.root" \
  || rm -f nanoout_1.root

ls -lh nanoout_1.root
```

```bash
cd ~/opencode-exercise
.venv/bin/python cms_nano_summary.py nanoout_1.root | head -40
```

This is the real test of the agent's work: does the script actually survive
contact with a NanoAOD file? Common ways a first attempt falls over — worth
feeding straight back to opencode rather than fixing by hand:

- Treating every branch as flat when the jagged collection branches need
  `n<Collection>` to interpret.
- Crashing on branches with no title instead of printing a blank description.
- Assuming a fixed set of collections rather than discovering them from the file.

If it fails, paste the traceback into opencode and let it debug — watching an
agent iterate on a real error is the point of the exercise.

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
| **opencode** | `"baseURL": "https://ellm.nrp-nautilus.io/v1"` in an `opencode.json` — in a project folder (as in Part 1), or in `~/.config/opencode/` for every project |
| **VS Code Copilot Chat** | Chat: Manage Language Models → Custom Endpoint (see Part 2) |
| **Claude Code** | `"ANTHROPIC_BASE_URL": "https://ellm.nrp-nautilus.io/anthropic"` in `~/.claude/settings.json` |
| **Continue** (VS Code/JetBrains) | Set `apiBase` in `~/.continue/config.json` |
| **Cursor** | Settings → Models → Add Custom Provider |
| **LangChain / LlamaIndex** | Pass `base_url` to `ChatOpenAI` or `OpenAI` constructor |
| **any `curl` / `httpx` script** | Replace `api.openai.com/v1` with `ellm.nrp-nautilus.io/v1` |

::: callout Claude Code with NRP
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
tool) cannot be produced by open-weights models. The JFC agent you
[launched at the start](1b_jfc_launch.html) uses exactly this setup to run a
full analysis framework on NRP — with the settings kept in a workshop-only
`CLAUDE_CONFIG_DIR`, so your own `~/.claude/settings.json` is left untouched.
:::

---

## Discussion

Key takeaways from this session:

- **Portability is the point.** The same NRP endpoint powers your notebook, your
  terminal agent, your IDE, and your analysis scripts. You bring the workflow;
  NRP supplies the inference.
- **No per-user billing.** NRP's managed LLM is a community resource. Members of
  any namespace with LLM access enabled reach it with a personal token — no usage
  metering against your grant.
- **Models live close to your data.** NRP GPUs sit alongside NRP's storage at US
  sites. For latency-sensitive agentic loops processing large files, running on
  NRP can be faster than routing through a commercial cloud.
- **Agents work in controlled directories.** An agent edits files in the project
  directory you open it in — it does not touch production systems. You review
  diffs before committing.

**Next:** [Build a Simple Agent](4_agent.html) — open the hood and build the
tool-calling loop that powers these tools yourself, in ~30 lines of Python.

---

## References

- [NRP managed LLM documentation](https://nrp.ai/documentation/userdocs/ai/llm-managed/)
- [Available models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/)
- [Client configs (opencode, VS Code, Claude Code, …)](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/)
- [Get your LLM token](https://nrp.ai/llmtoken)
- [opencode documentation](https://opencode.ai) · [opencode config files and `{file:…}` variables](https://opencode.ai/docs/config/)
