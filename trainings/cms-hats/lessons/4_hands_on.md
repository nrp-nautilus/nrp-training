---
title: Hands-On Exercise
teaching: 10
exercises: 0
---

::: callout Open the runnable notebook for this episode
**[▶ Open notebook in JupyterHub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats&targetpath=cms-hats&urlpath=lab%2Ftree%2Fcms-hats%2Fworkspace%2Fnotebooks%2F4_hands_on.ipynb)** — every command below is a Shift+Enter cell. Continues from the previous [Hands-On Prep](3_prep.html) episode.
:::

**Time:** 00:00-00:25

In this section we will use what we learned to run a simple jet classifer training job as a hands-on exercise.
We will then look at how we can view the results of this jetr classification job and then we will utilize batch jobs to do training sweeps. 

## Run training and analysis

Run the GPU training job first:

```bash
kubectl delete job -n us-cms jet-class-${USER} --ignore-not-found  # precaution: Jobs are immutable, so clear any stale run from before `apply` fails on a name collision
kubectl apply -n us-cms -f /tmp/jet-class-${USER}.yaml
kubectl get jobs,pods,pvc -n us-cms
kubectl logs -n us-cms job/jet-class-${USER} -f
```

When training completes, run the CPU analysis job — its manifest was already
prepared back in [Hands-On Prep](3_prep.html):

```bash
kubectl delete job -n us-cms jet-class-analysis-${USER} --ignore-not-found  # same precaution as above
kubectl apply -n us-cms -f /tmp/jet-class-analysis-${USER}.yaml
kubectl logs -n us-cms job/jet-class-analysis-${USER} -f
```

Both jobs mount the shared training PVC at `/training` and use
`/training/jet-class` for the jet classifier outputs. The training job writes
artifacts such as the model, prediction arrays, history, and metadata. The
analysis job writes plots and `metrics.json` into the same run directory.

<details>
<summary>Expected output (analysis job log)</summary>

```text
Analyzing run: single
Accuracy: 0.7690
Analysis complete. Wrote artifacts:
  - /training/jet-class/run-single/confusion_matrix.png
  - /training/jet-class/run-single/feature_data.npz
  - /training/jet-class/run-single/feature_distributions.png
  - /training/jet-class/run-single/history.json
  - /training/jet-class/run-single/jet_classifier.keras
  - /training/jet-class/run-single/metadata.json
  - /training/jet-class/run-single/metrics.json
  - /training/jet-class/run-single/predictions.npz
  - /training/jet-class/run-single/roc_curve.png
  - /training/jet-class/run-single/training_history.png
stream closed EOF for us-cms/jet-class-analysis-ddiaz-kxgf8 (jet-class-analysis)
```
</details>

## Copy your results locally

Everything above lives in the PVC, not on your machine. `kubectl cp` copies
files out of a pod — but the training and analysis Jobs' pods are done
running by now, and `kubectl cp` needs a *live* container to copy through, so
those pods no longer work as a source.

`yamls/test-pod.yaml`, already prepared as `/tmp/pvc-browser-${USER}.yaml`
back in [Hands-On Prep](3_prep.html#6-prepare-the-pvc-browser-pod), solves
that: a small pod that mounts the same PVC and just sleeps, so you have
something running to copy through.

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

Apply it and wait for it to be ready:

```bash
kubectl apply -n us-cms -f /tmp/pvc-browser-${USER}.yaml
kubectl wait --for=condition=Ready pod/test-pod-${USER}-pvc -n us-cms --timeout=60s
```

Copy the run directory down, then clean up the browser pod — it has no other
purpose once you're done:

```bash
kubectl cp us-cms/test-pod-${USER}-pvc:/training/jet-class/run-single ./jet-class-results-${USER}
kubectl delete pod -n us-cms test-pod-${USER}-pvc
```

You should now have `jet_classifier.keras`, the metrics/history JSON files,
and the PNG plots (`confusion_matrix.png`, `roc_curve.png`,
`training_history.png`, `feature_distributions.png`) sitting in
`./jet-class-results-${USER}` on your own machine.

## Extension: hyperparameter sweep (optional)

The run above uses one fixed model size. This extension runs the *same*
training script four times in parallel — as one Kubernetes
[Indexed Job](https://kubernetes.io/docs/tasks/job/indexed-parallel-processing-static/)
— at four different model sizes, then compares accuracy against how much GPU
work each size actually took. It's a better demonstration of GPU utilization
than the single run above: instead of one job finishing quickly, you get
multiple GPUs training in parallel and a direct look at the accuracy/compute
tradeoff.

::: important
This extension records each run's wall-clock training time in
`metadata.json`/`metrics.json`. The prebuilt
`ghcr.io/ddiaz006/cms-hats-jet-class:0.2` image already includes this. If
you built your own image earlier (before this note was added), rebuild and
push it again (see [step 4 of Hands-On Prep](3_prep.html#4-the-container-image))
to pick up the change. Without it, the sweep still runs and still compares
accuracy vs. model size — it just skips the accuracy-vs-time plot.
:::

All three manifests below were already prepared as `/tmp/jet-class-sweep-${USER}.yaml`,
`/tmp/jet-class-sweep-analysis-${USER}.yaml`, and
`/tmp/jet-class-sweep-compare-${USER}.yaml` back in [Hands-On
Prep](3_prep.html#7-prepare-the-sweep-manifests-optional) — shown here for
reference.

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

### Run the sweep

```bash
kubectl delete job -n us-cms jet-class-sweep-${USER} --ignore-not-found  # precaution: Jobs are immutable
kubectl apply -n us-cms -f /tmp/jet-class-sweep-${USER}.yaml
kubectl get jobs,pods -n us-cms
```

```bash
kubectl wait -n us-cms --for=condition=Complete job/jet-class-sweep-${USER} --timeout=30m
```

Then the per-run analysis, then the comparison:

```bash
kubectl delete job -n us-cms jet-class-sweep-analysis-${USER} --ignore-not-found
kubectl apply -n us-cms -f /tmp/jet-class-sweep-analysis-${USER}.yaml
kubectl wait -n us-cms --for=condition=Complete job/jet-class-sweep-analysis-${USER} --timeout=10m

kubectl delete job -n us-cms jet-class-sweep-compare-${USER} --ignore-not-found
kubectl apply -n us-cms -f /tmp/jet-class-sweep-compare-${USER}.yaml
kubectl wait -n us-cms --for=condition=Complete job/jet-class-sweep-compare-${USER} --timeout=5m
kubectl logs -n us-cms job/jet-class-sweep-compare-${USER}
```

The logged table shows model size, parameter count, training time (if
available), and accuracy side by side for all four runs.

If you set `MLFLOW_TRACKING_URI` (see [MLflow tracking](3_prep.html#mlflow-tracking)
in Hands-On Prep), all four sweep runs land in the
`jet-classifier-sweep-<your username>` experiment. Open the [MLflow
UI](https://us-cms-mlflow.nrp-nautilus.io) and use its built-in **Compare
Runs** view for the same accuracy-vs-model-size comparison the
`sweep_comparison.png` plot above gives you, but interactively — sortable by
any logged param or metric, no `kubectl cp` needed.

### Copy the comparison plots locally

Reuses the same PVC-browser pod (and the `/tmp/pvc-browser-${USER}.yaml`
prepared back in [Hands-On Prep](3_prep.html#6-prepare-the-pvc-browser-pod))
as the single-run copy step above — if `test-pod-${USER}-pvc` isn't still
running, recreate it from the same file:

```bash
kubectl get pod -n us-cms test-pod-${USER}-pvc || \
  (kubectl apply -n us-cms -f /tmp/pvc-browser-${USER}.yaml && \
   kubectl wait --for=condition=Ready pod/test-pod-${USER}-pvc -n us-cms --timeout=60s)
```

```bash
kubectl cp us-cms/test-pod-${USER}-pvc:/training/jet-class/sweep_comparison.png ./sweep_comparison-${USER}.png
kubectl cp us-cms/test-pod-${USER}-pvc:/training/jet-class/sweep_time_comparison.png ./sweep_time_comparison-${USER}.png 2>/dev/null || true
kubectl delete pod -n us-cms test-pod-${USER}-pvc
```

The second `kubectl cp` is expected to fail (and is ignored) if you're on the
prebuilt image without `training_seconds` — you'll still have
`sweep_comparison.png`.

### Clean up

```bash
kubectl delete job -n us-cms jet-class-sweep-${USER} jet-class-sweep-analysis-${USER} jet-class-sweep-compare-${USER} --ignore-not-found
```
