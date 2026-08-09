---
title: Kubernetes Basics — Pods, Logs & Debugging
teaching: 10
exercises: 15
---

::: callout Open the runnable notebook for this episode
**[▶ Open notebook in JupyterHub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats&targetpath=cms-hats&urlpath=lab%2Ftree%2Fcms-hats%2Fworkspace%2Fnotebooks%2F2_kubernetes_basics.ipynb)** — every command below is a Shift+Enter cell; the YAML manifest is in the workspace's `yamls/` folder.
:::

**Time:** 00:00-00:15

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

## kubectl flags you'll reach for constantly

| Flag | Purpose |
|---|---|
| `-n <namespace>` | Target a specific namespace (`us-cms` for this training). |
| `-w` / `--watch` | Stream live updates instead of a one-shot list. Ctrl-C to stop. |
| `-o wide` | Add columns: node, pod IP, container image, etc. |
| `--previous` (on `kubectl logs`) | Logs from the *previous* container instance — essential for crashloops. |

## Launch a pod

Set your username and make a temporary copy of the pod manifest, same as the
other exercises in this training:

```bash
export USER=<username>
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
