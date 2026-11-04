#!/usr/bin/env bash
# The National Research Platform (UCLA Health) — check your work.
#
#   bash check.sh <section 1-2>
#

EP="$1"

PASS=0; WARN=0; FAIL=0

ok()   { printf '  ✅ %s\n' "$1"; PASS=$((PASS+1)); }
skip() { printf '  ⚪ %s — not found (not created yet, or already cleaned up)\n' "$1"; WARN=$((WARN+1)); }
bad()  { printf '  ❌ %s\n     ↳ %s\n' "$1" "$2"; FAIL=$((FAIL+1)); }

case "$EP" in

1)
  echo "Section 1 — access checks"
  if kubectl version --client >/dev/null 2>&1; then ok "kubectl installed ($(kubectl version --client 2>/dev/null | head -1 | awk '{print $NF}'))"
  else bad "kubectl not found" "use the training JupyterHub, or install kubectl and a kubeconfig"; fi
  if kubectl auth whoami >/dev/null 2>&1; then ok "authenticated to the cluster as $(kubectl auth whoami -o jsonpath='{.status.userInfo.username}' 2>/dev/null)"
  else bad "not authenticated" "grab your kubeconfig from portal.nrp.ai and put it at ~/.kube/config"; fi
  if command -v helm >/dev/null 2>&1; then ok "helm installed ($(helm version --short 2>/dev/null))"
  else skip "helm (optional — only for running your own hub)"; fi
  ;;

2)
  echo "Section 2 — AI services"
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

  if python3 -c 'import openai' >/dev/null 2>&1; then ok "the openai SDK is importable (section 2 of the notebook)"
  else bad "python3 -c 'import openai' failed" "the training hub image ships it; elsewhere: pip install openai"; fi
  ;;

*)
  echo "usage: bash check.sh <section 1-2>"; exit 1;;
esac

echo
printf '%d passed · %d not found · %d need attention\n' "$PASS" "$WARN" "$FAIL"
if [ "$FAIL" -eq 0 ]; then echo "🎉 Looking good!"; else echo "Stuck? Ask in the NRP support chat: https://nrp.ai/contact/"; fi
