---
title: Hands-On Prep
teaching: 10
exercises: 0
---

::: callout Open the runnable notebook for this episode
**[▶ Open notebook in JupyterHub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats&targetpath=cms-hats&urlpath=lab%2Ftree%2Fcms-hats%2Fworkspace%2Fnotebooks%2F3_prep.ipynb)** — every command below is a Shift+Enter cell. If you're on the Analysis Hub, `nbgitpuller` already cloned the repo for you — skip straight to [Step 2](#2-set-your-username).
:::

**Time:** 00:00-00:25

In this section we will prepare to run the hands-on exercise: training and
evaluating a **jet classifier** on NRP GPUs.

## What you're building: a jet classifier

At the LHC, quarks and gluons produced in a collision don't fly out as free
particles — they fragment and hadronize into a collimated spray of particles
called a **jet**. Different progenitors leave different fingerprints on that
spray: gluon and light-quark jets are mostly unstructured, while jets seeded
by a boosted **W**, **Z**, or top quark carry visible substructure (at least
one "prong") from the heavier particle's decay products landing inside a
single jet. Telling these apart — **jet tagging** — is a standard part of
many LHC analyses, e.g. finding boosted W/Z bosons or top quarks in
high-energy events.

This exercise trains a classifier to do exactly that, using the
[`hls4ml_lhc_jets_hlf`](https://www.openml.org/search?type=data&id=42468)
dataset: roughly 830,000 simulated jets, each labeled as one of five classes
— gluon (**g**), light quark (**q**), **W**, **Z**, or top quark (**t**) —
and described by 16 high-level features (energy correlation functions, jet
mass, particle multiplicity, and related substructure variables) rather than
raw detector images. That keeps the input small enough to train a plain
fully-connected neural network directly on tabular data — no convolutions,
no jet images.

`jet_class.py` scales the network up from a teaching-sized 64→32→32 model to
`4096→4096→2048→1024` and trains with mixed precision on a GPU, so you'll see
a real (if short) GPU training job rather than a CPU toy. **This scale-up has
no scientific motivation** — the teaching-sized model already classifies
these jets just fine; it's sized deliberately larger purely to turn a CPU-fast
toy example into something that actually exercises a GPU. `analyze_jet_class.py`
then evaluates the trained model: accuracy, a confusion matrix, ROC curves,
and feature-distribution plots.

This material is adapted from [Javier Duarte's PHYS 139/239 course at
UCSD](https://jduarte.physics.ucsd.edu/phys139_239/03_Tabular_Data_NN.html),
which covers the same exercise — and its extensions, like regularization,
learning rate, and optimizer choice — in much more depth if you want to go
further.

## 1. Clone the training materials

**Skip this step on the NRP USCMS Analysis Hub** — the launch link above
already clones the repo into your home directory. This step is only for
Method 2 (your own machine).

Clone the branch containing the files for this training:

```bash
git clone --branch materials/cms-hats --single-branch https://github.com/nrp-nautilus/nrp-training.git ~/cms-hats
cd ~/cms-hats/workspace
```

If you already cloned the training materials, update your local copy instead:

```bash
cd ~/cms-hats
git pull
cd workspace
```

---

## 2. Set your username

Set a short username once and use the same value for each command in this
training. This keeps your Kubernetes object names separate from everyone else's.

```bash
export USER=<username>
cd ~/cms-hats/workspace
```

---

## 3. Create a shared PVC for the training

The hands-on jobs write their outputs to one persistent volume claim (PVC) for
the whole training. You only need to create this PVC once. If you need more
space later, the storage request can be increased, but it cannot be decreased.
The jet classifier examples write under `/training/jet-class`.

This uses `rook-cephfs` (CephFS) rather than the more commonly-seen
`rook-ceph-block` (RBD), and requests `ReadWriteMany` rather than
`ReadWriteOnce`. That's deliberate, not a typo: the [hyperparameter sweep
extension](4_hands_on.html#extension-hyperparameter-sweep-optional) in the
next lesson runs multiple training pods against this same PVC at once, and
block storage only allows one pod to attach a `ReadWriteOnce` volume at a
time — a second pod trying to attach it fails with a `Multi-Attach error`.
CephFS supports multiple pods reading and writing concurrently, and works
identically to RBD for the single-pod case too, so there's no downside to
using it everywhere.

One catch: this cluster's CSI drivers report `fsGroupPolicy:
ReadWriteOnceWithFSType`, meaning Kubernetes only auto-`chown`s a volume to
match the pod's `fsGroup` for `ReadWriteOnce` volumes — it skips that step
entirely for `ReadWriteMany` ones like this PVC. Without it, the training
container (running as a non-root user) can't write to a freshly-provisioned
CephFS volume at all. Every Job manifest that mounts this PVC — training,
analysis, and the sweep variants — works around this with a small
`fix-permissions` init container that `chown`s the mount before the main
container starts; you'll see it at the top of each manifest below.

`yamls/pvc.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cms-nrp-hats-<username>
  namespace: us-cms
spec:
  storageClassName: rook-cephfs
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 5Gi
```

Make a temporary copy of the PVC manifest and replace the username placeholder:

```bash
cp yamls/pvc.yaml /tmp/cms-nrp-hats-pvc-${USER}.yaml
perl -pi -e 's/<username>/$ENV{USER}/g' /tmp/cms-nrp-hats-pvc-${USER}.yaml
```

Apply the PVC manifest:

```bash
kubectl apply -n us-cms -f /tmp/cms-nrp-hats-pvc-${USER}.yaml
```

Verify that the PVC exists:

```bash
kubectl get pvc -n us-cms cms-nrp-hats-${USER}
```

---

## 4. The Container Image

The training job runs a container image. Kubernetes cannot use a local unnamed
Docker image, so the image needs a registry name that the cluster can pull.

You can use the prepare image 
```bash
export IMAGE=ghcr.io/ddiaz006/cms-hats-jet-class:0.2
```

Or, you can build your own. 
<details>
  <summary>Click to reveal docker instructions</summary>

Use a name like:

```text
ghcr.io/<github-user-or-org>/cms-hats-jet-class:0.2
```

From the `workspace/` directory, set the image name:

```bash
export IMAGE=ghcr.io/<github-user-or-org>/cms-hats-jet-class:0.2
```

For most Linux/Intel systems:

```bash
docker build -f code/Dockerfile.jet-class -t "$IMAGE" .
docker push "$IMAGE"
```

For Apple Silicon Macs, build the Linux AMD64 image that the cluster will run:

```bash
docker build --platform linux/amd64 -f code/Dockerfile.jet-class -t "$IMAGE" .
docker push "$IMAGE"
```
</details>


If the image is hosted on GHCR, make sure the package is public or the cluster
will not be able to pull it. A private image usually shows up as
`ImagePullBackOff` with a `401 Unauthorized` message.

You can test that the image is anonymously pullable by logging out and pulling
it:

```bash
docker logout ghcr.io
docker pull "$IMAGE"
```
---


## 5. Prepare the YAML

Set the image name. Use the same `USER` value from the previous step so your Job
uses the shared PVC you created above.

```bash
export IMAGE=ghcr.io/<github-user-or-org>/cms-hats-jet-class:0.2
cd ~/cms-hats/workspace
```

<details>
<summary><code>yamls/jet-class-job.yaml</code></summary>

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: jet-class-<username>
  namespace: us-cms
spec:
  template:
    spec:
      restartPolicy: Never
      securityContext:
        runAsUser: 1000
        runAsGroup: 100
        fsGroup: 100
        fsGroupChangePolicy: OnRootMismatch
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
      initContainers:
      - name: fix-permissions
        image: busybox:1.36
        command: ["sh", "-c", "chown -R 1000:100 /training"]
        securityContext:
          runAsUser: 0
          runAsGroup: 0
        resources:
          requests:
            cpu: 10m
            memory: 32Mi
          limits:
            cpu: 100m
            memory: 64Mi
        volumeMounts:
        - name: training-storage
          mountPath: /training
      containers:
      - name: jet-class
        image: <YOUR_IMAGE>
        env:
        - name: RUN_ID
          value: single
        - name: OUTPUT_DIR
          value: /training/jet-class
        - name: EPOCHS
          value: "50"
        - name: BATCH_SIZE
          value: "8192"
        - name: MODEL_WIDTHS
          value: "4096,4096,2048,1024"
        - name: MIXED_PRECISION
          value: "1"
        - name: MLFLOW_TRACKING_URI
          value: http://mlflow.us-cms-af.svc.cluster.local:5000
        - name: MLFLOW_EXPERIMENT_NAME
          value: jet-classifier-<username>
        resources:
          requests:
            cpu: "4"
            memory: 8Gi
            nvidia.com/gpu: 1
          limits:
            cpu: "4"
            memory: 8Gi
            nvidia.com/gpu: 1
        volumeMounts:
        - name: training-storage
          mountPath: /training

      volumes:
      - name: training-storage
        persistentVolumeClaim:
          claimName: cms-nrp-hats-<username>
```

</details>

### MLflow tracking

The training and analysis scripts log to the shared
[MLflow](https://us-cms-mlflow.nrp-nautilus.io) instance running in the
cluster — the Job manifest above points at its **in-cluster** address
(`http://mlflow.us-cms-af.svc.cluster.local:5000`), which reaches the
tracking server directly and skips the SSO login the external URL requires.
Params (model widths, batch size, learning rate, ...), per-epoch loss and
accuracy, final test accuracy, and the analysis plots all show up under an
experiment named `jet-classifier-<your username>`, so runs from different
people in the training don't mix together. Open the [MLflow
UI](https://us-cms-mlflow.nrp-nautilus.io) (this one does need your SSO
login) in a browser to see them.

This is entirely best-effort: if `MLFLOW_TRACKING_URI` is unset or the
server is unreachable, both scripts print a warning and keep going — a
flaky or down MLflow instance never fails the actual exercise.

### Training parameters

`jet_class.py` reads all of these from environment variables. The Job manifest
above sets the ones that matter most for GPU utilization explicitly; the rest
fall back to the script's defaults. The full ~830,000-jet dataset is always
loaded in every run — there's no sampling or truncation, so "run on the full
dataset" isn't a separate mode to switch on.

| Variable | Default | Description |
| --- | --- | --- |
| `DATASET` | `hls4ml_lhc_jets_hlf` | OpenML dataset name. Always fetched in full — no row limit. |
| `EPOCHS` | `50` | Passes over the full training split. |
| `BATCH_SIZE` | `8192` | Rows per gradient step. Larger batches mean fewer, bigger matmuls per epoch. |
| `LEARNING_RATE` | `0.001` | Adam optimizer step size. |
| `MODEL_WIDTHS` | `4096,4096,2048,1024` | Comma-separated hidden layer sizes for the dense classifier — the main lever on model size (and GPU work per step). |
| `MIXED_PRECISION` | `1` | Trains in `mixed_float16` when truthy; set to `0` to force full `float32`. |
| `SEED` | `42` | Base random seed; offset by `RUN_ID` when `RUN_ID` is numeric (used for multi-run sweeps). |
| `TEST_FRACTION` | `0.2` | Fraction of jets held out as the test split. |
| `VALIDATION_FRACTION` | `0.25` | Fraction of the remaining train+val jets held out for validation. |
| `SAVE_FEATURE_DATA` | `1` | Also writes the raw feature/label arrays to `feature_data.npz`, used by the analysis job's feature-distribution plot. |
| `MLFLOW_TRACKING_URI` | unset (disabled) | MLflow tracking server URL. Unset or unreachable disables tracking entirely — training still runs and writes local outputs either way. |
| `MLFLOW_EXPERIMENT_NAME` | `jet-classifier` | MLflow experiment name runs are grouped under. |
| `RUN_ID` | `single` (falls back to `JOB_COMPLETION_INDEX`) | Names the run's output subdirectory (`run-<RUN_ID>`) and offsets `SEED` when numeric. |
| `OUTPUT_DIR` | `/training/jet-class` | Where run directories are written on the shared PVC. |

Make a temporary copy of the training manifest and replace the placeholders:

```bash
cp yamls/jet-class-job.yaml /tmp/jet-class-${USER}.yaml
perl -pi -e 's/<username>/$ENV{USER}/g; s|<YOUR_IMAGE>|$ENV{IMAGE}|g' /tmp/jet-class-${USER}.yaml
```

The manifest creates the GPU training Job, mounts the shared PVC at
`/training`, and writes jet classifier outputs under `/training/jet-class`.

Do the same for the CPU analysis manifest you'll use once training finishes —
preparing both now, while `$USER` and `$IMAGE` are set, means the next
episode is just `kubectl apply`:

<details>
<summary><code>yamls/jet-class-analysis-job.yaml</code></summary>

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: jet-class-analysis-<username>
  namespace: us-cms
spec:
  template:
    spec:
      restartPolicy: Never
      securityContext:
        runAsUser: 1000
        runAsGroup: 100
        fsGroup: 100
        fsGroupChangePolicy: OnRootMismatch
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
      initContainers:
      - name: fix-permissions
        image: busybox:1.36
        command: ["sh", "-c", "chown -R 1000:100 /training"]
        securityContext:
          runAsUser: 0
          runAsGroup: 0
        resources:
          requests:
            cpu: 10m
            memory: 32Mi
          limits:
            cpu: 100m
            memory: 64Mi
        volumeMounts:
        - name: training-storage
          mountPath: /training
      containers:
      - name: jet-class-analysis
        image: <YOUR_IMAGE>
        command: ["python", "/workspace/analyze_jet_class.py"]
        env:
        - name: RUN_ID
          value: single
        - name: OUTPUT_DIR
          value: /training/jet-class
        resources:
          requests:
            cpu: "2"
            memory: 4Gi
          limits:
            cpu: "2"
            memory: 4Gi
        volumeMounts:
        - name: training-storage
          mountPath: /training

      volumes:
      - name: training-storage
        persistentVolumeClaim:
          claimName: cms-nrp-hats-<username>
```

</details>

```bash
cp yamls/jet-class-analysis-job.yaml /tmp/jet-class-analysis-${USER}.yaml
perl -pi -e 's/<username>/$ENV{USER}/g; s|<YOUR_IMAGE>|$ENV{IMAGE}|g' /tmp/jet-class-analysis-${USER}.yaml
```

---

## 6. Prepare the PVC browser pod

The training and analysis Jobs' pods stop running once they finish, but
`kubectl cp` (used in the next lesson to copy your results locally) needs a
*live* container to copy through. `yamls/test-pod.yaml` is a small pod that
mounts the same PVC and just sleeps, so you have something running to copy
through whenever you need it — for the single run's results, and later for
the sweep extension's comparison plots.

<details>
<summary><code>yamls/test-pod.yaml</code></summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod-<username>-pvc
spec:
  containers:
  - name: mypod
    image: gitlab-registry.nrp-nautilus.io/prp/gsutil:latest
    command: ["sh", "-c", "sleep infinity"]
    resources:
      limits:
        memory: 4Gi
        cpu: 1
      requests:
        memory: 4Gi
        cpu: 1
    volumeMounts:
    - mountPath: /training
      name: data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: cms-nrp-hats-<username>
```

</details>

```bash
cp yamls/test-pod.yaml /tmp/pvc-browser-${USER}.yaml
perl -pi -e 's/<username>/$ENV{USER}/g' /tmp/pvc-browser-${USER}.yaml
```

---

## 7. Prepare the sweep manifests (optional)

Only needed if you plan to do the [hyperparameter sweep
extension](4_hands_on.html#extension-hyperparameter-sweep-optional) in the
next lesson — skip to [Hands-On Exercise](4_hands_on.html) if not.

The sweep runs the same training script four times in parallel, as one
Kubernetes [Indexed
Job](https://kubernetes.io/docs/tasks/job/indexed-parallel-processing-static/),
at four different model sizes, then compares accuracy against how much GPU
work each size actually took.

::: important
This extension records each run's wall-clock training time in
`metadata.json`/`metrics.json`. The prebuilt
`ghcr.io/ddiaz006/cms-hats-jet-class:0.2` image already includes this. If
you built your own image earlier (before this note was added), rebuild and
push it again (see [step 4](#4-the-container-image) above) to pick up the
change. Without it, the sweep still runs and still compares accuracy vs.
model size — it just skips the accuracy-vs-time plot.
:::

`yamls/jet-class-sweep-job.yaml`. `completions: 4` runs indices `0`-`3`, one
per model size; `parallelism: 2` caps it at two GPUs in use at once — raise
or lower that to match how many GPUs your namespace can actually claim at
the same time. Kubernetes sets `JOB_COMPLETION_INDEX` in each pod
automatically; the script picks a `MODEL_WIDTHS` value based on it and
otherwise runs exactly like the single-run Job:

<details>
<summary><code>yamls/jet-class-sweep-job.yaml</code></summary>

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: jet-class-sweep-<username>
  namespace: us-cms
spec:
  completions: 4
  parallelism: 2
  completionMode: Indexed
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      securityContext:
        runAsUser: 1000
        runAsGroup: 100
        fsGroup: 100
        fsGroupChangePolicy: OnRootMismatch
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
      initContainers:
      - name: fix-permissions
        image: busybox:1.36
        command: ["sh", "-c", "chown -R 1000:100 /training"]
        securityContext:
          runAsUser: 0
          runAsGroup: 0
        resources:
          requests:
            cpu: 10m
            memory: 32Mi
          limits:
            cpu: 100m
            memory: 64Mi
        volumeMounts:
        - name: training-storage
          mountPath: /training
      containers:
      - name: jet-class-sweep
        image: <YOUR_IMAGE>
        command: ["bash", "-c"]
        args:
        - |
          WIDTHS=("512,256" "1024,1024,512" "2048,2048,1024,512" "4096,4096,2048,1024")
          export MODEL_WIDTHS="${WIDTHS[$JOB_COMPLETION_INDEX]}"
          echo "Sweep index $JOB_COMPLETION_INDEX -> MODEL_WIDTHS=$MODEL_WIDTHS"
          exec python /workspace/jet_class.py
        env:
        - name: EPOCHS
          value: "50"
        - name: BATCH_SIZE
          value: "8192"
        - name: MIXED_PRECISION
          value: "1"
        - name: MLFLOW_TRACKING_URI
          value: http://mlflow.us-cms-af.svc.cluster.local:5000
        - name: MLFLOW_EXPERIMENT_NAME
          value: jet-classifier-sweep-<username>
        resources:
          requests:
            cpu: "4"
            memory: 8Gi
            nvidia.com/gpu: 1
          limits:
            cpu: "4"
            memory: 8Gi
            nvidia.com/gpu: 1
        volumeMounts:
        - name: training-storage
          mountPath: /training

      volumes:
      - name: training-storage
        persistentVolumeClaim:
          claimName: cms-nrp-hats-<username>
```

</details>

`yamls/jet-class-sweep-analysis-job.yaml` — same Indexed Job pattern, but
CPU-only and reusing `analyze_jet_class.py` completely unmodified: it already
falls back to `JOB_COMPLETION_INDEX` for `RUN_ID`, so each of the 4 pods
analyzes its own run:

<details>
<summary><code>yamls/jet-class-sweep-analysis-job.yaml</code></summary>

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: jet-class-sweep-analysis-<username>
  namespace: us-cms
spec:
  completions: 4
  parallelism: 4
  completionMode: Indexed
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      securityContext:
        runAsUser: 1000
        runAsGroup: 100
        fsGroup: 100
        fsGroupChangePolicy: OnRootMismatch
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
      initContainers:
      - name: fix-permissions
        image: busybox:1.36
        command: ["sh", "-c", "chown -R 1000:100 /training"]
        securityContext:
          runAsUser: 0
          runAsGroup: 0
        resources:
          requests:
            cpu: 10m
            memory: 32Mi
          limits:
            cpu: 100m
            memory: 64Mi
        volumeMounts:
        - name: training-storage
          mountPath: /training
      containers:
      - name: jet-class-sweep-analysis
        image: <YOUR_IMAGE>
        command: ["python", "/workspace/analyze_jet_class.py"]
        resources:
          requests:
            cpu: "2"
            memory: 4Gi
          limits:
            cpu: "2"
            memory: 4Gi
        volumeMounts:
        - name: training-storage
          mountPath: /training

      volumes:
      - name: training-storage
        persistentVolumeClaim:
          claimName: cms-nrp-hats-<username>
```

</details>

`yamls/jet-class-sweep-compare-job.yaml` — a single CPU job that reads all
four `metrics.json` files and plots accuracy against model size (and against
training time, if available):

<details>
<summary><code>yamls/jet-class-sweep-compare-job.yaml</code></summary>

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: jet-class-sweep-compare-<username>
  namespace: us-cms
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      securityContext:
        runAsUser: 1000
        runAsGroup: 100
        fsGroup: 100
        fsGroupChangePolicy: OnRootMismatch
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
      initContainers:
      - name: fix-permissions
        image: busybox:1.36
        command: ["sh", "-c", "chown -R 1000:100 /training"]
        securityContext:
          runAsUser: 0
          runAsGroup: 0
        resources:
          requests:
            cpu: 10m
            memory: 32Mi
          limits:
            cpu: 100m
            memory: 64Mi
        volumeMounts:
        - name: training-storage
          mountPath: /training
      containers:
      - name: jet-class-sweep-compare
        image: <YOUR_IMAGE>
        command: ["python", "-c"]
        args:
        - |
          import glob
          import json

          import matplotlib
          matplotlib.use("Agg")
          import matplotlib.pyplot as plt

          rows = []
          for path in sorted(glob.glob("/training/jet-class/run-*/metrics.json")):
              m = json.load(open(path))
              if not m["run_id"].isdigit():
                  continue
              rows.append(m)
          rows.sort(key=lambda m: int(m["run_id"]))

          if not rows:
              raise SystemExit("No sweep runs found under /training/jet-class/run-<index>/metrics.json")

          print(f"{'run':>4}  {'widths':<28} {'params':>10}  {'seconds':>8}  accuracy")
          for m in rows:
              secs = m.get("training_seconds")
              secs_str = f"{secs:.1f}" if secs is not None else "n/a"
              print(f"{m['run_id']:>4}  {','.join(str(w) for w in m['model_widths']):<28} "
                    f"{m['model_parameters']:>10,}  {secs_str:>8}  {m['accuracy']:.4f}")

          fig, ax = plt.subplots(figsize=(7, 5))
          ax.plot([m["model_parameters"] for m in rows], [m["accuracy"] for m in rows], "o-")
          ax.set_xscale("log")
          ax.set_xlabel("Model parameters")
          ax.set_ylabel("Test accuracy")
          ax.set_title("Jet classifier sweep: accuracy vs model size")
          for m in rows:
              ax.annotate(f"run {m['run_id']}", (m["model_parameters"], m["accuracy"]))
          fig.tight_layout()
          fig.savefig("/training/jet-class/sweep_comparison.png", dpi=150)
          print("Wrote /training/jet-class/sweep_comparison.png")

          if all(m.get("training_seconds") is not None for m in rows):
              fig, ax = plt.subplots(figsize=(7, 5))
              ax.plot([m["training_seconds"] for m in rows], [m["accuracy"] for m in rows], "o-")
              ax.set_xlabel("Training time [s]")
              ax.set_ylabel("Test accuracy")
              ax.set_title("Jet classifier sweep: accuracy vs training time")
              for m in rows:
                  ax.annotate(f"run {m['run_id']}", (m["training_seconds"], m["accuracy"]))
              fig.tight_layout()
              fig.savefig("/training/jet-class/sweep_time_comparison.png", dpi=150)
              print("Wrote /training/jet-class/sweep_time_comparison.png")
          else:
              print("Skipping accuracy-vs-time plot: some runs are missing training_seconds "
                    "(rebuild your image from the current jet_class.py to get it)")
        resources:
          requests:
            cpu: "1"
            memory: 2Gi
          limits:
            cpu: "1"
            memory: 2Gi
        volumeMounts:
        - name: training-storage
          mountPath: /training

      volumes:
      - name: training-storage
        persistentVolumeClaim:
          claimName: cms-nrp-hats-<username>
```

</details>

Template all three:

```bash
cp yamls/jet-class-sweep-job.yaml /tmp/jet-class-sweep-${USER}.yaml
cp yamls/jet-class-sweep-analysis-job.yaml /tmp/jet-class-sweep-analysis-${USER}.yaml
cp yamls/jet-class-sweep-compare-job.yaml /tmp/jet-class-sweep-compare-${USER}.yaml
perl -pi -e 's/<username>/$ENV{USER}/g; s|<YOUR_IMAGE>|$ENV{IMAGE}|g' \
  /tmp/jet-class-sweep-${USER}.yaml \
  /tmp/jet-class-sweep-analysis-${USER}.yaml \
  /tmp/jet-class-sweep-compare-${USER}.yaml
```

All manifests needed for the next lesson — required and optional — are now
ready in `/tmp`.
