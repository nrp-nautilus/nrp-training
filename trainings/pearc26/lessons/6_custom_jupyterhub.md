---
title: Advanced — Deploy a Custom JupyterHub & Build Images in NRP GitLab
teaching: 20
exercises: 50
---

::: callout Launch the workspace in JupyterHub
**[▶ Open the runnable notebook for this episode](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fpearc26&targetpath=pearc26&urlpath=lab%2Ftree%2Fpearc26%2Fworkspace%2Fnotebooks%2F6_custom_jupyterhub.ipynb)** — `yamls/jhub-values.yaml` for this episode is in the workspace.
:::

**Session 6 · 70 min**

The capstone: deploy your **own** JupyterHub with Helm — controlled access, custom images, per-profile resource limits, shared storage — then see how to build custom container images with NRP GitLab CI/CD. This is the recipe instructors and PIs use to stand up course and lab hubs on NRP.

**Conventions.** Each participant works in their **own pre-created namespace** (`nrp-training-000` … `nrp-training-099`) — JupyterHub can only be deployed once per namespace. Claim yours now; the request is keyed by your hub login, so it's idempotent — you get the **same** slot back every time, and re-running this cell after a break is safe:

```bash
export NRP_NAMESPACE=$(curl -s "http://nrp-claim.nrp-training.svc.cluster.local/claim?user=${JUPYTERHUB_USER:-$NRP_USER}")
export NRP_RELEASE=jhub-$NRP_USER
echo "namespace=$NRP_NAMESPACE release=$NRP_RELEASE"
```

<details>
<summary>Expected output</summary>

```text
namespace=nrp-training-042 release=jhub-alice
```
</details>

`$NRP_NAMESPACE` and `$NRP_RELEASE` are what the commands below (and `check.sh 6`) pick up — no hand-editing. Replace `<namespace>`/`<release-name>` in any manifest with these.

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
```

```bash
kubectl get services -n <namespace>
```

```bash
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
```

```bash
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
helm list -n <namespace>
```

```bash
sleep 5
kubectl logs -n <namespace> -l app=jupyterhub,component=hub --tail=50
```

```bash
kubectl get pods -n <namespace> -l app=jupyterhub,component=singleuser-server
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

::: quiz Quick check — the capstone
1. What role does the Helm values file play in your deployment?
- [x] It customizes the chart's templates — auth, images, storage, resources — in one YAML file
- [ ] It replaces kubectl for managing the cluster
- [ ] It builds the container images the hub uses
> The z2jh chart contains the templates for every hub/proxy/spawner object; your values file is the *entire* description of your deployment. Version-control it and you can rebuild the hub anywhere.

2. Your course hub goes to production. What happens to the Dummy authenticator?
- [x] Swap it for CILogon/OIDC so students use campus credentials
- [ ] Keep it and share the password with the class
- [ ] Remove authentication entirely — the ingress is already HTTPS
> Dummy auth is a tutorial convenience. The workspace's `cilogon-jupyterhub-config.yaml` shows the production pattern: institutional login, allowlists, no passwords to distribute.

3. Why tag course images with commit SHAs instead of only `latest`?
- [x] So the environment never changes underneath students mid-semester
- [ ] Because `latest` images pull more slowly
- [ ] Because GitLab requires unique tags
> `latest` moves every time CI runs. Pinning profiles to a SHA (or release tag) means the same image all semester — reproducibility is the whole reason you built a custom image.

4. You edited `jhub-values.yaml` to add an ingress. How do the changes reach your running hub?
- [x] `helm upgrade <release> jupyterhub/jupyterhub --values yamls/jhub-values.yaml`
- [ ] `kubectl apply -f yamls/jhub-values.yaml`
- [ ] Delete the release and reinstall from scratch
> A values file is chart *input*, not a Kubernetes manifest — `kubectl apply` on it fails. `helm upgrade` re-renders the templates with your new values and rolls out only what changed; you did this live when adding the ingress and profiles.

5. Every student's server shows the same `/home/shared` folder. What makes that work?
- [x] One RWX CephFS PVC mounted into every user pod via `extraVolumes`/`extraVolumeMounts`
- [ ] Each student's home PVC is cloned from a master copy
- [ ] The hub copies the files into each home directory at spawn
> It's the `jupyterhub-shared-volume` claim from the storage episode — RWX means all user pods mount it simultaneously. Instructors drop a dataset in once; the whole class sees it instantly (mount it read-only for students in production).
:::

## Get your own NRP access — for after PEARC

Everything today ran on the tutorial's shared training cluster and a namespace we handed you; that access **stops working after PEARC26**. Let's spend the last part of the session getting you set up with your *own* NRP access so you can keep going. Instructors are circulating — grab one if any step stalls.

**1. Register your identity.** NRP authenticates through **CILogon**, so you sign in with your existing campus/institutional account — no new password.

- Go to **[portal.nrp.ai](https://portal.nrp.ai)** and log in with CILogon (pick your institution).
- Follow [Getting started](https://nrp.ai/documentation/userdocs/start/getting-started/) to complete your profile.

**2. Get into a namespace.** Compute on NRP lives in a namespace tied to a PI/project.

- **Have a PI or project already?** Ask them to add you — an admin runs `kubectl` to bind you to their namespace. Send them your CILogon identity (the email shown in the portal).
- **Starting your own?** Request a namespace/allocation via **[nrp.ai/contact](https://nrp.ai/contact/)** — the same **Matrix** channel we've used for live help today ([element.nrp-nautilus.io](https://element.nrp-nautilus.io)). Say what you're doing and roughly what resources you need.

**3. Point `kubectl` at NRP.** Once you're in a namespace:

- Grab your personal kubeconfig from the portal ([get-config](https://nrp.ai/documentation/userdocs/start/get-config/)) and drop it at `~/.kube/config`.
- Verify: `kubectl config get-contexts` then `kubectl get pods -n <your-namespace>`.
- Everything you did today — pods, jobs, GPUs, PVCs, S3, LLM services, Helm-deployed hubs — works the same against your own namespace.

**4. Keep the materials.** This whole tutorial stays online, archived for reproducibility:

- Lessons + runnable notebooks: **[training.nrp-nautilus.io](https://training.nrp-nautilus.io/)** and **[GitHub](https://github.com/nrp-nautilus/nrp-training)**.
- Docs home: **[nrp.ai/documentation](https://nrp.ai/documentation/)**. Live community help: the Matrix channel above.

::: callout Questions?
This is also the open **Q&A** — anything from today's exercises, your own use case, getting a course hub for your students, or GPU/allocation policy. Ask away.
:::

Thanks for spending the day with us — go build something on the National Research Platform.
