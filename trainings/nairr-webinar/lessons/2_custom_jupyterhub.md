---
title: Deploy a Custom JupyterHub & Build Images in NRP GitLab
teaching: 15
exercises: 30
questions:
  - How do I deploy a JupyterHub of my own on NRP?
  - How do I give students a menu of environments and resource sizes?
  - How do I build a custom course image and keep it stable all semester?
objectives:
  - Deploy JupyterHub with Helm from a values file.
  - Expose it on a public hostname with an Ingress.
  - Add image profiles, per-profile resource limits, and shared class storage.
  - Build a custom course image with NRP GitLab CI/CD.
keypoints:
  - The values file *is* your deployment — version-control it and you can rebuild anywhere.
  - `helm upgrade` re-renders the chart with new values; it is not `kubectl apply`.
  - One RWX volume mounted into every server is how a class shares datasets.
  - Pin course images to a commit SHA so the environment never shifts mid-semester.
---

::: callout Open the runnable notebook
**[▶ Open the notebook for this session](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fnairr-webinar&targetpath=nairr-webinar&urlpath=lab%2Ftree%2Fnairr-webinar%2Fworkspace%2Fnotebooks%2F2_custom_jupyterhub.ipynb)** — `yamls/jhub-values.yaml` for this session is in the workspace.
:::

**Time:** 00:15–01:00

Deploy your **own** JupyterHub with Helm — controlled access, custom images,
per-profile resource limits, shared storage — then see how to build custom
container images with NRP GitLab CI/CD. This is the recipe instructors and PIs
use to stand up course and lab hubs on NRP.

::: important Read this before you deploy a real hub

This tutorial takes a deliberate shortcut so it fits in a webinar. Every hub you
deploy **after** today should follow the documented path in [Deploy
JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/), and the
difference that matters is **authentication**.

| | This tutorial | A hub you actually run |
|---|---|---|
| Authenticator | `DummyAuthenticator` | `CILogonOAuthenticator` |
| Who can sign in | anyone who knows the shared password | your campus IdP, narrowed by `allowed_idps` / `allowed_users` |
| Prerequisite | none | an OAuth client registered with CILogon |
| Lead time | zero | **plan on several days to more than a week** |

`DummyAuthenticator` is a password in a values file. It is fine for a
throwaway namespace for one hour; it is **not** acceptable for a hub with a
public hostname. NRP's docs are blunt about this: leaving a hub open for anyone
to sign in can get your namespace locked.

The real path uses **CILogon**, the same federated login NRP itself uses — your
students sign in with their existing campus credentials. The catch is that
CILogon is an **independent service, not operated by NRP**, and you register
your own OAuth client with them at
[cilogon.org/oauth2/register](https://cilogon.org/oauth2/register):

- **Callback URL:** `https://<your-hostname>.nrp-nautilus.io/hub/oauth_callback`
- **Client type:** Confidential · **Refresh tokens:** No
- **Scopes:** `org.cilogon.userinfo,openid,profile,email`

CILogon staff review each registration by hand and email you a client ID and
secret once it is approved — **budget a few days, and it can stretch past a
week**. Two consequences for planning a course:

1. **Start the registration well before the term.** It is the long pole, and
   nothing on the NRP side unblocks it.
2. **Pick your hostname first.** It is baked into the callback URL you register,
   so changing it later means going back to CILogon.

Everything else on this page — Helm, the values file, profiles, resource
limits, shared storage, custom images — is identical either way. Only the
`hub.config` authentication block changes, plus an
[`allowed_idps` allowlist](https://cilogon.org/idplist/) for your institution.
`yamls/cilogon-jupyterhub-config.yaml` in the workspace is a working example of
that block — see [5.4 Real authentication](#5-4-real-authentication).
:::

::: prereq Tools you need on your own machine

The training hub has all of this preinstalled, so nothing below is needed
*today*. To run the same commands from your laptop against your own namespace,
you need three tools and the cluster config:

| What | Why | Where |
|---|---|---|
| `kubectl` | talks to the Kubernetes API — every `kubectl` command on this page | [kubernetes.io/docs/tasks/tools](https://kubernetes.io/docs/tasks/tools/) |
| **`kubelogin`** | CILogon/OIDC login for `kubectl`. **The NRP kubeconfig does not work without it** | [github.com/int128/kubelogin](https://github.com/int128/kubelogin) |
| `helm` | installs and upgrades the JupyterHub chart | [helm.sh/docs/intro/install](https://helm.sh/docs/intro/install/) |
| **Nautilus kubeconfig** | points `kubectl` at Nautilus and carries your CILogon identity — save it as `~/.kube/config`, no extension | [nrp.ai/config](https://nrp.ai/config) |

`kubelogin` is a `kubectl` plugin, so the binary must land on your `PATH` under
the name **`kubectl-oidc_login`** — that exact name is how `kubectl` finds it.
The NRP docs give a copy-paste installer for Linux and macOS, plus fixes for
headless machines, WSL, and port conflicts:
[cluster access via `kubectl`](https://nrp.ai/documentation/userdocs/start/getting-started/#cluster-access-via-kubectl).

Fetch the kubeconfig and confirm the whole chain works:

```bash
mkdir -p ~/.kube
curl -o ~/.kube/config -fSL https://nrp.ai/config

kubectl config get-contexts     # should list the `nautilus` context
kubectl auth whoami             # triggers the CILogon browser login the first time
helm version --short
```

You also need to be an **admin** of the namespace you deploy into — a plain
member cannot install a chart.
:::

**Conventions.** Each participant works in their **own pre-created namespace**
(`nrp-training-000` … `nrp-training-099`) — JupyterHub can only be deployed
once per namespace. Set your short username, render your personal manifests,
and claim your namespace in one step. The claim is keyed by your hub login, so
it is idempotent — you get the **same** slot back every time, and re-running
this after a break is safe:

```bash
export NRP_USER=changeme   # ✏️ EDIT to your short name
cd ~/nairr-webinar/workspace
if [ "$NRP_USER" = changeme ]; then echo "⚠️  Edit NRP_USER above first, then re-run"; else
  mkdir -p my-yamls
  for f in yamls/*; do sed "s/<username>/$NRP_USER/g" "$f" > "my-yamls/$(basename "$f")"; done
  echo "✅ my-yamls/ rendered for $NRP_USER"
fi
# claim your own namespace for the session (idempotent — same slot every time you ask):
export NRP_NAMESPACE=$(curl -s "http://nrp-claim.nrp-training.svc.cluster.local/claim?user=${JUPYTERHUB_USER:-$NRP_USER}")
export NRP_RELEASE=jhub-$NRP_USER
echo "namespace=$NRP_NAMESPACE release=$NRP_RELEASE"
```

<details>
<summary>Expected output</summary>

```text
✅ my-yamls/ rendered for alice
namespace=nrp-training-042 release=jhub-alice
```
</details>

`$NRP_NAMESPACE` and `$NRP_RELEASE` are what the commands below (and
`check.sh 2`) pick up — no hand-editing. Every manifest is rendered into
**`my-yamls/`** with `<username>` already filled in, so wherever this page says
*"replace `<username>`"*, it is already done in your copy.

> Terminal steps don't share these variables — run the same `export` lines in
> any terminal you open. Re-running the render overwrites edits you made in
> `my-yamls/`.

> 📘 **Docs:** [Deploy JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/) · [Build images](https://nrp.ai/documentation/userdocs/tutorial/images/) · [NRP GitLab CI](https://nrp.ai/documentation/userdocs/development/gitlab/) · [Z2JH (upstream)](https://z2jh.jupyter.org)

## 1. Helm in one paragraph

Helm is a package manager for Kubernetes — instead of authoring every
Deployment, Service, and ConfigMap by hand, you install a **chart** (a reusable
bundle of templates) and tune it through a **values file**. The [Zero to
JupyterHub chart](https://z2jh.jupyter.org) packages the entire
hub/proxy/spawner stack; your whole deployment is one YAML file of values.

In the training hub, `helm` is preinstalled — verify, then add the chart
repository:

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

### First — what's already running in your namespace?

JupyterHub can only be deployed **once per namespace**: a second release fights
the first one over the `proxy-public` service and the hub database. Your claimed
slot should be empty, but check before you install — if you've run this tutorial
before, or the slot was recycled, there may already be a hub sitting in it.

```bash
helm list -n $NRP_NAMESPACE
kubectl get pods -n $NRP_NAMESPACE
```

<details>
<summary>Expected output</summary>

```text
NAME	NAMESPACE	REVISION	STATUS	CHART	APP VERSION
No resources found in nrp-training-042 namespace.
```
</details>

An empty `helm list` and no pods means you're clear — skip ahead and deploy.

If a release *is* listed, look at the `NAME` column. Tear it down only if it's
yours; in a shared namespace someone else's class may be running on it. Set
`OLD_RELEASE` to that name — otherwise leave it alone and ask whoever owns the
namespace.

```bash
# ⚠️  Optional — only if the command above listed a JupyterHub you want gone.
OLD_RELEASE=changeme   # ✏️ the NAME shown by `helm list` above

if [ "$OLD_RELEASE" = changeme ]; then
  echo "Nothing to do — set OLD_RELEASE only if you need to remove an existing hub."
else
  helm uninstall "$OLD_RELEASE" -n $NRP_NAMESPACE
  # wait for the pods to actually go away before redeploying
  kubectl wait --for=delete pod -l app=jupyterhub -n $NRP_NAMESPACE --timeout=120s 2>/dev/null || true
  helm list -n $NRP_NAMESPACE
  kubectl get pods -n $NRP_NAMESPACE
fi
```

`helm uninstall` leaves PVCs behind on purpose — the hub database and any user
home directories survive, so a reinstall picks them back up. [Section
8](#8-cleanup) shows how to delete those too if you really want
a clean slate.

### Install the chart

```bash
helm upgrade --cleanup-on-fail --install $NRP_RELEASE jupyterhub/jupyterhub \
  --namespace $NRP_NAMESPACE \
  --values my-yamls/jhub-values.yaml \
  --wait \
  --timeout=10m
```

<details>
<summary>Expected output</summary>

```text
Release "jhub-alice" does not exist. Installing it now.
NAME: jhub-alice
NAMESPACE: nrp-training-042
STATUS: deployed
REVISION: 1
NOTES:
       You have successfully installed the official JupyterHub Helm chart!
```
</details>

Inspect what the chart created — every one of these is an ordinary Kubernetes
object:

```bash
kubectl get pods -n $NRP_NAMESPACE
```

```bash
kubectl get services -n $NRP_NAMESPACE
```

```bash
kubectl get pvc -n $NRP_NAMESPACE
```

You should see the **hub** pod (auth, sessions, spawning), the **proxy** pod
(routing), a `hub-db-dir` PVC — and, once someone logs in, per-user pods and
`claim-<user>` PVCs.

## 4. Expose it with an Ingress

`my-yamls/jhub-values.yaml` already ends with an `ingress` block, commented out,
with **your** hostname rendered in — the setup step substituted `<username>` for
you, so it is globally unique:

```yaml
ingress:
  enabled: true
  ingressClassName: haproxy
  hosts: ["jhub-<username>.nrp-nautilus.io"]
  pathSuffix: ''
  tls:
    - hosts:
      - jhub-<username>.nrp-nautilus.io
```

The quickest way to enable it is a one-liner that strips the leading `#` from
those lines:

```bash
sed -i '/^#ingress:/,$ s/^#//' my-yamls/jhub-values.yaml
tail -9 my-yamls/jhub-values.yaml
```

Upgrade the release and verify:

```bash
helm upgrade $NRP_RELEASE jupyterhub/jupyterhub \
  --namespace $NRP_NAMESPACE \
  --values my-yamls/jhub-values.yaml \
  --wait --timeout=10m
```

```bash
kubectl get ingress -n $NRP_NAMESPACE
```

After ~a minute for HAProxy + Let's Encrypt, open
`https://jhub-$NRP_USER.nrp-nautilus.io`, log in as `admin` with the
Dummy password, and spawn a server. **You now have a working multi-user
JupyterHub on national research infrastructure.**

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

Add a profile or two to your values file, `helm upgrade` again, and reload the
spawn page — the menu updates live. A GPU profile adds
`extra_resource_limits: {"nvidia.com/gpu": "1"}`.

This is where a course gets shaped: give the intro unit a Small CPU profile and
the deep-learning unit a GPU profile, and students pick the right one from a
dropdown instead of you managing machines.

### 5.3 Shared storage for the whole class

Mount one RWX CephFS volume into **every** user server:

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

Instructors drop datasets and notebooks into `/home/shared` once; every student
sees them instantly. Mount it read-only for students in production.

### 5.4 Real authentication

For production, replace the Dummy authenticator with institutional login.
`yamls/cilogon-jupyterhub-config.yaml` in the workspace shows a CILogon/OIDC
configuration — campus credentials, an allowlist or admin-managed access, no
passwords to distribute. For a class roster, the allowlist is your enrollment
list.

Swapping it in needs a `client_id` and `client_secret` from CILogon, which you
have to request from them and wait on — see the lead-time warning at the top of
this page. That wait is the reason today's hub uses the Dummy authenticator.

## 6. Operating your hub

```bash
helm list -n $NRP_NAMESPACE
```

```bash
sleep 5
kubectl logs -n $NRP_NAMESPACE -l app=jupyterhub,component=hub --tail=50
```

```bash
kubectl get pods -n $NRP_NAMESPACE -l app=jupyterhub,component=singleuser-server
```

Troubleshooting is the standard Kubernetes trio: `describe` the failing pod,
read namespace `events`, check hub/proxy `logs`.

## 7. Building custom images in NRP GitLab

The stock Jupyter images only go so far — real courses need their own package
stacks. NRP GitLab ([gitlab.nrp-nautilus.io](https://gitlab.nrp-nautilus.io))
builds images for you in CI and hosts them in its container registry.

The workflow:

1. **Create a project** on NRP GitLab and add a `Dockerfile` — typically
   `FROM quay.io/jupyter/scipy-notebook:…` plus your `pip`/`conda` installs.
2. **Add `.gitlab-ci.yml`** — a single Kaniko job builds and pushes on every
   commit:

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

3. **Use the image** anywhere on the cluster — in a pod spec, or as a hub
   profile:

```yaml
  - display_name: My Course Image
    kubespawner_override:
      image_spec: gitlab-registry.nrp-nautilus.io/<group>/<project>:latest
```

Best practices: tag with commit SHAs (not just `latest`) so a course
mid-semester never changes under your students; use `--cache=true` for fast
rebuilds; keep credentials in CI variables, never in the Dockerfile.

## 8. Cleanup

If this was a trial run, uninstall your Helm release so the cluster is left
clean:

```bash
helm uninstall $NRP_RELEASE -n $NRP_NAMESPACE
```

User PVCs are kept by default; delete them only if you're sure:

```bash
kubectl delete pvc -n $NRP_NAMESPACE -l app=jupyterhub,component=singleuser-storage
```

If this is a real course hub, leave it running — the `cull` settings in the
values file close idle student sessions automatically.

::: quiz Quick check
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
- [x] `helm upgrade $NRP_RELEASE jupyterhub/jupyterhub --values my-yamls/jhub-values.yaml`
- [ ] `kubectl apply -f my-yamls/jhub-values.yaml`
- [ ] Delete the release and reinstall from scratch
> A values file is chart *input*, not a Kubernetes manifest — `kubectl apply` on it fails. `helm upgrade` re-renders the templates with your new values and rolls out only what changed.

5. Every student's server shows the same `/home/shared` folder. What makes that work?
- [x] One RWX CephFS PVC mounted into every user pod via `extraVolumes`/`extraVolumeMounts`
- [ ] Each student's home PVC is cloned from a master copy
- [ ] The hub copies the files into each home directory at spawn
> RWX means all user pods mount the same claim simultaneously. Instructors drop a dataset in once; the whole class sees it instantly.
:::

## Where to go next

- **Get your own namespace** if you were following along on the training hub —
  see [Getting your own access](1_intro.html#getting-your-own-access).
- **Docs:** [nrp.ai/documentation](https://nrp.ai/documentation/)
- **Live help:** the NRP Matrix channel at [nrp.ai/contact](https://nrp.ai/contact/)
- **These materials:** [training.nrp-nautilus.io](https://training.nrp-nautilus.io/)
  and [GitHub](https://github.com/nrp-nautilus/nrp-training)

::: callout Questions?
This is the open Q&A — your own course, GPU and allocation policy, migrating an
existing class onto NRP. Ask away.
:::

<iframe src="https://app.sli.do/event/8FY6gX1uNxrVyYpeSyWPA3" height="100%" width="100%" frameBorder="0" style="min-height: 560px;" allow="clipboard-write" title="Slido"></iframe>
