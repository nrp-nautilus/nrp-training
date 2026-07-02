---
title: Hands-On Prep
teaching: 10
exercises: 0
---

**Time:** 00:00-00:25

In this section we will prepare to run the hands-on exercise 


## 1. Clone the training materials

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
The jet classifier examples write under `/training/jet-class`; the CMS data
access example writes under `/training/cms-data`.

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


## 5. Prepare the YAML

Set the image name. Use the same `USER` value from the previous step so your Job
uses the shared PVC you created above.

```bash
export IMAGE=ghcr.io/<github-user-or-org>/cms-hats-jet-class:0.2
cd ~/cms-hats/workspace
```

Make a temporary copy of the training manifest and replace the placeholders:

```bash
cp yamls/jet-class-job.yaml /tmp/jet-class-${USER}.yaml
perl -pi -e 's/<username>/$ENV{USER}/g; s|<YOUR_IMAGE>|$ENV{IMAGE}|g' /tmp/jet-class-${USER}.yaml
```

The manifest creates the GPU training Job, mounts the shared PVC at
`/training`, and writes jet classifier outputs under `/training/jet-class`.
