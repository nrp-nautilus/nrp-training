---
title: "Live Demo: NRP from a Terminal"
teaching: 12
exercises: 0
questions:
  - What does the cluster look like from kubectl?
  - What does a call to the LLM gateway look like on the wire?
  - How do I run a job on a GPU?
objectives:
  - Count nodes by region and GPU nodes by model from node labels.
  - Call the gateway with curl, read its rate-limit headers and token counts, and use a task name instead of a model.
  - Submit a GPU Job, watch it go from Pending to Running, read its output and delete it.
keypoints:
  - Topology and hardware are labels on the nodes, so `kubectl get nodes -L` and `-l` answer "where" and "what" questions.
  - The gateway speaks the OpenAI API; the rate limit and the model that answered come back in the response.
  - Task names such as `coding` are priority lists of models on the gateway.
  - A Job states what it needs, runs, and gives the GPU back.
---

**Time:** about 12 minutes, after the [presentation](1_presentation.html).

Everything runs in a notebook on the **Bash** kernel on the training JupyterHub, where `kubectl` already points at the `nrp-training-k8s` namespace and `OPENAI_API_KEY` holds an LLM token.

::: callout Open the notebook
**[▶ Demo: NRP from a terminal](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fscinet-sc26&targetpath=scinet-sc26&urlpath=lab%2Ftree%2Fscinet-sc26%2Fworkspace%2Fnotebooks%2Fdemo.ipynb)**

The link signs you in at jh-training.nrp-nautilus.io, copies this training's files into your server, and opens the notebook.
:::

## 1. The cluster

Topology and hardware are labels on every node. `-L` shows a label as a column, and `-l` keeps only the nodes that have it:

```bash
kubectl get nodes --no-headers | wc -l
kubectl get nodes -L topology.kubernetes.io/region,topology.kubernetes.io/zone | head
kubectl get nodes -L topology.kubernetes.io/region --no-headers | awk '{print $6}' | sort | uniq -c | sort -rn
```

```text
 289 us-west
 105 us-central
 100 us-east
  15 us-mountain
  13 pacific
   5 eu
   5
   4 latin-america
```

The same with `nvidia.com/gpu.product` counts GPU nodes by model:

```bash
kubectl get nodes -l nvidia.com/gpu.product -L nvidia.com/gpu.product --no-headers | awk '{print $6}' | sort | uniq -c | sort -rn | head
```

With admin rights you can also see the services from the talk:

```bash
kubectl get ds agent -n netbox-agent             # the NetBox agent, on 529 nodes
kubectl get ds testpoint -n perfsonar            # the perfSONAR testpoint, on 526
kubectl get ds node-exporter -n monitoring       # node-exporter, on all 536
kubectl get applications -n argo                 # what Argo CD manages
kubectl get aigatewayroutes,inferencepools -n nrp-llm
```

## 2. The LLM gateway

Off the hub, get a token at [nrp.ai/llmtoken](https://nrp.ai/llmtoken) and put it in `OPENAI_API_KEY`. The model names:

```bash
curl -s https://ellm.nrp-nautilus.io/v1/models -H "Authorization: Bearer $OPENAI_API_KEY" | jq -r '.data[].id'
```

Ask a question; `jq` picks out the model that answered, the token counts and the answer:

```bash
curl -s https://ellm.nrp-nautilus.io/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d '{"model": "qwen3", "reasoning_effort": "low",
       "messages": [{"role": "user", "content": "In two sentences: what does a network operations center do?"}]}' \
  | jq '{model, usage, answer: .choices[0].message.content}'
```

The rate limit is in the response headers: 48,000 output tokens a minute, per token and model.

```bash
curl -si https://ellm.nrp-nautilus.io/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d '{"model": "qwen3", "reasoning_effort": "low", "messages": [{"role": "user", "content": "Say hi."}]}' \
  | grep -i ratelimit
```

```text
x-ratelimit-limit: 48000, 48000;w=60
x-ratelimit-remaining: 47998
x-ratelimit-reset: 42
```

Ask for a task instead of a model with `"model": "coding"`, and the gateway tries a list of models in order. In our test, DeepSeek V4.1 Flash, the first on the list, answered. Reasoning models spend tokens thinking, so `"reasoning_effort": "low"` keeps the answers quick.

## 3. A GPU job

`workspace/yamls/gpu-job.yaml` asks for one GPU with more than 20 GB of memory, Ampere or newer, and trains a small network on MNIST. Put your short name in `ME`, then:

```bash
ME=yourname
sed "s/<username>/$ME/" ../yamls/gpu-job.yaml | kubectl apply -f -
kubectl get pods -l job-name=gpu-train-$ME -o wide      # again until it's Running
kubectl logs -f job/gpu-train-$ME
kubectl delete job gpu-train-$ME
```

If it stays in Pending, the events at the end of `kubectl describe pod -l job-name=gpu-train-$ME` say why, usually that no matching GPU is free.

::: callout If you have more time
Look around the operations side in a browser: [argocd.nrp-nautilus.io](https://argocd.nrp-nautilus.io/), [grafana.nrp-nautilus.io](https://grafana.nrp-nautilus.io/), the perfSONAR mesh at [perfsonar.nrp-nautilus.io](https://perfsonar.nrp-nautilus.io/) and the LLM status page at [nrp.ai/llm-status](https://nrp.ai/llm-status/). Some of these need an operator login.
:::
