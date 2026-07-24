#!/usr/bin/env bash
# Deploy (or refresh) the namespace claim server. Run with an admin kubeconfig.
# The server is cluster-internal only (no Ingress) — attendee notebooks reach it at
# http://nrp-claim.nrp-training.svc.cluster.local/.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> generating ConfigMap nrp-claim-app from server.py"
kubectl create configmap nrp-claim-app -n nrp-training \
  --from-file=server.py=server.py \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> applying deploy.yaml"
kubectl apply -f deploy.yaml

echo "==> rolling the Deployment to pick up code changes"
kubectl rollout restart deploy/nrp-claim -n nrp-training
kubectl rollout status  deploy/nrp-claim -n nrp-training --timeout=120s

echo
echo "Done. In-cluster URL: http://nrp-claim.nrp-training.svc.cluster.local/"
echo "Smoke test:  kubectl -n nrp-training port-forward deploy/nrp-claim 8080:8080 &"
echo "             curl -s localhost:8080/status"
