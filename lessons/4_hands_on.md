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

`yamls/test-pod.yaml` solves that: a small pod that mounts the same PVC and
just sleeps, so you have something running to copy through.

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

Render it and wait for it to be ready:

```bash
cp yamls/test-pod.yaml /tmp/pvc-browser-${USER}.yaml
perl -pi -e 's/<username>/$ENV{USER}/g' /tmp/pvc-browser-${USER}.yaml
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
