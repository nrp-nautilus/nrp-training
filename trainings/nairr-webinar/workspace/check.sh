#!/usr/bin/env bash
# NAIRR AI Education Webinar — Prototype NRP Classroom — check your work.
#
#   bash check.sh <section 1-2>
#
# Section 2 needs $NRP_NAMESPACE (the namespace you are deploying into).
# Resources you already cleaned up show as "not found" — that is fine once
# you have finished that section.

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
  else skip "helm (needed for section 2)"; fi
  ;;

2)
  NSP="${NRP_NAMESPACE:-}"
  if [ -z "$NSP" ] || [ "$NSP" = changeme ]; then
    echo "Set your namespace first:  export NRP_NAMESPACE=<namespace>"
    exit 1
  fi
  echo "Section 2 — your own JupyterHub (namespace $NSP)"
  rel=$(helm list -n "$NSP" -q 2>/dev/null | head -1)
  if [ -z "$rel" ]; then skip "helm release in $NSP"
  else
    st=$(helm status "$rel" -n "$NSP" -o json 2>/dev/null | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    if [ "$st" = deployed ]; then ok "helm release $rel is deployed"
    else bad "helm release $rel status: ${st:-unknown}" "helm status $rel -n $NSP"; fi
  fi
  for comp in hub proxy; do
    ph=$(kubectl get pod -n "$NSP" -l "app=jupyterhub,component=$comp" -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
    if [ -z "$ph" ]; then skip "$comp pod in $NSP"
    elif [ "$ph" = Running ]; then ok "$comp pod Running"
    else bad "$comp pod is $ph" "kubectl describe pod -n $NSP -l app=jupyterhub,component=$comp"; fi
  done
  st=$(kubectl get pvc hub-db-dir -n "$NSP" -o jsonpath='{.status.phase}' 2>/dev/null)
  if [ -z "$st" ]; then skip "pvc/hub-db-dir (created by the chart)"
  elif [ "$st" = Bound ]; then ok "pvc/hub-db-dir Bound (hub database has storage)"
  else bad "pvc/hub-db-dir is $st" "kubectl describe pvc hub-db-dir -n $NSP — check storageClassName in your values"; fi
  nsrv=$(kubectl get pod -n "$NSP" -l "app=jupyterhub,component=singleuser-server" --no-headers 2>/dev/null | wc -l | tr -d ' ')
  if [ "${nsrv:-0}" -gt 0 ]; then ok "$nsrv user server(s) spawned — someone logged in to your hub 🎓"
  else skip "user servers (log in to your hub and spawn one to complete the loop)"; fi
  host=$(kubectl get ingress -n "$NSP" -l app=jupyterhub -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null)
  if [ -z "$host" ]; then skip "ingress (section 4 of the lesson)"
  else
    body=$(curl -s "https://$host/hub/login" --max-time 15)
    code=$(curl -s -o /dev/null -w '%{http_code}' "https://$host/hub/login" --max-time 15)
    if [ "$code" = 200 ] && printf '%s' "$body" | grep -qi 'jupyterhub\|id="login-main"'; then
      ok "https://$host serves the hub login page"
    elif [ "$code" = 200 ]; then
      bad "https://$host answers 200 but it is not a JupyterHub login page" "is another app already using that hostname? check the ingress host in your values"
    else bad "https://$host answered '$code'" "certificate + HAProxy need ~60s after the upgrade"; fi
  fi
  ;;

*)
  echo "usage: bash check.sh <section 1-2>"; exit 1;;
esac

echo
printf '%d passed · %d not found · %d need attention\n' "$PASS" "$WARN" "$FAIL"
if [ "$FAIL" -eq 0 ]; then echo "🎉 Looking good!"; else echo "Stuck? Ask in the NRP support chat: https://nrp.ai/contact/"; fi
