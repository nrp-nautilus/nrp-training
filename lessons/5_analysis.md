---
title: Check In on the Agent — How JFC Ran, and What It Found
teaching: 5
exercises: 5
questions:
  - Did the agent you launched at the start produce a credible physics result?
  - What did the setup actually do to run Claude Code on NRP?
  - What does a production agentic research framework actually encode?
objectives:
  - Explain how Claude Code was pointed at NRP's Anthropic-compatible endpoint without touching your own settings.
  - Reproduce each setup step by hand.
  - Judge an agent's analysis output against a known physics target.
  - Identify what the JFC specification adds beyond a bare agent loop.
keypoints:
  - NRP speaks the Anthropic API at `/anthropic`, so Claude Code runs on NRP models with no subscription.
  - A workshop-only `CLAUDE_CONFIG_DIR` keeps your own `~/.claude` untouched.
  - JFC is an orchestrator + subagents across seven phases — the Lesson 4 loop, scaled up.
  - The framework's value is encoded process — typed findings, bounded iteration, versioned prompts.
  - Open-weights models substituting for Opus is an experiment; where it degrades is the result.
---

At the start of the tutorial you ran one setup script and [launched the JFC agent](1b_jfc_launch.html)
on a H→4ℓ mass measurement. It has been working through CMS Open Data on NRP GPUs ever since,
while you built a ~30-line agent yourself in [Build a Simple Agent](4_agent.html).

This lesson has three parts: check on the agent, walk through what the setup did to get Claude
Code running on NRP, and judge what the agent produced.

::: callout Didn't get the agent running?
You can still do this lesson. [Launch it now](1b_jfc_launch.html) — or use the
[JupyterHub backup notebook](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fclariphy&targetpath=clariphy&urlpath=lab%2Ftree%2Fclariphy%2Fworkspace%2Fnotebooks%2F5_analysis.ipynb)
— even ten minutes of agent work gives you something to look at, and the reference analysis
notes in Part 6 give you a comparison point either way.
:::

---

## First: where is your agent?

Go back to the agent's terminal. It is either still working, waiting for you to answer a
question, or finished. If it stopped to ask something, answer it and let it carry on while we
look at how it got started.

From a **second terminal**, the check script summarises the state of the exercise — whether
Claude Code is pointed at NRP, whether the data is staged, and how much the agent has written
(macOS, Linux or WSL; on Windows, browse `%USERPROFILE%\jfc-exercise\jfc\analyses\h4l_rogue`
in File Explorer instead):

```bash
source ~/jfc-exercise/nrp-env.sh
curl -fsSL https://raw.githubusercontent.com/nrp-nautilus/nrp-training/materials/clariphy/workspace/check.sh | bash -s 5
```

Then look at what it has produced so far:

```bash
cd "$ROGUE"
echo "=== files produced so far ==="
find . -maxdepth 2 -newer prompt.md -type f \
     -not -path './.git/*' -not -path './data/*' -not -path './docs/*' 2>/dev/null | head -30

echo
echo "=== figures ==="
find . -name '*.png' -o -name '*.pdf' 2>/dev/null | grep -v '^./docs/' | head -10
```

---

## JFC: the loop you built, scaled up

JFC is the same loop as your `run_agent()`, scaled up: an **orchestrator** that writes no code
itself, spawning **executor** and **reviewer** subagents across seven phases, with a human gate
before unblinding.

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

Each phase runs **execute → review → check → commit**, and a reviewer finding a physics problem
traceable to an earlier phase triggers a formal *regression* back to that phase.

Where your `run_agent()` had two tools and an eight-turn cap, JFC has typed review findings,
phase gates, and regressions back to earlier phases. The fast path you launched stripped most of
that away — which is exactly what makes its output worth judging now.

---

## Running it on NRP

JFC drives **Claude Code**, which speaks the Anthropic API. NRP exposes an
**Anthropic-compatible endpoint** alongside the OpenAI-compatible one you've used all day:

| Endpoint | Speaks | Used by |
|---|---|---|
| `https://ellm.nrp-nautilus.io/v1` | OpenAI API | `openai` SDK, opencode, VS Code (Lessons 2–4) |
| `https://ellm.nrp-nautilus.io/anthropic` | Anthropic API | **Claude Code** — the JFC agent |

So Claude Code can be pointed at NRP's open-weights models with the same LLM token you've been
using, and the entire JFC framework runs on NRP GPUs.

::: callout Set expectations honestly
This is a **research-grade experiment, not a guaranteed-success demo.** JFC's specification
explicitly requires every subagent to run on Claude Opus (*"Never use Sonnet or Haiku for any
analysis subagent. This is non-negotiable."*). You substituted open-weights models for that.
Expect rougher plans, more review iterations, and occasional stalls. NRP's own docs also warn
that **not all models route cleanly through the Anthropic-compatible endpoint**, and that
Anthropic's built-in web-search tool cannot be produced by open-weights models — which matters
because JFC's methodology asks agents to fetch and cite numeric constants.

Finding *where* it degrades is the interesting result.
:::

---

## What it takes to run

**Why your laptop, not JupyterHub.** This exercise hands an agent a real machine to work on. It
installs its own toolchain (`claude`, `pixi`), downloads ~865 MiB of samples, spawns parallel
worker processes, and runs unattended for tens of minutes. Hub sessions are resource-capped and
time-limited, the interactive `claude` TUI wants a real terminal rather than a notebook cell,
and a session that culls mid-run takes the agent's work with it. Locally, none of that is in
your way — and inference still happens on NRP GPUs; only the agent process and the data are
local.

**Time budget.** By hand, the setup takes ~10–15 minutes, most of it the data download; the
setup script does the same work unattended. The agent run itself is open-ended — Phil budgets
~20–30 minutes for the fast path to produce something worth looking at, which is why it ran in
the background during the other lessons. A *complete* JFC analysis runs for hours and is
deliberately out of scope; see [Take it further](#take-it-further).

**Resources.** Your local machine wants at least:

| | Fast path (today) | Full JFC path (take-home) |
|---|---|---|
| CPU | **4 cores** | 8 cores |
| RAM | **8 GB** (16 GB comfortable) | 16 GB |
| Disk | ~2 GB | ~6–8 GB |

No GPU needed — inference happens on NRP's GPUs, not yours. Any reasonably
modern laptop clears the fast-path bar.

**Why 4 cores.** The agent itself is almost entirely network-bound, sitting idle waiting on NRP
inference; it uses negligible CPU. Cores matter for the analysis code the agent *writes* —
decompressing ROOT files with uproot is CPU-bound, and the fits at the end lean on threaded
BLAS.

Returns diminish quickly past ~8 cores, for a specific reason: the natural way to parallelise
this is one worker per sample file, but the dataset is extremely lopsided — `ZZTo4L.root` is
572 MiB of the 865 MiB total, so **two thirds of the work sits in a single file** that per-file
parallelism cannot split. Extra workers finish the small samples and then idle.

**Careful: cores and RAM multiply.** JFC's scale-out rules tell agents to reach for
`ProcessPoolExecutor` on anything taking 2–15 minutes, and each worker holds its own arrays. On
an 8 GB machine keep the pool at ~4; asking for 12 workers on 12 files is the fastest route to
an OOM kill.

Disk breaks down as ~865 MiB of extracted samples, ~30 MiB of repositories, a few hundred MiB
for the `claude` and `pixi` binaries, and whatever the agent writes. The take-home path adds a
pixi environment carrying the full scientific-Python stack plus pandoc and LaTeX, which is the
multi-gigabyte part.

RAM is driven by that same `ZZTo4L.root`: ROOT files are internally compressed, so materialising
all of its branches at once lands in the multi-gigabyte range. Note the irony — JFC's own coding
rules say *"Prototype on a slice. ~1000 events first, full data only for production"*, but the
fast path deliberately strips those rules out, so a naive agent is **more** likely to exhaust
memory here than under the full specification. If a subagent got OOM-killed, that is the
reason, and telling the agent to read a slice or specific branches fixes it.

---

## How the setup worked

At the start, `jfc_setup.sh` (or `jfc_setup.ps1` on Windows) ran **Parts 1–4** below for you,
and you ran **Part 5** yourself. Each part shows the plain commands for that step and why it is
done that way — run them in order and you end up where the script left you. The script only
adds guard rails around the same commands: it checks your token before downloading anything,
resumes an interrupted download, skips finished steps on a re-run, and never copies over files
the agent has changed.

The commands below are the macOS, Linux and WSL version (bash or zsh); on Windows,
`jfc_setup.ps1` does the equivalent. Every path is under `~/jfc-exercise`, and each block
`cd`s where it needs to be, so it doesn't matter where your terminal starts.

One principle runs through all of it: **nothing touches your own configuration.** Everything
lives in `~/jfc-exercise`, apart from the `claude` and `pixi` binaries — so undoing it is
`rm -rf ~/jfc-exercise`.

---

## Part 1: Install Claude Code and Pixi

Two tools: the `claude` CLI (the agent runtime) and [Pixi](https://pixi.sh) (the environment
manager JFC uses — it is non-negotiable in the spec; agents are forbidden from using bare `pip`
or `conda`).

```bash
curl -fsSL https://claude.ai/install.sh | bash
curl -fsSL https://pixi.sh/install.sh | PIXI_NO_PATH_UPDATE=1 sh   # don't edit shell rc files

export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
claude --version
pixi --version
```

The agent runs in its own terminal and you will likely open a second one to watch it, so save
your token and paths to a small file that any terminal can load with `source`. This
deliberately does **not** edit `~/.bashrc` or `~/.zshrc`: the settings apply only in terminals
where you source the file, and deleting `~/jfc-exercise` removes them.

```bash
# Paste your personal token from https://nrp.ai/llmtoken between the quotes
# (or leave the placeholder to use an OPENAI_API_KEY you have already exported).
TOKEN="<paste-your-token-here>"
[[ "$TOKEN" == "<"* ]] || export OPENAI_API_KEY="$TOKEN"
[[ -n "$OPENAI_API_KEY" && "$OPENAI_API_KEY" != "<"* ]] || echo "⚠️  No token yet: paste it into TOKEN above and run this again."

export WORK="$HOME/jfc-exercise"
mkdir -p "$WORK"
cat > "$WORK/nrp-env.sh" <<EOF
# NRP settings for the CLARIPHY JFC exercise. Load with: source ~/jfc-exercise/nrp-env.sh
export OPENAI_API_BASE="https://ellm.nrp-nautilus.io/v1"
export OPENAI_API_KEY="$OPENAI_API_KEY"
export WORK="$WORK"
export ROGUE="$WORK/jfc/analyses/h4l_rogue"
export CLAUDE_CONFIG_DIR="$WORK/claude-config"
export PATH="\$HOME/.local/bin:\$HOME/.pixi/bin:\$PATH"
EOF
chmod 600 "$WORK/nrp-env.sh"

source "$WORK/nrp-env.sh"
echo "Saved to $WORK/nrp-env.sh. OPENAI_API_KEY = ${OPENAI_API_KEY:0:8}..."
```

---

## Part 2: Point Claude Code at NRP

Claude Code reads an `env` block from its user-level `settings.json`. This is where the
Anthropic-compatible endpoint and your NRP token go.

That file normally lives in `~/.claude/` — and if you already use Claude Code for your own
work, it is your real configuration. Writing the NRP settings there means backing it up and
overwriting it, and one accidental second run overwrites the backup as well.

**So we leave it alone.** Claude Code honours a `CLAUDE_CONFIG_DIR` environment variable that
moves its whole user configuration somewhere else, and `nrp-env.sh` sets it to
`~/jfc-exercise/claude-config`. Any terminal where you have run
`source ~/jfc-exercise/nrp-env.sh` gets the NRP setup; every other terminal keeps your normal
Claude Code; and re-running this step only rewrites a workshop file you can throw away.

**Model choice matters more than usual here.** Claude Code speaks the Anthropic protocol, and
NRP's `/anthropic` endpoint is a *translation layer* over an OpenAI-style backend. That
translation is where things break: reasoning models emit "thinking" blocks, and every agent turn
emits tool-use blocks, and a bridge that mislabels either one will crash Claude Code's SDK with
`API Error: Content block is not a text block`. We default to **`gpt-oss`** because it is the
model vLLM uses as its own worked example in the
[vLLM ↔ Claude Code guide](https://docs.vllm.ai/en/stable/serving/integrations/claude_code/), so
that path is the one actually exercised upstream. `glm-5` and `minimax-m2` are the next
candidates if it misbehaves.

**`WebSearch` is denied on purpose.** It is a server-side Anthropic tool that only Claude models
can emit — open-weights models on NRP cannot produce it, so leaving it enabled just burns turns
on a tool that can never succeed. This matters for JFC, whose methodology insists every numeric
constant be cited (*"any uncited numeric constant is Category A"*): with web search unavailable,
the reference PDFs in `docs/` are the citable source. `WebFetch` is a different, client-side
tool and still works if the agent has a specific URL.

::: important
This step does **not** read or modify `~/.claude`. Claude Code only uses the NRP config in
terminals where `CLAUDE_CONFIG_DIR` points at it — the ones where you sourced `nrp-env.sh`. For
your normal Claude Code, open a fresh terminal.
:::

```bash
NRP_MODEL="gpt-oss"        # vLLM's documented Claude Code example — see note above
NRP_CONTEXT="131072"

export CLAUDE_CONFIG_DIR="$HOME/jfc-exercise/claude-config"   # workshop-only, NOT ~/.claude
mkdir -p "$CLAUDE_CONFIG_DIR"

cat > "$CLAUDE_CONFIG_DIR/settings.json" <<EOF
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://ellm.nrp-nautilus.io/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "$OPENAI_API_KEY",
    "ANTHROPIC_MODEL": "$NRP_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "$NRP_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "$NRP_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "$NRP_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL": "$NRP_MODEL",
    "ENABLE_TOOL_SEARCH": "false",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "$NRP_CONTEXT",
    "CLAUDE_CODE_EFFORT_LEVEL": "max",
    "CLAUDE_STREAM_IDLE_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
    "DISABLE_TELEMETRY": "1",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_MAX_RETRIES": "10"
  },
  "permissions": {
    "deny": ["WebSearch"]
  }
}
EOF
chmod 600 "$CLAUDE_CONFIG_DIR/settings.json"

cat "$CLAUDE_CONFIG_DIR/settings.json"
```

Confirm the Anthropic-compatible endpoint answers with your token before handing it a
multi-hour job. `HTTP 200` plus a non-empty `reply` means Claude Code will work.

Note the generous `max_tokens`. NRP's models are **reasoning models** — they spend part of the
output budget thinking privately before emitting any visible text (the same behaviour you saw in
[Chat with LLMs](2_chat.html)). Ask for 64 tokens and the model will burn all 64 on reasoning
and hand back `"content": null` with `"stop_reason": "max_tokens"` — which looks like a broken
endpoint but is just an under-funded request.

```bash
curl -s -o /tmp/anthropic_check.json -w 'HTTP %{http_code}\n' \
  -X POST "https://ellm.nrp-nautilus.io/anthropic/v1/messages" \
  -H "x-api-key: $OPENAI_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "{\"model\":\"${NRP_MODEL:-gpt-oss}\",\"max_tokens\":1000,\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly: NRP OK\"}]}"

python3 -c '
import json
d = json.load(open("/tmp/anthropic_check.json"))
if "error" in d:
    print("ERROR:", d["error"]); raise SystemExit
c = d.get("content")
text = "".join(b.get("text", "") for b in c) if isinstance(c, list) else (c or "")
print("model:      ", d.get("model"))
print("stop_reason:", d.get("stop_reason"))
print("reply:      ", repr(text.strip()))
'
```

Reading the result:

| What you see | Meaning |
|---|---|
| `HTTP 200`, `stop_reason: end_turn`, non-empty reply | Working — go on to Part 3 |
| `HTTP 200`, `stop_reason: max_tokens`, empty reply | The model spent its whole budget reasoning. Raise `max_tokens` — not an endpoint problem |
| `ERROR: ...` mentioning the model | That model doesn't route cleanly through the Anthropic bridge — try another |
| `HTTP 401` / `403` | Token problem — check `OPENAI_API_KEY` |

This check only proves the endpoint answers. The bridge can still fail **later**, once Claude
Code starts making tool calls — see below.

::: callout If Claude Code dies with "Content block is not a text block"
This is the failure to expect, and it is a **bridge bug, not your configuration**. The Anthropic
protocol requires a `text_delta` to target an open `text` block; translation layers routinely
mislabel *thinking* blocks and *tool-use* blocks, and Claude Code's SDK rejects the stream. It
typically hits on the agent's very first tool call. The same bug is documented against
[sglang](https://github.com/sgl-project/sglang/issues/24293) and
[LiteLLM](https://github.com/BerriAI/litellm/issues/29441).

In order:

1. Set `NRP_MODEL="glm-5"` or `"minimax-m2"`, re-run the settings step, relaunch. (Used the
   setup script? Re-run it as `NRP_MODEL=glm-5 bash jfc_setup.sh` — only the config changes.)
2. **Fall back to opencode.** The fast path stages only `prompt.md`, `docs/` and
   `h4l_ntuplize.py` — none of JFC's subagent machinery — so nothing about it actually requires
   Claude Code. opencode talks to NRP over `/v1` with no Anthropic translation in the way, and
   you configured it in [Agentic Workflows](3_agentic.html):

   ```bash
   source ~/jfc-exercise/nrp-env.sh
   cd "$ROGUE"
   opencode
   ```

   Then paste the contents of `prompt.md` at the opencode prompt.

Claude Code is only strictly required for the take-home full-spec path, which spawns subagents.
:::

The [LLM status dashboard](https://nrp.ai/llm-status/) shows what's currently up.

---

## Part 3: Get the data and the framework

We use one working directory and **absolute paths** throughout. Phil's README navigates with
relative `../../../` hops, which are easy to get wrong once you `cd` into the analysis
directory — using `$WORK` avoids that entirely.

```bash
export WORK="$HOME/jfc-exercise"
mkdir -p "$WORK" && cd "$WORK"
echo "WORK=$WORK"
```

### The CMS Open Data samples

Flat ntuples (~857 MiB) produced from 2017 NANOAOD with `h4l_ntuplize.py`: 10/fb of data plus
Higgs signal (ggH, VBF, VH), ZZ, ggZZ, Drell-Yan and tt̄ backgrounds, hosted on NRP S3.

The download takes a few minutes. The cell is safe to re-run — it skips the download if
`data/` already exists.

```bash
DATA_URL="https://s3-west.nrp-nautilus.io/transfer-bucket/h4l-data.tgz"

cd "$WORK"
if [ -d data ]; then
    echo "data/ already present — skipping download."
else
    curl -fL -o data.tgz "$DATA_URL"
    tar xzf data.tgz && rm -f data.tgz    # drop the 857 MiB tarball once extracted
fi
du -sh data 2>/dev/null; ls data | head
```

### The framework and the tutorial context

Two repositories: `jfc` on the `jfc_lite` branch (the framework and its specification), and
`h4l_agent_test` (this analysis's prompt, reference papers and ntuplizer).

```bash
cd "$WORK"
# needs git; without it, the setup script downloads GitHub snapshots instead
[ -d h4l_agent_test ] || git clone -q https://github.com/violatingcp/h4l_agent_test.git
[ -d jfc ]            || git clone -q -b jfc_lite https://github.com/violatingcp/jfc.git
ls -d h4l_agent_test jfc
```

---

## Part 4: The fast path — prompt and context only

Phil's tutorial offers two routes, and this is the deliberate trade:

| | **Standard** (slow) | **Fast / "go rogue"** ← *we did this* |
|---|---|---|
| JFC methodology, agent roles, conventions | ✅ full spec | ❌ none |
| Phase structure and multi-agent review | ✅ enforced | ❌ agent improvises |
| Pixi environment scaffolded for you | ✅ | ❌ agent builds its own |
| Physics prompt, reference papers, ntuplizer | ✅ | ✅ |
| Setup time | ~10 min + long `pixi install` | minutes |

The fast path hands the model the **physics problem and the papers, but none of JFC's
guardrails**. It gets you to a running agent inside a tutorial slot, and it makes the value of
the full specification obvious by contrast — the JFC authors ship analysis notes from both
configurations in `h4l_agent_test/analysis_notes/` if you want to compare outcomes.

```bash
export ROGUE="$WORK/jfc/analyses/h4l_rogue"
mkdir -p "$ROGUE" && cd "$ROGUE"

ln -sfn "$WORK/data" data                              # symlink, don't copy 857 MiB
cp "$WORK/h4l_agent_test/h4l_ntuplize.py" .
cp -r "$WORK/h4l_agent_test/docs" .
cp -r "$WORK/h4l_agent_test/.claude" .
cp "$WORK/h4l_agent_test/prompt.md" .

ls -a
```

What got staged:

| File | Role |
|---|---|
| `prompt.md` | The physics ask — channel, samples with cross-sections, and explicit scope cuts ("just increase the overall normalization on the backgrounds", "cut the exploration steps short") |
| `docs/` | The reference papers, including arXiv:1706.09936 — the CMS H→4ℓ publication this follows |
| `h4l_ntuplize.py` | How the ntuples were produced from NANOAOD, so the agent can read the branch structure |
| `.claude/` | Project-level Claude Code settings. A different file from the `settings.json` written in Part 2 (which lives in `~/jfc-exercise/claude-config`) — project scope, no overlapping keys, so the NRP config still applies |
| `data/` | Symlink to the samples |

The prompt is the analysis's founding document — everything the agent does traces back to it:

```bash
head -5 "$ROGUE/prompt.md"
```

---

## Part 5: Launch the agent

This is the one step you ran yourself, in a fresh terminal:

```bash
source ~/jfc-exercise/nrp-env.sh      # token, PATH and the workshop-only Claude Code config
cd "$ROGUE"
cat prompt.md | claude --permission-mode auto
```

`source` loads the settings from Part 1 into that terminal only — including
`CLAUDE_CONFIG_DIR`, which is what makes this `claude` use the NRP config from Part 2 rather than
your own. `cat prompt.md |` hands the physics prompt from Part 4 to Claude Code as its opening
message. (On Windows, `start-agent.cmd` does the same, passing an instruction to read
`prompt.md` as a command-line argument.)

`--permission-mode auto` lets the agent write files and run commands without confirming each
one — appropriate here because it is working in a scratch directory it created, and it is about
to run hundreds of steps. Everything it touches lives under `h4l_rogue/`.

---

## Part 6: What "good" looks like

::: callout Read back how it thought
The interesting part is not only the final number — it is the trajectory. Scroll back through
the agent's terminal:

- **Where did it start?** A good agent inspects the ntuple branches before writing selection code.
- **Did it plan or dive in?** JFC forces plan-mode first; without the spec, weaker models tend to start coding immediately.
- **Did it check itself?** Look for a cutflow, a data/MC comparison, a sanity plot — or the absence of one.
- **Where did it get stuck?** Long silences, repeated failed edits, or looping on the same error are the honest signal about open-weights models driving a long agentic task.
:::

For this analysis the physics target is concrete, which makes grading the agent easy: a
four-lepton invariant mass spectrum with a **Higgs peak near 125 GeV** sitting on a ZZ
continuum, and a signal-strength fit returning **μ ≈ 1** within uncertainties.

Judge the run on:

1. **Did it produce a mass plot at all?** The single most common failure is never getting past data loading.
2. **Is the peak in the right place?** A peak at 125 GeV means the four-lepton kinematics were reconstructed correctly. A peak somewhere else means a bug worth finding.
3. **Are the backgrounds normalized?** Cross-sections are in `prompt.md`; each sample must be scaled to 10/fb.
4. **Is μ credible?** A μ of 1.0 ± 0.3 is a real result. A μ of 40, or a fit with χ² identically zero, is not — JFC's spec calls χ² = 0 *"an alarm, not a result"*.
5. **Could someone else reproduce it?** The prompt explicitly asks that the mass and μ extraction be easy to rerun.

Compare against the reference PDFs the JFC authors produced with Claude Opus and full JFC
context, which are checked into the tutorial repo:

```bash
ls -la "$WORK/h4l_agent_test/analysis_notes/"
```

---

<a id="take-it-further"></a>

## Take it further: the full JFC specification

The fast path removed the framework. Putting it back is the actual point of JFC — and is the
natural take-home from this session.

Run this **after the workshop** (the `pixi install` alone pulls a full scientific-Python stack,
and the analysis runs for hours):

```bash
source ~/jfc-exercise/nrp-env.sh      # token, PATH and the workshop-only Claude Code config
cd ~/jfc-exercise/jfc
pixi run scaffold analyses/h4l_analysis --type measurement
cd analyses/h4l_analysis
pixi install

# stage the same physics context, plus the isolation config the spec needs
ln -sfn ~/jfc-exercise/data data
cp  ~/jfc-exercise/h4l_agent_test/h4l_ntuplize.py .
cp -r ~/jfc-exercise/h4l_agent_test/docs .
cp -r ~/jfc-exercise/h4l_agent_test/.claude .
cp  ~/jfc-exercise/h4l_agent_test/.analysis_config .
cp  ~/jfc-exercise/h4l_agent_test/prompt.md .

cat prompt.md | claude --permission-mode auto
```

Scaffolding creates the phase directories, per-phase `CLAUDE.md` files, a `pixi.toml`, and
symlinks to `agents/`, `conventions/` and `methodology/` — the full specification. Check
`.analysis_config` if your data lives somewhere other than `$PWD/data`.

Then read what the spec actually enforces — it is the most transferable part of this lesson even
if you never run a full analysis:

- `jfc/src/methodology/03-review.md` — the review protocol: Category A/B/C findings, iteration caps, and the rule that a result more than 3σ from a well-measured reference is automatically blocking.
- `jfc/src/agents/executor.md` — how a subagent is briefed. Note that prompts are *files under version control*, not ad-hoc strings.
- `jfc/analyses/h4l_analysis/CLAUDE.md` — the orchestrator contract, including the regression checklist it must run after every review.

Those three ideas — **typed findings, bounded iteration, and prompts as versioned artifacts** —
are what separate this from the loop you wrote in Lesson 4, and they transfer to any agentic
system you build.

---

## Discussion

- **The framework is the product.** JFC ships almost no analysis code. Its value is the
  encoded *process*: what a phase must produce, who reviews it, what blocks advancement. That is
  the same insight from Lesson 4 — tool descriptions and error strings are prompts — applied to
  an entire research workflow.
- **Portability, again.** JFC was written against Anthropic's API. It ran here on open-weights
  models on NRP GPUs, unchanged, because the endpoint speaks the same protocol.
- **Human gates are load-bearing.** JFC pauses for human approval before unblinding — the
  agent does not decide on its own when to look at the full dataset.
- **Honest reporting.** If your run stalled or produced a wrong peak, that is a legitimate
  result about open-weights models on long agentic tasks. Bring it to the discussion — the
  failure modes are more useful to this community right now than a clean success.

**Where this came from:** JFC is by Eric Moreno, Sam Bright-Thonney, Andrzej Novak, Daniel Garcia
and Phil Harris — *AI Agents Can Already Autonomously Perform Experimental High Energy Physics*.
The H→4ℓ exercise is Phil Harris's USCMS tutorial, adapted here to run on NRP.

---

## After the workshop: clean up

Stop the agent with **Ctrl+C** in its terminal. Copy anything you want to keep out of
`~/jfc-exercise/jfc/analyses/h4l_rogue`, then remove the exercise:

```bash
rm -rf ~/jfc-exercise
```

That deletes the samples, the repositories, the agent's output, the workshop-only Claude Code
config, and `nrp-env.sh` — the files that hold your token. On Windows, delete
`%USERPROFILE%\jfc-exercise`. Your own `~/.claude` was never modified. `claude` and `pixi` stay
installed; see the [Claude Code](https://code.claude.com/docs/en/setup#uninstall-claude-code)
and [Pixi](https://pixi.sh/latest/installation/) docs if you want to remove them too.

---

## References

- [JFC framework](https://github.com/jfc-mit/jfc) · [`jfc_lite` branch used here](https://github.com/violatingcp/jfc/tree/jfc_lite)
- [h4l_agent_test tutorial](https://github.com/violatingcp/h4l_agent_test)
- [NRP client configurations](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/) — the Claude Code settings used in [Part 2](#part-2-point-claude-code-at-nrp)
- [Claude Code settings](https://code.claude.com/docs/en/settings) — including `CLAUDE_CONFIG_DIR`
- [NRP available models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/) · [LLM status dashboard](https://nrp.ai/llm-status/)
- [CMS H→4ℓ, JHEP 11 (2017) 047](https://arxiv.org/abs/1706.09936) — the reference analysis
- [Pixi](https://pixi.sh) · [Claude Code](https://github.com/anthropics/claude-code)
