---
title: Basic Docker & Kubernetes Hands-On
teaching: 10
exercises: 60
---

::: callout Launch the workspace in JupyterHub
**[▶ Open the runnable notebook for this episode](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fpearc26&targetpath=pearc26&urlpath=lab%2Ftree%2Fpearc26%2Fworkspace%2Fnotebooks%2F2_kubernetes.ipynb)** — every command below is a Shift+Enter cell; the YAML manifests are in the workspace's `yamls/` folder.
:::

**Morning session · 9:40 – 10:50 AM**

This episode is the core Kubernetes hands-on: scheduling pods and jobs, persistent storage, multi-container pods, ConfigMaps and Secrets, Deployments, exposing an HTTPS service, steering pods with taints/tolerations and node affinity, and launching a GPU pod.

**Conventions.** Hands-on examples use the **`nrp-training-k8s`** namespace. In any YAML or command, replace **`<username>`** with a short version of your name or username to avoid collisions with other participants. Manifests live in the workspace `yamls/` folder.

> 📘 **Docs:** [Kubernetes basics](https://nrp.ai/documentation/userdocs/tutorial/basic/) · [GPU pods](https://nrp.ai/documentation/userdocs/running/gpu-pods/) · [Run jobs](https://nrp.ai/documentation/userdocs/running/jobs/) · [Storage](https://nrp.ai/documentation/userdocs/storage/intro/) · [Live resources](https://nrp.ai/viz/resources/)

## kubectl flags you'll reach for constantly

| Flag | Purpose |
|---|---|
| `-n <namespace>` | Target a specific namespace. |
| `-l key=value` | Filter resources by label. |
| `-w` / `--watch` | Stream live updates instead of a one-shot list. Ctrl-C to stop. |
| `-o wide` | Add columns: node, pod IP, container image, etc. |
| `-o yaml` / `-o json` | Print the full resource manifest. |
| `-o jsonpath='{...}'` | Extract one field. |
| `--show-labels` | Append a column with every label a resource carries. |
| `--previous` (on `kubectl logs`) | Logs from the *previous* container instance — essential for crashloops. |

## Hands-on: a simple pod

Open `yamls/test-pod.yaml` and replace `<username>` in `metadata.name`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod-<username>
  namespace: nrp-training-k8s
spec:
  containers:
  - name: mypod
    image: ubuntu:22.04
    command: ["sh", "-c", "echo 'Hello from NRP!' && sleep 3600"]
    resources:
      limits:  { memory: 100Mi, cpu: 100m }
      requests: { memory: 100Mi, cpu: 100m }
```

Notice `requests` and `limits` are identical — the Gatekeeper-safe default from Episode 1.

Launch and inspect:

```bash
kubectl apply -n nrp-training-k8s -f yamls/test-pod.yaml
kubectl get pods -n nrp-training-k8s
kubectl logs test-pod-<username> -n nrp-training-k8s
```

<details>
<summary>Expected output</summary>

```text
pod/test-pod-<username> created

NAME                  READY   STATUS    RESTARTS   AGE
test-pod-<username>   1/1     Running   0          12s

Hello from NRP!
```
</details>

Run a command inside it, then open an interactive shell (Ctrl-D to exit):

```bash
kubectl exec test-pod-<username> -n nrp-training-k8s -- echo 'Command executed successfully'
kubectl exec -it test-pod-<username> -n nrp-training-k8s -- /bin/bash
```

::: callout The debugging trio
When something doesn't behave the way you expect:

```bash
kubectl describe pod test-pod-<username> -n nrp-training-k8s          # status + last events
kubectl get events -n nrp-training-k8s --sort-by=.metadata.creationTimestamp | tail -20
kubectl logs test-pod-<username> -n nrp-training-k8s --previous        # logs from the prior crash
```

`describe` shows scheduling decisions and container state; `get events` shows the namespace timeline; `--previous` is essential for crashlooping pods.
:::

Clean up:

```bash
kubectl delete pod test-pod-<username> -n nrp-training-k8s
```

## Hands-on: persistent storage with a PVC

Pods are ephemeral — anything written to the container filesystem disappears when the pod terminates. **PersistentVolumeClaims** ask Kubernetes for long-lived storage you can mount into pods. On NRP we typically use `rook-ceph-block-east` for general-purpose `ReadWriteOnce` block storage.

Open `yamls/pvc.yaml` — it contains a 1 GiB PVC and a writer pod that mounts it at `/data`. Replace `<username>` in both names, then:

```bash
kubectl apply -n nrp-training-k8s -f yamls/pvc.yaml
kubectl get pvc -n nrp-training-k8s
kubectl get pod pvc-pod-<username> -n nrp-training-k8s
```

<details>
<summary>Expected output (Ceph provisioning takes ~30–60s on first claim)</summary>

```text
NAME             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS           AGE
pvc-<username>   Bound    pvc-99a63070-eb3d-490a-82fd-4e5811e4a5df   1Gi        RWO            rook-ceph-block-east   45s

NAME                 READY   STATUS    RESTARTS   AGE
pvc-pod-<username>   1/1     Running   0          47s
```
</details>

Prove the data survives pod deletion — delete only the pod, re-apply, and read the file back:

```bash
kubectl exec pvc-pod-<username> -n nrp-training-k8s -- cat /data/log.txt
kubectl delete pod pvc-pod-<username> -n nrp-training-k8s
kubectl apply -n nrp-training-k8s -f yamls/pvc.yaml
kubectl exec pvc-pod-<username> -n nrp-training-k8s -- cat /data/log.txt   # previous line still there
```

**Don't delete the PVC yet** — the next section reuses it.

## Hands-on: multi-container pod (sidecar pattern)

A pod can hold more than one container — they share the network namespace (same `localhost`) and any volumes mounted into both. This is the classic **sidecar** pattern: a main container plus a supporting one (log shipping, file syncing, format conversion).

`yamls/multicontainer.yaml` defines a pod whose **writer** container appends a tick line to a shared file every 5 seconds while a **reader** container tails the same file. It reuses `pvc-<username>` from the previous section — first delete the writer pod so the RWO volume detaches:

```bash
kubectl delete pod pvc-pod-<username> -n nrp-training-k8s --ignore-not-found
kubectl apply -n nrp-training-k8s -f yamls/multicontainer.yaml
kubectl get pod sidecar-<username> -n nrp-training-k8s
```

Read each container's log stream separately with `-c`:

```bash
kubectl logs sidecar-<username> -c writer -n nrp-training-k8s --tail=5
kubectl logs sidecar-<username> -c reader -n nrp-training-k8s --tail=5
```

<details>
<summary>Expected output</summary>

```text
# writer:
writer-tick 1 04:55:58
writer-tick 2 04:56:04

# reader (tailing the shared file from a different process):
reader started, tailing /shared/data.log
writer-tick 1 04:55:58
writer-tick 2 04:56:04
```
</details>

Every line the writer appends shows up in the reader's stream — both containers see the same volume. Clean up (this also releases the PVC):

```bash
kubectl delete -n nrp-training-k8s -f yamls/multicontainer.yaml
kubectl delete -n nrp-training-k8s -f yamls/pvc.yaml
```

## Hands-on: ConfigMap, Secret, and env vars

Hard-coding paths, hostnames, or API tokens into images is a recipe for pain. Kubernetes gives you two purpose-built objects:

- **ConfigMap** — non-sensitive key/value config, stored as plain text.
- **Secret** — sensitive values (tokens, passwords, TLS keys), stored base64-encoded with separate RBAC.

`yamls/configmap-secret.yaml` ships a ConfigMap, a Secret, and a Pod that pulls ConfigMap keys in bulk via `envFrom` and the Secret via `secretKeyRef`. Replace `<username>` in all names and apply:

```bash
kubectl apply -n nrp-training-k8s -f yamls/configmap-secret.yaml
kubectl logs env-pod-<username> -n nrp-training-k8s
```

<details>
<summary>Expected output</summary>

```text
GREETING=Hello from NRP
SERVER_PORT=8080
API_TOKEN starts with: tutorial…
```
</details>

Look inside each object:

```bash
kubectl get configmap app-config-<username> -n nrp-training-k8s -o yaml | grep -A2 '^data:'
kubectl get secret    app-secret-<username> -n nrp-training-k8s -o jsonpath='{.data.API_TOKEN}' | base64 -d ; echo
```

Base64 is **storage format, not encryption** — anyone who can `get secret` in your namespace can read it. Clean up:

```bash
kubectl delete -n nrp-training-k8s -f yamls/configmap-secret.yaml
```

::: quiz Quick check — pods & config
1. Both sidecar containers saw the same `writer-tick` lines. What do containers in one pod share?
- [x] The network namespace (same `localhost`) and any volumes mounted into both
- [ ] Nothing — they talk over the cluster network like separate pods
- [ ] The entire filesystem of the main container
> Containers in a pod are co-scheduled on one node, share `localhost`, and see any volume mounted into each of them — that's what makes the sidecar pattern work.

2. Your pod is crashlooping. Which command shows why the *previous* container instance died?
- [ ] `kubectl logs -f` on the pod
- [x] `kubectl logs <pod> --previous`
- [ ] `kubectl delete` and re-apply, then read the logs quickly
> The current container may have no useful output yet — `--previous` reads the logs of the instance that crashed. Pair it with `describe` and `get events`: the debugging trio.

3. `env-pod` printed `GREETING=Hello from NRP`. Where did that value come from?
- [x] A ConfigMap, injected as environment variables via `envFrom`
- [ ] It was hard-coded in the container image
- [ ] A Secret, decoded at startup
> Non-sensitive config lives in ConfigMaps (`envFrom` pulls all keys in bulk); sensitive values live in Secrets referenced via `secretKeyRef`. Neither is baked into the image.
:::

## Hands-on: Deployment

A **Deployment** keeps a set of identical pods running: it restarts them when they fail and rolls out new versions without downtime. Open `yamls/deployment.yaml`, replace `<username>`, apply:

```bash
kubectl apply -n nrp-training-k8s -f yamls/deployment.yaml
kubectl get deploy,rs,pod -n nrp-training-k8s -l app=hello-deploy-<username>
```

Try the basic operations:

```bash
# scale to 4 replicas
kubectl scale deployment hello-deploy-<username> -n nrp-training-k8s --replicas=4

# delete one pod and watch the Deployment immediately recreate it
VICTIM=$(kubectl get pod -n nrp-training-k8s -l app=hello-deploy-<username> -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "$VICTIM" -n nrp-training-k8s
kubectl get pods -n nrp-training-k8s -l app=hello-deploy-<username>   # still 4

# rolling update to a different image
kubectl set image deployment/hello-deploy-<username> -n nrp-training-k8s hello=nginx:alpine
kubectl rollout status deployment/hello-deploy-<username> -n nrp-training-k8s
```

### Working with running pods: cp, port-forward, patch

Pick one pod from the Deployment:

```bash
POD=$(kubectl get pod -n nrp-training-k8s -l app=hello-deploy-<username> -o jsonpath='{.items[0].metadata.name}')
```

Copy files in and out:

```bash
echo "training data v1" > /tmp/dataset.txt
kubectl cp /tmp/dataset.txt nrp-training-k8s/"$POD":/tmp/dataset.txt
kubectl exec "$POD" -n nrp-training-k8s -- cat /tmp/dataset.txt
```

Tunnel a pod port to your terminal (foreground; use a second terminal for `curl`):

```bash
kubectl port-forward "$POD" -n nrp-training-k8s 8080:80
# second terminal:
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8080
```

Patch a single field without re-applying YAML:

```bash
kubectl patch deployment hello-deploy-<username> -n nrp-training-k8s -p '{"spec":{"replicas":2}}'
```

Clean up:

```bash
kubectl delete -n nrp-training-k8s -f yamls/deployment.yaml
```

## Hands-on: batch Job

A **Job** runs pods until a target number complete successfully. Open `yamls/job.yaml`, replace `<username>`, apply, and watch π get computed:

```bash
kubectl apply -n nrp-training-k8s -f yamls/job.yaml
kubectl get jobs -n nrp-training-k8s
kubectl logs -n nrp-training-k8s -l job-name=pi-<username>
```

<details>
<summary>Expected output (after 50–120s of CPU work)</summary>

```text
3.14159265358979323846264338327950288419716939937510582097494459230781640628620…

NAME             STATUS     COMPLETIONS   DURATION   AGE
pi-<username>    Complete   1/1           53s        57s
```
</details>

The Job auto-deletes 10 minutes after completion (`ttlSecondsAfterFinished: 600`).

## Hands-on: exposing a service over HTTPS

To expose an HTTP application publicly you need three objects: a **Deployment** (runs the pods), a **Service** (stable in-cluster name), and an **Ingress** on the `haproxy` class that routes a public hostname to the Service. NRP runs HAProxy as the ingress controller, and Cert Manager issues a free Let's Encrypt TLS certificate automatically for any `*.nrp-nautilus.io` hostname.

Open `yamls/ingress-demo.yaml` and replace **every** `<username>` (the hostname `hello-<username>.nrp-nautilus.io` must be globally unique):

```bash
kubectl apply -n nrp-training-k8s -f yamls/ingress-demo.yaml
kubectl get deploy,svc,ingress -n nrp-training-k8s -l k8s-app=hello-web-<username>
```

Wait ~60 seconds for HAProxy and the certificate, then:

```bash
curl -sI https://hello-<username>.nrp-nautilus.io | head -5
```

<details>
<summary>Expected output</summary>

```text
HTTP/2 200
server: nginx/1.29.1
content-type: text/plain
```
</details>

Open the URL in your browser and reload a few times — the `Server name` line cycles between the two replicas. Clean up (this releases the public hostname):

```bash
kubectl delete -n nrp-training-k8s -f yamls/ingress-demo.yaml
```

## Scheduling: labels, affinity, taints, and tolerations

NRP is a heterogeneous shared cluster — 500+ nodes, many GPU SKUs, and pools reserved for specific projects. Scheduling primitives are how you say "*put my pod **here**, not **there***":

| Primitive | Lives on | Asks the question |
|---|---|---|
| **Node label** | Node | "What is this node? (GPU type, region, owner…)" |
| **`nodeSelector` / `nodeAffinity`** | Pod | "Which nodes am I willing to land on?" |
| **Taint** | Node | "Who is allowed to land here?" |
| **Toleration** | Pod | "I have permission to land on those tainted nodes." |

Labels + affinity are an **attraction**; taints + tolerations are a **repulsion**. You usually need **both**: a toleration to be allowed onto a reserved node, plus an affinity rule so the scheduler actually picks it.

### The PEARC26 reserved GPU pool

For the tutorial, NRP has a pool of NVIDIA A10 GPU nodes reserved:

- **Label** `nrp-training=true` — marks the tutorial nodes.
- **Taint** `nautilus.io/reservation=nrp:NoSchedule` — keeps other workloads off them.

Explore the pool:

```bash
kubectl get nodes -l nrp-training=true -L nvidia.com/gpu.product
kubectl get nodes -l nrp-training=true \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.taints}{"\n"}{end}'
```

<details>
<summary>Expected output</summary>

```text
NAME                         STATUS   ROLES    AGE      VERSION    GPU.PRODUCT
hcc-nrp-shor-c5825.unl.edu   Ready    <none>   3y300d   v1.33.12   NVIDIA-A10
hcc-nrp-shor-c5905.unl.edu   Ready    <none>   3y300d   v1.33.8    NVIDIA-A10
…

hcc-nrp-shor-c5825.unl.edu	[{"effect":"NoSchedule","key":"nautilus.io/reservation","value":"nrp"}, …]
```
</details>

To land on the pool, a pod spec needs both blocks — this pattern appears in every GPU manifest in the workspace:

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

`preferred…` is a soft hint — the scheduler picks a reserved node if one is free but won't strand your pod if all are busy. The `required…` variant blocks scheduling until a matching node frees up. Beyond this tutorial the same pattern targets specific GPU models (`nvidia.com/gpu.product=NVIDIA-A100-PCIE-40GB`), CUDA versions (`nvidia.com/cuda.runtime.major=12`), or regions (`topology.kubernetes.io/region=us-west`).

## Hands-on: your first GPU pod

`yamls/gpu-pod.yaml` requests one GPU via resource limits:

```yaml
    resources:
      limits:
        nvidia.com/gpu: 1
      requests:
        nvidia.com/gpu: 1
```

Resource keys by hardware type:

- **NVIDIA GPUs (generic):** `nvidia.com/gpu: <count>`
- **Qualcomm Cloud AI 100:** `qualcomm.com/qaic: <count>` — Nautilus has 8 Cloud AI 100 Ultra cards × 4 SoCs = 32 devices; each runs LLMs up to ~25B parameters
- **Specific products:** `nvidia.com/a100`, `nvidia.com/rtxa6000`, etc. — see [GPU pods docs](https://nrp.ai/documentation/userdocs/running/gpu-pods/)

Launch it, exec in, and run `nvidia-smi`:

```bash
kubectl apply -n nrp-training-k8s -f yamls/gpu-pod.yaml
kubectl get pods -n nrp-training-k8s
kubectl exec -it tutorial-<username>-gpu-pod -n nrp-training-k8s -- nvidia-smi
```

<details>
<summary>Expected output</summary>

```text
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.126.09             Driver Version: 580.126.09     CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
|   0  NVIDIA A10                     On  |   00000000:06:00.0 Off |                    0 |
+-----------------------------------------+------------------------+----------------------+
```
</details>

**Important — GPUs are scarce shared resources.** Delete the pod as soon as you're done:

```bash
kubectl delete pod tutorial-<username>-gpu-pod -n nrp-training-k8s
```

## End of episode — cleanup

```bash
kubectl delete pod test-pod-<username>            -n nrp-training-k8s --ignore-not-found
kubectl delete -f yamls/multicontainer.yaml       -n nrp-training-k8s --ignore-not-found
kubectl delete -f yamls/pvc.yaml                  -n nrp-training-k8s --ignore-not-found
kubectl delete -f yamls/configmap-secret.yaml     -n nrp-training-k8s --ignore-not-found
kubectl delete -f yamls/deployment.yaml           -n nrp-training-k8s --ignore-not-found
kubectl delete -f yamls/job.yaml                  -n nrp-training-k8s --ignore-not-found
kubectl delete -f yamls/ingress-demo.yaml         -n nrp-training-k8s --ignore-not-found
kubectl delete pod tutorial-<username>-gpu-pod    -n nrp-training-k8s --ignore-not-found

# what did I leave running?
kubectl get all -n nrp-training-k8s
```

Then verify: `bash check.sh 2` in the workspace (or the last cell of the notebook).

::: quiz Quick check — before the break
1. You deleted a pod that mounted a PVC, then re-created it from the same manifest. What happened to the files in /data?
- [x] Still there — the PVC's lifecycle is independent of any pod
- [ ] Wiped when the pod terminated
- [ ] Recovered only if the pod landed on the same node
> That is the whole point of a PersistentVolumeClaim: storage outlives pods. You proved it with `cat /data/log.txt` after the delete/re-apply cycle.

2. Your pod must run on the reserved (tainted) A10 nodes. What does its spec need?
- [ ] Just a nodeSelector for the pool label
- [x] A toleration for the taint *and* a node-affinity rule for the pool label
- [ ] A label on the pod matching the node
> The toleration gets you *permission* to land on tainted nodes; the affinity makes the scheduler actually *prefer* them. Repulsion + attraction — you usually need both.

3. `kubectl get secret … | base64 -d` printed your token in plain text. Is a Secret encrypted?
- [ ] Yes — base64 is a form of encryption
- [x] No — base64 is only an encoding; access is protected by RBAC, not cryptography
- [ ] Only if the cluster admin enables TLS
> Base64 is storage format, not encryption. Anyone who can `get secret` in the namespace can read the value — protect Secrets with RBAC and separate namespaces.

4. You delete one pod of a 4-replica Deployment. What does the cluster do?
- [x] Immediately creates a replacement to get back to 4
- [ ] Runs with 3 replicas until you re-apply the manifest
- [ ] Fails the Deployment
> Kubernetes continuously reconciles actual state toward desired state. The ReplicaSet notices 3 ≠ 4 and spawns a new pod — you watched it happen.

5. Serving `https://hello-<you>.nrp-nautilus.io` took three objects. Which set, doing what?
- [x] Deployment (runs the pods) + Service (stable in-cluster name) + Ingress (routes the public hostname)
- [ ] Pod + ConfigMap + Secret
- [ ] Deployment + PVC + Job
> The Ingress on the `haproxy` class maps the hostname to the Service, which load-balances across the Deployment's pods — and Cert Manager issued the Let's Encrypt certificate without you asking.

6. Your GPU manifest uses `preferredDuringScheduling…` affinity for the reserved pool. Every reserved node is busy — what happens?
- [x] The pod may schedule on another suitable node — *preferred* is a soft hint
- [ ] It pends until a reserved node frees up
- [ ] The scheduler evicts someone else's pod from the pool
> `preferred…` trades placement for availability; the `required…` variant would leave your pod Pending until a matching node frees up. Pick per how strict your hardware needs are.
:::
