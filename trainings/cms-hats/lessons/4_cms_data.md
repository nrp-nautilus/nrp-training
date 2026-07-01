---
title: CMS Data Access on NRP
teaching: 20
exercises: 20
---

**Time:** 00:00-00:40

In this section we will run a CMS-focused Jupyter pod on NRP, mount an X.509
proxy as a Kubernetes Secret, use `xrdcp` to access a CMS ROOT file, and inspect
the file with `uproot`.

The NRP documentation generally recommends JupyterHub for quick interactive
work, but also documents running your own Jupyter pod when you need a custom
container image: [ML/Jupyter pod](https://nrp.ai/documentation/userdocs/jupyter/jupyter-pod/).

## Create an X.509 proxy secret

Start with an X.509 proxy file you copied from Fermilab LPC or CERN lxplus onto
the machine where you run `kubectl`.

```bash
export USER=<username>
export X509_PROXY_FILE=/tmp/<x509-proxy-file>
```

Create or update a Kubernetes Secret containing the proxy:

```bash
kubectl create secret generic cms-x509-proxy-${USER} \
  --from-file=proxy="${X509_PROXY_FILE}" \
  -n us-cms \
  --dry-run=client -o yaml | kubectl apply -f -
```

The pod template mounts this secret and copies it to `/tmp/x509/proxy`, which is
then exposed to tools through:

```bash
export X509_USER_PROXY=/tmp/x509/proxy
```

## Build the CMS Jupyter image

The image starts from Rocky Linux 9, installs OSG CA certificates and the XRootD
client tools, then installs JupyterLab and Python packages for ROOT-file
inspection.

From `workspace/`, build and push the image:

```bash
export IMAGE=ghcr.io/<github-user-or-org>/cms-xrootd-jupyter:0.1
docker build --platform linux/amd64 -f Dockerfile.cms-jupyter -t "$IMAGE" .
docker push "$IMAGE"
```

If the image is hosted on GHCR, make sure the package is public or create an
image pull secret. For this tutorial, a public image is simpler.

## Launch the Jupyter pod

Create a temporary copy of the pod manifest and replace the placeholders:

```bash
cd ~/cms-hats/workspace
cp yamls/cms-jupyter-pod.yaml /tmp/cms-jupyter-${USER}.yaml
sed -i "s/<username>/${USER}/g" /tmp/cms-jupyter-${USER}.yaml
sed -i "s|<YOUR_IMAGE>|${IMAGE}|g" /tmp/cms-jupyter-${USER}.yaml
```

Apply the pod:

```bash
kubectl delete pod -n us-cms cms-jupyter-${USER} --ignore-not-found
kubectl apply -n us-cms -f /tmp/cms-jupyter-${USER}.yaml
kubectl wait -n us-cms --for=condition=Ready pod/cms-jupyter-${USER} --timeout=10m
kubectl get pods -n us-cms
```

Start port forwarding:

```bash
kubectl port-forward -n us-cms pod/cms-jupyter-${USER} 8888:8888
```

In another terminal, get the Jupyter token from the pod logs:

```bash
kubectl logs -n us-cms pod/cms-jupyter-${USER}
```

Open `http://localhost:8888` in your browser and paste the token from the logs.

## Inspect the CMS file

Open `cms_uproot_example.ipynb` in JupyterLab. The notebook uses this file:

```text
root://eoscms.cern.ch//eos/cms/store/group/cmst3/group/l1tr/maglowac/AD_HLT_PF/QCD_Bin-Pt-15to7000_TuneCP5_13p6TeV_pythia8/re-emul_Run3Winter25MiniAOD-FEVTOUTPUT_142X_v7-v1/251124_134438/0000/nanoout_1.root
```

The notebook first copies the file into the pod with `xrdcp`, then opens the
local copy with `uproot`.

You can also test from a terminal in the Jupyter pod:

```bash
echo "$X509_USER_PROXY"
ls -l "$X509_USER_PROXY"
xrdcp -f root://eoscms.cern.ch//eos/cms/store/group/cmst3/group/l1tr/maglowac/AD_HLT_PF/QCD_Bin-Pt-15to7000_TuneCP5_13p6TeV_pythia8/re-emul_Run3Winter25MiniAOD-FEVTOUTPUT_142X_v7-v1/251124_134438/0000/nanoout_1.root /tmp/nanoout_1.root
```

## Clean up

Stop the port-forward with `Ctrl-C`, then delete the pod:

```bash
kubectl delete pod -n us-cms cms-jupyter-${USER}
```

Keep or delete the secret depending on whether you plan to reuse it:

```bash
kubectl delete secret -n us-cms cms-x509-proxy-${USER}
```
