---
title: Setup
wide: true
---

## Prerequisites for NRP Training

Before attending the training session, please ensure you have completed the following setup steps.

## Two ways to follow along

There are two ways to run the hands-on exercises in this training:

1. **NRP USCMS Analysis Hub (recommended).** A JupyterHub-based environment with
   the training materials and Python packages already installed — nothing to
   set up on your laptop ahead of time. You'll still need your own personal
   API token (same step either way — see below) and one login step done at
   the start of the session.
2. **Your own machine (alternative).** You call NRP's managed LLM endpoint
   directly from a local Python environment. This is lighter-weight than the
   Kubernetes-heavy trainings — there's no `kubectl`/`kubelogin` to install,
   you just need Python and your own personal API token (covered in
   [Introduction — LLMs on NRP](1_intro.html)).

Everything past this setup page — the endpoint, the `openai` SDK calls, the
notebooks — is identical either way.

Jump to: [NRP USCMS Analysis Hub (recommended)](#method-1-nrp-uscms-analysis-hub-recommended) ·
[Your own machine (alternative)](#method-2-your-own-machine-alternative)

### 1. NRP Access Requirements

**Institutional Account Access**
- You must have an institutional account with NRP access via Authentik
    - You can use a CERN account or institutional account, but choose one and stick with it
- NRP access is available to users from US academic institutions or those collaborating with US institutions
- If you don't have access, see [Getting Started with NRP](https://nrp.ai/documentation/userdocs/start/getting-started/)

**Namespace Membership**
- You must be part of at least one namespace to participate in the training
- Check your namespaces at: [https://nrp.ai/namespaces/](https://nrp.ai/namespaces/)
- **Students**: Contact your research supervisor to be added to their namespace
- **Faculty/Researchers**: Request namespace admin status in [Matrix](https://nrp.ai/contact/)

::: Important
   We are using the namespace `us-cms`

   Ask Daniel or Martin to add you if you have not been added already
:::

## Method 1: NRP USCMS Analysis Hub (recommended)

You still need the account and namespace access from
[NRP Access Requirements](#1-nrp-access-requirements) above — this method just
skips installing anything on your laptop. The Python packages used in the
exercises (`openai`, etc.) are already set up on the hub image, but you'll
still need to get your own personal API token (see
[Introduction — LLMs on NRP](1_intro.html#getting-access)).

::: callout Launch the workspace in JupyterHub
**[▶ Launch the workspace on the NRP USCMS Analysis Hub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats-llm&targetpath=cms-hats-llm&urlpath=lab%2Ftree%2Fcms-hats-llm%2Fworkspace)** — signs you in at [uscms-af.nrp-nautilus.io](https://uscms-af.nrp-nautilus.io), pulls the tutorial workspace, and opens JupyterLab.
:::

That's it — no `kubectl` setup is needed for this training. [Introduction —
LLMs on NRP](1_intro.html), the first lesson, covers the endpoint, getting
your personal API token, and how to verify access.

## Method 2: Your own machine (alternative)

Complete these steps **before** the session — they can't be done live.

::: important
Also watch out for `~`: it means a different directory in each place. On
your own machine it's your local home directory; in the Analysis Hub's
JupyterLab terminal it's `/home/jovyan`. A command like `cd ~/cms-hats-llm/workspace`
lands somewhere different depending on which terminal you're actually typing
it into — don't copy a command you ran in one context straight into the
other without checking where it actually points.
:::

::: callout tl;dr
Get an NRP account and namespace access → install Python 3 and `pip install
openai` → get your personal token from [nrp.ai/llmtoken](https://nrp.ai/llmtoken)
(covered in [Introduction — LLMs on NRP](1_intro.html)) → clone the training
materials.
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

Clone the branch containing the files for this training:

```bash
git clone --branch materials/cms-hats-llm --single-branch https://github.com/nrp-nautilus/nrp-training.git ~/cms-hats-llm
cd ~/cms-hats-llm/workspace
```

If you already cloned the training materials, update your local copy instead:

```bash
cd ~/cms-hats-llm
git pull
cd workspace
```

</details>

<details>
<summary><strong>3. Get your API token</strong></summary>

Go to [https://nrp.ai/llmtoken](https://nrp.ai/llmtoken) and click **Get LLM
token**, then export it locally:

```bash
export OPENAI_API_KEY="<your-token>"
export OPENAI_API_BASE="https://ellm.nrp-nautilus.io/v1"
```

This is covered in more detail, including how to verify it works, in
[Introduction — LLMs on NRP](1_intro.html#getting-access).

</details>

</div>

## Getting Help

If you encounter issues during setup:

- **Support Chat**: [Join NRP's Support Chat](https://nrp.ai/contact/) for community support
- **Email**: [usersupport@nrp-nautilus.io](mailto:usersupport@nrp-nautilus.io)
- **Documentation**: [NRP Getting Started Guide](https://nrp.ai/documentation/userdocs/start/getting-started/)

## Additional Resources

- [NRP Portal](https://nrp.ai)
- [NRP Documentation](https://nrp.ai/documentation/)
- [Namespace Management](https://nrp.ai/namespaces/)
- [LLM-specific docs](https://nrp.ai/documentation/userdocs/ai/llm-managed/)
