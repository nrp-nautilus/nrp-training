---
title: Agentic Workflows
teaching: 25
exercises: 0
---

::: callout Open a JupyterHub terminal
**[▶ Open a JupyterHub terminal](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=main&urlpath=lab%2Ftree%2Fnrp-training%2Ftrainings%2Fcra2%2Fworkspace)** — opens JupyterLab on jh-training.nrp-nautilus.io; use a Terminal for the `opencode` steps below.
:::

**Time:** 01:05-01:30

This section points an agentic coding CLI at the NRP managed LLM and has it
write a small program from scratch. The CLI we use is
[`opencode`](https://opencode.ai), a terminal UI similar in spirit to Claude
Code or Cursor's CLI — it plans, edits files, runs tools, and iterates. The
key teaching point is portability: anything that speaks an OpenAI-compatible
base URL works against NRP, so the agentic workflow you already use locally
runs unchanged against NRP's managed inference.

Run all commands from a JupyterHub terminal. Command blocks are formatted for
copy/paste into that terminal.

## Schedule

| Time | Topic | Outcome |
| --- | --- | --- |
| 01:05-01:10 | Setup | Install `opencode` and point it at the NRP managed LLM. |
| 01:10-01:25 | Build a chess game | Drive `opencode` through a small but real coding task. |
| 01:25-01:30 | Discussion and Q&A | Implementation strategies for under-resourced classrooms. |

## 01:05-01:10 — Setup

Install `opencode` into the JupyterHub session. The installer drops the
binary in `~/.opencode/bin/` — no `sudo` needed.

```bash
curl -fsSL https://opencode.ai/install | bash
export PATH="$HOME/.opencode/bin:$PATH"
opencode --version
```

Write an `opencode` config that uses the NRP managed LLM via the already
exported `OPENAI_API_KEY`:

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
        "minimax-m2": { "name": "MiniMax M2"  },
        "gpt-oss":    { "name": "GPT-OSS"     },
        "qwen3":      { "name": "Qwen3 397B"  },
        "gemma":      { "name": "Gemma 31B"   }
      }
    }
  },
  "model": "nrp/gpt-oss"
}
JSON
```

`gpt-oss` is the default model here because it tends to do well on code; you
can switch in-session with `Ctrl+P → Switch models`.

## 01:10-01:25 — Build a chess game

Create a clean project directory and launch the agent:

```bash
mkdir -p ~/chess && cd ~/chess
opencode
```

Inside the `opencode` TUI, press `/` to open the prompt and paste:

```text
Write a single-file Python program chess_game.py that lets two humans play
chess in the terminal. Use the python-chess library. Render the board after
every move using board.unicode(). Accept moves in SAN (e.g., "e4", "Nf3").
When the game ends, print the result. Add a top-of-file docstring. After
writing the file, add a requirements.txt pinning python-chess to 1.999, and
tell me the exact commands to install and play.
```

`opencode` plans, writes `chess_game.py` and `requirements.txt`, and prints
the run instructions. Install and play:

```bash
pip install -r requirements.txt
python chess_game.py
```

> ⚠️ **Don't name the file `chess.py`** — it shadows the `python-chess`
> package. `import chess` then re-imports your script and `chess.Board()`
> raises `AttributeError`. Models sometimes pick `chess.py` anyway because
> the prompt says "chess game"; if that happens, rename it. Models have also
> been known to invent versions like `python-chess==1.10.0` that do not
> exist on PyPI — the actual current pin is `python-chess==1.999`. The
> prompt above pre-pins to avoid the round-trip.

Try a few moves: `e4`, `e5`, `Nf3`, `Nc6`, `Bb5`, `a6`, `Bxc6`, `dxc6`.
Press `Ctrl+C` to quit.

**Switch models inside `opencode`** with `Ctrl+P → Switch models`. Try the
same prompt against `qwen3` (the largest context window) or `minimax-m2`
(strong general-purpose reasoning) — same agent, same prompt, different
inference backend.

## 01:25-01:30 — Discussion and Q&A

Key teaching points:

- Any agentic coding tool that supports an OpenAI-compatible base URL —
  `opencode`, Crush, Continue, Cursor's custom-provider field, Claude Code via
  `ANTHROPIC_BASE_URL` — works against NRP. You bring the workflow you
  already use; NRP supplies the inference.
- Agents work in a controlled directory or workspace, not against production
  systems. The user still reviews diffs and decides what to commit.
- Persistent workspaces (Coder, an SSH dev host, or even a checked-out repo
  on a long-lived JupyterHub session) make it possible to pause and resume
  agentic work across class sessions.
- Managed LLMs are the lowest-friction classroom path — students don't buy
  separate model access, and there's no token-handoff theater.

Practical classroom strategies:

- Pre-create namespaces, quotas, secrets, and any needed resource exceptions
  before class.
- Use a prepared JupyterHub image with `kubectl`, `helm`, common Python
  packages, and LLM environment variables already configured (this is what
  the training JupyterHub does).
- Reserve accelerator-heavy workflows for short, time-boxed demos.
- Give each student a unique username convention for pod and workspace
  names.
- Include cleanup commands in every activity.
- Prefer reviewable repository workflows over untracked generated files.
- Move to custom JupyterHubs when a course needs controlled enrollment,
  custom images, shared PVCs, or repeatable per-student profiles.

Reference: [client configs](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/).
