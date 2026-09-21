---
title: Launch the Agent — JFC Physics Analysis on NRP
teaching: 5
exercises: 10
questions:
  - Can an agent run a complete physics analysis, not just write a script?
objectives:
  - Launch the JFC H→4ℓ analysis on CMS Open Data, running on NRP models.
  - Leave the agent running while you work through the rest of the tutorial.
keypoints:
  - One setup script installs the tools, points Claude Code at NRP, and stages the data — without touching your own settings.
  - The agent runs unattended; the final lesson looks at what it produced and at how the setup worked.
---

::: important Run this on your own laptop — and start it now
This exercise runs in a **terminal on your own machine** (macOS, Linux or Windows), not on
JupyterHub. The agent needs tens of minutes of unattended time, so you **start it now** and
leave it working while you do [Chat with LLMs](2_chat.html),
[Agentic Workflows](3_agentic.html) and [Build a Simple Agent](4_agent.html).

In the final lesson, [Check In on the Agent](5_analysis.html), we look at what it produced —
and walk through what the setup did to get it running.
:::

## What you're launching

**[JFC](https://github.com/jfc-mit/jfc)** ("Just Furnish Context") is a framework from Eric
Moreno, Sam Bright-Thonney, Andrzej Novak, Dolores Garcia, Yiyang Zhao and Philip Harris that runs a *complete*
HEP analysis — strategy, event selection, statistical inference, and a 50–100 page analysis
note — from a single physics prompt. An **orchestrator** that writes no code itself spawns
**executor** and **reviewer** subagents across seven phases, with a human gate before
unblinding.

```
┌──────────────────────────────────────────────────────────────┐
│                       ORCHESTRATOR                            │
│   Never writes code. Holds: prompt, summaries, verdicts only  │
└─────┬────────────────────────────────────────────────────────┘
      ▼
  Phase 1 ──▶ Phase 2 ──▶ Phase 3 ──▶ Phase 4a ──▶ Phase 4b ──▶ Phase 4c ──▶ Phase 5
  Strategy    Explore     Selection    Expected     10% valid.   Full data    Document
  (2-bot)     (self)      (1-bot)      (1bot+bib)   (+HUMAN)     (1-bot)      (2-bot)
```

::: callout Introduction to JFC — Andrzej Novak
Andrzej Novak (MIT), one of the authors of JFC, introduces the framework at this point in the
session. If you haven't run the setup script yet, start [Step 1](#step-1-run-the-setup-script)
before the introduction begins, so the download runs while you listen.
:::

Today's exercise follows Phil Harris's
[h4l_agent_test](https://github.com/violatingcp/h4l_agent_test) tutorial: a **H→4ℓ mass
measurement on CMS Open Data**, reproducing the spirit of JHEP 11 (2017) 047. It uses JFC's
*fast path* — the physics prompt and reference papers, without the full specification — so the
agent can get to a result within the session. JFC drives Claude Code, which we point at
open-weights models on **NRP GPUs**, using your NRP token: no Anthropic subscription needed.

This is a research-grade experiment, not a guaranteed-success demo — JFC was built for Claude
Opus, and today it runs on open-weights models. Expect rough edges; where it struggles is part
of what we discuss at the end.

**You need:** your NRP token from [nrp.ai/llmtoken](https://nrp.ai/llmtoken) (see
[Lesson 1](1_intro.html#getting-access)), ~2 GB of free disk, 8 GB of RAM, and an internet
connection. No GPU — inference runs on NRP.

---

## Step 1: Run the setup script

The script installs Claude Code and Pixi, points Claude Code at NRP, downloads the JFC
repositories and ~860 MiB of CMS Open Data samples, and stages the analysis. It asks for your
NRP token, checks it before downloading anything, and ends with **All set**.

It **does not modify your own settings** — not `~/.claude`, not your shell startup files;
everything goes into `~/jfc-exercise`. If anything is interrupted, just run it again.

### macOS, Linux, or WSL

```bash
curl -fsSLO https://raw.githubusercontent.com/nrp-nautilus/nrp-training/materials/clariphy/workspace/jfc_setup.sh
bash jfc_setup.sh
```

### Windows

In **PowerShell** — no Administrator rights needed:

```powershell
curl.exe -fsSLO https://raw.githubusercontent.com/nrp-nautilus/nrp-training/materials/clariphy/workspace/jfc_setup.ps1
powershell -ExecutionPolicy Bypass -File .\jfc_setup.ps1
```

Installing [Git for Windows](https://git-scm.com/downloads/win) first is recommended. If you
have WSL, running the bash script inside WSL is the better-trodden path.

::: callout Run it before the session if you can
The samples are ~860 MiB. On shared conference Wi-Fi, with a room full of people downloading
them at once, that can be slow. If you already have your token, run the script ahead of time —
at the session you then only need Step 2.
:::

---

## Step 2: Launch the agent

When the script prints **All set**, open a **fresh terminal** (macOS, Linux or WSL) and run:

```bash
source ~/jfc-exercise/nrp-env.sh
cd "$ROGUE"
cat prompt.md | claude --permission-mode auto
```

On **Windows**, double-click `start-agent.cmd` in `%USERPROFILE%\jfc-exercise` instead.

Answer any first-run questions Claude Code asks; after that it works on the analysis by itself.

::: important Keep it running
The agent needs its terminal and your network connection for the rest of the session. Don't
close the terminal, keep the laptop lid open, and plug in if you can. On macOS, running
`caffeinate -i` in another terminal stops the machine idle-sleeping until you press Ctrl+C.
:::

::: callout If something goes wrong
- **The script stops with ❌** — it prints what to fix. Fix it and run the script again;
  finished steps are skipped.
- **Claude Code exits with `Content block is not a text block`** — that model isn't getting
  along with NRP's Anthropic bridge. Switch models and launch again:
  `NRP_MODEL=glm-5 bash jfc_setup.sh` (Windows: `$env:NRP_MODEL = "glm-5"`, then re-run
  `jfc_setup.ps1`), then repeat Step 2.
- **Still stuck?** Ask an instructor, or run the exercise on JupyterHub instead:

**[▶ Open the JFC backup notebook in JupyterHub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fclariphy&targetpath=clariphy&urlpath=lab%2Ftree%2Fclariphy%2Fworkspace%2Fnotebooks%2F5_analysis.ipynb)** — the same setup on jh-training.nrp-nautilus.io, run cell by cell; the agent is launched from a JupyterLab terminal.
:::

---

## Leave it running

That's it. Leave the agent working and move on to [Chat with LLMs](2_chat.html). Glance at its
terminal between lessons — if it has stopped to ask a question, answer it and let it continue.

At the end, [Check In on the Agent](5_analysis.html) looks at what it produced, and walks
through every step the setup took to get it running.
