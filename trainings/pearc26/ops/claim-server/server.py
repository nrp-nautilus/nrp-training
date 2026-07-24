#!/usr/bin/env python3
"""nrp-training namespace claim server.

A tiny, dependency-free coordination service. The 100 attendee namespaces
(nrp-training-000 .. nrp-training-099) already exist and already bind the shared
jupyterhub-sa as admin, so this server does NOT create namespaces or manage RBAC.
Its only job is collision-free *assignment*: hand each attendee one unused number
and remember it.

The cluster itself is the database: a claim is stored as annotations on the
namespace object, so state is durable across restarts and instructors can read it
with plain kubectl. A single replica plus an in-process lock fully serializes
claims, so there are no races even when 50 people curl at once.

Endpoints (all GET so a bare `curl` works from a notebook terminal):
  /                     help text
  /claim?user=NAME      assign (or return existing) namespace for NAME -> "nrp-training-042"
  /release?user=NAME    free NAME's namespace
  /status               human-readable table of current claims (for instructors)
  /healthz              "ok"

Config via env: PREFIX (nrp-training-), LABEL_SELECTOR (nrp-training=true),
TTL_SECONDS (21600 = 6h), PORT (8080).
"""
import json
import os
import re
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PREFIX = os.environ.get("PREFIX", "nrp-training-")
LABEL_SELECTOR = os.environ.get("LABEL_SELECTOR", "nrp-training=true")
TTL_SECONDS = int(os.environ.get("TTL_SECONDS", "21600"))
PORT = int(os.environ.get("PORT", "8080"))

CLAIMED_BY = "nrp.ai/claimed-by"
CLAIMED_AT = "nrp.ai/claimed-at"

SA_DIR = "/var/run/secrets/kubernetes.io/serviceaccount"
API = "https://kubernetes.default.svc"
NAME_RE = re.compile(r"^" + re.escape(PREFIX) + r"\d{3}$")

_lock = threading.Lock()


def _sa_token():
    with open(os.path.join(SA_DIR, "token")) as f:
        return f.read().strip()


def _ssl_ctx():
    return ssl.create_default_context(cafile=os.path.join(SA_DIR, "ca.crt"))


def _api(method, path, body=None):
    url = API + path
    data = None
    headers = {"Authorization": "Bearer " + _sa_token(), "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        # merge-patch so we only touch the annotations we name
        headers["Content-Type"] = "application/merge-patch+json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, context=_ssl_ctx(), timeout=15) as resp:
        return json.loads(resp.read().decode())


def list_namespaces():
    """Return [(name, claimed_by_or_None, claimed_at_float, resource_version), ...] sorted by number."""
    q = urllib.parse.urlencode({"labelSelector": LABEL_SELECTOR})
    out = _api("GET", "/api/v1/namespaces?" + q)
    rows = []
    for item in out.get("items", []):
        name = item["metadata"]["name"]
        if not NAME_RE.match(name):
            continue
        ann = item["metadata"].get("annotations") or {}
        by = ann.get(CLAIMED_BY) or None
        rv = item["metadata"].get("resourceVersion")
        try:
            at = float(ann.get(CLAIMED_AT) or 0)
        except ValueError:
            at = 0.0
        rows.append((name, by, at, rv))
    rows.sort(key=lambda r: r[0])
    return rows


def patch(name, claimed_by, claimed_at, resource_version=None):
    """Set (or, with None values, clear) the claim annotations on a namespace.

    When resource_version is given it becomes an optimistic-concurrency precondition:
    the Kubernetes API applies the patch only if the object hasn't changed since we
    read it, otherwise it returns 409 Conflict. That is what makes claims safe across
    any number of replicas — no shared in-process lock required.
    """
    meta = {"annotations": {CLAIMED_BY: claimed_by, CLAIMED_AT: claimed_at}}
    if resource_version is not None:
        meta["resourceVersion"] = resource_version
    _api("PATCH", "/api/v1/namespaces/" + name, {"metadata": meta})


def _try_claim(user, now):
    """One compare-and-swap attempt. Returns a namespace name, or None if all taken.
    Raises HTTPError(409) if we lost a race and the caller should re-read and retry."""
    rows = list_namespaces()
    # already hold a live lease? refresh it and return the same slot (idempotent)
    for name, by, at, rv in rows:
        if by == user and (now - at) < TTL_SECONDS:
            patch(name, user, str(now), rv)
            return name
    # otherwise take the lowest-numbered free (never claimed, or expired) slot
    for name, by, at, rv in rows:
        if by is None or (now - at) >= TTL_SECONDS:
            patch(name, user, str(now), rv)
            return name
    return None


def claim(user):
    now = time.time()
    # The lock is a courtesy that serializes requests *within* this replica so peers
    # don't fight each other; cross-replica safety comes from the CAS + retry below.
    with _lock:
        for _ in range(20):
            try:
                return _try_claim(user, now)
            except urllib.error.HTTPError as e:
                if e.code == 409:
                    continue  # someone else changed that namespace first — re-read
                raise
    return None  # gave up after sustained contention (should never happen in practice)


def release(user):
    now = time.time()
    freed = []
    with _lock:
        for name, by, at, rv in list_namespaces():
            if by == user:
                try:
                    patch(name, None, None, rv)
                    freed.append(name)
                except urllib.error.HTTPError as e:
                    if e.code != 409:
                        raise  # 409 just means it changed under us; skip it
    return freed


def status_text():
    now = time.time()
    rows = list_namespaces()
    live = [(n, by, at) for n, by, at, rv in rows if by and (now - at) < TTL_SECONDS]
    free = sum(1 for n, by, at, rv in rows if not by or (now - at) >= TTL_SECONDS)
    lines = ["%d/%d claimed, %d free (TTL %dh)" % (len(live), len(rows), free, TTL_SECONDS // 3600), ""]
    for name, by, at in live:
        age = int(now - at)
        lines.append("  %-20s  %-30s  %dm ago" % (name, by, age // 60))
    return "\n".join(lines) + "\n"


HELP = (
    "nrp-training namespace claim server\n\n"
    "  curl -s $URL/claim?user=$NRP_USER      -> claim (or re-fetch) your namespace\n"
    "  curl -s $URL/release?user=$NRP_USER    -> release it\n"
    "  curl -s $URL/status                    -> who has what (instructors)\n"
)


def _clean_user(raw):
    user = (raw or "").strip()
    return user[:120] if user else ""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, text):
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parts = urllib.parse.urlparse(self.path)
        route = parts.path.rstrip("/") or "/"
        qs = urllib.parse.parse_qs(parts.query)
        user = _clean_user(qs.get("user", [""])[0])
        try:
            if route == "/":
                self._send(200, HELP)
            elif route == "/healthz":
                self._send(200, "ok\n")
            elif route == "/status":
                self._send(200, status_text())
            elif route == "/claim":
                if not user:
                    self._send(400, "missing ?user= (pass your username, e.g. ?user=$NRP_USER)\n")
                    return
                name = claim(user)
                if name:
                    self._send(200, name + "\n")
                else:
                    self._send(503, "all namespaces are claimed right now — ask an instructor\n")
            elif route == "/release":
                if not user:
                    self._send(400, "missing ?user=\n")
                    return
                freed = release(user)
                self._send(200, ("released " + ", ".join(freed) if freed else "nothing to release") + "\n")
            else:
                self._send(404, "not found\n")
        except urllib.error.HTTPError as e:
            self._send(502, "kube API error: %s %s\n" % (e.code, e.reason))
        except Exception as e:  # noqa: BLE001 - surface anything to the caller
            self._send(500, "error: %s\n" % e)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    sys.stderr.write("claim server listening on :%d (prefix=%s ttl=%ds)\n" % (PORT, PREFIX, TTL_SECONDS))
    server.serve_forever()


if __name__ == "__main__":
    main()
