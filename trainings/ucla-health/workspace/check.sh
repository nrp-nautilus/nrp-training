#!/usr/bin/env bash
# The National Research Platform (UCLA Health) — check your work.
#
#   bash check.sh 1   # AI services
#   bash check.sh 2   # GPUs
#

EP="$1"

PASS=0; WARN=0; FAIL=0

ok()   { printf '  ✅ %s\n' "$1"; PASS=$((PASS+1)); }
skip() { printf '  ⚪ %s\n' "$1"; WARN=$((WARN+1)); }
bad()  { printf '  ❌ %s\n     ↳ %s\n' "$1" "$2"; FAIL=$((FAIL+1)); }

case "$EP" in

1)
  echo "Part 1 — AI services"
  if [ -n "${OPENAI_API_BASE:-}" ]; then ok "OPENAI_API_BASE is set ($OPENAI_API_BASE)"
  else bad "OPENAI_API_BASE is not set" "on the training hub it is exported for you; otherwise export it to https://ellm.nrp-nautilus.io/v1"; fi
  if [ -n "${OPENAI_API_KEY:-}" ]; then ok "OPENAI_API_KEY is set (${OPENAI_API_KEY:0:8}...)"
  else bad "OPENAI_API_KEY is not set" "mint a token at https://nrp.ai/llmtoken and export it"; fi

  if [ -n "${OPENAI_API_BASE:-}" ]; then
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 \
             -H "Authorization: Bearer ${OPENAI_API_KEY:-none}" "$OPENAI_API_BASE/models")
    if [ "$code" = 200 ]; then ok "endpoint reachable — GET /models answered 200"
    else bad "GET /models answered '$code'" "check the LLM status dashboard: https://nrp.ai/llm-status/"; fi
  fi

  # the real token test: /models is unauthenticated on the NRP gateway, chat/completions is not
  if [ -n "${OPENAI_API_BASE:-}" ] && [ -n "${OPENAI_API_KEY:-}" ]; then
    body=$(curl -s --max-time 60 -X POST "$OPENAI_API_BASE/chat/completions" \
      -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
      -d '{"model":"gpt-oss","max_tokens":16,"messages":[{"role":"user","content":"say ok"}]}')
    if printf '%s' "$body" | grep -q '"choices"'; then ok "chat/completions works — your token is valid 🎉"
    elif printf '%s' "$body" | grep -qi 'model'; then skip "chat/completions (that model may have rotated out — try another from /models)"
    else bad "chat/completions did not return choices" "token rejected, or the model is down — see https://nrp.ai/llm-status/"; fi
  fi

  if python3 -c 'import openai' >/dev/null 2>&1; then ok "the openai SDK is importable"
  else bad "python3 -c 'import openai' failed" "the training hub image ships it; elsewhere: pip install openai"; fi
  ;;

2)
  echo "Part 2 — GPUs"
  if kubectl version --client >/dev/null 2>&1; then ok "kubectl installed"
  else bad "kubectl not found" "use the training JupyterHub, or install kubectl: https://nrp.ai/documentation/userdocs/start/getting-started/"; fi
  NS="${NS:-nrp-training-k8s}"
  if [ "$(kubectl auth can-i create jobs -n "$NS" 2>/dev/null)" = yes ]; then ok "you can create jobs in $NS"
  else bad "cannot create jobs in $NS" "on your own laptop, set NS=<your namespace> and rerun"; fi
  if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then ok "this session has a GPU: $(nvidia-smi -L | head -1)"
  else skip "a GPU in this session (only needed for section 2 of the notebook; restart your server with a GPU)"; fi
  if python3 -c 'import torch' >/dev/null 2>&1; then ok "PyTorch is importable"
  else skip "PyTorch (only needed for section 2 of the notebook)"; fi
  ;;

*)
  echo "usage: bash check.sh <part 1-2>"; exit 1;;
esac

echo
printf '%d passed · %d optional · %d need attention\n' "$PASS" "$WARN" "$FAIL"
if [ "$FAIL" -eq 0 ]; then echo "🎉 Looking good!"; else echo "Stuck? Ask in the NRP support chat: https://nrp.ai/contact/"; fi
