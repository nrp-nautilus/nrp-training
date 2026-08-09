#!/usr/bin/env bash
# CMS HATS tutorial — check your work.
#
#   bash check.sh <episode 1-5> [username]
#
# Username comes from $USER, or the second argument. Episode 5 also needs a
# .p12 certificate already imported (grid-cert-import) before grid-proxy-init
# will have anything to check. Resources you already cleaned up show as
# "not found" — that is fine once you have finished that section.

NS=us-cms
EP="$1"
U="${2:-$USER}"

PASS=0; WARN=0; FAIL=0

ok()   { printf '  ✅ %s\n' "$1"; PASS=$((PASS+1)); }
skip() { printf '  ⚪ %s — not found (not created yet, or already cleaned up)\n' "$1"; WARN=$((WARN+1)); }
bad()  { printf '  ❌ %s\n     ↳ %s\n' "$1" "$2"; FAIL=$((FAIL+1)); }

need_user() {
  if [ -z "$U" ] || [ "$U" = changeme ]; then
    echo "Set your username first:  export USER=<yourname>   (or: bash check.sh $EP <yourname>)"
    exit 1
  fi
}

pod_check() { # pod_check <name> <want-phase> <hint>
  local name="$1" want="$2" hint="$3" phase
  phase=$(kubectl get pod "$name" -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)
  if [ -z "$phase" ]; then skip "pod/$name"
  elif [ "$phase" = "$want" ]; then ok "pod/$name is $phase"
  else bad "pod/$name is $phase (expected $want)" "$hint"
  fi
}

job_check() { # job_check <name> <hint>
  local name="$1" hint="$2" succ
  succ=$(kubectl get job "$name" -n $NS -o jsonpath='{.status.succeeded}' 2>/dev/null)
  if [ -z "$succ" ]; then skip "job/$name"
  elif [ "$succ" -ge 1 ] 2>/dev/null; then ok "job/$name succeeded"
  else bad "job/$name not finished" "$hint"
  fi
}

case "$EP" in

1)
  echo "Episode 1 — access checks"
  if kubectl auth whoami >/dev/null 2>&1; then ok "kubectl talks to the cluster ($(kubectl auth whoami -o jsonpath='{.status.userInfo.username}' 2>/dev/null))"
  else bad "kubectl cannot reach the cluster" "on your own machine: did you finish Method 1 setup? on the hub: run grid-kube-setup, then any kubectl command"; fi
  if kubectl get pods -n $NS >/dev/null 2>&1; then ok "allowed to list pods in $NS"
  else bad "cannot list pods in $NS" "ask Daniel or Martin to add you to the us-cms namespace"; fi
  ;;

2)
  need_user
  echo "Episode 2 — Kubernetes basics ($U)"
  pod_check "pod-basics-$U" Running "kubectl describe pod pod-basics-$U -n $NS"
  ;;

3)
  need_user
  echo "Episode 3 — hands-on prep ($U)"
  st=$(kubectl get pvc "cms-nrp-hats-$U" -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)
  if [ -z "$st" ]; then skip "pvc/cms-nrp-hats-$U"
  elif [ "$st" = Bound ]; then ok "pvc/cms-nrp-hats-$U is Bound"
  else bad "pvc/cms-nrp-hats-$U is $st" "first Ceph provisioning takes ~30-60s; kubectl describe pvc cms-nrp-hats-$U -n $NS"; fi
  if [ -f "/tmp/jet-class-$U.yaml" ]; then ok "training manifest prepared (/tmp/jet-class-$U.yaml)"
  else skip "/tmp/jet-class-$U.yaml (run the 'Prepare the YAML' step)"; fi
  if [ -f "/tmp/jet-class-analysis-$U.yaml" ]; then ok "analysis manifest prepared (/tmp/jet-class-analysis-$U.yaml)"
  else skip "/tmp/jet-class-analysis-$U.yaml (run the 'Prepare the YAML' step)"; fi
  if [ -f "/tmp/pvc-browser-$U.yaml" ]; then ok "PVC browser manifest prepared (/tmp/pvc-browser-$U.yaml)"
  else skip "/tmp/pvc-browser-$U.yaml (run the 'Prepare the PVC browser pod' step)"; fi
  if [ -f "/tmp/jet-class-sweep-$U.yaml" ]; then ok "sweep training manifest prepared (/tmp/jet-class-sweep-$U.yaml)"
  else skip "/tmp/jet-class-sweep-$U.yaml (optional — only needed for the sweep extension)"; fi
  if [ -f "/tmp/jet-class-sweep-analysis-$U.yaml" ]; then ok "sweep analysis manifest prepared (/tmp/jet-class-sweep-analysis-$U.yaml)"
  else skip "/tmp/jet-class-sweep-analysis-$U.yaml (optional — only needed for the sweep extension)"; fi
  if [ -f "/tmp/jet-class-sweep-compare-$U.yaml" ]; then ok "sweep compare manifest prepared (/tmp/jet-class-sweep-compare-$U.yaml)"
  else skip "/tmp/jet-class-sweep-compare-$U.yaml (optional — only needed for the sweep extension)"; fi
  ;;

4)
  need_user
  echo "Episode 4 — hands-on exercise ($U)"
  job_check "jet-class-$U" "kubectl logs -n $NS job/jet-class-$U -f"
  job_check "jet-class-analysis-$U" "kubectl logs -n $NS job/jet-class-analysis-$U -f"
  ;;

5)
  echo "Episode 5 — CMS data access (grid certificate)"
  if [ -f "$HOME/.globus/usercert.pem" ]; then ok "grid certificate imported (~/.globus/usercert.pem)"
  else skip "~/.globus/usercert.pem (run grid-cert-import)"; fi
  if [ -s "$HOME/.globus/x509up" ]; then
    if command -v grid-proxy-info >/dev/null 2>&1 && grid-proxy-info -exists -valid 0:05 >/dev/null 2>&1; then
      ok "grid proxy present and not yet expired (~/.globus/x509up)"
    else ok "grid proxy present (~/.globus/x509up) — run grid-proxy-init again if it's expired"; fi
  else skip "~/.globus/x509up (run grid-proxy-init)"; fi
  if [ -f "$HOME/jet_pt.png" ] || [ -f jet_pt.png ]; then ok "jet_pt.png plot created"
  else skip "jet_pt.png (run the uproot plotting step)"; fi
  ;;

*)
  echo "usage: bash check.sh <episode 1-5> [username]"; exit 1;;
esac

echo
printf '%d passed · %d not created/cleaned up · %d need attention\n' "$PASS" "$WARN" "$FAIL"
if [ "$FAIL" -eq 0 ]; then echo "🎉 Looking good!"; else echo "Stuck? Ask in the NRP support chat: https://nrp.ai/contact/"; fi
