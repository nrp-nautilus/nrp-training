---
title: Deploy JupyterHub with Helm
teaching: 40
exercises: 0
---

::: callout Open the Helm notebook in JupyterHub
**[▶ Open the Helm notebook in JupyterHub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=main&urlpath=lab%2Ftree%2Fnrp-training%2Ftrainings%2Fcra2%2Fworkspace%2F4_jupyterhub_helm.ipynb)** — opens the runnable Helm notebook (in this repo) live on jh-training.nrp-nautilus.io.
:::

In Part 2 you **used** NRP's managed AI. Now you'll **deploy your own**
JupyterHub on the cluster: install the Helm chart into your namespace, expose
it at a URL, customize it, and tear it down.

> This notebook uses the **Bash** kernel — every cell is a shell command, so
> there's nothing to copy into a terminal. (The optional RAG bonus at the very
> end is the one exception — it's a Python cell.)

## Key concepts

- **Helm** is the package manager for Kubernetes: instead of writing every
  Deployment, Service, and ConfigMap by hand, you install a **chart** (a bundle
  of templates) and tune it through a **values file**.
- The **JupyterHub chart** deploys a *hub*, a *proxy*, and per-user notebook
  servers. You set authentication, images, CPU/RAM/GPU limits, and storage in the
  values file.
- **One hub per namespace** — that's why each of you has your **own** namespace
  (`nrp-training-000` … `nrp-training-099`, on the slip you were handed).
- In this training session, `kubectl`, `helm`, and your kubeconfig are already
  set up — nothing to install.

## 1. Set your namespace and verify access

Put **your** assigned namespace in the cell below and run it. It should print
`yes` — that confirms your service account can deploy a hub there.

```python
cd ~/cra-tutorial   # the Bash kernel starts in your home dir; work from the repo
# 👇 CHANGE this to YOUR assigned namespace (from your slip), then run the cell.
export NAMESPACE=nrp-training-000

kubectl auth can-i create deployment -n "$NAMESPACE"   # expect: yes
```

## 2. Add the JupyterHub Helm repository

This tells Helm where to download the chart from.

```python
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update
echo "---"
kubectl auth whoami && helm version --short
```

## 3. Review the values file

This repo ships a complete, **NRP-tested** values file at
[`yamls/jhub-values.yaml`](yamls/jhub-values.yaml). A few settings in it are
non-obvious but **required on NRP** (the stock chart defaults get rejected):

- `service.type: ClusterIP` — NRP blocks `LoadBalancer` services.
- `hub.resources` / `proxy.chp.resources` with **requests *and* limits** — NRP
  requires every container to declare them.
- `scheduling.userScheduler` / `prePuller` **disabled** — they need
  *cluster-scoped* RBAC your namespace account doesn't have.
- `storageClass: rook-ceph-block-east` + region `us-east` — matches the training
  cluster's storage.

The parts you'll most likely tweak are the **password** and the **image
profiles**. Take a look:

```python
cd ~/cra-tutorial   # the Bash kernel starts in your home dir; work from the repo
cat yamls/jhub-values.yaml
```

## 4. Deploy with Helm

This installs the chart into **your** namespace with the values file. It waits
until the hub is ready (~1–2 min) and prints `STATUS: deployed`.

```python
cd ~/cra-tutorial   # the Bash kernel starts in your home dir; work from the repo
helm upgrade --cleanup-on-fail --install jhub jupyterhub/jupyterhub \
  --namespace "$NAMESPACE" \
  --version 3.3.7 \
  --values yamls/jhub-values.yaml \
  --wait --timeout 10m
```

See what got created — you should see a **hub** pod and a **proxy** pod
reach `Running` (user pods appear on demand when someone logs in):

```python
kubectl get pods,svc -n "$NAMESPACE"
```

## 5. Make it reachable at a URL

By default the hub is internal (`ClusterIP`). Add an **ingress** to expose it at a
public address. Pick a unique host name, then upgrade the release in place:

```python
cd ~/cra-tutorial   # the Bash kernel starts in your home dir; work from the repo
export HUBHOST="jhub-${NAMESPACE}.nrp-nautilus.io"

helm upgrade jhub jupyterhub/jupyterhub \
  --namespace "$NAMESPACE" --version 3.3.7 \
  --values yamls/jhub-values.yaml \
  --set ingress.enabled=true \
  --set ingress.ingressClassName=haproxy \
  --set ingress.hosts[0]="$HUBHOST" \
  --set ingress.tls[0].hosts[0]="$HUBHOST" \
  --wait --timeout 5m

echo "Give DNS + TLS a minute, then log in at:  https://$HUBHOST   (admin / training123)"
```

## 6. Customize

Customizing = change a value and re-run the upgrade. For small tweaks use
`--set`; for bigger ones edit `yamls/jhub-values.yaml` and re-run the deploy
cell. Example — guarantee every user 4 GB of RAM:

```python
cd ~/cra-tutorial   # the Bash kernel starts in your home dir; work from the repo
helm upgrade jhub jupyterhub/jupyterhub \
  --namespace "$NAMESPACE" --version 3.3.7 \
  --values yamls/jhub-values.yaml \
  --set ingress.enabled=true \
  --set ingress.ingressClassName=haproxy \
  --set ingress.hosts[0]="$HUBHOST" \
  --set ingress.tls[0].hosts[0]="$HUBHOST" \
  --set singleuser.memory.guarantee=4G \
  --wait --timeout 5m

echo "Updated: per-user RAM guarantee is now 4G"
```

## 7. Manage and clean up

Check your release and the hub logs:

```python
helm list -n "$NAMESPACE"
echo "--- hub logs (last 20 lines) ---"
kubectl logs -n "$NAMESPACE" -l component=hub --tail=20
```

**Please tear it down when you're done** so your namespace is free:

```python
helm uninstall jhub -n "$NAMESPACE"
# user-data PVCs are kept by default; delete them too only if you're sure:
# kubectl delete pvc -n "$NAMESPACE" -l component=singleuser-storage
kubectl get pods -n "$NAMESPACE"
```

## ⭐ Bonus — ask the *entire* JupyterHub docs with RAG

<details>
<summary><b>Click to expand</b></summary>

Customizing a hub means digging through the **Zero-to-JupyterHub** docs.
Instead, point the *same RAG idea from Part 2* at the docs and just **ask**:
the cell below fetches the key docs pages, embeds them with NRP's managed
embedding model, finds the most relevant, and answers — citing the page it used.

This is **one plain-Python cell**. To run it, switch the kernel to **Python 3**
(the kernel picker at the top-right) — or paste it into
[`2_inference.ipynb`](2_inference.ipynb). Edit `QUESTION` and run.

</details>

```python
QUESTION = "How do I give each user more memory?"

import os, re, urllib.request, numpy as np
from openai import OpenAI

# NRP sets OPENAI_API_BASE (not OPENAI_BASE_URL), so pass it explicitly.
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                base_url=os.environ.get("OPENAI_API_BASE", os.environ.get("OPENAI_BASE_URL")))

# A handful of the most useful z2jh docs pages (add more paths to widen coverage).
# We read the raw Markdown straight from GitHub -- no HTML to clean.
PAGES = [
    "administrator/optimization",
    "administrator/cost",
    "administrator/authentication",
    "jupyterhub/customizing/user-storage",
    "jupyterhub/customizing/user-environment",
    "jupyterhub/customizing/user-management",
]
BASE = "https://raw.githubusercontent.com/jupyterhub/zero-to-jupyterhub-k8s/main/docs/source/"

def clean(t):
    t = re.sub(r"```\{[^}]*\}", "", t)            # drop MyST directive fences
    t = re.sub(r"\{[a-z]+\}`([^`]*)`", r"\1", t)  # unwrap {role}`text`
    return re.sub(r"\s+", " ", t).strip()

# 1. Fetch each page and split it into ~700-character chunks
chunks, sources = [], []
for p in PAGES:
    try:
        md = urllib.request.urlopen(BASE + p + ".md", timeout=20).read().decode("utf-8", "ignore")
    except Exception as e:
        print("  (skipped", p, "->", e, ")"); continue
    text = clean(md)
    for i in range(0, len(text), 700):
        chunks.append(text[i:i+700]); sources.append(p)
print(f"Indexed {len(chunks)} chunks from {len(set(sources))} docs pages.")

# 2. Embed everything + the question, then rank by cosine similarity
def embed(texts):
    data = client.embeddings.create(model="qwen3-embedding", input=texts).data
    v = np.array([d.embedding for d in data])
    return v / np.linalg.norm(v, axis=1, keepdims=True)

vecs = embed(chunks)
qvec = embed([QUESTION])[0]
top = (vecs @ qvec).argsort()[::-1][:4]
context = "\n\n".join(f"[{sources[i]}] {chunks[i]}" for i in top)

# 3. Answer using only the retrieved excerpts
resp = client.chat.completions.create(
    model="minimax-m2",
    messages=[
        {"role": "system", "content": "Answer the JupyterHub Helm question using ONLY the provided docs excerpts. Include a short YAML snippet when it helps."},
        {"role": "user", "content": f"Docs excerpts:\n{context}\n\nQuestion: {QUESTION}"},
    ],
    max_tokens=1200,
)
msg = resp.choices[0].message
answer = msg.content or getattr(msg, "reasoning", "") or "(no answer returned)"

print("\n" + "=" * 78)
print("  QUESTION:", QUESTION)
print("=" * 78 + "\n")
print(answer.strip())
print("\n" + "-" * 78)
print("  sources:", ", ".join(dict.fromkeys(sources[i] for i in top)))
print("-" * 78)

```
