---
title: Kubernetes Basics — Pods, Logs & Debugging
teaching: 15
exercises: 20
---

::: callout Open the runnable notebook for this episode
**[▶ Open notebook in JupyterHub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats&targetpath=cms-hats&urlpath=lab%2Ftree%2Fcms-hats%2Fworkspace%2Fnotebooks%2F2_kubernetes_basics.ipynb)** — every command below is a Shift+Enter cell; the YAML manifest is in the workspace's `yamls/` folder.
:::

**Time:** 00:00-00:35

The rest of this training runs Kubernetes Jobs for you — you `kubectl apply` a
manifest and read the logs. Before that, it helps to see the basic unit those
Jobs are built from: a **pod**, and get comfortable with the handful of
commands you'll use on every pod and Job for the rest of the day.

**In this exercise you will:**

1. Launch a single pod from a YAML manifest.
2. Read its logs.
3. Run a one-off command inside it, then open an interactive shell.
4. Practice the two commands you reach for the moment something looks
   wrong — `describe` and `get events`.
5. Clean up.

Everything here is deliberately small — one pod, no PVC, no image to build —
so the mechanics stay visible. The jet-classifier exercise later in this
training reuses every command you learn here, just aimed at a Job instead of
a bare pod.

## One-time hub setup

::: callout Do this once at the start of the training
If you already did this earlier in the session, skip ahead. Otherwise, do it
now — the rest of the training assumes it's already done, including the
grid certificate needed by the last lesson.

**If you're on the Analysis Hub:**

🖥️ **Terminal step** — open a terminal in JupyterLab (**File → New →
Terminal**). `grid-kube-setup` and the `kubectl` login may already be done
if you followed the setup page; running them again is harmless:

```bash
grid-kube-setup
kubectl get pods -n us-cms   # triggers a device-code login if needed
```

Then the grid certificate, needed later in [CMS Data Access on
NRP](5_cms_data.html) — both prompt for a password/pass phrase, so they need
a real terminal too:

```bash
grid-cert-import
grid-proxy-init
```

Full walkthroughs with expected output: [Get kubectl working in the hub
terminal](0_setup.html#get-kubectl-working-in-the-hub-terminal) on the setup
page, and [Setting up your grid
certificate](5_cms_data.html#setting-up-your-grid-certificate) in CMS Data
Access.

**If you're on your own machine:** skip the block above — `grid-kube-setup`,
`grid-cert-import`, and `grid-proxy-init` are Analysis Hub tools with no
local install. You'll pick this up when you switch to the hub for CMS Data
Access.

**Everyone**, set a short username once and reuse it for every command in
this training:

```bash
export USER=<username>
```
:::

## kubectl flags you'll reach for constantly

| Flag | Purpose |
|---|---|
| `-n <namespace>` | Target a specific namespace (`us-cms` for this training). |
| `-w` / `--watch` | Stream live updates instead of a one-shot list. Ctrl-C to stop. |
| `-o wide` | Add columns: node, pod IP, container image, etc. |
| `--previous` (on `kubectl logs`) | Logs from the *previous* container instance — essential for crashloops. |

## Launch a pod

Using the `$USER` you set above, make a temporary copy of the pod manifest,
same as the other exercises in this training:

```bash
cd ~/cms-hats/workspace
cp yamls/pod-basics.yaml /tmp/pod-basics-${USER}.yaml
perl -pi -e 's/<username>/$ENV{USER}/g' /tmp/pod-basics-${USER}.yaml
```

`yamls/pod-basics.yaml` is deliberately minimal:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-basics-<username>
  namespace: us-cms
spec:
  containers:
  - name: mypod
    image: ubuntu:22.04
    command: ["sh", "-c", "echo 'Hello from NRP!' && sleep 3600"]
    resources:
      limits:   { memory: 100Mi, cpu: 100m }
      requests: { memory: 100Mi, cpu: 100m }
```

Apply it and wait for it to come up:

```bash
kubectl apply -n us-cms -f /tmp/pod-basics-${USER}.yaml
kubectl wait --for=condition=Ready pod/pod-basics-${USER} -n us-cms --timeout=60s
kubectl get pods -n us-cms
```

## Read the logs

```bash
sleep 5
kubectl logs pod-basics-${USER} -n us-cms
```

We sleep briefly first — `Ready` means the container is running, not that it
has necessarily flushed its first line of output yet.

<details>
<summary>Expected output</summary>

```text
pod/pod-basics-<username> created

NAME                        READY   STATUS    RESTARTS   AGE
pod-basics-<username>       1/1     Running   0          8s

Hello from NRP!
```
</details>

## Run commands inside the pod

Run a one-off command, then open an interactive shell (Ctrl-D to exit):

```bash
kubectl exec pod-basics-${USER} -n us-cms -- echo 'Command executed successfully'
```

```bash
kubectl exec -it pod-basics-${USER} -n us-cms -- /bin/bash
```

## The debugging trio: describe, events, previous logs

::: callout When something doesn't behave the way you expect
```bash
kubectl describe pod pod-basics-${USER} -n us-cms          # status + last events
```

```bash
kubectl get events -n us-cms --field-selector involvedObject.name=pod-basics-${USER} --sort-by=.metadata.creationTimestamp
```

`describe` shows scheduling decisions and container state; `get events`
(filtered to just this pod with `--field-selector`) shows its scheduling
timeline — pulling the image, mounting volumes, starting the container. Drop
the `--field-selector` to see every event in the namespace instead. For a
**crashlooping** pod, add `--previous` to read
the dead container's logs — `kubectl logs <pod> -n us-cms --previous`. On a
healthy pod it just says *"previous terminated container not found"* — that's
expected, not an error.
:::

## Clean up

```bash
kubectl delete pod pod-basics-${USER} -n us-cms
```

With the basic pod lifecycle in hand — apply, logs, exec, describe, events,
delete — the rest of this training is the same handful of commands aimed at
Jobs instead of a bare pod.

## Taints, tolerations, and node affinity

NRP is a heterogeneous shared cluster — pools of nodes get reserved for
specific projects or trainings, and are marked off with a **taint** so
nobody else's workload accidentally lands there.

| Primitive | Lives on | Asks the question |
| --- | --- | --- |
| Node label | Node | "What is this node?" |
| `nodeSelector` / `nodeAffinity` | Pod | "Which nodes am I willing to land on?" |
| Taint | Node | "Who is allowed to land here?" |
| Toleration | Pod | "I have permission to land on those tainted nodes." |

Labels + affinity are an **attraction**; taints + tolerations are a
**repulsion**. Landing on a reserved pool on purpose usually needs both: a
toleration for permission, plus an affinity rule so the scheduler actually
picks one of those nodes instead of just tolerating them in passing.

::: danger[Only add a toleration when you're told to]
A toleration doesn't grant extra cluster-wide permissions, but it does let
your pod schedule onto nodes someone deliberately set aside — usually for a
specific project's reservation or limited/contended hardware. Adding a
toleration to a pod spec just because it won't schedule, without knowing
*why* the node is tainted, is how you end up occupying capacity that isn't
meant for you.

Only add a toleration when a lesson or your namespace admin explicitly gives
you the block to use — like the jet classifier YAMLs later in this training
already do. If `kubectl describe pod` shows something like `0/N nodes are
available: N node(s) had untolerated taint` and you *don't* have a specific
toleration you were told to use, that's the scheduler correctly telling you
those nodes aren't for you — the fix is to find capacity elsewhere, not to
copy a toleration you found by searching around.
:::

The jet classifier training, analysis, and sweep Jobs later in this training
pull a custom image and need GPU-backed nodes reserved for this training, so
their manifests include both:

```yaml
spec:
  tolerations:
  - key: nautilus.io/reservation
    operator: Equal
    value: nrp
    effect: NoSchedule
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: nrp-training
            operator: In
            values: ["true"]
```

`preferredDuringSchedulingIgnoredDuringExecution` is a **soft** hint — the
scheduler picks a reserved node if one's free but won't strand your pod if
all of them are busy. `pod-basics.yaml` (this lesson) and the PVC-browser
pod used later to copy results don't have this block at all — they don't
pull the custom training image and run fine on any regular node, so there's
nothing to tolerate.
