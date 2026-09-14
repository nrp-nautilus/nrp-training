#!/usr/bin/env bash
# CLARIPHY — LLMs and AI tools on NRP — check your work.
#
#   bash check.sh <episode 1-4>
#
# No username needed — this training doesn't create per-user cluster resources.

NS=clariphy
EP="$1"

PASS=0; WARN=0; FAIL=0

ok()   { printf '  ✅ %s\n' "$1"; PASS=$((PASS+1)); }
skip() { printf '  ⚪ %s — not found\n' "$1"; WARN=$((WARN+1)); }
bad()  { printf '  ❌ %s\n     ↳ %s\n' "$1" "$2"; FAIL=$((FAIL+1)); }

llm_check() {
  if [ -n "$OPENAI_API_KEY" ] && [ -n "$OPENAI_API_BASE" ]; then
    # /models answers even without a token, so check with a one-token chat request instead.
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 60 -X POST "$OPENAI_API_BASE/chat/completions" \
      -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
      -d '{"model":"gemma-small","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}')
    case "$code" in
      200)     ok "NRP accepted your token ($OPENAI_API_BASE)" ;;
      401|403) bad "NRP rejected your token (HTTP $code)" "token invalid/expired, or not in a namespace with LLM access? get one at nrp.ai/llmtoken, or ask an instructor" ;;
      000)     bad "could not reach $OPENAI_API_BASE" "check your network connection" ;;
      *)       bad "LLM endpoint answered HTTP $code" "gemma-small may be down (nrp.ai/llm-status), or ask an instructor" ;;
    esac
  else bad "OPENAI_API_KEY / OPENAI_API_BASE not set" "export your personal token from nrp.ai/llmtoken (see Lesson 1)"; fi
}

case "$EP" in

1)
  echo "Episode 1 — introduction & access"
  if kubectl get pods -n $NS >/dev/null 2>&1; then ok "allowed to list pods in $NS"
  else skip "cannot list pods in $NS (only needed if you'll also run kubectl exercises)"; fi
  llm_check
  ;;

2)
  echo "Episode 2 — chat with LLMs"
  llm_check
  if [ -n "$OPENAI_API_KEY" ] && [ -n "$OPENAI_API_BASE" ]; then
    reply=$(curl -s -X POST "$OPENAI_API_BASE/chat/completions" --max-time 90 \
      -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
      -d '{"model":"gemma-small","max_tokens":50,"messages":[{"role":"user","content":"Say OK"}]}' \
      | python3 -c 'import json,sys; print((json.load(sys.stdin)["choices"][0]["message"]["content"] or "").strip())' 2>/dev/null)
    if [ -n "$reply" ]; then ok "chat completion round-trip works — your token is valid"
    else bad "chat completion returned nothing" "token invalid/expired, or gemma-small not in the current catalog"; fi
  fi
  ;;

3)
  echo "Episode 3 — agentic workflows (opencode & IDE)"
  export PATH="$HOME/.opencode/bin:$PATH"
  TOKEN_FILE="$HOME/.nrp-llm-token"
  if command -v opencode >/dev/null 2>&1; then ok "opencode installed ($(opencode --version 2>/dev/null))"
  else skip "opencode not on PATH (Install, Part 1)"; fi
  if grep -qs 'ellm.nrp-nautilus.io' "$HOME/opencode-exercise/opencode.json"; then ok "NRP provider config in ~/opencode-exercise/opencode.json"
  elif grep -qs 'ellm.nrp-nautilus.io' "$HOME/.config/opencode/opencode.json"; then ok "NRP provider in your global opencode config"
  else skip "~/opencode-exercise/opencode.json (Configure NRP as the provider, Part 1)"; fi
  if [ -s "$TOKEN_FILE" ]; then
    case "$(cat "$TOKEN_FILE")" in
      "<"*) bad "~/.nrp-llm-token still holds the placeholder" "re-run the token step with your real token" ;;
      *)    ok "token saved for opencode (~/.nrp-llm-token)" ;;
    esac
  else skip "~/.nrp-llm-token (token step, Part 1)"; fi
  # A fresh terminal has no token exported; fall back to the one saved for opencode.
  if [ -z "${OPENAI_API_KEY:-}" ] && [ -s "$TOKEN_FILE" ]; then
    OPENAI_API_KEY="$(cat "$TOKEN_FILE")"; OPENAI_API_BASE="${OPENAI_API_BASE:-https://ellm.nrp-nautilus.io/v1}"
  fi
  llm_check
  ;;

4)
  echo "Episode 4 — build a simple agent"
  if python3 -c 'import openai' >/dev/null 2>&1; then ok "openai Python package importable"
  else bad "openai package not importable" "pip install openai"; fi
  llm_check
  ;;

5)
  echo "Episode 5 — agentic physics analysis (JFC on NRP)"
  JFC="${JFC_WORK:-$HOME/jfc-exercise}"
  ROGUE_DIR="$JFC/jfc/analyses/h4l_rogue"
  export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
  # A fresh terminal has no token exported; reuse the one saved by Part 1 / jfc_setup.sh.
  if [ -z "${OPENAI_API_KEY:-}" ] && [ -f "$JFC/nrp-env.sh" ]; then . "$JFC/nrp-env.sh"; fi
  if command -v claude >/dev/null 2>&1; then ok "claude CLI installed ($(claude --version 2>/dev/null | head -1))"
  else skip "claude not on PATH (Part 1, or run jfc_setup.sh)"; fi
  if command -v pixi >/dev/null 2>&1; then ok "pixi installed ($(pixi --version 2>/dev/null))"
  else skip "pixi not on PATH (Part 1, or run jfc_setup.sh)"; fi
  CFG="$JFC/claude-config/settings.json"
  if [ -f "$CFG" ]; then
    if grep -q '/anthropic' "$CFG" 2>/dev/null; then ok "workshop-only Claude Code config points at NRP ($CFG)"
    else bad "$CFG does not reference /anthropic" "re-run Part 2, or jfc_setup.sh"; fi
  else skip "$CFG (Part 2, or run jfc_setup.sh)"; fi
  if grep -q 'ellm.nrp-nautilus.io/anthropic' "$HOME/.claude/settings.json" 2>/dev/null; then
    printf '  ℹ️  ~/.claude/settings.json also points at NRP (older version of this lesson) — restore ~/.claude/settings.json.bak if you have one\n'
  fi
  if [ -f "$ROGUE_DIR/prompt.md" ]; then ok "h4l exercise staged in $ROGUE_DIR"
  else skip "$ROGUE_DIR/prompt.md (staging step, Part 4)"; fi
  if [ -e "$JFC/data" ]; then ok "CMS Open Data samples present"
  else skip "$JFC/data (download step, Part 3)"; fi
  if [ -f "$ROGUE_DIR/prompt.md" ]; then
    nfiles=$(find "$ROGUE_DIR" -maxdepth 2 -newer "$ROGUE_DIR/prompt.md" -type f \
             -not -path '*/.git/*' -not -path '*/data/*' -not -path '*/docs/*' 2>/dev/null | wc -l | tr -d ' ')
    nfigs=$(find "$ROGUE_DIR" \( -name '*.png' -o -name '*.pdf' \) \
            -not -path '*/docs/*' -not -path '*/data/*' 2>/dev/null | wc -l | tr -d ' ')
    if [ "$nfiles" -gt 0 ]; then ok "agent has written $nfiles file(s) so far, $nfigs figure(s)"
    else skip "agent output in $ROGUE_DIR (launch the agent, Part 5)"; fi
  fi
  llm_check
  ;;

*)
  echo "usage: bash check.sh <episode 1-5>"; exit 1;;
esac

echo
printf '%d passed · %d not found · %d need attention\n' "$PASS" "$WARN" "$FAIL"
if [ "$FAIL" -eq 0 ]; then echo "🎉 Looking good!"; else echo "Stuck? Ask in the NRP support chat: https://nrp.ai/contact/"; fi
