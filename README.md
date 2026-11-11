# Inside the National Research Platform

SCinet tutorial · SC26 setup week (the NOC move) · Chicago · November 2026 · 1 hour

For the SCinet volunteers: how NRP is **built** (the network underneath, how a node joins,
storage, ingress), how it's **run** (GitLab and Argo CD, CI in Kata VMs, NetBox fed by LLDP,
Prometheus and Thanos, perfSONAR, security, an LLM ops bot), the **AI service** (Envoy AI
Gateway, InferencePools, vLLM on GPUs at nine sites) and how to **use it**. About 39 minutes of
slides, a 15-minute demo (a terminal, then a small agent in Python), then questions.

[SCinet: the NOC move](https://sc26.supercomputing.org/2026/02/scinet-behind-the-scenes-the-noc-move/)

## Schedule

| # | Page | Time | Covers |
|---|---|---|---|
| 1 | [Presentation](lessons/1_presentation.md) | 39 min | The animated deck, access steps, and where each topic is documented |
| 2 | [Live demo](lessons/2_demo.md) | 15 min | The cluster from kubectl, the LLM gateway with curl, a GPU Job, your own agent |
| — | Questions | 6 min | |

Seven slides are marked optional (about 5 minutes); [deck/README.md](deck/README.md) lists them
in the order to cut, and explains the slide order.

## Layout

- `config.yml`: title, landing-page metadata and page order.
- `lessons/`: the two pages.
- `slides/`: the animated deck (`.html`), the PowerPoint fallback (`.pptx`) and its `.pdf`.
- `workspace/`: the demo notebook (Bash kernel) and the GPU job.
- `deck/`: the slide sources and builders, the cluster snapshot behind the numbers, and the presenter's run sheet ([deck/README.md](deck/README.md)).

## Hands-on requirements

None. The demo runs on the training JupyterHub (`jh-training.nrp-nautilus.io`), where the LLM
token is preset and `kubectl` points at the `nrp-training-k8s` namespace.
