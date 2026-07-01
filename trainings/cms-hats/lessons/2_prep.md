---
title: Hands-On Prep
teaching: 10
exercises: 0
---

**Time:** 00:00-00:25

In this section we will prepare to run the hands-on exercise 


## 1. Create a PVC to store your work
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jet-class-output-<username>
  namespace: us-cms
spec:
  storageClassName: rook-ceph-block
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```
---

## 2. The Container Image

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
docker build -f Dockerfile.jet-class -t "$IMAGE" .
docker push "$IMAGE"
```

For Apple Silicon Macs, build the Linux AMD64 image that the cluster will run:

```bash
docker build --platform linux/amd64 -f Dockerfile.jet-class -t "$IMAGE" .
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


## 3. Prepare the YAML

Set a short username and image name. Use the same `USER` value everywhere so
your Job and PVC names are unique.

```bash
export USER=<username>
export IMAGE=ghcr.io/<github-user-or-org>/cms-hats-jet-class:0.2
cd ~/cms-hats/workspace
```

Make a temporary copy of the training manifest and replace the placeholders:

```bash
cp yamls/jet-class-job.yaml /tmp/jet-class-${USER}.yaml
sed -i "s/<username>/${USER}/g" /tmp/jet-class-${USER}.yaml
sed -i "s|<YOUR_IMAGE>|${IMAGE}|g" /tmp/jet-class-${USER}.yaml
```

The first manifest creates both the PVC and the GPU training Job.
