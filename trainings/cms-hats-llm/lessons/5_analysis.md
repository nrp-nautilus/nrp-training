---
title: Agentic Physics Analysis — Running JFC on NRP LLMs
teaching: 10
exercises: 35
questions:
  - Can an agent run a complete physics analysis, not just write a script?
  - How do I point Claude Code at NRP instead of paying for a subscription?
  - What does a production agentic research framework actually encode?
objectives:
  - Configure Claude Code against NRP's Anthropic-compatible endpoint.
  - Stage and launch the JFC H→4ℓ analysis on CMS Open Data.
  - Judge an agent's analysis output against a known physics target.
  - Identify what the JFC specification adds beyond a bare agent loop.
keypoints:
  - NRP speaks the Anthropic API at `/anthropic`, so Claude Code runs on NRP models with no subscription.
  - JFC is an orchestrator + subagents across seven phases — the Lesson 4 loop, scaled up.
  - The framework's value is encoded process — typed findings, bounded iteration, versioned prompts.
  - Open-weights models substituting for Opus is an experiment; where it degrades is the result.
---

::: callout Open the notebook in JupyterHub
**[▶ Open notebook in JupyterHub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats-llm&targetpath=cms-hats-llm&urlpath=lab%2Ftree%2Fcms-hats-llm%2Fworkspace%2Fnotebooks%2F5_analysis.ipynb)** — clones the training repo and opens `workspace/notebooks/5_analysis.ipynb` on uscms-af.nrp-nautilus.io. Uses a **bash kernel** — every command below is a Shift+Enter cell.
:::

In [Build a Simple Agent](4_agent.html) you built a ~30-line agent with two tools. This lesson
jumps to the other end of the scale: **[JFC](https://github.com/jfc-mit/jfc)** ("Just Furnish
Context"), a framework from Eric Moreno, Sam Bright-Thonney, Andre Novak, Daniel Garcia and
Phil Harris that runs a *complete* HEP analysis — strategy, event selection, statistical
inference, and a 50–100 page analysis note — from a single physics prompt.

It is the same loop you just built, scaled up: an **orchestrator** that writes no code itself,
spawning **executor** and **reviewer** subagents across seven phases, with a human gate before
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

Each phase runs **execute → review → check → commit**, and a reviewer finding a physics problem
traceable to an earlier phase triggers a formal *regression* back to that phase.

The exercise here follows Phil Harris's
[h4l_agent_test](https://github.com/violatingcp/h4l_agent_test) tutorial: a **H→4ℓ mass
measurement on CMS Open Data**, reproducing the spirit of JHEP 11 (2017) 047.

---

## Running it on NRP

JFC drives **Claude Code**, which speaks the Anthropic API. NRP exposes an
**Anthropic-compatible endpoint** alongside the OpenAI-compatible one you've used all day:

| Endpoint | Speaks | Used by |
|---|---|---|
| `https://ellm.nrp-nautilus.io/v1` | OpenAI API | `openai` SDK, opencode, VS Code (Lessons 2–4) |
| `https://ellm.nrp-nautilus.io/anthropic` | Anthropic API | **Claude Code** — this lesson |

So Claude Code can be pointed at NRP's open-weights models with the same LLM token you've been
using, and the entire JFC framework runs on NRP GPUs.

::: callout Set expectations honestly
This is a **research-grade experiment, not a guaranteed-success demo.** JFC's specification
explicitly requires every subagent to run on Claude Opus (*"Never use Sonnet or Haiku for any
analysis subagent. This is non-negotiable."*). You are about to substitute open-weights models
for that. Expect rougher plans, more review iterations, and occasional stalls. NRP's own docs
also warn that **not all models route cleanly through the Anthropic-compatible endpoint**, and
that Anthropic's built-in web-search tool cannot be produced by open-weights models — which
matters because JFC's methodology asks agents to fetch and cite numeric constants.

Finding *where* it degrades is the interesting result. Keep notes.
:::

**Time budget.** The setup below runs ~10–15 minutes, most of it `pixi install` and the data
download. The agent run itself is open-ended — Phil budgets ~20–30 minutes for the fast path to
produce something worth looking at. A *complete* JFC analysis runs for hours and is deliberately
out of scope; see [Take it further](#take-it-further) at the end.

---

## Part 1: Install Claude Code and Pixi

Two tools: the `claude` CLI (the agent runtime) and [Pixi](https://pixi.sh) (the environment
manager JFC uses — it is non-negotiable in the spec; agents are forbidden from using bare `pip`
or `conda`).

```bash
curl -fsSL https://claude.ai/install.sh | bash
curl -fsSL https://pixi.sh/install.sh | sh

export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
claude --version
pixi --version
```

As in [Agentic Workflows](3_agentic.html), a JupyterLab terminal is a **separate process** from
the notebook — `export`s there do not reach it. Persist the `PATH` and your token so every new
terminal picks them up:

```bash
# Paste your personal token from https://nrp.ai/llmtoken if it isn't already set.
: "${OPENAI_API_BASE:=https://ellm.nrp-nautilus.io/v1}"
: "${OPENAI_API_KEY:=<paste-your-token-here>}"

for RC in ~/.bashrc ~/.bash_profile; do
    touch "$RC"
    grep -v -E 'OPENAI_API_BASE=|OPENAI_API_KEY=|\.opencode/bin|\.pixi/bin|NRP managed LLM \(cms-hats-llm training\)' "$RC" > "$RC.tmp" && mv "$RC.tmp" "$RC"
    cat >> "$RC" <<EOF

# --- NRP managed LLM (cms-hats-llm training) ---
export OPENAI_API_BASE="$OPENAI_API_BASE"
export OPENAI_API_KEY="$OPENAI_API_KEY"
export PATH="\$HOME/.local/bin:\$HOME/.pixi/bin:\$HOME/.opencode/bin:\$PATH"
EOF
done

echo "Persisted. OPENAI_API_KEY = ${OPENAI_API_KEY:0:8}..."
```

---

## Part 2: Point Claude Code at NRP

Claude Code reads an `env` block from `~/.claude/settings.json`. This is where the
Anthropic-compatible endpoint and your NRP token go.

The model IDs matter. JFC is extremely context-hungry — the orchestrator passes methodology
files, phase specs and upstream artifacts into every subagent — so pick a long-context model
with solid tool calling. `qwen3` (1.01M context) is the natural default; `glm-5` (300K) and
`gpt-oss` (131K, strong at code) are reasonable alternates. Claude Code asks for
"opus"/"sonnet"/"haiku" tiers internally, so all of them are mapped to NRP models below.

::: important
This writes your **user-level** Claude Code settings. If you already use Claude Code against
Anthropic's API, the cell below backs up any existing file to `~/.claude/settings.json.bak`
first — restore it after the workshop.
:::

```bash
NRP_MODEL="qwen3"          # 1.01M context — see the model table in Lesson 1
NRP_CONTEXT="1010000"

mkdir -p ~/.claude
[ -f ~/.claude/settings.json ] && cp ~/.claude/settings.json ~/.claude/settings.json.bak && echo "Backed up existing settings to ~/.claude/settings.json.bak"

cat > ~/.claude/settings.json <<EOF
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
  }
}
EOF

python3 -m json.tool ~/.claude/settings.json
```

Confirm the Anthropic-compatible endpoint answers with your token before handing it a
multi-hour job. `HTTP 200` plus a non-empty `reply` means Claude Code will work.

Note the generous `max_tokens`. `qwen3` is a **reasoning model** — it spends part of its output
budget thinking privately before emitting any visible text (the same behaviour you saw in
[Chat with LLMs](2_chat.html)). Ask it for 64 tokens and it will burn all 64 on reasoning and
hand back `"content": null` with `"stop_reason": "max_tokens"` — which looks like a broken
endpoint but is just an under-funded request.

```bash
curl -s -o /tmp/anthropic_check.json -w 'HTTP %{http_code}\n' \
  -X POST "https://ellm.nrp-nautilus.io/anthropic/v1/messages" \
  -H "x-api-key: $OPENAI_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"qwen3","max_tokens":1000,"messages":[{"role":"user","content":"Reply with exactly: NRP OK"}]}'

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

If you need a different model, set `NRP_MODEL="glm-5"` or `"gpt-oss"` and re-run the settings
cell in Part 2, then re-run this check. The [LLM status dashboard](https://nrp.ai/llm-status/)
shows what's currently up.

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
    curl -L -o data.tgz "$DATA_URL"
    tar xzf data.tgz
fi
du -sh data 2>/dev/null; ls data | head
```

### The framework and the tutorial context

Two repositories: `jfc` on the `jfc_lite` branch (the framework and its specification), and
`h4l_agent_test` (this analysis's prompt, reference papers and ntuplizer).

```bash
cd "$WORK"
[ -d h4l_agent_test ] || git clone -q https://github.com/violatingcp/h4l_agent_test.git
[ -d jfc ]            || git clone -q -b jfc_lite https://github.com/violatingcp/jfc.git
ls -d h4l_agent_test jfc
```

---

## Part 4: The fast path — prompt and context only

Phil's tutorial offers two routes, and this is the deliberate trade:

| | **Standard** (slow) | **Fast / "go rogue"** ← *we do this* |
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

What you just staged:

| File | Role |
|---|---|
| `prompt.md` | The physics ask — channel, samples with cross-sections, and explicit scope cuts ("just increase the overall normalization on the backgrounds", "cut the exploration steps short") |
| `docs/` | The reference papers, including arXiv:1706.09936 — the CMS H→4ℓ publication this follows |
| `h4l_ntuplize.py` | How the ntuples were produced from NANOAOD, so the agent can read the branch structure |
| `.claude/` | Project-level Claude Code settings. Different file from the `~/.claude/settings.json` you wrote in Part 2 — project scope, no overlapping keys, so your NRP config still applies |
| `data/` | Symlink to the samples |

Skim the prompt before launching — it is the analysis's founding document, and everything the
agent does traces back to it:

```bash
head -5 "$ROGUE/prompt.md"
```

---

## Part 5: Launch the agent

🖥️ **Terminal step** — `claude` is an interactive terminal UI, so launch it from a real
JupyterLab terminal (**File → New → Terminal**), not the notebook. If that terminal was open
before you ran the persistence cell in Part 1, run `source ~/.bashrc` first, or just open a
fresh one.

```bash
cd ~/jfc-exercise/jfc/analyses/h4l_rogue
export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
cat prompt.md | claude --permission-mode auto
```

`--permission-mode auto` lets the agent write files and run commands without confirming each
one — appropriate here because it is working in a scratch directory it created, and it is about
to run hundreds of steps. Everything it touches lives under `h4l_rogue/`.

::: callout Watch it think
The interesting part is not the final number — it is the trajectory. Keep an eye on:

- **Where does it start?** A good agent inspects the ntuple branches before writing selection code.
- **Does it plan or dive in?** JFC forces plan-mode first; without the spec, weaker models tend to start coding immediately.
- **Does it check itself?** Watch for a cutflow, a data/MC comparison, a sanity plot — or the absence of one.
- **Where does it get stuck?** Long silences, repeated failed edits, or looping on the same error are the honest signal about open-weights models driving a long agentic task.
:::

While it runs, inspect what it is producing from the notebook — the agent writes to disk
continuously, so you can watch artifacts appear without interrupting it:

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

## Part 6: What "good" looks like

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

**Where this came from:** JFC is by Eric Moreno, Sam Bright-Thonney, Andre Novak, Daniel Garcia
and Phil Harris — *AI Agents Can Already Autonomously Perform Experimental High Energy Physics*.
The H→4ℓ exercise is Phil Harris's USCMS tutorial, adapted here to run on NRP.

---

## References

- [JFC framework](https://github.com/jfc-mit/jfc) · [`jfc_lite` branch used here](https://github.com/violatingcp/jfc/tree/jfc_lite)
- [h4l_agent_test tutorial](https://github.com/violatingcp/h4l_agent_test)
- [NRP client configurations](https://nrp.ai/documentation/userdocs/ai/llm-managed/client-configs/) — the Claude Code settings used in Part 2
- [NRP available models](https://nrp.ai/documentation/userdocs/ai/llm-managed/models/) · [LLM status dashboard](https://nrp.ai/llm-status/)
- [CMS H→4ℓ, JHEP 11 (2017) 047](https://arxiv.org/abs/1706.09936) — the reference analysis
- [Pixi](https://pixi.sh) · [Claude Code](https://github.com/anthropics/claude-code)
