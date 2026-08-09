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
kubectl delete job -n us-cms jet-class-${USER} --ignore-not-found
kubectl apply -n us-cms -f /tmp/jet-class-${USER}.yaml
kubectl get jobs,pods,pvc -n us-cms
kubectl logs -n us-cms job/jet-class-${USER} -f
```

When training completes, prepare and run the CPU analysis job:

```bash
cp yamls/jet-class-analysis-job.yaml /tmp/jet-class-analysis-${USER}.yaml
perl -pi -e 's/<username>/$ENV{USER}/g; s|<YOUR_IMAGE>|$ENV{IMAGE}|g' /tmp/jet-class-analysis-${USER}.yaml

kubectl delete job -n us-cms jet-class-analysis-${USER} --ignore-not-found
kubectl apply -n us-cms -f /tmp/jet-class-analysis-${USER}.yaml
kubectl logs -n us-cms job/jet-class-analysis-${USER} -f
```

Both jobs mount the shared training PVC at `/training` and use
`/training/jet-class` for the jet classifier outputs. The training job writes
artifacts such as the model, prediction arrays, history, and metadata. The
analysis job writes plots and `metrics.json` into the same run directory.
