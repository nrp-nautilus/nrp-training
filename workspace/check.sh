#!/usr/bin/env bash
# CMS HATS — LLMs on NRP — check your work.
#
#   bash check.sh <episode 1-4>
#
# No username needed — this training uses a shared workshop token and doesn't
# create per-user cluster resources.

NS=us-cms
EP="$1"

PASS=0; WARN=0; FAIL=0

ok()   { printf '  ✅ %s\n' "$1"; PASS=$((PASS+1)); }
skip() { printf '  ⚪ %s — not found\n' "$1"; WARN=$((WARN+1)); }
bad()  { printf '  ❌ %s\n     ↳ %s\n' "$1" "$2"; FAIL=$((FAIL+1)); }

llm_check() {
  if [ -n "$OPENAI_API_KEY" ] && [ -n "$OPENAI_API_BASE" ]; then
    code=$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $OPENAI_API_KEY" "$OPENAI_API_BASE/models" --max-time 15)
    if [ "$code" = 200 ]; then ok "managed LLM endpoint reachable ($OPENAI_API_BASE)"
    else bad "LLM endpoint answered '$code'" "token invalid/expired? get one at nrp.ai/llmtoken, or ask an instructor"; fi
  else bad "OPENAI_API_KEY / OPENAI_API_BASE not set" "pre-exported on the training hub; on your own machine export both yourself"; fi
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
      -d '{"model":"gemma-small-e4b","max_tokens":50,"messages":[{"role":"user","content":"Say OK"}]}' \
      | python3 -c 'import json,sys; print((json.load(sys.stdin)["choices"][0]["message"]["content"] or "").strip())' 2>/dev/null)
    if [ -n "$reply" ]; then ok "chat completion round-trip works — your token is valid"
    else bad "chat completion returned nothing" "token invalid/expired, or gemma-small-e4b not in the current catalog"; fi
  fi
  ;;

3)
  echo "Episode 3 — agentic workflows (opencode & IDE)"
  if command -v opencode >/dev/null 2>&1; then ok "opencode installed ($(opencode --version 2>/dev/null))"
  else skip "opencode not on PATH (curl -fsSL https://opencode.ai/install | bash)"; fi
  if [ -f "$HOME/.config/opencode/opencode.json" ]; then ok "opencode NRP provider config present"
  else skip "~/.config/opencode/opencode.json (write the NRP provider config)"; fi
  llm_check
  ;;

4)
  echo "Episode 4 — build a simple agent"
  if python3 -c 'import openai' >/dev/null 2>&1; then ok "openai Python package importable"
  else bad "openai package not importable" "pip install openai"; fi
  llm_check
  ;;

*)
  echo "usage: bash check.sh <episode 1-4>"; exit 1;;
esac

echo
printf '%d passed · %d not found · %d need attention\n' "$PASS" "$WARN" "$FAIL"
if [ "$FAIL" -eq 0 ]; then echo "🎉 Looking good!"; else echo "Stuck? Ask in the NRP support chat: https://nrp.ai/contact/"; fi
