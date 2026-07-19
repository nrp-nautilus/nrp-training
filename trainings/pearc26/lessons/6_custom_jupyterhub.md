---
title: Advanced — Deploy a Custom JupyterHub & Build Images in NRP GitLab
teaching: 20
exercises: 50
---

::: callout Launch the workspace in JupyterHub
**[▶ Launch the workspace in JupyterHub](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fpearc26&targetpath=pearc26&urlpath=lab%2Ftree%2Fpearc26%2Fworkspace)** — `yamls/jhub-values.yaml` for this episode is in the workspace.
:::

**Afternoon session · 1:40 – 2:50 PM**

The capstone: deploy your **own** JupyterHub with Helm — controlled access, custom images, per-profile resource limits, shared storage — then see how to build custom container images with NRP GitLab CI/CD. This is the recipe instructors and PIs use to stand up course and lab hubs on NRP.

**Conventions.** Each participant has a **pre-created namespace** (handed out by the instructors) — JupyterHub can only be deployed once per namespace, so please stick to yours. Replace `<namespace>` and `<release-name>` (e.g. `jhub-<username>`) below.

> 📘 **Docs:** [Deploy JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/) · [Build images](https://nrp.ai/documentation/userdocs/tutorial/images/) · [NRP GitLab CI](https://nrp.ai/documentation/userdocs/development/gitlab/) · [Z2JH (upstream)](https://z2jh.jupyter.org)

## 1. Helm in one paragraph

Helm is a package manager for Kubernetes — instead of authoring every Deployment, Service, and ConfigMap by hand, you install a **chart** (a reusable bundle of templates) and tune it through a **values file**. The [Zero to JupyterHub chart](https://z2jh.jupyter.org) packages the entire hub/proxy/spawner stack; your whole deployment is one YAML file of values.

In the tutorial hub, `helm` is preinstalled — verify, then add the chart repository:

```bash
kubectl auth whoami && helm version --short

helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update
helm repo list
```

<details>
<summary>Expected output</summary>

```text
"jupyterhub" has been added to your repositories
Update Complete. ⎈Happy Helming!⎈

NAME         URL
jupyterhub   https://jupyterhub.github.io/helm-chart/
```
</details>

## 2. Examine the values file

Open `yamls/jhub-values.yaml`. Key sections:

```yaml
hub:
  config:
    JupyterHub:
      authenticator_class: dummy      # tutorial only — swap for CILogon/OIDC in production
      admin_access: true
      admin_users: ["admin"]
    DummyAuthenticator:
      password: "training123"
  db:
    type: sqlite-pvc
    pvc:
      accessModes: [ReadWriteOnce]
      storage: 1Gi
      storageClassName: rook-ceph-block-east
proxy:
  secretToken: 'secret_token'         # replace before deploying!
singleuser:
  storage:
    type: dynamic
    capacity: 5Gi
    homeMountPath: /home/jovyan
    dynamic:
      storageClass: rook-ceph-block-east
      pvcNameTemplate: claim-{username}{servername}
      storageAccessModes: [ReadWriteOnce]
  image:
    name: quay.io/jupyter/scipy-notebook
    tag: 2024-04-22
  cpu: {limit: 2, guarantee: 2}
  memory: {limit: 8G, guarantee: 8G}
  defaultUrl: "/lab"
cull:                                  # required on NRP — close inactive sessions
  enabled: true
  timeout: 3600
  every: 600
```

Generate a real proxy token and put it in the file in place of `secret_token`:

```bash
openssl rand -hex 32
```

## 3. Deploy

```bash
helm upgrade --cleanup-on-fail --install <release-name> jupyterhub/jupyterhub \
  --namespace <namespace> \
  --values yamls/jhub-values.yaml \
  --wait \
  --timeout=10m
```

<details>
<summary>Expected output</summary>

```text
Release "<release-name>" does not exist. Installing it now.
NAME: <release-name>
NAMESPACE: <namespace>
STATUS: deployed
REVISION: 1
NOTES:
       You have successfully installed the official JupyterHub Helm chart!
```
</details>

Inspect what the chart created — everything is an object you met this morning:

```bash
kubectl get pods -n <namespace>
kubectl get services -n <namespace>
kubectl get pvc -n <namespace>
```

You should see the **hub** pod (auth, sessions, spawning), the **proxy** pod (routing), a `hub-db-dir` PVC — and, once someone logs in, per-user pods and `claim-<user>` PVCs.

## 4. Expose it with an Ingress

Add an `ingress` section to `yamls/jhub-values.yaml` — pick a globally unique hostname:

```yaml
ingress:
  enabled: true
  ingressClassName: haproxy
  hosts: ["<your-jupyterhub-name>.nrp-nautilus.io"]
  pathSuffix: ''
  tls:
    - hosts:
      - <your-jupyterhub-name>.nrp-nautilus.io
```

Upgrade the release and verify:

```bash
helm upgrade <release-name> jupyterhub/jupyterhub \
  --namespace <namespace> \
  --values yamls/jhub-values.yaml \
  --wait --timeout=10m

kubectl get ingress -n <namespace>
```

After ~a minute for HAProxy + Let's Encrypt, open `https://<your-jupyterhub-name>.nrp-nautilus.io`, log in as `admin` with the Dummy password, and spawn a server. **You now have a working multi-user JupyterHub on national research infrastructure.**

## 5. Make it yours

### 5.1 Multiple image profiles

Give users a menu of environments — add to `singleuser`:

```yaml
singleuser:
  profileList:
  - display_name: Scipy
    kubespawner_override:
      image_spec: quay.io/jupyter/scipy-notebook:2024-04-22
    default: True
  - display_name: Tensorflow (CUDA)
    kubespawner_override:
      image_spec: quay.io/jupyter/tensorflow-notebook:cuda-2024-04-22
  - display_name: Pytorch (CUDA 12)
    kubespawner_override:
      image_spec: quay.io/jupyter/pytorch-notebook:cuda12-2024-04-22
  - display_name: Datascience (scipy, Julia, R)
    kubespawner_override:
      image_spec: quay.io/jupyter/datascience-notebook:2024-04-22
```

### 5.2 Per-profile resource limits

```yaml
  - display_name: Small (2 CPU, 4GB RAM)
    kubespawner_override:
      image_spec: quay.io/jupyter/scipy-notebook:2024-04-22
      cpu_limit: 2
      cpu_guarantee: 2
      mem_limit: 4G
      mem_guarantee: 4G
  - display_name: Large (8 CPU, 16GB RAM)
    kubespawner_override:
      image_spec: quay.io/jupyter/scipy-notebook:2024-04-22
      cpu_limit: 8
      cpu_guarantee: 8
      mem_limit: 16G
      mem_guarantee: 16G
```

Add a profile or two to your values file, `helm upgrade` again, and reload the spawn page — the menu updates live. (A GPU profile adds `extra_resource_limits: {"nvidia.com/gpu": "1"}` plus the reservation toleration pattern from this morning.)

### 5.3 Shared storage for the whole class

Mount the RWX CephFS volume from the storage episode into **every** user server:

```yaml
singleuser:
  storage:
    extraVolumes:
      - name: jupyterhub-shared
        persistentVolumeClaim:
          claimName: jupyterhub-shared-volume
    extraVolumeMounts:
      - name: jupyterhub-shared
        mountPath: /home/shared
```

Instructors drop datasets and notebooks into `/home/shared` once; every student sees them instantly.

### 5.4 Real authentication

For production, replace the Dummy authenticator with institutional login. `yamls/cilogon-jupyterhub-config.yaml` in the workspace shows a CILogon/OIDC configuration — campus credentials, an allowlist or admin-managed access, no passwords to distribute.

## 6. Operating your hub

```bash
helm list -n <namespace>                                              # releases + chart versions
kubectl logs -n <namespace> -l app=jupyterhub,component=hub --tail=50 # hub logs
kubectl get pods -n <namespace> -l app=jupyterhub,component=singleuser-server  # active users
```

Troubleshooting follows the Episode 2 debugging trio: `describe` the failing pod, read namespace `events`, check hub/proxy `logs`.

## 7. Building custom images in NRP GitLab

The stock Jupyter images only go so far — real courses need their own package stacks. NRP GitLab ([gitlab.nrp-nautilus.io](https://gitlab.nrp-nautilus.io)) builds images for you in CI and hosts them in its container registry.

The workflow:

1. **Create a project** on NRP GitLab and add a `Dockerfile` — typically `FROM quay.io/jupyter/scipy-notebook:…` plus your `pip`/`conda` installs.
2. **Add `.gitlab-ci.yml`** — a single Kaniko job builds and pushes on every commit:

```yaml
image: ghcr.io/osscontainertools/kaniko:debug

stages:
- build-and-push

build-and-push-job:
  stage: build-and-push
  variables:
    GODEBUG: "http2client=0"
  script:
  - echo "{\"auths\":{\"$CI_REGISTRY\":{\"username\":\"$CI_REGISTRY_USER\",\"password\":\"$CI_REGISTRY_PASSWORD\"}}}" > /kaniko/.docker/config.json
  - /kaniko/executor --cache=true --push-retry=10 --context $CI_PROJECT_DIR --dockerfile $CI_PROJECT_DIR/Dockerfile --destination $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA --destination $CI_REGISTRY_IMAGE:latest
```

3. **Use the image** anywhere on the cluster — in a pod spec, or as a hub profile:

```yaml
  - display_name: My Course Image
    kubespawner_override:
      image_spec: gitlab-registry.nrp-nautilus.io/<group>/<project>:latest
```

Best practices: tag with commit SHAs (not just `latest`) so a course mid-semester never changes under your students; use `--cache=true` for fast rebuilds; keep credentials in CI variables, never in the Dockerfile.

## 8. End of tutorial — cleanup

Uninstall your Helm release so the cluster is left clean:

```bash
helm uninstall <release-name> -n <namespace>
```

User PVCs are kept by default; delete them only if you're sure:

```bash
kubectl delete pvc -n <namespace> -l app=jupyterhub,component=singleuser-storage
```

## Where to go from here

- **Keep using NRP** — get a real account via [CILogon getting started](https://nrp.ai/documentation/userdocs/start/getting-started/); the tutorial credentials stop working after PEARC26.
- **Request a course hub** or namespace: [nrp.ai/contact](https://nrp.ai/contact/) (Matrix chat — the same channel for live help today).
- **All materials** stay online at [training.nrp-nautilus.io](https://training.nrp-nautilus.io/) and on [GitHub](https://github.com/nrp-nautilus/nrp-training), archived for reproducibility.

Thanks for spending the day with us — go build something on the National Research Platform.
