# Namespace claim server

A tiny coordination service so each PEARC26 attendee gets one collision-free
`nrp-training-NNN` namespace, self-service, from a notebook terminal.

## Why

All 100 attendee namespaces (`nrp-training-000` … `nrp-training-099`) already
exist and already bind the shared `jupyterhub-sa` as `admin`+`edit`. So any
attendee's notebook can already deploy into any of them — the **only** missing
piece is telling each person *which* number is theirs without two people grabbing
the same one. This server does exactly that and nothing more: it does **not**
create namespaces or touch RBAC.

## How it works

- **The cluster is the database.** A claim is stored as annotations on the
  namespace itself (`nrp.ai/claimed-by`, `nrp.ai/claimed-at`), so state survives
  pod restarts and instructors can read it with plain `kubectl`.
- **Stateless + HA.** The server holds no state, so it runs **2 replicas** for
  availability. Claim safety comes from Kubernetes **optimistic concurrency**: each
  patch carries the namespace's `resourceVersion` as a precondition, so if a peer
  claimed the same slot first the API returns `409` and the server re-reads and
  retries. Verified: **50 concurrent claims spread across both replicas → 50
  distinct namespaces, zero collisions.**
- **Idempotent per identity.** Keyed by `$JUPYTERHUB_USER` (the real hub login),
  so re-asking returns the *same* slot. Leases expire after `TTL_SECONDS` (6h).
- **Dependency-free.** `server.py` is stdlib-only and talks to the Kubernetes API
  with the mounted service-account token, so it runs on a stock `python:3.12-slim`
  image with the code delivered via a ConfigMap — no image to build.

## Cluster-internal only

There is **no Ingress** — nothing public, no DNS or cert to manage. Attendee
notebooks run in singleuser pods inside `nrp-training`, so they reach the ClusterIP
Service directly at `http://nrp-claim.nrp-training.svc.cluster.local/`. This was
verified reachable from a pod carrying the z2jh `singleuser` labels (so the
`singleuser` NetworkPolicy applies) — its broad egress rule permits in-cluster IPs.

## Deploy

```bash
./deploy.sh                # generate ConfigMap from server.py, apply, roll
```

`deploy.sh` regenerates the `nrp-claim-app` ConfigMap from `server.py` each run, so
editing `server.py` + re-running is the whole update loop.

## Attendee usage (what the lessons run)

```bash
curl -s "http://nrp-claim.nrp-training.svc.cluster.local/claim?user=$JUPYTERHUB_USER"
# -> nrp-training-042   (same slot every time)
```

## Endpoints

| Route | Purpose |
|---|---|
| `GET /claim?user=NAME`   | assign (or re-fetch) NAME's namespace → `nrp-training-NNN` |
| `GET /release?user=NAME` | free NAME's namespace |
| `GET /status`            | human-readable table of current claims (instructors) |
| `GET /healthz`           | `ok` |

## Instructor ops

```bash
# who has what, live (from an admin machine, via port-forward)
kubectl -n nrp-training port-forward deploy/nrp-claim 8080:8080 &
curl -s localhost:8080/status

# or straight from kubectl (the cluster is the source of truth)
kubectl get ns -l nrp-training=true \
  -o custom-columns=NS:.metadata.name,BY:'.metadata.annotations.nrp\.ai/claimed-by'

# reset everything before the event (clear all claims)
kubectl get ns -l nrp-training=true -o name \
  | xargs -I{} kubectl annotate {} nrp.ai/claimed-by- nrp.ai/claimed-at-
```

## Config (env on the Deployment)

`PREFIX` (`nrp-training-`), `LABEL_SELECTOR` (`nrp-training=true`),
`TTL_SECONDS` (`21600`), `PORT` (`8080`).
