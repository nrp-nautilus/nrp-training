"""'AI in the Classroom': Jupyter AI, the API, and stable task names.

Part of the NAIRR Classroom webinar deck: slides.py imports the section files in order. Shared constants
and helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
"""
from common import *  # noqa: F401,F403

section("AI in the Classroom", "Where a lot of courses are going.")

AI_CELLS = """%load_ext jupyter_ai_magics

%%ai openai-chat:qwen3
Explain a p-value to a biology student in three sentences.

# or from Python, with a token from nrp.ai/llmtoken
from openai import OpenAI
client = OpenAI(base_url="https://ellm.nrp-nautilus.io/v1",
                api_key=os.environ["OPENAI_API_KEY"])"""
add("Hosted Models in JupyterLab", [
    Bullets(X0, TOP + 0.15, 5.6, 5.2, [
        "NRP hosts open-weight models (Qwen, DeepSeek, Gemma, gpt-oss and more) behind one OpenAI-compatible "
        "endpoint",
        "**Jupyter AI** in JupyterLab: a chat panel, and an `%%ai` cell magic, pointed at NRP's models",
        "Put it in your course image: students log in and use it, no token handoff",
        "Or students call the models from Python, with a token from **nrp.ai/llmtoken**",
        "Free for research and education, like the rest of NRP"], size=17, gap=10),
    Code(6.55, TOP + 0.15, 6.18, 4.2, AI_CELLS, size=12.5, title="Notebook cells", typed=True),
    Link(6.55, TOP + 4.5, 6.18, 0.3, "https://nrp.ai/documentation/userdocs/ai/llm-managed/", size=13),
], secs=70, notes="""
A word on AI, since that's where a lot of courses are going. NRP hosts open-weight models, Qwen, DeepSeek, Gemma, gpt-oss and more, behind one OpenAI-compatible endpoint. The easiest way into a class is Jupyter AI: a chat panel in JupyterLab and an %%ai cell magic, pointed at NRP's models. That's what you saw in Carl Boettiger's class in Frank's talk, and it's in the image of the hub this webinar runs on. Put it in your course image and students just log in and use it, with no token handoff. Students can also call the models from Python with their own token. It's all free for research and education.
""")

def chain_of(task):
    r = next(r for r in S["llm_routes"] if task in r["models"])
    out = []
    for b in sorted(r["backends"], key=lambda b: b["priority"]):
        n = b["name"].replace("envoy-ai-gateway-nrp-", "").replace("envoy-ai-gateway-sdsc-", "").replace("-direct", "")
        n = {"massedcompute-gemma4": "gemma-small-e4b"}.get(n, n)
        out.append(n)
    return out


trows = [["Ask for", "Tried in this order"]] + [[t, " → ".join(chain_of(t))] for t in TASKS
                                                if any(t in r["models"] for r in S["llm_routes"])]
tm = [Table(X0, TOP + 0.1, 7.15, 5.0, trows, [1.55, 5.6], size=12.5, mono=(0, 1), row_h=0.5, cls="rows")]
coding = chain_of("coding")
tm.append(Box(8.2, TOP + 0.1, 4.53, 0.75, "model: coding", None, state="active", head_size=16))
ORD = ["1st choice", "2nd choice", "3rd choice", "4th choice", "5th", "6th", "7th"]
CH_Y, CH_H, CH_DY = TOP + 1.1, 0.62, 0.78
for i, n in enumerate(coding):
    y = CH_Y + i * CH_DY
    tm.append(Box(8.75, y, 3.98, CH_H, n, ORD[i], state="white", head_size=15, sub_size=11.5,
                  hl=[1] if i == 0 else [2] if i == 1 else None, mono_sub=False))
    tm.append(Arrow(8.45, TOP + 0.85, 8.45, y + CH_H / 2, head=False, color="C9D4E3"))
    tm.append(Arrow(8.45, y + CH_H / 2, 8.75, y + CH_H / 2, hl=[1] if i == 0 else [2] if i == 1 else None))
tm.append(Raw(8.75, CH_Y, 3.98, CH_H, '<div class="eject">unhealthy: ejected</div>', only=[2],
              draw=lambda s, k: (s.rect(8.75, CH_Y, 3.98, CH_H, fill=RED, radius=0.12),
                                 s.text(8.75, CH_Y, 3.98, CH_H, P("unhealthy: ejected", size=13, bold=True, color=WHITE,
                                                                 align="c"), anchor="m"))))
EXPL = {0: "A fallback order, not a ranking of users or models.",
        1: "Every request goes to the 1st choice while it's healthy.",
        2: "Only when it's down, or ejected by the health checks, does the 2nd choice answer."}
for k, s_ in EXPL.items():
    tm.append(Text(8.2, CH_Y + len(coding) * CH_DY + 0.1, 4.53, 0.8, T(s_, size=15, bold=k > 0, color=NAVY if k else BODY),
                   only=[k] if k < 2 else [2]))
add("Models and Task Names", tm, steps=2, cls="tasks", secs=60, notes=f"""
One detail that matters for course materials: the model catalog changes, so you can ask for a task instead of a model. The name coding isn't a model; it's an ordered list: {', then '.join(coding)}. That order is about failover, not about who gets better service.

[click] Every request for coding goes to the first choice while it's healthy.

[click] If it's down, the next one answers. For a course, that means an assignment written against a task name keeps working all term, even as models come and go. There's a list for coding, general, reasoning, vision and more.
""")
