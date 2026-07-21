---
title: Persistent Storage & I/O for AI/Scientific Workloads
teaching: 15
exercises: 15
---

::: callout Launch the workspace in JupyterHub
**[▶ Open the runnable notebook for this episode](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fpearc26&targetpath=pearc26&urlpath=lab%2Ftree%2Fpearc26%2Fworkspace%2Fnotebooks%2F4_storage.ipynb)** — every command below is a Shift+Enter cell; manifests are in the workspace's `yamls/` folder.
:::

**Afternoon session · 12:15 – 12:45 PM**

AI and scientific workloads live or die on I/O: where the dataset sits, how fast checkpoints write, and whether ten students can read the same files at once. This episode maps NRP's storage options to those needs and gets hands-on with each from a notebook terminal.

> 📘 **Docs:** [Storage intro](https://nrp.ai/documentation/userdocs/storage/intro/) · [Ceph](https://nrp.ai/documentation/userdocs/storage/ceph/) · [S3](https://nrp.ai/documentation/userdocs/storage/ceph-s3/) · [Policies](https://nrp.ai/documentation/userdocs/start/policies/)

## Storage options on NRP

| Option | Access mode | Best for | Caveats |
|---|---|---|---|
| **Pod filesystem** | per-container | scratch during a single run | gone when the pod dies |
| **`emptyDir`** | per-pod, shared by its containers | fast scratch, staging downloads | gone when the pod dies; counts against ephemeral-storage |
| **RBD block (`rook-ceph-block-*`)** | `ReadWriteOnce` | home dirs, checkpoints, databases | one pod at a time |
| **CephFS (`rook-cephfs-*`)** | `ReadWriteMany` | shared datasets, course materials, multi-pod pipelines | slightly slower metadata than block |
| **S3 (Ceph RGW)** | HTTP, from anywhere | dataset distribution, results publishing, cross-site access | object semantics, not POSIX |

Your JupyterHub home directory (`/home/jovyan`) is itself an RBD PVC — everything you save in the notebook survives server restarts, but it is sized in gigabytes; keep bulk data on CephFS or S3.

### Choosing an access mode

- **`ReadWriteOnce` (RWO)** — one node mounts read-write. Block storage. You saw the consequence in Episode 2: the sidecar exercise had to delete the first pod before the second could mount.
- **`ReadWriteMany` (RWX)** — many pods on many nodes mount simultaneously. CephFS. This is what a classroom shared folder or a multi-worker training job wants.

## Hands-on: an RWX CephFS volume shared by many pods

`yamls/shared-pvc.yaml` creates a CephFS-backed PVC. Apply it and note the `RWX` access mode:

```bash
kubectl apply -n nrp-training-k8s -f yamls/shared-pvc.yaml
kubectl get pvc -n nrp-training-k8s | grep shared
```

<details>
<summary>Expected output</summary>

```text
jupyterhub-shared-volume   Bound    pvc-…   5Gi   RWX   rook-cephfs   30s
```
</details>

Unlike the Episode 2 PVC, **many pods can mount this claim at the same time** — in the final episode this exact volume becomes the `/home/shared` folder every student sees in a course JupyterHub.

## Hands-on: S3 object storage

NRP runs S3-compatible object storage on Ceph. It's the right tool when data must be reachable from outside the cluster, shared across sites, or published alongside a paper. Any S3 client works — `aws` CLI, `boto3`, `s3fs`, rclone.

`yamls/pod-awscli.yaml` starts a pod with the AWS CLI image, a 100 Gi `emptyDir` scratch volume at `/scratch`, and installs `boto3` + `torch` on boot. It also pulls the shared tutorial S3 credentials in from a Secret (`nrp-tutorial-s3`) as environment variables — so inside the pod both `aws` and `boto3` authenticate automatically, no `aws configure` step. Replace `<username>` and apply:

```bash
kubectl apply -n nrp-training-k8s -f yamls/pod-awscli.yaml
kubectl get pod tutorial-<username>-pod -n nrp-training-k8s -w
```

Wait for the install loop to log `Done with installs`, then exec in and talk to S3:

```bash
kubectl exec -it tutorial-<username>-pod -n nrp-training-k8s -- bash

# inside the pod — the tutorial key is already in the environment
# ($AWS_ACCESS_KEY_ID / $AWS_SECRET_ACCESS_KEY / $AWS_ENDPOINT_URL / $S3_BUCKET):
aws --endpoint $AWS_ENDPOINT_URL s3 ls
aws --endpoint $AWS_ENDPOINT_URL s3 ls s3://$S3_BUCKET/

# stage the shared dataset onto the fast local scratch:
aws --endpoint $AWS_ENDPOINT_URL s3 cp s3://$S3_BUCKET/dataset.tar.gz /scratch/
tar xzf /scratch/dataset.tar.gz -C /scratch     # 30 sample images + labels.csv + shards

# publish your own results back — write under your username so you don't
# clobber the shared dataset (everyone shares one bucket in this tutorial):
echo "hello from <username>" > /scratch/result.txt
aws --endpoint $AWS_ENDPOINT_URL s3 cp /scratch/result.txt s3://$S3_BUCKET/<username>/result.txt
```

> On your own laptop (outside this pod) you'd first run `aws configure` and paste
> an access key / secret from [nrp.ai/s3token](https://nrp.ai/s3token), then use the
> same `--endpoint` commands. Request your own S3 credentials via the User Portal.

The same works from Python with `boto3` — it reads the same credentials from the environment:

```python
import boto3, os
s3 = boto3.client("s3", endpoint_url=os.environ["AWS_ENDPOINT_URL"])
bucket = os.environ["S3_BUCKET"]
for obj in s3.list_objects_v2(Bucket=bucket).get("Contents", []):
    print(obj["Key"], obj["Size"])
```

## I/O patterns for AI workloads

A pattern that serves nearly every training job on NRP:

1. **Stage in** — copy the dataset from S3 (or CephFS) to node-local scratch (`emptyDir`) at job start. Local NVMe is far faster for the random reads of a dataloader.
2. **Checkpoint out** — write checkpoints to an RWO block PVC (or push to S3) at epoch boundaries, not every step.
3. **Publish** — copy final artifacts to S3 where collaborators (or your future self) can fetch them without cluster access.

For classrooms, the equivalent pattern is: course materials on an **RWX CephFS volume** mounted read-only into every student server, student work on **per-user RWO home volumes** — exactly what we'll configure in the final episode.

## Cleanup

```bash
kubectl delete pod tutorial-<username>-pod -n nrp-training-k8s --ignore-not-found
```

Keep `jupyterhub-shared-volume` — the custom JupyterHub episode mounts it. Verify with `bash check.sh 4`.

::: quiz Quick check
1. Ten student pods need to read the same course dataset at the same time. Which storage fits?
- [ ] An RBD block PVC (`rook-ceph-block-east`)
- [x] A CephFS PVC with ReadWriteMany
- [ ] An emptyDir volume
> RWO block storage mounts on one node at a time (you hit that limit in the sidecar exercise). CephFS RWX mounts into many pods on many nodes — the classroom shared-folder pattern.

2. Where should a training job stage its dataset for the fastest dataloader reads?
- [ ] Read it straight from S3 every epoch
- [x] Copy it once to node-local scratch (`emptyDir`) at job start
- [ ] Keep it in the home PVC
> Stage in → local NVMe scratch, checkpoint out → PVC or S3 at epoch boundaries, publish → S3. Local scratch is far faster for random reads than any network storage.

3. What's true of NRP's S3 storage?
- [x] Reachable over HTTP from anywhere — object semantics, not a POSIX filesystem
- [ ] It mounts into pods like a normal directory
- [ ] Its contents disappear when your pod terminates
> S3 is the right tool for distribution and publishing: any S3 client works from inside or outside the cluster, but you `get`/`put` objects instead of doing POSIX file I/O.

4. Your JupyterHub home directory (`/home/jovyan`) survives server restarts. What is it, really?
- [x] A per-user RWO block PVC — persistent, but sized in gigabytes
- [ ] Node-local disk on whichever node you spawned
- [ ] A CephFS share common to all users
> Every hub user gets a `claim-<username>` RBD PVC as their home. It persists across sessions but it's small — keep bulk datasets on CephFS RWX volumes or S3, not in your home.

5. During training, when and where should checkpoints be written?
- [x] To an RWO PVC or S3 at epoch boundaries — not every step
- [ ] To emptyDir scratch, for speed
- [ ] To stdout, so they end up in `kubectl logs`
> emptyDir dies with the pod — the one place a checkpoint must not live. Durable storage at epoch boundaries balances safety against I/O overhead: stage in → scratch, checkpoint out → PVC/S3, publish → S3.
:::
