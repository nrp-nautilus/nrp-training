---
title: Setup
wide: true
---

## Before the session

Setup is deliberately minimal — there is no Kubernetes tooling to install, no
`kubectl`, no grid certificate. Just two things need to happen ahead of time:

### 1. Log into nrp.ai

Go to [nrp.ai](https://nrp.ai/) and sign in with your institutional credentials
through Authentik. Access is open to users at US academic institutions and their
collaborators.

If anything is unclear, [Getting Started with NRP](https://nrp.ai/documentation/userdocs/start/getting-started/)
is the authoritative walkthrough — accounts, namespaces, and the portal.

### 2. Ask to be added to the CLARIPHY namespace

::: important
An NRP account by itself is **not** enough to use the managed LLM service. Your
account must belong to a namespace that has **LLM access enabled** — a
per-namespace feature flag, not an account-level one.
:::

The **CLARIPHY namespace already has LLM access enabled**. Message
Daniel Diaz to be added to it before the session. You
can see which namespaces you belong to at
[https://nrp.ai/namespaces/](https://nrp.ai/namespaces/).

If you already work in another namespace that has LLM access enabled, that works
just as well — you do not need to switch.

---

That's it for advance setup. Your personal LLM API token is the third thing you
need, but it takes about thirty seconds to get and is covered — with a
verification step — at the start of
[Introduction — LLMs on NRP](1_intro.html#getting-access). Leave it until the
session starts.

---

## How to follow along

The tutorial is built around the **NRP training hub**: everyone gets the same
JupyterLab environment, with the materials and Python packages already installed,
so nothing depends on what is on your laptop. The one exception is the JFC agent
exercise, which runs on your own machine through a setup script.

### NRP training hub (recommended)

A JupyterHub environment with the training materials and Python packages already
installed. Nothing to install on your laptop; you just need the account,
namespace, and token above.

::: callout Launch the workspace in JupyterHub
**[▶ Launch the workspace on the NRP training hub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fclariphy&targetpath=clariphy&urlpath=lab%2Ftree%2Fclariphy%2Fworkspace)** — signs you in at [jh-training.nrp-nautilus.io](https://jh-training.nrp-nautilus.io), pulls the tutorial workspace, and opens JupyterLab.
:::

### Your own machine (alternative)

You can also run the notebooks on your own laptop, calling NRP's managed LLM
endpoint from a local Python environment.

::: important
The JFC agentic-analysis exercise — which you [launch](1b_jfc_launch.html) right
after the introduction and [check on](5_analysis.html) at the end — is meant to be
run **locally, not on the hub**: the agent installs its own toolchain and downloads
~1 GB of data, which is slow and cramped inside a hub session. A setup script does
the whole install for you on macOS, Linux or Windows. If you can, grab your token
from [nrp.ai/llmtoken](https://nrp.ai/llmtoken) and
[run the script before the session](1b_jfc_launch.html#step-1-run-the-setup-script),
so the download isn't competing for conference Wi-Fi. If it won't work on your
machine, the lesson links a JupyterHub backup.
:::

<div class="details-group" data-details-group>
<button type="button" data-expand-all>Expand all</button>

<details>
<summary><strong>1. Get the training materials</strong></summary>

Open a terminal in the folder where you keep your projects, then:

```bash
git clone --branch materials/clariphy --single-branch https://github.com/nrp-nautilus/nrp-training.git clariphy
cd clariphy
```

This creates the **tutorial folder**, `clariphy`. The next steps all run from inside it.

- **No git?** Download the
  [materials as a ZIP](https://github.com/nrp-nautilus/nrp-training/archive/refs/heads/materials/clariphy.zip),
  unzip it, rename the `nrp-training-materials-clariphy` folder to `clariphy`, and
  open a terminal inside it.
- **Already have it?** Run `git pull` from inside the tutorial folder to update.

</details>

<details>
<summary><strong>2. Create a Python environment</strong></summary>

You need Python 3.9 or newer. Install the tutorial's packages into a **virtual
environment** — a `.venv` folder inside the tutorial folder — rather than into
your system Python. Many macOS and Linux systems now refuse a plain
`pip install` for exactly that reason, and a virtual environment can't clash with
your other projects. Deleting `.venv` undoes it.

**macOS, Linux, WSL**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r workspace/requirements.txt
```

**Windows (PowerShell)**

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r workspace\requirements.txt
```

If Windows says `py` is not recognized, use `python` instead.

</details>

<details>
<summary><strong>3. Open the notebooks</strong></summary>

From the tutorial folder:

**macOS, Linux, WSL**

```bash
source .venv/bin/activate
python -m jupyter lab
```

**Windows (PowerShell)**

```powershell
.venv\Scripts\python -m jupyter lab
```

In JupyterLab, open `workspace/notebooks/`. [Chat with LLMs](2_chat.html) and
[Build a Simple Agent](4_agent.html) run as they are. The
[Agentic Workflows](3_agentic.html) notebook uses the bash kernel the hub provides;
on your own machine, run the commands from its lesson page in a terminal instead
(macOS, Linux or WSL).

</details>

<details>
<summary><strong>4. Set your token</strong></summary>

The notebooks ask you to paste your token into their first cell. For commands you
run in a terminal, set it in that terminal — it lasts until you close it:

**macOS, Linux, WSL**

```bash
export OPENAI_API_KEY="<paste-your-token-here>"
export OPENAI_API_BASE="https://ellm.nrp-nautilus.io/v1"
```

**Windows (PowerShell)**

```powershell
$env:OPENAI_API_KEY = "<paste-your-token-here>"
$env:OPENAI_API_BASE = "https://ellm.nrp-nautilus.io/v1"
```

Replace the placeholder with your token from [nrp.ai/llmtoken](https://nrp.ai/llmtoken).
Don't add it to your shell startup files, and don't commit it anywhere.

</details>

</div>

::: callout How to read the commands on this site
- **Shell commands are bash.** They run as they are in a JupyterHub terminal, and in a
  macOS, Linux or WSL terminal. Where Windows PowerShell needs something different, it is
  shown separately.
- **Commands say where they run.** The *tutorial folder* is `clariphy` — `~/clariphy` on
  the hub, wherever you put it on your own machine. Exercises create their own new folders
  in your home directory (`~/opencode-exercise`, `~/jfc-exercise`), and their commands `cd`
  there first, so it doesn't matter where your terminal started.
- **Nothing edits your existing setup.** No command changes your shell startup files, the
  configuration of tools you already use, or your system Python.
- **Re-running is safe.** If a step fails partway, fix the problem and run it again.
- **Replace placeholders** such as `<paste-your-token-here>` before you run a command.
:::

---

## Getting help

- **Support chat**: [NRP contact](https://nrp.ai/contact/)
- **Email**: [usersupport@nrp-nautilus.io](mailto:usersupport@nrp-nautilus.io)
- **Docs**: [Getting Started](https://nrp.ai/documentation/userdocs/start/getting-started/) ·
  [LLM docs](https://nrp.ai/documentation/userdocs/ai/llm-managed/) ·
  [Namespaces](https://nrp.ai/namespaces/)
