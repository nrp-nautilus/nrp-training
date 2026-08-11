---
title: Build a Simple Agent — Tool Calling & the Agent Loop
teaching: 15
exercises: 45
questions:
  - What is an agent, and how is it different from a chat completion?
  - How do I describe a Python function so an LLM can call it?
  - What does the tool-calling round trip look like at the message level?
  - How do I wrap it all in a loop to get a working agent?
objectives:
  - Explain the agent loop — model, tool call, result, model — repeated until done.
  - Write a JSON tool schema for a plain Python function.
  - Execute one tool-calling round trip by hand and inspect every message.
  - Build a reusable ~30-line agent loop with two physics tools.
  - Add guardrails — an iteration cap and error messages the model can recover from.
keypoints:
  - An agent is an LLM + tool schemas + a `while` loop. No framework required.
  - The model never executes anything — it requests a call, your code runs it and reports back.
  - Tool results are ordinary messages with `role="tool"`; the transcript is the agent's state.
  - Tool `description` fields are prompts — good ones are the difference between a tool that gets used and one that gets ignored.
  - Readable error strings let the model self-correct; `max_turns` keeps the loop bounded.
---

::: callout Open the notebook in JupyterHub
**[▶ Open notebook in JupyterHub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats-llm&targetpath=cms-hats-llm&urlpath=lab%2Ftree%2Fcms-hats-llm%2Fworkspace%2Fnotebooks%2F4_agent.ipynb)** — clones the training repo and opens `workspace/notebooks/4_agent.ipynb` on uscms-af.nrp-nautilus.io.
:::

In Part 2 you *called* the model; in Part 3 you *used* pre-built agents
(opencode, VS Code). Now you build one yourself — a working agent in about 30
lines of Python, no framework — so you understand exactly what those tools do
under the hood and can build your own when you get home.

Work through the notebook top to bottom (**Shift+Enter** to run each cell). The notebook covers:

| Step | Topic |
|---|---|
| 1 | Setup — client and model choice |
| 2 | What is an agent? The loop, conceptually |
| 3 | First tool: PDG lookup — function, schema, and one round trip by hand |
| 4 | Second tool: invariant mass from (pT, η, φ, m) |
| 5 | The agent loop — `run_agent()` and a dimuon-resonance demo |
| 6 | Guardrails — iteration caps, errors as messages, self-correction |
| 7 | Exercises — your own questions, a third tool, agentic RAG challenge |

**Prerequisites:** `OPENAI_API_BASE` and `OPENAI_API_KEY` must be set — export
your personal token from [https://nrp.ai/llmtoken](https://nrp.ai/llmtoken)
(covered in [Lesson 1](1_intro.html#getting-access)). CPU-only is sufficient.

---

The content below is the notebook rendered as Markdown with example outputs. Run the live notebook on JupyterHub to execute cells and see your own results.

---

## 1. Setup

Same client as in the Chat notebook — one `OpenAI` client pointed at NRP. This
notebook is a separate kernel from Lesson 2, so it needs its own token set —
edit the `OPENAI_API_KEY` line below with your personal token from
[Lesson 1](1_intro.html#step-2-get-an-api-token).

```python
import os, json, math
from openai import OpenAI

os.environ.setdefault("OPENAI_API_BASE", "https://ellm.nrp-nautilus.io/v1")
os.environ.setdefault("OPENAI_API_KEY", "<paste-your-token-here>")

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_API_BASE"],
)

# Tool calling needs a model that supports it. gpt-oss is reliable at tools;
# qwen3-small also works well. Small models call tools less consistently.
MODEL = "gpt-oss"

print("Client ready, using model:", MODEL)
```

---

## 2. What Is an Agent?

Everything you did in the Chat notebook was a **single round trip**: you send
messages, the model sends text back. The model can only *talk*.

An **agent** adds two things:

1. **Tools** — Python functions the model is allowed to request, described to
   it as JSON schemas.
2. **A loop** — keep calling the model until it stops asking for tools and
   gives a final answer.

```
        ┌──────────────────────────────────────────┐
        │                                          │
        ▼                                          │
  ┌───────────┐   tool_calls?   ┌──────────────┐   │
  │ call LLM  │ ──── yes ─────► │ run tool(s)  │───┘
  └───────────┘                 │ append result│
        │                       └──────────────┘
       no
        │
        ▼
  final answer
```

**The model never executes anything.** It replies with *"please run
`invariant_mass` with these arguments"*; **your code** runs the function and
sends the result back as a new message. The model then decides what to do next.
The growing message list *is* the agent's entire state.

opencode, Claude Code, and Cursor (previous lesson) are exactly this loop —
just with more tools (file editing, shell) and more polish.

---

## 3. Your First Tool: a PDG Lookup

A tool needs two parts:

1. a **plain Python function**, and
2. a **schema** telling the model the tool's name, what it does, and what
   arguments it takes.

We start with a small particle-property table (values from the PDG).

```python
# --- Part 1: the plain Python function -------------------------------------
PDG = {
    "electron": {"mass_GeV": 0.000511, "charge": -1, "lifetime": "stable"},
    "muon":     {"mass_GeV": 0.10566,  "charge": -1, "lifetime": "2.197e-6 s"},
    "tau":      {"mass_GeV": 1.77693,  "charge": -1, "lifetime": "2.903e-13 s"},
    "photon":   {"mass_GeV": 0.0,      "charge": 0,  "lifetime": "stable"},
    "proton":   {"mass_GeV": 0.93827,  "charge": +1, "lifetime": "stable"},
    "neutron":  {"mass_GeV": 0.93957,  "charge": 0,  "lifetime": "878.4 s (free)"},
    "pi+":      {"mass_GeV": 0.13957,  "charge": +1, "lifetime": "2.603e-8 s"},
    "pi0":      {"mass_GeV": 0.13498,  "charge": 0,  "lifetime": "8.43e-17 s"},
    "k+":       {"mass_GeV": 0.49368,  "charge": +1, "lifetime": "1.238e-8 s"},
    "j/psi":    {"mass_GeV": 3.0969,   "charge": 0,  "width": "92.6 keV"},
    "upsilon":  {"mass_GeV": 9.4604,   "charge": 0,  "width": "54 keV"},
    "w":        {"mass_GeV": 80.369,   "charge": +1, "width": "2.085 GeV"},
    "z":        {"mass_GeV": 91.188,   "charge": 0,  "width": "2.4955 GeV"},
    "higgs":    {"mass_GeV": 125.20,   "charge": 0,  "width": "~3.7 MeV"},
    "top":      {"mass_GeV": 172.57,   "charge": "+2/3", "width": "1.42 GeV"},
}

ALIASES = {
    "z boson": "z", "w boson": "w", "higgs boson": "higgs", "top quark": "top",
    "jpsi": "j/psi", "psi": "j/psi", "pion": "pi+", "kaon": "k+",
    "mu": "muon", "e": "electron", "gamma": "photon", "upsilon(1s)": "upsilon",
}

def pdg_lookup(name):
    """Look up mass, charge, and lifetime/width of a particle."""
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    if key not in PDG:
        return (f"Unknown particle '{name}'. "
                f"Known particles: {', '.join(sorted(PDG))}")
    return json.dumps({"name": key, **PDG[key]})

# It's just a function — test it like one:
print(pdg_lookup("Z boson"))
print(pdg_lookup("axion"))
```

**Example output:**
```
{"name": "z", "mass_GeV": 91.188, "charge": 0, "width": "2.4955 GeV"}
Unknown particle 'axion'. Known particles: electron, higgs, j/psi, k+, muon, neutron, photon, pi+, pi0, proton, tau, top, upsilon, w, z
```

Note the error message: instead of raising, `pdg_lookup` returns a *helpful
string* listing what it does know. The model will read this and correct itself
— more on that in section 6.

Now the schema. This is the only "boilerplate" in the whole notebook — it is
how the model learns the tool exists. The `description` fields matter: they are
prompt text, and good descriptions are the difference between a tool the model
uses correctly and one it ignores.

```python
# --- Part 2: the schema the model sees -------------------------------------
PDG_SCHEMA = {
    "type": "function",
    "function": {
        "name": "pdg_lookup",
        "description": (
            "Look up the mass (GeV), charge, and lifetime or width of a "
            "particle by name, e.g. 'muon', 'Z', 'J/psi'. Returns JSON, or "
            "an error message listing the known particles."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Particle name, e.g. 'muon', 'Z', 'J/psi'",
                },
            },
            "required": ["name"],
        },
    },
}
```

### One round trip, by hand

Before hiding anything in a loop, do **one full tool-calling cycle manually**
so you see every message. Pass the schema via `tools=` and ask a question the
model can't answer without it:

```python
messages = [
    {"role": "user",
     "content": "What is the mass of the J/psi in GeV? Use the tool."},
]

resp = client.chat.completions.create(
    model=MODEL, messages=messages, tools=[PDG_SCHEMA], max_tokens=1000,
)
msg = resp.choices[0].message

print("content    =", repr(msg.content))
print("tool_calls =", msg.tool_calls)
```

**Example output:**
```
content    = ''
tool_calls = [ChatCompletionMessageToolCall(id='call_ab12', function=Function(
    arguments='{"name": "J/psi"}', name='pdg_lookup'), type='function')]
```

The model did **not** answer. Instead `tool_calls` contains a request:
*call `pdg_lookup` with `{"name": "J/psi"}`* — plus an `id` so results can be
matched to requests. `content` is empty (or holds private reasoning, for
reasoning models).

Now do our half of the deal: run the function, append **both** the assistant's
request and our result to the transcript, and call the model again.

```python
tc = msg.tool_calls[0]
args = json.loads(tc.function.arguments)
result = pdg_lookup(**args)
print(f"Ran {tc.function.name}({args}) -> {result}\n")

# 1) the assistant's tool request goes into the transcript...
messages.append({
    "role": "assistant",
    "content": msg.content or "",
    "tool_calls": [{
        "id": tc.id,
        "type": "function",
        "function": {"name": tc.function.name,
                     "arguments": tc.function.arguments},
    }],
})
# 2) ...followed by our result, as a role="tool" message
messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

# 3) call the model again with the updated transcript
resp = client.chat.completions.create(
    model=MODEL, messages=messages, tools=[PDG_SCHEMA], max_tokens=1000,
)
print("Final answer:", resp.choices[0].message.content)
```

**Example output:**
```
Ran pdg_lookup({'name': 'J/psi'}) -> {"name": "j/psi", "mass_GeV": 3.0969, "charge": 0, "width": "92.6 keV"}

Final answer: The J/psi meson has a mass of 3.0969 GeV.
```

That's the entire mechanism. Everything else in this notebook is wrapping
those three steps in a `while` loop.

---

## 4. A Second Tool: Invariant Mass

One tool is a lookup; two tools is an agent that has to **plan**. This one
computes the invariant mass of two particles from CMS-style kinematics
(pT, η, φ, mass). Flat scalar arguments keep the schema simple — prefer that
over nested objects when you design your own tools.

```python
def invariant_mass(pt1, eta1, phi1, m1, pt2, eta2, phi2, m2):
    """Invariant mass (GeV) of two particles from pt/eta/phi/mass (GeV)."""
    def p4(pt, eta, phi, m):
        px, py, pz = pt * math.cos(phi), pt * math.sin(phi), pt * math.sinh(eta)
        E = math.sqrt(px**2 + py**2 + pz**2 + m**2)
        return E, px, py, pz
    E1, px1, py1, pz1 = p4(pt1, eta1, phi1, m1)
    E2, px2, py2, pz2 = p4(pt2, eta2, phi2, m2)
    m2_val = (E1 + E2)**2 - (px1 + px2)**2 - (py1 + py2)**2 - (pz1 + pz2)**2
    return f"{math.sqrt(max(m2_val, 0.0)):.3f} GeV"

MASS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "invariant_mass",
        "description": (
            "Compute the invariant mass (GeV) of a two-particle system from "
            "each particle's transverse momentum pt (GeV), pseudorapidity "
            "eta, azimuthal angle phi (radians), and mass m (GeV)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pt1":  {"type": "number", "description": "pT of particle 1 in GeV"},
                "eta1": {"type": "number", "description": "eta of particle 1"},
                "phi1": {"type": "number", "description": "phi of particle 1 in radians"},
                "m1":   {"type": "number", "description": "mass of particle 1 in GeV"},
                "pt2":  {"type": "number", "description": "pT of particle 2 in GeV"},
                "eta2": {"type": "number", "description": "eta of particle 2"},
                "phi2": {"type": "number", "description": "phi of particle 2 in radians"},
                "m2":   {"type": "number", "description": "mass of particle 2 in GeV"},
            },
            "required": ["pt1", "eta1", "phi1", "m1",
                         "pt2", "eta2", "phi2", "m2"],
        },
    },
}

# Sanity check the function directly (two ~Z-like muons):
print(invariant_mass(35.0, 0.5, 0.8, 0.10566, 32.0, -1.15, -2.2, 0.10566))
```

**Example output:**
```
90.910 GeV
```

---

## 5. The Agent Loop

Now the loop itself. A registry maps tool names to functions; the loop calls
the model, executes whatever it asks for, and repeats until the model answers
in plain text (or we hit `max_turns`).

```python
TOOL_FUNCS   = {"pdg_lookup": pdg_lookup, "invariant_mass": invariant_mass}
TOOL_SCHEMAS = [PDG_SCHEMA, MASS_SCHEMA]

SYSTEM = (
    "You are a particle-physics assistant with tools for particle properties "
    "and kinematics. Always use the tools for numerical values instead of "
    "relying on memory. When you have everything you need, give a final "
    "answer in plain text with units."
)

def run_agent(question, model=MODEL, max_turns=8, verbose=True, show_reasoning=False):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    for turn in range(max_turns):
        resp = client.chat.completions.create(
            model=model, messages=messages,
            tools=TOOL_SCHEMAS, max_tokens=2000,
        )
        msg = resp.choices[0].message

        if show_reasoning:
            # Reasoning models (gpt-oss, minimax-m2, qwen3) expose private
            # chain-of-thought here — this is what lets you see *why* the
            # model retried "tauon" as "tau", not just that it did.
            reasoning = getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None)
            if reasoning:
                print(f"  [turn {turn}] reasoning: {reasoning}\n")

        if not msg.tool_calls:                      # plain text -> we're done
            return msg.content or "(no content returned)"

        # record the assistant's tool request(s) in the transcript
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name,
                              "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ],
        })

        # execute each requested tool and append its result
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
                result = str(TOOL_FUNCS[tc.function.name](**args))
            except Exception as e:                  # bad args, unknown tool...
                result = f"ERROR: {type(e).__name__}: {e}"
            if verbose:
                print(f"  [turn {turn}] {tc.function.name}"
                      f"({tc.function.arguments}) -> {result}")
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": result})

    return "(stopped: max_turns reached without a final answer)"
```

Now give it a question that requires **planning across both tools** — it must
know the muon mass before it can compute the invariant mass, and must check
resonances to interpret the result:

```python
answer = run_agent(
    "In one event I reconstruct two opposite-sign muons with "
    "(pT, eta, phi) = (35.0 GeV, 0.5, 0.8) and (32.0 GeV, -1.15, -2.2). "
    "What is their invariant mass, and which known resonance is it most "
    "compatible with? Verify the resonance mass with the PDG tool."
)
print("\n=== Final answer ===\n" + answer)
```

**Example output:**
```
  [turn 0] pdg_lookup({"name": "muon"}) -> {"name": "muon", "mass_GeV": 0.10566, "charge": -1, "lifetime": "2.197e-6 s"}
  [turn 1] invariant_mass({"pt1": 35.0, "eta1": 0.5, "phi1": 0.8, "m1": 0.10566, "pt2": 32.0, "eta2": -1.15, "phi2": -2.2, "m2": 0.10566}) -> 90.910 GeV
  [turn 2] pdg_lookup({"name": "Z"}) -> {"name": "z", "mass_GeV": 91.188, "charge": 0, "width": "2.4955 GeV"}

=== Final answer ===
The invariant mass of the dimuon system is 90.91 GeV. This is most compatible
with the Z boson (m_Z = 91.188 GeV, width 2.50 GeV) — the measured mass lies
well within one natural width of the Z peak.
```

Watch the `[turn N]` trace: the agent looks up the muon mass, feeds it into
`invariant_mass`, gets ≈ 90.9 GeV, checks the Z with `pdg_lookup`, and only
then answers. Nobody told it that plan — it came from the question, the tool
descriptions, and the intermediate results.

Run it again: the exact sequence may differ (tools may be batched in one turn
or spread across several). That non-determinism is normal for agents.

---

## 6. When Things Go Wrong — Guardrails

Three guardrails are already in the loop above; they are the difference
between a demo and something you can trust:

1. **`max_turns`** — a model that gets confused can call tools forever. Always
   bound the loop.
2. **Errors as messages, not crashes** — the `try/except` turns bad arguments
   into an `ERROR: ...` string the model can read and recover from. The
   helpful "unknown particle" message in `pdg_lookup` works the same way.
3. **The model executes nothing** — only functions in `TOOL_FUNCS` can run,
   with arguments parsed by *your* code. Never `eval()` model output, and
   keep tools free of side effects (no file deletion, no shell) until you
   trust the loop.

Watch the agent recover from a failed lookup by itself:

```python
print(run_agent(
    "What is the lifetime of the tau lepton, in seconds? "
    "Try looking up 'tauon' first.",
    show_reasoning=True,
))
```

**Example output:**
```
  [turn 0] pdg_lookup({"name": "tauon"}) -> Unknown particle 'tauon'. Known particles: electron, higgs, j/psi, k+, muon, neutron, photon, pi+, pi0, proton, tau, top, upsilon, w, z
  [turn 1] pdg_lookup({"name": "tau"}) -> {"name": "tau", "mass_GeV": 1.77693, "charge": -1, "lifetime": "2.903e-13 s"}

The tau lepton has a lifetime of 2.903e-13 seconds.
```

The first call fails, the error message lists the known names, and the model
retries with `tau` — self-correction, driven entirely by a good error string.
There's no alias table mapping "tauon" to "tau" anywhere in this code — the
model reads the plain-text error, recognizes "tau" in the list as the
particle it meant, and retries. That's genuine reasoning over text, not a
lookup trick.

`show_reasoning=True` above prints the model's private chain-of-thought, if it
returns any, so you can watch that reasoning happen instead of just inferring
it from the retry. Whether you see much depends on the model: `gpt-oss` may
not spend much reasoning budget on a lookup this simple — try
`model="minimax-m2"` for a more talkative trace.

---

## 7. Exercises

**Exercise 1 — your own question.** Ask the agent something that needs both
tools in a different combination, e.g. two electrons near the Upsilon, or a
muon pair at 3.1 GeV. Watch the trace: did it plan the way you expected?

**Exercise 2 — add a third tool.** The momentum of each daughter in a
two-body decay at rest is

$$p = \frac{\sqrt{\left(M^2 - (m_1+m_2)^2\right)\left(M^2 - (m_1-m_2)^2\right)}}{2M}$$

Implement `two_body_decay_momentum(M, m1, m2)`, write its schema, register it
in `TOOL_FUNCS` and `TOOL_SCHEMAS`, and ask:
*"What is the momentum of each muon when a J/psi decays at rest to mu+mu-?"*
The agent should look up both masses, then call your new tool.

```python
# Exercise 2 — starter skeleton
def two_body_decay_momentum(M, m1, m2):
    """Momentum (GeV) of each daughter in a two-body decay at rest."""
    # your code here (see the formula above; return a string with units)
    ...

DECAY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "two_body_decay_momentum",
        "description": "...",          # describe it well — the model reads this!
        "parameters": {
            "type": "object",
            "properties": {
                # M, m1, m2 ...
            },
            "required": ["M", "m1", "m2"],
        },
    },
}

# TOOL_FUNCS["two_body_decay_momentum"] = two_body_decay_momentum
# TOOL_SCHEMAS.append(DECAY_SCHEMA)
# print(run_agent("What is the momentum of each muon when a J/psi "
#                 "decays at rest to mu+ mu-?"))
```

<details>
<summary><strong>Click to reveal a solution</strong></summary>

```python
def two_body_decay_momentum(M, m1, m2):
    """Momentum (GeV) of each daughter in a two-body decay at rest."""
    val = (M**2 - (m1 + m2)**2) * (M**2 - (m1 - m2)**2)
    p = math.sqrt(max(val, 0.0)) / (2 * M)
    return f"{p:.4f} GeV"

DECAY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "two_body_decay_momentum",
        "description": (
            "Compute the momentum (GeV) of each daughter particle in a "
            "two-body decay M -> m1 + m2, evaluated in the rest frame of M."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "M":  {"type": "number", "description": "Mass of the parent particle, in GeV"},
                "m1": {"type": "number", "description": "Mass of the first daughter particle, in GeV"},
                "m2": {"type": "number", "description": "Mass of the second daughter particle, in GeV"},
            },
            "required": ["M", "m1", "m2"],
        },
    },
}

TOOL_FUNCS["two_body_decay_momentum"] = two_body_decay_momentum
TOOL_SCHEMAS.append(DECAY_SCHEMA)
print(run_agent("What is the momentum of each muon when a J/psi "
                "decays at rest to mu+ mu-?"))
```

For J/ψ → μ⁺μ⁻ (M=3.0969 GeV, m1=m2=0.10566 GeV) this gives ≈1.545 GeV per
muon — matches the equal-mass shortcut `p = √(M²/4 − m²)`.

</details>

**Challenge (take-home) — a retrieval tool.** Wrap the RAG `retrieve()`
function from the Chat notebook as a `search_docs(query)` tool. Your agent can
then *decide* when to search documentation — which is precisely how "agentic
RAG" works in production systems.

---

## Takeaways

- An agent = LLM + tool schemas + a `while` loop. ~30 lines, no framework.
- The model only ever *requests* tool calls; your code executes them and
  reports back with `role="tool"` messages. The transcript is the state.
- Tool `description` fields are prompts — write them carefully.
- Guardrails from day one: bound the loop, return errors as readable strings,
  never execute arbitrary model output.
- The agentic tools from the previous lesson (opencode, Claude Code) are this
  exact loop with file-editing and shell tools attached. You now know how
  they work.

**Next:** [Agentic Physics Analysis](5_analysis.html) — the same loop scaled up
to a full research framework, running a H→4ℓ measurement on NRP models.
