---
title: Hands-On Exercise
teaching: 10
exercises: 0
---

**Time:** 00:00-00:25

In this section we will use what we learned to run a simple jet classifer training job as a hands-on exercise.
We will then look at how we can view the results of this jetr classification job and then we will utilize batch jobs to do training sweeps. 

## Run training and analysis

Run the GPU training job first:

```bash
kubectl delete job -n us-cms jet-class-${USER} --ignore-not-found
kubectl apply -n us-cms -f /tmp/jet-class-${USER}.yaml
kubectl get jobs,pods,pvc -n us-cms
kubectl logs -n us-cms job/jet-class-${USER} -f
```

When training completes, prepare and run the CPU analysis job:

```bash
cp yamls/jet-class-analysis-job.yaml /tmp/jet-class-analysis-${USER}.yaml
sed -i "s/<username>/${USER}/g" /tmp/jet-class-analysis-${USER}.yaml
sed -i "s|<YOUR_IMAGE>|${IMAGE}|g" /tmp/jet-class-analysis-${USER}.yaml

kubectl delete job -n us-cms jet-class-analysis-${USER} --ignore-not-found
kubectl apply -n us-cms -f /tmp/jet-class-analysis-${USER}.yaml
kubectl logs -n us-cms job/jet-class-analysis-${USER} -f
```

Both jobs mount the same PVC. The training job writes artifacts such as the
model, prediction arrays, history, and metadata. The analysis job writes plots
and `metrics.json` into the same run directory.
