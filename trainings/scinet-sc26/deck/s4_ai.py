"""'AI on NRP': the LLM service, the request path, gateway policies, vLLM, the ops bot.

Part of the SCinet deck: slides.py imports the section files in order. Shared constants and
helpers come from common.py; add(..., secs=N) sets the slide's duration for the timing tags.
"""
from common import *  # noqa: F401,F403

# ═════════════════════════════════════════════════════════════════════════════════════
# AI
# ═════════════════════════════════════════════════════════════════════════════════════
section("AI on NRP", "[0:23] The AI service: the most interesting system we run right now.")

# GPUs per model, from the snapshot
per_model = {}
for p in S["llm_placement"]:
    m = model_name(p["workload"])
    g = next(s for s in S["llm_servers"] if s["name"] == p["workload"])
    d = per_model.setdefault(m, {})
    d[short_gpu(p["gpu"])] = d.get(short_gpu(p["gpu"]), 0) + sum(g["gpu"].values())
ORDER = ["deepseek-v4-flash", "glm-5", "kimi", "minimax", "qwen3", "qwen3-small", "gpt-oss", "gemma", "gemma-small",
         "gemma-small-e4b", "qwen3-embedding"]
mrows = [["Model name", "Serving on"]] + [[m, ", ".join(f"{v} × {k}" for k, v in sorted(per_model[m].items(),
                                                                                       key=lambda kv: -kv[1]))]
                                          for m in ORDER if m in per_model]
add("The LLM Service", [
    Bullets(X0, TOP + 0.15, 5.5, 5.2, [
        "OpenAI API: `ellm.nrp-nautilus.io/v1`",
        "Anthropic API, for Claude Code and similar tools: `ellm.nrp-nautilus.io/anthropic`",
        f"{len(MODEL_NAMES)} model names, the same on both",
        f"{S['llm_gpus']} GPUs serve them, from A10s to H200s, at {len({p['site'] for p in S['llm_placement']})} sites",
        f"About {TOKENS_A_DAY} tokens a day (September 2026)",
        "Free for research and education, with a token from nrp.ai/llmtoken"], size=17, gap=8),
    Table(6.45, TOP + 0.1, 6.28, 4.95, mrows, [2.5, 3.78], size=13, mono=(0,), row_h=0.41, cls="rows"),
    Text(6.45, TOP + 5.1, 6.28, 0.3, T(f"Model-server pods by GPU, {SNAP}. The catalog changes.", size=12, color=MUTED)),
    Raw(0, 0, 0.1, 0.1, "<style>.llmsvc ul.bl code { white-space: nowrap; font-weight: 600; color: var(--navy); }</style>",
        pptx=False),
], cls="llmsvc", notes=f"""
[0:23] The LLM service. There's an OpenAI-compatible endpoint, and an Anthropic-compatible one at /anthropic, which is what our Claude Code configuration points at. Every model server behind them is vLLM speaking the OpenAI API, so the Anthropic side is a translation: the gateway in front, which we'll follow step by step in a minute, turns an Anthropic Messages request into an OpenAI chat completion, and turns the answer, streaming included, back into Anthropic's format. That's Envoy AI Gateway, version 1.0 on the cluster. Our docs warn that not every model routes cleanly through it; tool calls depend on the model. {len(MODEL_NAMES)} model names behind it, for open-weight models like DeepSeek, GLM, Kimi, Qwen and Gemma. {S['llm_gpus']} GPUs serve them, and it's used heavily: about seven billion tokens a day in September. It's free for research and education with a token.

On the right is what's serving each model right now: DeepSeek on H100s, GLM on H200s and H100s, Kimi and MiniMax on eight A100s each, and the small models on A10s and A6000s. Let me show you where those GPUs are.
""")

LLM = llm_sites(GEO, S)


def llm_map_html():
    w, h = GEO["width"], GEO["height"]
    land = "".join("M" + "L".join(f"{x:g},{y:g}" for x, y in pts) + "Z" for pts in GEO["paths"])
    r = PIN_STYLE["llm"][1]
    svg = (f'<svg class="usmap llm" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}"><path class="land" '
           f'd="{land}"/><defs><path id="pin-llm" d="{pin_path(r)}"/></defs>')
    for i, p in enumerate(LLM):
        svg += (f'<g transform="translate({p["x"]:.1f},{p["y"]:.1f})"><g class="pin k-llm" style="--d:{0.2 + i * 0.25:.2f}s">'
                f'<use href="#pin-llm"/><circle cy="{-1.6 * r:.1f}" r="{0.62 * r:.1f}"/><text y="{-1.6 * r:.1f}" '
                f'text-anchor="middle" dominant-baseline="central">{p["n"]}</text></g></g>')
    return svg + "</svg>"


lrows = [["#", "Site", "Models", "GPUs"]] + [[str(p["n"]), " + ".join(
    s.replace("University of California, San Diego", "UC San Diego").replace("San Diego State University", "SDSU")
    .replace("California State University, Sacramento", "Sacramento State")
    .replace("California State Polytechnic University, Humboldt", "Cal Poly Humboldt")
    .replace("University of Nebraska, Lincoln", "Nebraska–Lincoln").replace("University of New Mexico", "UNM")
    for s in p["sites"]), ", ".join(p["models"]), p["gpu_text"]] for p in LLM]
add("Where the Models Run", [
    Raw(X0, TOP + 0.3, 5.9, 3.95, llm_map_html(),
        draw=lambda s, k: s.image(FIG / "llm_map.png", X0, TOP + 0.3, 5.9, 3.95, align="l", valign="t")),
    Table(6.7, TOP + 0.1, 6.03, 5.0, lrows, [0.35, 1.9, 2.3, 1.5], size=11.5, row_h=0.5, cls="rows", bold_first=False),
    Text(X0, TOP + 4.45, 5.9, 0.9, T("Every pin is a set of model servers in the same cluster, behind the same "
                                     "endpoint. Fresno State and Internet2 Ann Arbor are placed by city.", size=13,
                                     color=MUTED)),
], cls="llmsites", notes="""
[0:24] Here's where the model servers are running this week: the San Diego campuses, Nebraska, Sacramento State, Chico State, Fresno State, Humboldt, New Mexico, and an Internet2 node in Ann Arbor. That's the point of the whole design: GPUs that campuses contributed, wherever they are, serving one endpoint. A request from Chicago can be answered by a GPU in Fresno or Ann Arbor, and the user never knows.
""")

# The request path, step by step
RP_Y, RP_H = TOP + 0.3, 1.0
rp = [Box(X0, RP_Y, 1.55, RP_H, "Client", "OpenAI API", head_size=16, sub_size=12, hl=[1, 4]),
      Box(2.6, RP_Y, 2.35, RP_H, "Envoy AI Gateway", "ellm.nrp-nautilus.io", head_size=15, sub_size=12, hl=[1, 2, 4]),
      Box(5.5, RP_Y, 2.25, RP_H, "AIGatewayRoute", "x-ai-eg-model: qwen3", head_size=15, sub_size=12, mono_sub=True,
          hl=[2]),
      Box(8.3, RP_Y, 2.05, RP_H, "InferencePool", "with an endpoint picker", head_size=15, sub_size=12, hl=[3]),
      Arrow(2.15, RP_Y + 0.5, 2.6, RP_Y + 0.5, hl=[1]), Arrow(4.95, RP_Y + 0.5, 5.5, RP_Y + 0.5, hl=[2]),
      Arrow(7.75, RP_Y + 0.5, 8.3, RP_Y + 0.5, hl=[3]),
      Box(2.6, RP_Y + 1.75, 2.35, 0.95, "llm-auth", "ext_authz over gRPC; fail closed", state="white", head_size=15,
          sub_size=12, hl=[1]),
      Arrow(3.77, RP_Y + 1.0, 3.77, RP_Y + 1.75, hl=[1]),
      Box(5.5, RP_Y + 1.75, 2.25, 0.95, "Rate limiter", "output tokens per API token and model", state="white",
          head_size=15, sub_size=12, hl=[4]),
      Arrow(4.95, RP_Y + 0.9, 5.5, RP_Y + 2.2, hl=[4], step=4)]
pods = [("vLLM pod a", "queue 6 · KV cache 88%"), ("vLLM pod b", "queue 0 · KV cache 31%"),
        ("vLLM pod c", "queue 2 · KV cache 64%")]
for i, (h, b) in enumerate(pods):
    rp.append(Box(10.9, RP_Y - 0.25 + i * 0.85, 1.83, 0.72, h, b, state="white", head_size=13, sub_size=10.5,
                  hl=[3] if i == 1 else None))
    rp.append(Arrow(10.35, RP_Y + 0.5, 10.9, RP_Y + 0.11 + i * 0.85, hl=[3] if i == 1 else None,
                    color=MUTED if i == 1 else "C9D4E3"))
rp.append(Text(10.9, RP_Y + 2.33, 1.83, 0.4, T("example values", size=11, color=MUTED, align="c")))
CAPS = {0: ("One request, five stops", "The gateway is the Envoy Gateway from the ingress slide, plus its AI "
            "extension, Envoy AI Gateway. A client asks for `qwen3`."),
        1: ("1. Who are you?", "The gateway sends the bearer token to an external auth service over gRPC. If auth "
            "can't answer, the request fails: fail closed."),
        2: ("2. Which model?", "The gateway reads `model` from the JSON body into the `x-ai-eg-model` header, and an "
            "AIGatewayRoute rule matches it to a backend: here an InferencePool."),
        3: ("3. Which pod?", "The endpoint picker scores the pool's vLLM pods by queue depth, KV-cache use and "
            "prefix-cache hits, and picks one."),
        4: ("4. The answer, and the token count", "vLLM's answer goes back through the gateway, which reads the token "
            "counts and tells the rate limiter how many output tokens this API token just used on this model.")}
for k, (h, b) in CAPS.items():
    rp.append(Text(X0, TOP + 3.45, W, 1.6, [T(h, size=22, bold=True, color=NAVY), T(b, size=19, color=BODY, before=6)],
                   only=[k]))
# the request: a dot that walks the box edges to each stop (corners: top-right of the box it waits at)
CL_R, GW_L, GW_R, GW_C, RT_L, RT_R, IP_L, IP_R = 2.15, 2.6, 4.95, 3.775, 5.5, 7.75, 8.3, 10.35
TOP_E, MID, BOT_E = RP_Y, RP_Y + 0.5, RP_Y + 1.0
POD_B = (10.9, 12.73, RP_Y + 0.6, RP_Y + 0.96)            # left, right, top, middle of pod b
rp.append(packet("reqpath", {
    0: [(CL_R, TOP_E)],
    1: [(CL_R, TOP_E), (CL_R, MID), (GW_L, MID), (GW_L, BOT_E), (GW_C, BOT_E), (GW_C, RP_Y + 1.87), (GW_C, BOT_E),
        (GW_R, BOT_E), (GW_R, TOP_E)],                                  # into llm-auth and back
    2: [(GW_R, TOP_E), (GW_R, MID), (RT_L, MID), (RT_L, TOP_E), (RT_R, TOP_E)],
    3: [(RT_R, TOP_E), (RT_R, MID), (IP_L, MID), (IP_L, TOP_E), (IP_R, TOP_E), (IP_R, MID), (POD_B[0], POD_B[3]),
        (POD_B[0], POD_B[2]), (POD_B[1], POD_B[2])],
    4: [(POD_B[1], POD_B[2]), (POD_B[0], POD_B[2]), (POD_B[0], POD_B[3]), (IP_R, BOT_E), (GW_R, BOT_E),
        (CL_R, BOT_E), (CL_R, TOP_E)],                                   # the answer, back to the client
}, speed=5))
# ... and the token count: a small dot leaves the gateway for the rate limiter as the answer passes through
TOK = ((GW_R * PX, (RP_Y + 0.92) * PX), (RT_L * PX + 4, (RP_Y + 2.2) * PX))
rp.append(Raw(0, 0, 13.333, 7.5, f'''<style>
.reqpath .tok {{ position:absolute; width:18px; height:18px; margin:-9px 0 0 -9px; border-radius:50%; background:var(--orange);
  border:3px solid #fff; box-shadow:0 2px 6px rgba(0,0,0,.3); opacity:0; left:{TOK[0][0]:.0f}px; top:{TOK[0][1]:.0f}px; }}
.reqpath[data-cur="4"] .tok {{ animation: rptok .6s ease-in-out 1.45s forwards; }}
@keyframes rptok {{ 0% {{ opacity:1; left:{TOK[0][0]:.0f}px; top:{TOK[0][1]:.0f}px; }}
  100% {{ opacity:1; left:{TOK[1][0]:.0f}px; top:{TOK[1][1]:.0f}px; }} }}
</style><span class="tok"></span>''', pptx=False, style="pointer-events:none;z-index:6;"))
add("A Request, Step by Step", rp, steps=4, cls="reqpath", builds=True, notes="""
[0:25] One request through the gateway. Remember Envoy Gateway from the ingress slide: the LLM gateway is the same thing plus its AI extension, Envoy AI Gateway. A client asks for qwen3 with the standard OpenAI API.

[click] First, who are you. Envoy calls an external auth service, llm-auth, over gRPC with the bearer token, and it fails closed: if auth can't answer, nobody gets through.

[click] Second, which model. The gateway parses the JSON body, lifts the model name into a header, x-ai-eg-model, and an AIGatewayRoute rule matches that header to a backend. Here the backend is an InferencePool, from the Gateway API inference extension.

[click] Third, which pod. The pool has an endpoint picker that scores the vLLM pods on queue depth, KV-cache use, and whether a pod already has this prompt's prefix cached, which matters a lot for chat and agents. The numbers here are illustrative; the logic is real.

[click] Fourth, the answer. It comes back through the gateway to the client. On the way, the gateway reads the token counts from the response and reports the output tokens to the rate limiter, which keeps a per-minute count for each API token and model. That count is what the limit on the next slide checks.
""")

BTP = '''apiVersion: gateway.envoyproxy.io/v1alpha1
kind: BackendTrafficPolicy
metadata: {name: envoy-ai-gateway-nrp, namespace: nrp-llm}
spec:
  rateLimit:
    type: Global
    global:
      rules:
      - clientSelectors:
        - headers:
          - {name: authorization, type: Distinct}
          - {name: x-ai-eg-model, type: Distinct}
        limit: {requests: 48000, unit: Minute}
        cost:
          request: {from: Number, number: 1}
          response:
            from: Metadata
            metadata: {namespace: io.envoy.ai_gateway,
                       key: llm_output_token}
  retry:
    numRetries: 2
    retryOn: {httpStatusCodes: [500, 502, 503, 504]}
  healthCheck:
    active: {type: HTTP, http: {path: /health}, interval: 10s,
             unhealthyThreshold: 3}
    passive: {consecutive5XxErrors: 2, baseEjectionTime: 30s,
              maxEjectionPercent: 50}'''
HDRS = '''$ curl -si https://ellm.nrp-nautilus.io/v1/chat/completions \\
    -H "Authorization: Bearer $OPENAI_API_KEY" \\
    -d '{"model": "qwen3", ...}' | grep -i ratelimit
x-ratelimit-limit: 48000, 48000;w=60
x-ratelimit-remaining: 47999
x-ratelimit-reset: 9'''
add("Gateway Policies", [
    Code(X0, TOP, 6.45, 5.3, BTP, size=10, lang="yaml",
         lines_hl={**{i: [1] for i in range(5, 20)}, **{i: [2] for i in range(20, 23)},
                   **{i: [3] for i in range(23, 28)}}),
    Text(7.25, TOP + 0.05, 5.48, 2.3, [
        T("**Rate limit:** 48,000 output tokens a minute, per API token and model", size=16, step=1),
        T("**Retries:** twice, on 5xx", size=16, before=10, step=2),
        T("**Health:** probe /health every 10 s; eject a pod after two 5xx", size=16, before=10, step=3)]),
    Text(7.25, TOP + 2.55, 5.48, 0.35, T("What a client sees (demo, 10 Nov)", size=14, bold=True, color=NAVY)),
    Code(7.25, TOP + 2.95, 5.48, 2.35, HDRS, size=10.5),
], steps=3, cls="policies", notes="""
[0:26] The policy behind that, straight from the cluster. [click] The rate limit is global, keyed on the authorization header and the model, and what counts against it is the number of output tokens in each response: 48,000 a minute per API token and model. Clients see it in standard rate-limit headers, as in the curl on the right. [click] Retries, twice, on 500-series errors. [click] Active health checks on /health every ten seconds, and passive outlier detection: two 5xx in a row and the pod is ejected for thirty seconds, never more than half the pool.
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
tm.append(Text(8.2, TOP + 5.1, 4.53, 0.4, T("GitLab Duo Self-Hosted uses `service`.", size=13, color=MUTED)))
add("Ask for a Task, Not a Model", tm, steps=2, cls="tasks", notes=f"""
[0:27] One thing I like about this setup: you can ask for a task instead of a model. The model name coding is not a model. It's an ordered list of backends: {', then '.join(coding)}. That order is about failover, not about who gets better service: no user and no request is ranked above another.

[click] Every request for coding goes to the first choice as long as it's healthy.

[click] If it's down, or the health checks from the previous slide have ejected it, the gateway falls through to the second, and so on. Users and tools get a stable name while the catalog rotates underneath. Our own GitLab's AI features use one of these, service.
""")

# Fitting a big model: the memory math for GLM-5.3 on 4 × H200, then the levers and what runs where today
FIT_PARAMS, FIT_BUDGET, FIT_MAX = 744, 4 * 141, 1500           # billions of parameters; GB
FIT_ROWS = [("BF16", "2 bytes a weight", 2 * FIT_PARAMS, RED), ("FP8", "1 byte", FIT_PARAMS, RED),
            ("NVFP4", "4 bits, plus scales", 465, BLUE)]
FX, FY = X0, TOP + 0.75                                         # the chart's top-left, inches
FB0, FBW = 1.6, 4.25                                            # bar origin and full width (= FIT_MAX), inches
FROW0, FROWD, FROWH = 0.45, 0.62, 0.44


def fit_x(gb):
    return FB0 + FBW * gb / FIT_MAX


def fit_html():
    px = lambda v: f"{v * PX:.0f}px"
    h = (f'<div class="fband" style="left:{px(FB0)};top:{px(0.25)};width:{px(fit_x(FIT_BUDGET) - FB0)};height:{px(2.0)}">'
         + "".join(f'<i style="left:{px(fit_x(141 * g) - FB0)}"></i>' for g in (1, 2, 3)) + "</div>"
         f'<p class="flab" style="left:{px(FB0)};top:{px(-0.05)}">4 × H200 = {FIT_BUDGET} GB</p>')
    for i, (lab, sub, gb, col) in enumerate(FIT_ROWS):
        y = FROW0 + i * FROWD
        w = fit_x(gb) - FB0
        verdict = f"{gb:,} GB · doesn't fit" if gb > FIT_BUDGET else f"{gb} GB"
        out = " out" if FIT_BUDGET < gb < 1000 else ""           # short red bars: the label goes past the end
        inner = (f'<p class="fn"><b>{lab}</b><span>{sub}</span></p>'
                 f'<div class="fbar {"bad" if gb > FIT_BUDGET else "ok"}" style="left:{px(FB0)};width:{px(w)};'
                 f'height:{px(FROWH)}"><i></i><em class="{out}">{verdict}</em></div>')
        if gb <= FIT_BUDGET:
            inner += (f'<div class="fkv" style="left:{px(fit_x(gb))};width:{px(fit_x(FIT_BUDGET) - fit_x(gb))};'
                      f'height:{px(FROWH)}"></div><p class="fok" style="left:{px(fit_x(FIT_BUDGET) + 0.12)};'
                      f'line-height:{px(FROWH)}">fits; the rest holds the KV cache</p>')
        h += f'<div class="frow" data-s="{i + 1}" style="top:{px(y)};height:{px(FROWH)}">{inner}</div>'
    h += f'<div class="fline" style="left:{px(fit_x(FIT_BUDGET))};top:{px(0.2)};height:{px(2.1)}"></div>'
    h += f'<div class="fax" style="left:{px(FB0)};top:{px(2.35)};width:{px(FBW)}"></div>'
    for v in (0, 500, 1000, 1500):
        h += f'<p class="ftk" style="left:{px(fit_x(v) - 0.5)};top:{px(2.4)}">{v:,} GB</p>'
    css = """<style>
.fitm .sb2 { position:absolute; }
.fitm .fband { position:absolute; background:#E3ECF5; border-radius:6px; }
.fitm .fband i { position:absolute; top:0; bottom:0; width:0; border-left:2px dashed #fff; }
.fitm .flab, .fitm .ftk, .fitm .fok { position:absolute; margin:0; white-space:nowrap; }
.fitm .flab { font:700 24px var(--f-body); color:var(--navy); }
.fitm .ftk { width:144px; text-align:center; font-size:20px; color:var(--muted); }
.fitm .fax { position:absolute; height:2px; background:var(--muted); }
.fitm .fline { position:absolute; width:0; border-left:4px dashed var(--navy); z-index:3; }
.fitm .frow { position:absolute; left:0; right:0; }
.fitm .fn { position:absolute; left:0; width:220px; top:-4px; line-height:1.05; }
.fitm .fn b { display:block; font-size:30px; color:var(--navy); } .fitm .fn span { font-size:20px; color:var(--muted); }
.fitm .fbar { position:absolute; top:0; }
.fitm .fbar i { position:absolute; left:0; top:0; bottom:0; width:0; border-radius:6px; transition:width 1.1s cubic-bezier(.3,.7,.2,1) .2s; }
.fitm .fbar.bad i { background:#C9554D; } .fitm .fbar.ok i { background:var(--blue); }
.fitm .frow.on .fbar i { width:100%; }
.fitm .fbar em { position:absolute; right:12px; top:0; bottom:0; display:flex; align-items:center; font:700 22px var(--f-body); color:#fff; font-style:normal; white-space:nowrap; opacity:0; transition:opacity .4s 1.1s; z-index:2; }
.fitm .frow.on .fbar em { opacity:1; }
.fitm .fbar em.out { right:auto; left:calc(100% + 14px); color:#B3261E; }
.fitm .fkv { position:absolute; top:0; border-radius:0 6px 6px 0; background:repeating-linear-gradient(45deg,#F2C46D 0 8px,#F8DDA6 8px 16px); opacity:0; transition:opacity .5s 1.3s; }
.fitm .fok { top:0; font:700 22px var(--f-body); color:#1B7F55; opacity:0; transition:opacity .5s 1.5s; }
.fitm .frow.on .fkv, .fitm .frow.on .fok { opacity:1; }
</style>"""
    return css + h


def fit_draw(s, k):
    s.rect(FX + FB0, FY + 0.25, fit_x(FIT_BUDGET) - FB0, 2.0, fill="E3ECF5", radius=0.03)
    s.text(FX + FB0, FY - 0.08, 3.5, 0.3, P(f"4 × H200 = {FIT_BUDGET} GB", size=12, bold=True, color=NAVY))
    for i, (lab, sub, gb, col) in enumerate(FIT_ROWS):
        y = FY + FROW0 + i * FROWD
        s.text(FX, y - 0.04, 1.55, FROWH + 0.1, [P(lab, size=15, bold=True, color=NAVY, line=0.9),
                                                 P(sub, size=10, color=MUTED, line=0.9)])
        s.rect(FX + FB0, y, fit_x(gb) - FB0, FROWH, fill="C9554D" if gb > FIT_BUDGET else BLUE, radius=0.1)
        txt = f"{gb:,} GB · doesn't fit" if gb > FIT_BUDGET else f"{gb} GB"
        if FIT_BUDGET < gb < 1000:
            s.text(FX + fit_x(gb) + 0.1, y, 2.5, FROWH, P(txt, size=11, bold=True, color=RED), anchor="m")
        else:
            s.text(FX + FB0, y, fit_x(gb) - FB0 - 0.08, FROWH, P(txt, size=11, bold=True, color=WHITE, align="r"),
                   anchor="m")
        if gb <= FIT_BUDGET:
            s.rect(FX + fit_x(gb), y, fit_x(FIT_BUDGET) - fit_x(gb), FROWH, fill="F2C46D", radius=0.05)
            s.text(FX + fit_x(FIT_BUDGET) + 0.1, y, 3.0, FROWH,
                   P("fits; the rest holds the KV cache", size=11, bold=True, color="1B7F55"), anchor="m")
    s.line(FX + fit_x(FIT_BUDGET), FY + 0.2, FX + fit_x(FIT_BUDGET), FY + 2.3, color=NAVY, width=2, arrow=False,
           dash=True)
    s.line(FX + FB0, FY + 2.35, FX + FB0 + FBW, FY + 2.35, color=MUTED, width=1, arrow=False)
    for v in (0, 500, 1000, 1500):
        s.text(FX + fit_x(v) - 0.5, FY + 2.4, 1.0, 0.25, P(f"{v:,} GB", size=10, color=MUTED, align="c"))


FIT_TABLE = [["Model", "Weights", "Format", "GPUs"],
             ["glm-5", "465 GB", "NVFP4", "4 × H200, or 8 × H100"],
             ["kimi", "595 GB", "INT4", "8 × A100"],
             ["deepseek-v4-flash", "510 GB", "FP8", "2 nodes × 4 H100"],
             ["minimax", "250 GB", "MXFP8", "8 × A100"],
             ["qwen3", "186 GB", "FP8", "4 × A100"],
             ["qwen3-small", "31 GB", "FP8", "4 × A6000, or 1 × H200"],
             ["gpt-oss", "65 GB", "MXFP4", "2 × A6000"]]
add("Fitting Big Models on Contributed GPUs", [
    Text(X0, TOP + 0.05, 5.95, 0.65, [T(f"One model: GLM-5.3, {FIT_PARAMS} B parameters", size=18, bold=True, color=NAVY),
                                       T("What its weights need at each precision", size=14, color=MUTED, before=2)]),
    Raw(FX, FY, 5.95, 2.75, fit_html(), draw=fit_draw, cls="sb2"),
    Bullets(X0, TOP + 3.45, 5.95, 1.85, [
        "**Quantize:** FP8, NVFP4, MXFP4, INT4: ½ to ¼ the bytes of BF16",
        "**Split:** tensor parallel inside a node, pipeline parallel across nodes, expert parallel for MoE",
        "**Budget the KV cache:** what's left after the weights holds the context",
        "**Place by capability:** GPU memory and generation, not hostname"], size=14.5, gap=5, step=4),
    Text(6.95, TOP + 0.05, 5.78, 0.4, T("What runs where today", size=18, bold=True, color=NAVY), step=4),
    Table(6.95, TOP + 0.55, 5.78, 4.2, FIT_TABLE, [1.95, 0.9, 0.95, 1.98], size=12, mono=(0,), row_h=0.5, step=4),
    Text(6.95, TOP + 4.7, 5.78, 0.5, T(f"Weights: checkpoint size on Hugging Face. GPUs: the model servers on the "
                                       f"cluster, {SNAP}.", size=12, color=MUTED), step=4),
], steps=4, cls="fitm", secs=75, notes=f"""
How do models this big fit on GPUs that campuses happened to buy? Take GLM-5.3: {FIT_PARAMS} billion parameters. Four H200s give you {FIT_BUDGET} gigabytes of GPU memory.

[click] At 16-bit precision, two bytes a weight, the weights alone are about 1.5 terabytes. No.

[click] At FP8, one byte a weight, {FIT_PARAMS} gigabytes. Still no.

[click] At NVFP4, four bits a weight plus scaling factors, the checkpoint is 465 gigabytes. It fits, and the hundred or so gigabytes left over hold the KV cache: the memory every request's context needs while it's being served, the KV-cache use the endpoint picker looked at.

[click] So there are four levers. Quantize. Split the model: tensor parallel across a node's GPUs, pipeline parallel across nodes, expert parallel for mixture-of-experts models. Budget the KV cache: a longer context or more requests at once both need more of it. And place by capability: a model server asks for GPU memory and compute capability, never a hostname, so any contributed card that fits is useful. On the right is what that adds up to today, from gpt-oss on two A6000s to DeepSeek across two nodes, which is coming up.
""")

STS = """apiVersion: apps/v1
kind: StatefulSet
metadata: {name: qwen38-flash-next-a100, namespace: nrp-llm}
spec:
  replicas: 2
  template:
    metadata:
      labels: {component: llm, service-group: qwen-vllm-inference}
    spec:
      containers:
      - image: vllm/vllm-openai:v0.33.0
        args: ["vllm serve Qwen/Qwen3.8-Flash-Next-FP8 --port 5000
                --tensor-parallel-size 4 --enable-expert-parallel
                --enable-prefix-caching --max-model-len 1000000
                --kv-cache-dtype bfloat16 --otlp-traces-endpoint ..."]
        resources:
          limits: {cpu: "36", memory: 440Gi, nvidia.com/a100: 4}
        readinessProbe: {httpGet: {path: /health, port: 5000}}
      affinity:   # GPU memory > 80 GB, Ampere or newer
  volumeClaimTemplates:
  - metadata: {name: qwen38-flash-cache}
    spec: {storageClassName: linstor-igrok,
           resources: {requests: {storage: 256Gi}}}"""
sts_hl = {8: [1], 11: [2], 12: [2], 13: [2], 14: [2], 15: [2], 18: [3], 20: [4], 21: [4], 22: [4], 23: [4]}
add("Serving with vLLM", [
    Code(X0, TOP + 0.05, 7.6, 5.3, STS, size=11, lang="yaml", lines_hl=sts_hl,
         title="qwen3, from the cluster (shortened)"),
    Text(8.45, TOP + 0.1, 4.28, 5.2, [
        T("**Labels** put the pod in the `qwen3` pool, the InferencePool from the request slide", size=16, step=1),
        T("**vLLM**: the FP8 checkpoint, tensor parallel 4, expert parallel, prefix caching, traces to OpenTelemetry", size=16,
          before=12, step=2),
        T("**Health**: probes on `/health`; vLLM and DCGM metrics go to the same Prometheus and Thanos, and drive the "
          "LLM status page", size=16, before=12, step=3),
        T("**Weights** on a Linstor volume, so a restart doesn't download them again", size=16, before=12, step=4),
        T(f"{len([x for x in S['llm_servers'] if not x['name'].endswith('-worker')])} servers like this. Their config is "
          "in GitLab (`prp/llm-proxy`), applied by hand, not yet by Argo CD", size=15, color=MUTED, before=20)]),
], steps=4, cls="vllm", notes="""
[0:28] What one of those model servers looks like, from the cluster, shortened. It's a StatefulSet. [click] Its labels put it in the qwen3 pool from the request slide. [click] vLLM runs the FP8 checkpoint with tensor parallelism across four A100s and expert parallelism, the levers from the last slide, plus prefix caching and traces to an OpenTelemetry collector. [click] Health probes on /health, and the metrics go into the same Prometheus and Thanos as everything else; they drive the public LLM status page. [click] And the weights sit on a Linstor volume, the replicated block storage from earlier, so a restart doesn't re-download them.

This is one of the services I mentioned that isn't in Argo yet: the config lives in GitLab and gets applied by hand.
""")

qs = [Bullets(X0, TOP + 0.15, 5.4, 5.2, [
    "A pool selects its pods by label, so a model can have replicas anywhere",
    "Extra replicas run at **opportunistic** priority on idle GPUs; on a reserved node they also tolerate its "
    "reservation taint",
    "`qwen3-small`: 4 × A6000 at Chico State, plus two 1-GPU replicas on Fresno State's H200 node, which is "
    "reserved for Fresno",
    "`glm-5` and `gemma` borrow H100s and A100s at low priority too",
    "When the owners' pods need the GPUs, the borrowed replicas are preempted; the endpoint picker routes around "
    "the gap"], size=16, gap=8),
    Box(6.4, TOP + 0.2, 6.33, 0.85, "InferencePool qwen3-small", "selects pods by label: service-group=qwen3-small",
        state="active", head_size=16, sub_size=12)]
reps = [("CSU Chico", "4 × A6000", "normal"), ("Fresno State", "1 × H200 · opportunistic", "gold"),
        ("Fresno State", "1 × H200 · opportunistic", "gold")]
for i, (h, b, st) in enumerate(reps):
    x = 6.4 + i * 2.15
    qs.append(Box(x, TOP + 1.75, 2.03, 1.1, h, b, state=st, head_size=15, sub_size=11.5,
                  cls=f"rep r{i}"))
    qs.append(Arrow(9.56, TOP + 1.05, x + 1.0, TOP + 1.75, cls=f"rep r{i}"))
qs.append(Raw(6.4 + 2 * 2.15, TOP + 1.75, 2.03, 1.1, '<div class="eject gone">preempted</div>', only=[1],
              pptx=False))
qs.append(Text(6.4, TOP + 3.15, 6.33, 1.5, T("Fresno's own pods need the GPU back. One replica is preempted; the "
                                             "pool keeps answering from the other two.", size=16, color=BODY),
               step=1))
add("Borrowing Idle GPUs", qs, steps=1, cls="scavenge", notes="""
[0:29] This is my favorite trick, and it's the reservation taint and the opportunistic priority from the sharing slide, applied to inference. A model's pool selects pods by label, so we can add replicas anywhere. qwen3-small runs on four A6000s at Chico State, and we add two replicas on Fresno State's H200 node. That node is reserved for Fresno, so the replicas tolerate the reservation taint, and they run at opportunistic priority, so they only use those GPUs while Fresno's own work doesn't. [click] When Fresno needs a GPU, the scheduler preempts a replica, the endpoint picker stops sending it traffic, and the service keeps answering. Idle GPUs anywhere in the country become inference capacity, with no effect on their owners.
""")

# Multi-node serving: each step adds one part of the picture, with its bullet
MN_Y = TOP + 0.85                       # top of the node frames
MN_NODES = [(X0, "Node A · 4 × H100", "head pod", "serves the API · pipeline stage 1"),
            (5.0, "Node B · 4 × H100", "worker pod", "headless · pipeline stage 2")]
tn = [Frame(0.42, TOP + 0.4, 8.16, 3.4, label="group: deepseek-v41-flash-vllm", line=BLUE, dashed=True,
            label_color=BLUE, label_size=12, step=5)]
for x0, lab, pod, podsub in MN_NODES:
    tn.append(Frame(x0, MN_Y, 3.4, 2.75, label=lab, line="B9C7D8", label_size=14))
    tn.append(Box(x0 + 0.15, MN_Y + 0.45, 3.1, 0.66, pod, podsub, head_size=14, sub_size=11, step=3, hl=[3],
                  cls="mnpod"))
    tn.append(Box(x0 + 2.12, MN_Y + 0.3, 1.13, 0.28, "supervisor", None, state="gold", head_size=10.5, step=4))
    for g in range(4):
        tn.append(Box(x0 + 0.15 + g * 0.8, MN_Y + 1.35, 0.7, 0.8, f"GPU {g}", None, state="white", head_size=12,
                      hl=[1]))
    tn.append(Text(x0 + 0.15, MN_Y + 2.22, 3.1, 0.35, T("NVLink: tensor parallel 4", size=12, color=BLUE, bold=True,
                                                        align="c"), step=1))
tn += [Arrow(X0 + 3.3, MN_Y + 1.75, 5.1, MN_Y + 1.75, color=ORANGE, width=3, step=2),
       Text(X0 + 3.4, MN_Y + 1.3, 1.0, 0.35, T("NCCL", size=13, bold=True, color=ORANGE, align="c"), step=2),
       flow([[(X0 + 3.25, MN_Y + 1.75), (5.15, MN_Y + 1.75)]], n=2, dur=0.9, r=7, only=[2]),
       Arrow(X0 + 3.25, MN_Y + 0.66, 5.15, MN_Y + 0.66, color=AMBER, dashed=True, width=2, head=True, step=4),
       Arrow(5.15, MN_Y + 0.9, X0 + 3.25, MN_Y + 0.9, color=AMBER, dashed=True, width=2, head=True, step=4),
       Text(X0, TOP + 3.95, 7.8, 0.4, T("Two copies of this pair run on SDSC's Expanse H100 nodes.", size=15,
                                         color=BODY)),
       Bullets(8.8, TOP + 0.15, 3.93, 5.3, [
           ("DeepSeek V4.1 Flash: 510 GB of weights; one 4 × H100 node holds 320 GB", 0, 0),
           ("**Tensor parallel 4** inside each node, over NVLink; the experts spread across the GPUs too", 0, 1),
           ("**Pipeline parallel 2** across the nodes: activations cross the network with NCCL", 0, 2),
           ("Two StatefulSets: the **head** pod serves the API, the **worker** runs headless", 0, 3),
           ("A **supervisor** in each pod restarts both when either restarts (LeaderWorkerSet isn't installed)", 0, 4),
           ("A **headless Service** gives the pods stable names; a **NetworkPolicy** keeps the NCCL traffic to the pair",
            0, 5)], size=15, gap=7),
       Raw(0, 0, 0.1, 0.1, """<style>
.mnode .mnpod .bx { transition: background .45s, border-color .45s; }
.mnode[data-cur="4"] .mnpod .bx { animation: mnrestart 1.4s ease .5s 2; }
@keyframes mnrestart { 0%, 100% { background: var(--card); border-color: #C9D4E3; } 40%, 60% { background: #F6D6D3; border-color: #B3261E; } }
</style>""", pptx=False)]
add("Multi-Node Serving", tn, steps=5, cls="mnode", optional=True, secs=60, notes="""
The biggest model doesn't fit on one node. DeepSeek V4.1 Flash is 510 gigabytes of weights, and a four-H100 node has 320, so it runs across two of them.

[click] Inside each node, tensor parallelism splits every layer across the four GPUs, which talk over NVLink; the model's experts are spread across them too.

[click] Across the nodes, pipeline parallelism: node A runs the first part of the layers, node B the rest, and the activations cross the network between them with NCCL, over Ethernet. The split isn't even, 14 layers on the head and 26 on the worker, because the head also serves the API.

[click] In Kubernetes that's two StatefulSets: the head pod serves the API, and the worker runs vLLM headless.

[click] The catch: if either pod restarts, the other is stuck waiting for a peer that no longer exists. Kubernetes has LeaderWorkerSet for this, but it isn't installed on Nautilus, so the team wrote a small supervisor that wraps vLLM in each pod. Each watches the other, and a restart on either side restarts both, so the pair re-forms.

[click] A headless Service gives the pods stable names to find each other, and a network policy keeps the NCCL ports to the pair. Two copies of this pair serve the model, on SDSC's Expanse nodes.
""")


ar = [("Open WebUI", "chat in the browser, with a terminals operator"), ("Web search", "SearXNG, for tools and chat"),
      ("Embeddings", "qwen3-embedding; TEI on a GPU"), ("Vector databases", "Milvus (managed) and Qdrant"),
      ("MCP route", "an MCP gateway; an accounting MCP server"), ("Telemetry", "OpenTelemetry collector into ClickHouse"),
      ("Coding agents", "Claude Code, opencode and others, with tested configurations")]
# the pieces sit on an ellipse around the models, each joined to the center by a line
AR_C, AR_RX, AR_RY, AR_W, AR_H = (6.667, TOP + 2.45), 4.55, 1.95, 2.7, 0.98
AR_CW, AR_CH = 2.5, 1.25                                                  # the center oval
ar_pos = [(AR_C[0] + AR_RX * math.cos(-math.pi / 2 + 2 * math.pi * i / len(ar)),
           AR_C[1] + AR_RY * math.sin(-math.pi / 2 + 2 * math.pi * i / len(ar))) for i in range(len(ar))]


def ar_gap(bx, by):
    """The stretch of a spoke between a box's edge and the center oval's edge: where the dots run."""
    dx, dy = AR_C[0] - bx, AR_C[1] - by
    t0 = min((AR_W / 2 + 0.05) / abs(dx) if dx else 9, (AR_H / 2 + 0.05) / abs(dy) if dy else 9)
    s = 1 / math.hypot(dx / (AR_CW / 2 + 0.05), dy / (AR_CH / 2 + 0.05))
    return [(bx + dx * t0, by + dy * t0), (AR_C[0] - dx * s, AR_C[1] - dy * s)]


spokes = "".join(f'<line x1="{AR_C[0] * PX:.0f}" y1="{AR_C[1] * PX:.0f}" x2="{x * PX:.0f}" y2="{y * PX:.0f}" '
                 f'pathLength="1" style="transition-delay:{0.15 + i * 0.15:.2f}s"/>' for i, (x, y) in enumerate(ar_pos))
ae = [Raw(0, 0, 13.333, 7.5, f"""<style>
.around .spk line {{ stroke: #B9C7D8; stroke-width: 3; stroke-dasharray: 1; stroke-dashoffset: 1; transition: stroke-dashoffset .5s ease; }}
.slide.active.around .spk line {{ stroke-dashoffset: 0; }}
.around .core {{ width:100%; height:100%; border-radius:50%; background:var(--navy); color:#fff; display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center; box-shadow:0 0 0 0 rgba(0,98,155,.45); }}
.around .core b {{ font:700 40px/1 var(--f-body); }} .around .core span {{ font-size:22px; color:var(--light); margin-top:6px; }}
.slide.active.around .core {{ animation: arpulse 2.4s ease-out 1.4s infinite; }}
@keyframes arpulse {{ 0% {{ box-shadow:0 0 0 0 rgba(0,98,155,.45); }} 100% {{ box-shadow:0 0 0 40px rgba(0,98,155,0); }} }}
</style><svg class="spk" width="1920" height="1080" style="position:absolute;left:0;top:0">{spokes}</svg>""",
          draw=lambda s, k: [s.line(AR_C[0], AR_C[1], x, y, color="B9C7D8", width=2, arrow=False) for x, y in ar_pos],
          style="pointer-events:none;"),
      flow([ar_gap(x, y) for x, y in ar_pos], n=1, dur=1.6, r=6, color="#00629B"),
      Raw(AR_C[0] - AR_CW / 2, AR_C[1] - AR_CH / 2, AR_CW, AR_CH,
          '<div class="core"><b>The models</b><span>on the same gateway</span></div>',
          draw=lambda s, k: (s.rect(AR_C[0] - AR_CW / 2, AR_C[1] - AR_CH / 2, AR_CW, AR_CH, fill=NAVY,
                                    shape=__import__("pptx.enum.shapes", fromlist=["MSO_SHAPE"]).MSO_SHAPE.OVAL),
                             s.text(AR_C[0] - AR_CW / 2, AR_C[1] - AR_CH / 2, AR_CW, AR_CH,
                                    [P("The models", size=20, bold=True, color=WHITE, align="c"),
                                     P("on the same gateway", size=11, color=LIGHT, align="c")], anchor="m")))]
for i, ((h, b_), (x, y)) in enumerate(zip(ar, ar_pos)):
    ae.append(Box(x - AR_W / 2, y - AR_H / 2, AR_W, AR_H, h, b_, state="white", head_size=16, sub_size=12,
                  cls="rise", style=f"transition-delay:{0.15 + i * 0.15:.2f}s"))
ae.append(Text(X0, 6.45, W, 0.4, T("All of it on the same cluster, most of it deployed the same way as everything else: "
                                    "from git.", size=15, color=MUTED, align="c")))
add("Around the Models", ae, cls="around", optional=True, notes="""
[0:30] Around the models there's a small ecosystem, all talking to the same gateway: Open WebUI for chat, web search, embeddings and two vector databases for retrieval, an MCP route, telemetry into ClickHouse, and tested configurations for coding agents. All of it runs on the same cluster.
""")


bot = [Box(X0, TOP + 0.3, 2.7, 1.2, "An operator in Slack", "mentions the bot with a question", head_size=15,
           sub_size=12, hl=[1]),
       Box(4.0, TOP + 0.3, 2.9, 1.2, "A model on NRP", "deepseek-v4-flash, through the same gateway", head_size=15,
           sub_size=12, hl=[1, 2, 3]),
       Box(8.2, TOP + 0.3, 4.53, 1.2, "16 read-only tools", "pods, logs, events, nodes · PromQL on Thanos · NRP "
           "docs search · accounting MCP · triage playbooks", head_size=15, sub_size=12, hl=[2]),
       Arrow(3.3, TOP + 0.9, 4.0, TOP + 0.9, hl=[1]),
       Arrow(6.9, TOP + 0.75, 8.2, TOP + 0.75, hl=[2]), Arrow(8.2, TOP + 1.05, 6.9, TOP + 1.05, hl=[2]),
       Text(6.95, TOP + 1.12, 1.25, 0.4, T("a loop", size=12, color=MUTED, align="c"), step=2),
       Box(4.0, TOP + 2.0, 2.9, 1.0, "An answer in the thread", "the finding, the evidence, the tool calls",
           head_size=15, sub_size=12, step=3, hl=[3]),
       Arrow(5.45, TOP + 1.5, 5.45, TOP + 2.0, step=3, hl=[3]),
       Text(X0, TOP + 3.2, 5.9, 0.4, T("Guardrails", size=19, bold=True, color=NAVY)),
       Bullets(X0, TOP + 3.65, 5.9, 2.0, ["RBAC denies secrets, exec and every write",
                                          "Namespace allowlist; credentials redacted",
                                          "Logs and events treated as untrusted (prompt injection)",
                                          "Budgets on tool calls, iterations and time"], size=15, gap=4),
       Text(6.83, TOP + 3.2, 5.9, 0.4, T("Status", size=19, bold=True, color=NAVY)),
       Bullets(6.83, TOP + 3.65, 5.9, 2.0, ["Phase 1, read-only: built and tested with mocks",
                                            "Phase 2, write actions behind two-human approval: not started",
                                            "Also an MCP server, and an eval harness to compare models"],
               size=15, gap=4)]
add("An LLM on Call: nrp-ops-bot", bot, steps=3, cls="opsbot", notes="""
[0:21] To close the AI part, where it meets the operations part. nrp-ops-bot is an operator's assistant in Slack, built from pieces you've now seen. [click] You mention it with a question, and it calls a model through the same gateway, deepseek-v4-flash. [click] The model works in a loop with sixteen read-only tools: pods, logs, events and nodes from Kubernetes, PromQL against the Thanos from the monitoring slide, a search index of our docs, the accounting server, and per-service triage playbooks. [click] It answers in the thread with the finding, the evidence and the tool calls it made, so you can check its work.

The guardrails matter more than the model: RBAC that denies secrets, exec and every write; redaction; and it treats pod logs and events as untrusted input, because a log line is a great place for a prompt injection. This is early: phase one is built and tested with mocks; write actions with two-human approval haven't started.
""")
