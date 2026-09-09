---
title: Setup
wide: true
---

## Before the session

This training is light on setup — there is no Kubernetes tooling to install, no
`kubectl`, no grid certificate. You need three things:

1. **An NRP account.**
2. **Membership in a namespace that has LLM access enabled.**
3. **A personal LLM API token.**

Steps 1 and 2 have to be done ahead of time. Step 3 takes about thirty seconds
and is covered in the first lesson.

---

### 1. Get an NRP account

Follow [Getting Started with NRP](https://nrp.ai/documentation/userdocs/start/getting-started/).
You sign in with your institutional credentials through Authentik; access is
open to users at US academic institutions and their collaborators.

That page is the authoritative walkthrough — accounts, namespaces, and the
portal — so we won't duplicate it here.

### 2. Join a namespace with LLM access

::: important
An NRP account by itself is **not** enough to use the managed LLM service. Your
account must belong to a namespace that has **LLM access enabled** — this is a
per-namespace feature flag, not an account-level one. If you are in a namespace
but LLM access was never turned on for it, tokens will be issued but requests
will be rejected.
:::

Check which namespaces you belong to at
[https://nrp.ai/namespaces/](https://nrp.ai/namespaces/).

For this tutorial there is a **CLARIPHY namespace with LLM access already
enabled**. Message **<TODO: CLARIPHY namespace contact>** to be added to it
before the session. If you already work in another namespace that has LLM
access enabled, that works just as well — you do not need to switch.

If you are not in any namespace yet:

- **Students** — ask your research supervisor to add you to theirs.
- **Faculty / researchers** — request namespace admin status via
  [NRP contact](https://nrp.ai/contact/).

### 3. Get your LLM token

Go to [https://nrp.ai/llmtoken](https://nrp.ai/llmtoken) and click **Get LLM
token**. This is covered in detail, with a verification step, in
[Introduction — LLMs on NRP](1_intro.html#getting-access) — you can leave it
until the session starts.

---

## How to follow along

Everything past this page — the endpoint, the `openai` SDK calls, the notebooks
— is identical whether you work on the NRP training hub or your own laptop.

### NRP training hub (recommended)

A JupyterHub environment with the training materials and Python packages already
installed. Nothing to install on your laptop; you just need the account,
namespace, and token above.

::: callout Launch the workspace in JupyterHub
**[▶ Launch the workspace on the NRP training hub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fclariphy&targetpath=clariphy&urlpath=lab%2Ftree%2Fclariphy%2Fworkspace)** — signs you in at [jh-training.nrp-nautilus.io](https://jh-training.nrp-nautilus.io), pulls the tutorial workspace, and opens JupyterLab.
:::

### Your own machine (alternative)

You call NRP's managed LLM endpoint directly from a local Python environment.

::: important
The final lesson, [Agentic Physics Analysis](5_analysis.html), is meant to be
run **locally, not on the hub** — the agent installs its own toolchain and
downloads ~1 GB of data, which is slow and cramped inside a hub session. If you
plan to follow that lesson live, set up the local path below as well.
:::

<div class="details-group" data-details-group>
<button type="button" data-expand-all>Expand all</button>

<details>
<summary><strong>1. Install Python and the openai SDK</strong></summary>

Python 3.9+ is required.

```bash
python3 --version
pip install --upgrade openai
```

</details>

<details>
<summary><strong>2. Clone the training materials</strong></summary>

```bash
git clone --branch materials/clariphy --single-branch https://github.com/nrp-nautilus/nrp-training.git ~/clariphy
cd ~/clariphy/workspace
```

Already cloned? Update instead:

```bash
cd ~/clariphy && git pull && cd workspace
```

</details>

<details>
<summary><strong>3. Export your token</strong></summary>

```bash
export OPENAI_API_KEY="<your-token>"
export OPENAI_API_BASE="https://ellm.nrp-nautilus.io/v1"
```

</details>

</div>

::: important
Watch out for `~`: on your own machine it is your local home directory; in the
hub's JupyterLab terminal it is `/home/jovyan`. `cd ~/clariphy/workspace` lands
somewhere different depending on which terminal you typed it into — don't copy a
command from one context straight into the other.
:::

---

## Getting help

- **Support chat**: [NRP contact](https://nrp.ai/contact/)
- **Email**: [usersupport@nrp-nautilus.io](mailto:usersupport@nrp-nautilus.io)
- **Docs**: [Getting Started](https://nrp.ai/documentation/userdocs/start/getting-started/) ·
  [LLM docs](https://nrp.ai/documentation/userdocs/ai/llm-managed/) ·
  [Namespaces](https://nrp.ai/namespaces/)
