#!/usr/bin/env bash
# PEARC26 tutorial — check your work.
#
#   bash check.sh <episode 1-6> [username]
#
# Username comes from $NRP_USER, or the second argument. Episode 6 also needs
# $NRP_NAMESPACE (the per-participant namespace handed out by the instructors).
# Resources you already cleaned up show as "not found" — that is fine once
# you have finished that section.

NS=nrp-training-k8s
EP="$1"
U="${2:-$NRP_USER}"

PASS=0; WARN=0; FAIL=0

ok()   { printf '  ✅ %s\n' "$1"; PASS=$((PASS+1)); }
skip() { printf '  ⚪ %s — not found (not created yet, or already cleaned up)\n' "$1"; WARN=$((WARN+1)); }
bad()  { printf '  ❌ %s\n     ↳ %s\n' "$1" "$2"; FAIL=$((FAIL+1)); }

need_user() {
  if [ -z "$U" ] || [ "$U" = changeme ]; then
    echo "Set your username first:  export NRP_USER=<yourname>   (or: bash check.sh $EP <yourname>)"
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

case "$EP" in

1)
  echo "Episode 1 — access checks"
  if kubectl auth whoami >/dev/null 2>&1; then ok "kubectl talks to the cluster ($(kubectl auth whoami -o jsonpath='{.status.userInfo.username}' 2>/dev/null))"
  else bad "kubectl cannot reach the cluster" "are you in a jh-training.nrp-nautilus.io terminal or notebook?"; fi
  if kubectl get pods -n $NS >/dev/null 2>&1; then ok "allowed to list pods in $NS"
  else bad "cannot list pods in $NS" "ask an instructor — your account may not be provisioned yet"; fi
  if jupyter kernelspec list 2>/dev/null | grep -q '^\s*bash\s'; then ok "bash kernel registered (notebooks are runnable)"
  else bad "bash kernel not registered" "restart your server (File → Hub Control Panel → Stop → Start)"; fi
  D=$(cd "$(dirname "$0")" 2>/dev/null && pwd)
  if [ -f "$D/yamls/test-pod.yaml" ]; then ok "workspace files present ($D/yamls)"
  else bad "workspace yamls/ missing" "re-click the launch button on training.nrp-nautilus.io/pearc26 to pull the materials"; fi
  if [ -n "$U" ] && [ "$U" != changeme ] && grep -q "test-pod-$U" "$D/my-yamls/test-pod.yaml" 2>/dev/null; then
    ok "my-yamls/ rendered with your username ($U)"
  else skip "my-yamls/ personalized manifests (run the ⚙️ setup cell in any episode notebook)"; fi
  ;;

2)
  need_user
  echo "Episode 2 — Kubernetes hands-on ($U)"
  pod_check "test-pod-$U" Running "kubectl describe pod test-pod-$U -n $NS"

  st=$(kubectl get pvc "pvc-$U" -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)
  if [ -z "$st" ]; then skip "pvc/pvc-$U"
  elif [ "$st" = Bound ]; then ok "pvc/pvc-$U is Bound"
  else bad "pvc/pvc-$U is $st" "first Ceph provisioning takes ~30-60s; kubectl describe pvc pvc-$U -n $NS"; fi
  pod_check "pvc-pod-$U" Running "kubectl describe pod pvc-pod-$U -n $NS"
  pod_check "sidecar-$U" Running "RWO volume still attached? delete pvc-pod-$U first"
  if kubectl get pod "sidecar-$U" -n $NS >/dev/null 2>&1; then
    if kubectl logs "sidecar-$U" -c reader -n $NS --tail=20 2>/dev/null | grep -q writer-tick; then
      ok "sidecar reader sees the writer's ticks (shared volume works)"
    else bad "sidecar reader shows no writer-tick lines" "kubectl logs sidecar-$U -c writer -n $NS — is the writer running?"; fi
  fi

  if kubectl get pod "env-pod-$U" -n $NS >/dev/null 2>&1; then
    if kubectl logs "env-pod-$U" -n $NS 2>/dev/null | grep -q GREETING; then ok "env-pod-$U printed its ConfigMap env"
    else bad "env-pod-$U has no GREETING in logs" "kubectl logs env-pod-$U -n $NS"; fi
  else skip "pod/env-pod-$U"; fi
  if kubectl get configmap "app-config-$U" -n $NS >/dev/null 2>&1; then ok "configmap/app-config-$U exists"
  else skip "configmap/app-config-$U"; fi
  if kubectl get secret "app-secret-$U" -n $NS >/dev/null 2>&1; then ok "secret/app-secret-$U exists"
  else skip "secret/app-secret-$U"; fi

  ready=$(kubectl get deploy "hello-deploy-$U" -n $NS -o jsonpath='{.status.readyReplicas}/{.spec.replicas}' 2>/dev/null)
  if [ -z "$ready" ]; then skip "deploy/hello-deploy-$U"
  elif [ "${ready%/*}" = "${ready#*/}" ]; then ok "deploy/hello-deploy-$U ready ($ready)"
  else bad "deploy/hello-deploy-$U at $ready" "kubectl get pods -n $NS -l app=hello-deploy-$U"; fi

  jc=$(kubectl get job "pi-$U" -n $NS -o jsonpath='{.status.succeeded}' 2>/dev/null)
  if [ -z "$jc" ]; then skip "job/pi-$U (auto-deletes 10 min after completing)"
  elif [ "$jc" -ge 1 ] 2>/dev/null; then
    if kubectl logs -n $NS -l "job-name=pi-$U" --tail=1 2>/dev/null | grep -q "^3\.14"; then ok "job/pi-$U completed — π computed"
    else ok "job/pi-$U completed"; fi
  else bad "job/pi-$U not finished" "π takes 50-120s of CPU; kubectl get job pi-$U -n $NS"; fi

  if kubectl get ingress -n $NS -l "k8s-app=hello-web-$U" 2>/dev/null | grep -q hello; then
    code=$(curl -s -o /dev/null -w '%{http_code}' "https://hello-$U.nrp-nautilus.io" --max-time 10)
    if [ "$code" = 200 ]; then ok "https://hello-$U.nrp-nautilus.io answers 200"
    else bad "https://hello-$U.nrp-nautilus.io answered '$code'" "HAProxy + certificate need ~60s after apply"; fi
  else skip "ingress hello-$U"; fi

  pod_check "tutorial-$U-gpu-pod" Running "GPU pods pend while the pool is busy: kubectl describe pod tutorial-$U-gpu-pod -n $NS"
  if [ "$(kubectl get pod "tutorial-$U-gpu-pod" -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)" = Running ]; then
    if kubectl exec "tutorial-$U-gpu-pod" -n $NS --request-timeout=15s -- nvidia-smi -L 2>/dev/null | grep -q "GPU 0"; then
      ok "nvidia-smi sees a GPU inside the pod"
    else bad "nvidia-smi found no GPU in the pod" "kubectl describe pod tutorial-$U-gpu-pod -n $NS — check the nvidia.com/gpu limit"; fi
  fi
  ;;

3)
  need_user
  echo "Episode 3 — AI applications ($U)"
  if [ -n "$OPENAI_API_KEY" ] && [ -n "$OPENAI_API_BASE" ]; then
    code=$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $OPENAI_API_KEY" "$OPENAI_API_BASE/models" --max-time 15)
    if [ "$code" = 200 ]; then
      ok "managed LLM endpoint reachable (/models needs no token)"
      reply=$(curl -s -X POST "$OPENAI_API_BASE/chat/completions" --max-time 90 \
        -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
        -d '{"model":"minimax-m2","max_tokens":300,"messages":[{"role":"user","content":"Say OK"}]}' \
        | python3 -c 'import json,sys; print((json.load(sys.stdin)["choices"][0]["message"]["content"] or "").strip())' 2>/dev/null)
      if [ -n "$reply" ]; then ok "chat completion round-trip works — your token is valid"
      else bad "chat completion returned nothing" "token invalid or expired? instructors can mint one at nrp.ai/llmtoken — or check minimax-m2 is still in the catalog"; fi
    else bad "LLM endpoint answered '$code'" "network problem reaching ellm.nrp-nautilus.io — ask an instructor"; fi
  else bad "OPENAI_API_KEY / OPENAI_API_BASE not set" "they are pre-exported on hub spawns; restart your server"; fi
  for sec in nrp-llm-token nrp-training-milvus-credentials; do
    if kubectl get secret "$sec" -n $NS >/dev/null 2>&1; then ok "secret/$sec present in $NS"
    else bad "secret/$sec missing from $NS" "ask an instructor — the RAG/TGI pods mount it"; fi
  done

  ph=$(kubectl get pod "tutorial-$U-gp3" -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)
  if [ -z "$ph" ]; then skip "pod/tutorial-$U-gp3 (PyTorch MNIST)"
  elif [ "$ph" = Succeeded ]; then
    if kubectl logs "tutorial-$U-gp3" -n $NS 2>/dev/null | grep -q "completed successfully"; then ok "PyTorch MNIST ran to completion on the A10"
    else ok "pod/tutorial-$U-gp3 Succeeded"; fi
  elif [ "$ph" = Running ]; then ok "pod/tutorial-$U-gp3 still Running (MNIST takes a few minutes)"
  else bad "pod/tutorial-$U-gp3 is $ph" "kubectl describe pod tutorial-$U-gp3 -n $NS"; fi

  pod_check "tutorial-$U-tgi" Running "model download takes 1-3 min; kubectl logs tutorial-$U-tgi -n $NS"
  if [ "$(kubectl get pod "tutorial-$U-tgi" -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)" = Running ]; then
    if kubectl logs "tutorial-$U-tgi" -n $NS 2>/dev/null | grep -qE "Connected|Serving"; then ok "TGI finished loading zephyr-7b-beta — ready for port-forward"
    else bad "TGI is still loading the model" "downloads take 1-3 min — kubectl logs tutorial-$U-tgi -n $NS and retry shortly"; fi
  fi
  pod_check "tutorial-$U-vectordb" Running "kubectl describe pod tutorial-$U-vectordb -n $NS"
  if [ "$(kubectl get pod "tutorial-$U-vectordb" -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)" = Running ]; then
    if kubectl exec "tutorial-$U-vectordb" -n $NS --request-timeout=15s -- test -f /scratch/nrp_docs_rag.py 2>/dev/null; then
      ok "nrp_docs_rag.py staged in /scratch (Stage 2 kubectl cp done)"
    else skip "nrp_docs_rag.py in /scratch (Stage 2: kubectl cp yamls/nrp_docs_rag.py …)"; fi
  fi
  ;;

4)
  need_user
  echo "Episode 4 — storage ($U)"
  info=$(kubectl get pvc jupyterhub-shared-volume -n $NS -o jsonpath='{.status.phase} {.spec.accessModes[0]}' 2>/dev/null)
  case "$info" in
    "Bound ReadWriteMany") ok "pvc/jupyterhub-shared-volume Bound, RWX (many pods can mount it)";;
    "") skip "pvc/jupyterhub-shared-volume";;
    *) bad "pvc/jupyterhub-shared-volume: $info" "kubectl describe pvc jupyterhub-shared-volume -n $NS";;
  esac
  pod_check "tutorial-$U-pod" Running "the install loop logs 'Done with installs' when ready: kubectl logs tutorial-$U-pod -n $NS"
  if [ "$(kubectl get pod "tutorial-$U-pod" -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)" = Running ]; then
    if kubectl logs "tutorial-$U-pod" -n $NS 2>/dev/null | grep -q "Done with installs"; then ok "boto3/torch installs finished — ready to exec in"
    else bad "install loop still running" "wait for 'Done with installs': kubectl logs tutorial-$U-pod -n $NS -f"; fi
    # S3 creds arrive as env vars from the nrp-tutorial-s3 Secret; prove real access
    # by listing the shared dataset from inside the pod (needs auth + endpoint + bucket).
    if kubectl exec "tutorial-$U-pod" -n $NS --request-timeout=25s -- \
         sh -c 'aws --endpoint "$AWS_ENDPOINT_URL" s3 ls "s3://$S3_BUCKET/dataset.tar.gz"' >/dev/null 2>&1; then
      ok "S3 works — tutorial bucket + dataset reachable from the pod (creds wired via Secret)"
    else skip "S3 access (dataset not listed — is the nrp-tutorial-s3 secret present and installs finished?)"; fi
  fi
  ;;

5)
  echo "Episode 5 — JupyterHub tour (no cluster resources to check)"
  if [ -n "$JUPYTERHUB_USER" ]; then ok "you are on a JupyterHub-spawned server (user: $JUPYTERHUB_USER)"
  else bad "JUPYTERHUB_USER not set" "run this from a jh-training notebook or terminal"; fi
  if command -v helm >/dev/null; then ok "helm is installed ($(helm version --short 2>/dev/null)) — ready for the final episode"
  else bad "helm not found" "restart your server; the spawn hook installs it"; fi
  if [ -d "$HOME/pearc26" ]; then ok "workspace pulled into ~/pearc26 (nbgitpuller launch link worked)"
  else bad "~/pearc26 not found" "click any 'Open the runnable notebook' button on training.nrp-nautilus.io/pearc26"; fi
  if [ -f "$HOME/.local/share/jupyter/jupyter_ai/config.json" ]; then ok "Jupyter AI wired to the managed LLM (chat panel ready)"
  else skip "Jupyter AI config (written at spawn — restart your server if the chat panel asks for keys)"; fi
  ;;

6)
  need_user
  NSP="${NRP_NAMESPACE:-}"
  if [ -z "$NSP" ] || [ "$NSP" = changeme ]; then
    echo "Set your assigned namespace first:  export NRP_NAMESPACE=<namespace>"
    exit 1
  fi
  echo "Episode 6 — your own JupyterHub (namespace $NSP)"
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
  else bad "pvc/hub-db-dir is $st" "kubectl describe pvc hub-db-dir -n $NSP — check the storageClassName in your values"; fi
  nsrv=$(kubectl get pod -n "$NSP" -l "app=jupyterhub,component=singleuser-server" --no-headers 2>/dev/null | wc -l | tr -d ' ')
  if [ "${nsrv:-0}" -gt 0 ]; then ok "$nsrv user server(s) spawned — someone logged in to your hub 🎓"
  else skip "user servers (log in to your hub and spawn one to complete the loop)"; fi
  # Only the hub's own ingress — a shared namespace may hold unrelated ones.
  host=$(kubectl get ingress -n "$NSP" -l app=jupyterhub -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null)
  if [ -z "$host" ]; then skip "ingress (section 4)"
  else
    body=$(curl -s "https://$host/hub/login" --max-time 15)
    code=$(curl -s -o /dev/null -w '%{http_code}' "https://$host/hub/login" --max-time 15)
    # A 200 alone proves little — anything on that host answers. Look for the hub.
    if [ "$code" = 200 ] && printf '%s' "$body" | grep -qi 'jupyterhub\|id="login-main"'; then
      ok "https://$host serves the hub login page"
    elif [ "$code" = 200 ]; then
      bad "https://$host answers 200 but it is not a JupyterHub login page" "is another app already using that hostname? check your ingress host in the values"
    else bad "https://$host answered '$code'" "certificate + HAProxy need ~60s after the upgrade"; fi
  fi
  ;;

*)
  echo "usage: bash check.sh <episode 1-6> [username]"; exit 1;;
esac

echo
printf '%d passed · %d not created/cleaned up · %d need attention\n' "$PASS" "$WARN" "$FAIL"
if [ "$FAIL" -eq 0 ]; then echo "🎉 Looking good!"; else echo "Stuck? Wave an instructor over or ask in Matrix: https://nrp.ai/contact/"; fi
