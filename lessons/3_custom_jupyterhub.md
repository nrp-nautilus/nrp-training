---
title: Deploy a Custom JupyterHub & Build Course Images
teaching: 10
exercises: 30
questions:
  - How do I deploy a JupyterHub of my own on NRP?
  - How do I give students a menu of environments and resource sizes?
  - How do I build a custom course image and keep it stable all semester?
objectives:
  - Deploy JupyterHub with Helm from a values file, on a public HTTPS hostname.
  - Add image profiles, per-profile resource limits, and shared class storage.
  - Build a custom course image with NRP GitLab CI/CD.
keypoints:
  - The values file *is* your deployment — version-control it and you can rebuild anywhere.
  - `helm upgrade` re-renders the chart with new values; it is not `kubectl apply`.
  - One RWX volume mounted into every server is how a class shares datasets.
  - Pin course images to a commit SHA so the environment never shifts mid-semester.
---

::: callout Open the runnable notebook
**[▶ Open the notebook for this section](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fhidsi&targetpath=hidsi&urlpath=lab%2Ftree%2Fhidsi%2Fworkspace%2Fnotebooks%2F3_custom_jupyterhub.ipynb)** — `yamls/jhub-values.yaml` for this section is in the workspace.
:::

**Time:** 00:50–01:30

Deploy your **own** JupyterHub with Helm — controlled access, custom images,
per-profile resource limits, shared storage — then see how to build custom
container images with NRP GitLab CI/CD. This is the recipe instructors and PIs
use to stand up course and lab hubs on NRP.

::: important Read this before you deploy a real hub

This section takes a deliberate shortcut so it fits in the time we have. Every
hub you deploy **after** today should follow the documented path in [Deploy
JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/), and the
difference that matters is **authentication**.

| | This workshop | A hub you actually run |
|---|---|---|
| Authenticator | `DummyAuthenticator` | `CILogonOAuthenticator` |
| Who can sign in | anyone who knows the shared password | your campus IdP, narrowed by `allowed_idps` / `allowed_users` |
| Prerequisite | none | an OAuth client registered with CILogon |
| Lead time | zero | **plan on several days to more than a week** |

`DummyAuthenticator` is a password in a values file. It is fine for a throwaway
namespace for 40 minutes; it is **not** acceptable for a hub with a public
hostname. NRP's docs are blunt about this: leaving a hub open for anyone to sign
in can get your namespace locked.

The real path uses **CILogon**, the same federated login NRP itself uses — your
students sign in with their existing campus credentials. The catch is that
CILogon is an **independent service, not operated by NRP**, and you register
your own OAuth client with them at
[cilogon.org/oauth2/register](https://cilogon.org/oauth2/register):

- **Callback URL:** `https://<your-hostname>.nrp-nautilus.io/hub/oauth_callback`
- **Client type:** Confidential · **Refresh tokens:** No
- **Scopes:** `org.cilogon.userinfo,openid,profile,email`

CILogon staff review each registration by hand and email you a client ID and
secret once approved — **budget a few days, and it can stretch past a week**.
Two consequences for planning a course:

1. **Start the registration well before the term.** It is the long pole, and
   nothing on the NRP side unblocks it.
2. **Pick your hostname first.** It is baked into the callback URL you register,
   so changing it later means going back to CILogon.

Everything else on this page — Helm, the values file, profiles, resource limits,
shared storage, custom images — is identical either way. Only the `hub.config`
authentication block changes, plus an [`allowed_idps`
allowlist](https://cilogon.org/idplist/) for your institution.
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
headless machines, WSL, and port conflicts: [cluster access via
`kubectl`](https://nrp.ai/documentation/userdocs/start/getting-started/#cluster-access-via-kubectl).

You also need to be an **admin** of the namespace you deploy into — a plain
member cannot install a chart.
:::

## Setup — claim your namespace

Each participant works in their **own pre-created namespace**
(`nrp-training-000` … `nrp-training-099`) — JupyterHub can only be deployed once
per namespace. Set your short username, render your personal manifests, and
claim your namespace in one step. The claim is keyed by your hub login, so it is
idempotent — you get the **same** slot back every time, and re-running it after
a break is safe:

```bash
export NRP_USER=changeme   # ✏️ EDIT to your short name
cd ~/hidsi/workspace
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
✅ my-yamls/ rendered for nautilus
namespace=nrp-training-042 release=jhub-nautilus
```
</details>

`$NRP_NAMESPACE` and `$NRP_RELEASE` are what the commands below (and
`check.sh 3`) pick up — no hand-editing. Every manifest is rendered into
**`my-yamls/`** with `<username>` already filled in, so wherever this page says
*"replace `<username>`"*, it is already done in your copy.

> Terminal sessions don't share these variables — run the same `export` lines in
> any terminal you open. Re-running the render overwrites edits you made in
> `my-yamls/`.

> 📘 **Docs:** [Deploy JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/) · [Build images](https://nrp.ai/documentation/userdocs/tutorial/images/) · [NRP GitLab CI](https://nrp.ai/documentation/userdocs/development/gitlab/) · [Z2JH (upstream)](https://z2jh.jupyter.org)

## 1. Helm in one paragraph

Helm is a package manager for Kubernetes — instead of authoring every
Deployment, Service, and ConfigMap by hand, you install a **chart** (a reusable
bundle of templates) and tune it through a **values file**. The [Zero to
JupyterHub chart](https://z2jh.jupyter.org) packages the entire
hub/proxy/spawner stack; your whole deployment is one YAML file of values.

The values file looks long until you see what it stands in for. Your 173 lines
render into **thirteen Kubernetes objects**, about 1,400 lines of manifests:

<svg viewBox="0 0 720 300" width="100%" role="img" aria-labelledby="helm-dia-t" xmlns="http://www.w3.org/2000/svg" style="max-width:720px;height:auto;display:block;margin:0 auto;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif">
<title id="helm-dia-t">One values file renders into thirteen Kubernetes objects</title>
<text x="360" y="18" text-anchor="middle" font-size="12.5" fill="currentColor" opacity=".75">What Kubernetes actually needs &#8212; 13 objects, ~1,400 lines of YAML</text>
<rect x="14" y="34" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="80" y="53" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">Deployment</tspan><tspan opacity=".65"> &#183; hub</tspan></text>
<rect x="154" y="34" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="220" y="53" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">Deployment</tspan><tspan opacity=".65"> &#183; proxy</tspan></text>
<rect x="294" y="34" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="360" y="53" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">Service</tspan><tspan opacity=".65"> &#183; hub</tspan></text>
<rect x="434" y="34" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="500" y="53" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">Service</tspan><tspan opacity=".65"> &#183; proxy-api</tspan></text>
<rect x="574" y="34" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="640" y="53" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">Service</tspan><tspan opacity=".65"> &#183; proxy-public</tspan></text>
<rect x="14" y="72" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="80" y="91" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">Ingress</tspan><tspan opacity=".65"> &#183; jupyterhub</tspan></text>
<rect x="154" y="72" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="220" y="91" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">ConfigMap</tspan><tspan opacity=".65"> &#183; hub</tspan></text>
<rect x="294" y="72" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="360" y="91" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">Secret</tspan><tspan opacity=".65"> &#183; hub</tspan></text>
<rect x="434" y="72" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="500" y="91" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">PVC</tspan><tspan opacity=".65"> &#183; hub-db-dir</tspan></text>
<rect x="574" y="72" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="640" y="91" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">ServiceAccount</tspan><tspan opacity=".65"> &#183; hub</tspan></text>
<rect x="154" y="110" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="220" y="129" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">Role</tspan><tspan opacity=".65"> &#183; hub</tspan></text>
<rect x="294" y="110" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="360" y="129" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">RoleBinding</tspan><tspan opacity=".65"> &#183; hub</tspan></text>
<rect x="434" y="110" width="132" height="30" rx="5" fill="currentColor" fill-opacity=".06" stroke="currentColor" stroke-opacity=".35"/>
<text x="500" y="129" text-anchor="middle" font-size="10.5" fill="currentColor"><tspan font-weight="600">NetworkPolicy</tspan><tspan opacity=".65"> &#183; proxy</tspan></text>
<path d="M14 152 L706 152 L442 204 L278 204 Z" fill="currentColor" fill-opacity=".05" stroke="currentColor" stroke-opacity=".3" stroke-dasharray="4 3"/>
<text x="360" y="176" text-anchor="middle" font-size="12" fill="currentColor" font-weight="600">Helm &#8212; the z2jh chart</text>
<text x="360" y="192" text-anchor="middle" font-size="10.5" fill="currentColor" opacity=".7">45 templates, rendered and kept in sync</text>
<path d="M360 204 L360 214" stroke="currentColor" stroke-opacity=".5" stroke-width="1.5" marker-end="url(#helm-dia-a)"/>
<defs><marker id="helm-dia-a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor" fill-opacity=".5"/></marker></defs>
<rect x="250" y="220" width="220" height="40" rx="6" fill="currentColor" fill-opacity=".1" stroke="currentColor" stroke-opacity=".6" stroke-width="1.5"/>
<text x="360" y="245" text-anchor="middle" font-size="13.5" fill="currentColor" font-weight="700">jhub-values.yaml</text>
<text x="360" y="278" text-anchor="middle" font-size="12.5" fill="currentColor" opacity=".75">What you write &#8212; 173 lines, six blocks that matter</text>
</svg>

And they all have to agree with each other. The hub's Deployment carries a
checksum of the ConfigMap and the Secret, so changing either restarts the hub
instead of leaving it running on stale config. The ServiceAccount needs a Role
granting `create` and `delete` on pods and PVCs — that is *how* the hub spawns a
user's server. `proxy-public` has to route to the proxy, which has to route to
the hub, which has to know its own public URL.

Hand-written, changing the single-user image means editing several files and
re-checking every reference between them. With the chart it is one line in one
file, and `helm upgrade` works out what has to change.

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

The chart brings the templates; this one file brings every decision. Read it a
block at a time — the whole thing is at the end of the section.

### 2.1 Who can log in

```yaml
hub:
  config:
    JupyterHub:
      authenticator_class: dummy
      admin_access: true
      admin_users: ["admin", "admin2"]
    DummyAuthenticator:
      password: "training123"
    # Allow all users to sign in (for tutorial purposes)
    Authenticator:
      allowed_users: set()
```

`authenticator_class: dummy` accepts **any** username with the shared
`password` — which is why this is a workshop hub and not a course hub.
`admin_users` gets the admin panel: other people's servers, the user list, a
shutdown button. There are **two** of them so you can be two people at once
later — [5.3](#5-3-shared-storage-for-the-whole-class) has you log in as both to
watch a shared folder work. `allowed_users: set()` is an *empty allowlist*, and
empty here means "no list — let everyone in".

That last line is the first thing to change in production. With CILogon
([5.4](#5-4-real-authentication)) the allowlist stops being a formality and
becomes your enrollment list.

### 2.2 The hub

```yaml
hub:
  db:
    type: sqlite-pvc
    pvc:
      accessModes: [ReadWriteOnce]
      storage: 1Gi
      storageClassName: rook-ceph-block-east
  resources:
    limits: {cpu: "2", memory: 1Gi}
    requests: {cpu: 100m, memory: 512Mi}
```

The hub process keeps its state — users, running servers, API tokens — in
SQLite on its own 1Gi volume, so restarting the hub does not lose who is logged
in. `rook-ceph-block-east` is NRP block storage; `ReadWriteOnce` is all a single
database pod needs.

### 2.3 The proxy

```yaml
proxy:
  secretToken: 'secret_token'
  service:
    type: ClusterIP
```

Every request to a user's server goes through the proxy, and `secretToken` is
the shared secret the hub uses to reprogram its routes. `secret_token` is a
placeholder that must never reach a real deployment — the install step in
[section 3](#install-the-chart) mints a real one into your copy before Helm
sees it.

`ClusterIP` keeps the proxy inside the cluster; the ingress
([2.6](#2-6-the-ingress)) is what faces the internet.

### 2.4 The single-user servers

Abridged to the decisions you will actually change — the environment, the size,
and the home directory:

```yaml
singleuser:
  image:                                # the default environment
    name: quay.io/jupyter/scipy-notebook
    tag: 2024-04-22
  cpu:                                  # what every server gets
    limit: 3
    guarantee: 3
  memory:
    limit: 10G
    guarantee: 10G
  storage:                              # a private home volume per user
    type: dynamic
    capacity: 5Gi
    homeMountPath: /home/jovyan
    dynamic:
      storageClass: rook-ceph-block-east
      pvcNameTemplate: claim-{username}{servername}
  defaultUrl: "/lab"
  profileList:                          # the spawn-page menu — more in 4.1
  - display_name: Scipy
    kubespawner_override:
      image_spec: quay.io/jupyter/scipy-notebook:2024-04-22
    default: True
```

**`image`** is the environment a server starts in — pin the tag, never `latest`.
**`cpu`/`memory`** apply to every server, and setting `guarantee` equal to
`limit` reserves the resources instead of overcommitting them. **`storage:
dynamic`** gives each user their own PVC, named from `pvcNameTemplate` and
mounted at `homeMountPath`, so `/home/jovyan` survives logouts, restarts and
culls. **`profileList`** is the menu on the spawn page; each entry's
`kubespawner_override` replaces the defaults above. The file ships with fifteen
profiles — one is shown here.

### 2.5 Culling idle servers

```yaml
cull:
  enabled: true
  timeout: 3600
  every: 600
```

Every 10 minutes (`every`) the culler shuts down servers idle for more than an
hour (`timeout`). Home volumes are untouched, so a student logs back in and
picks up where they left off.

::: callout Why `cull` is not optional
A student who closes their laptop lid leaves a pod holding CPU and memory. On
shared national infrastructure that is the fastest way to make your namespace
unpopular — and for a class of 40, it is the difference between a hub that fits
its allocation and one that does not.
:::

### 2.6 The ingress

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

This is what puts the hub on the public internet, and it goes in from the start
— no second deploy to expose it. The hostname has to be globally unique, which
is why the setup step substituted `<username>` for you. `ingressClassName:
haproxy` hands routing to the cluster's HAProxy controller, and the `tls` block
makes cert-manager request a Let's Encrypt certificate for that name — no
certificate files for you to manage.

### The whole file

Those are the blocks worth explaining; the rest is node affinity, image
pre-pullers and scheduler settings you can leave alone. Read it end to end in
the workspace at `yamls/jhub-values.yaml`, or
[on GitHub](https://github.com/nrp-nautilus/nrp-training/blob/materials/hidsi/workspace/yamls/jhub-values.yaml).

## 3. Deploy

### First — what is already running in your namespace?

JupyterHub can only be deployed **once per namespace**: a second release fights
the first over the `proxy-public` service and the hub database. Your claimed
slot should be empty, but check before you install.

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

An empty `helm list` and no pods means you are clear — deploy.

If a release *is* listed, look at the `NAME` column. Tear it down only if it is
yours; in a shared namespace someone else's class may be running on it.

<details>
<summary>Clear an existing JupyterHub</summary>

```bash
OLD_RELEASE=changeme   # ✏️ the NAME shown by `helm list` above

helm uninstall "$OLD_RELEASE" -n $NRP_NAMESPACE
kubectl wait --for=delete pod -l app=jupyterhub -n $NRP_NAMESPACE --timeout=120s 2>/dev/null || true
helm list -n $NRP_NAMESPACE
kubectl get pods -n $NRP_NAMESPACE
```

`helm uninstall` leaves PVCs behind on purpose — the hub database and any user
home directories survive, so a reinstall picks them back up. [Section
6](#6-cleanup) shows how to delete those too.
</details>

### Install the chart

```bash
# mint a proxy secret token — only replaces the placeholder, so re-runs keep the same token
if grep -q "'secret_token'" my-yamls/jhub-values.yaml; then
  sed -i "s|secretToken: .*|secretToken: '$(openssl rand -hex 32)'|" my-yamls/jhub-values.yaml
fi

helm upgrade --cleanup-on-fail --install $NRP_RELEASE jupyterhub/jupyterhub \
  --namespace $NRP_NAMESPACE \
  --values my-yamls/jhub-values.yaml \
  --wait \
  --timeout=10m
```

<details>
<summary>Expected output</summary>

```text
Release "jhub-nautilus" does not exist. Installing it now.
NAME: jhub-nautilus
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

```bash
kubectl get ingress -n $NRP_NAMESPACE
```

You should see the **hub** pod (auth, sessions, spawning), the **proxy** pod
(routing), a `hub-db-dir` PVC, an ingress carrying your hostname — and, once
someone logs in, per-user pods and `claim-<user>` PVCs.

### Log in

After ~a minute for HAProxy and Let's Encrypt, open
`https://jhub-$NRP_USER.nrp-nautilus.io`, log in as `admin` with the Dummy
password (`training123`), and spawn a server. `admin2` is a second account on
the same password — you will need it in 5.3. **You now have a working
multi-user JupyterHub on national research infrastructure.**

![JupyterHub spawn page](images/jhub-1.png)

## 4. Operating your hub

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

Check your work at any point:

```bash
bash check.sh 3
```

::: callout A good place to stop
That is a complete, working, publicly reachable JupyterHub — if this is as far
as you need to go today, tear it down in [6. Cleanup](#6-cleanup) so the
namespace is left clean.

Staying on? Section 5 turns it into *your* hub: an image menu, per-profile
sizes, a folder the whole class shares. Nothing below is required for the hub
you already have.
:::

## 5. Make it yours

Your hub is running, so every change below is one you can make right now. They
all follow the same pattern: write a small **overlay** file holding just the
change, then hand Helm both files.

```bash
helm upgrade $NRP_RELEASE jupyterhub/jupyterhub \
  --namespace $NRP_NAMESPACE \
  --values my-yamls/jhub-values.yaml \
  --values my-yamls/<overlay>.yaml \
  --wait --timeout=10m
```

::: callout Overlays — the tool you will still be using next semester
`--values` can be passed as many times as you like. Helm **merges** the files
rather than replacing one with the next, so the second file is not a
replacement for the first — it is a patch on top of it:

| In the base file | In the overlay | Result |
|---|---|---|
| `cull.timeout: 3600` | *not mentioned* | kept |
| `singleuser.image` | `singleuser.image` | the overlay's value wins |
| `profileList` — 15 entries | `profileList` — 2 entries | **replaced, not appended** |

Maps merge key by key, at any depth: an overlay that sets one field inside
`singleuser.storage` leaves the rest of `singleuser` alone. Lists are the
exception — they replace wholesale, which is why an overlay's `profileList`
becomes the entire menu rather than a longer one. Order matters, so the overlay
goes last.

This is worth keeping past today. Your base file is the hub you agreed to run,
and it stays in version control untouched; each change is a small file that
reads as a diff of one decision — a GPU profile for the deep-learning unit,
this term's dataset mounted, a longer cull timeout during finals week. Rolling
one back is deleting a flag rather than editing YAML under pressure, and
stacking several is just more `--values`.

When you come back to a hub months later and cannot remember what it is
actually running with, ask it:

```bash
helm get values $NRP_RELEASE -n $NRP_NAMESPACE      # what you supplied
helm get values $NRP_RELEASE -n $NRP_NAMESPACE -a   # everything, chart defaults included
```
:::

One thing to know before you start: **each command below layers only its own
overlay**, so it undoes the previous experiment. Pass several `--values` flags
to stack them.

### 5.1 Multiple image profiles

The file already ships with fifteen profiles. Replace them with a shorter menu —
this is the `singleuser.profileList` from [2.4](#2-4-the-single-user-servers):

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

**Try it:**

```bash
cat > my-yamls/overlay-profiles.yaml <<'EOF'
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
EOF

helm upgrade $NRP_RELEASE jupyterhub/jupyterhub \
  --namespace $NRP_NAMESPACE \
  --values my-yamls/jhub-values.yaml \
  --values my-yamls/overlay-profiles.yaml \
  --wait --timeout=10m
```

Reload the spawn page — the menu is four entries now. A server that is already
running keeps its old image until you stop and restart it.

### 5.2 Per-profile resource limits

Each entry's `kubespawner_override` can set size as well as image, which is how
one hub serves an intro unit and a deep-learning unit at once:

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

**Try it:**

```bash
cat > my-yamls/overlay-sizes.yaml <<'EOF'
singleuser:
  profileList:
  - display_name: Small (2 CPU, 4GB RAM)
    default: True
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
EOF

helm upgrade $NRP_RELEASE jupyterhub/jupyterhub \
  --namespace $NRP_NAMESPACE \
  --values my-yamls/jhub-values.yaml \
  --values my-yamls/overlay-sizes.yaml \
  --wait --timeout=10m
```

Reload the spawn page and pick **Small** — then check what the pod actually got:

```bash
kubectl get pod -n $NRP_NAMESPACE -l app=jupyterhub,component=singleuser-server \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].resources}{"\n"}{end}'
```

A GPU profile adds `extra_resource_limits: {"nvidia.com/gpu": "1"}`.

![JupyterHub profile menu](images/jhub-2.png)

**This is where a course gets shaped.** Give the intro unit a Small CPU profile
and the deep-learning unit a GPU profile, and students pick the right one from a
dropdown instead of you managing machines — or fielding "how much memory should
I ask for?" forty times.

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

This one needs a volume to mount, so create the claim first. `rook-cephfs` is
the RWX class — `rook-ceph-block-east`, which your home directories use, only
attaches to one pod at a time and would fail the moment a second student
spawned.

**Try it:**

```bash
kubectl apply -n $NRP_NAMESPACE -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jupyterhub-shared-volume
spec:
  storageClassName: rook-cephfs
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 5Gi
EOF

kubectl get pvc jupyterhub-shared-volume -n $NRP_NAMESPACE

cat > my-yamls/overlay-shared.yaml <<'EOF'
singleuser:
  storage:
    extraVolumes:
      - name: jupyterhub-shared
        persistentVolumeClaim:
          claimName: jupyterhub-shared-volume
    extraVolumeMounts:
      - name: jupyterhub-shared
        mountPath: /home/shared
EOF

helm upgrade $NRP_RELEASE jupyterhub/jupyterhub \
  --namespace $NRP_NAMESPACE \
  --values my-yamls/jhub-values.yaml \
  --values my-yamls/overlay-shared.yaml \
  --wait --timeout=10m
```

Stop and restart your server from the hub's control panel — a mount only
appears in a pod that starts with it — and `/home/shared` is there in the file
browser.

**Now prove it is actually shared.** One browser session is one logged-in user,
so being two people at once needs a second session:

1. As `admin`, open a terminal in your hub (**File ▸ New ▸ Terminal**) and drop
   a file in:

   ```bash
   echo "hello from admin" > /home/shared/hello.txt
   ```

2. Open a **private/incognito window** on the same
   `https://jhub-$NRP_USER.nrp-nautilus.io`, and log in as **`admin2`** with the
   same password. Spawn a server.

3. `admin2` gets its *own* empty home directory — but `/home/shared/hello.txt`
   is right there, and editing it from either account shows up in the other.

That is the classroom pattern in miniature: private homes, one common folder.
Instructors drop datasets and notebooks in once; every student sees them
instantly. Mount it read-only for students in production.

### 5.4 Real authentication

For production, replace the Dummy authenticator with institutional login:
campus credentials, no passwords to distribute, and a list of who is allowed in
that you control. `yamls/cilogon-jupyterhub-config.yaml` in the workspace is a
working `CILogonOAuthenticator` config; what changes between a departmental hub
and a locked-down course hub is only *which allow rule you write*.

This is the one change on this page you cannot try right now — it needs a
`client_id` and `client_secret` that CILogon issues by hand, and that wait is
the reason today's hub uses the Dummy authenticator at all. The patterns below
are what you will write once those arrive.

::: important Look your entity ID up — do not guess it
The key under `allowed_idps` is your identity provider's **entity ID**, and the
format varies a lot from campus to campus. Real ones:

```text
https://shib.unl.edu/idp/shibboleth            # Nebraska
https://idpz.utorauth.utoronto.ca/shibboleth   # Toronto — not "shib.utoronto.ca"
http://google.com/accounts/o8/id               # Google — http, and no hostname you would guess
https://github.com/login/oauth/authorize       # GitHub
```

There is no pattern to derive yours from — look it up in the
**[CILogon IdP list](https://cilogon.org/idplist/)** and paste it exactly. A
key that does not match an entity ID CILogon knows simply never matches a
login, and nobody gets in.
:::

#### Everyone at one campus

Name your institution's identity provider and let any address on its domain in:

```yaml
hub:
  config:
    JupyterHub:
      authenticator_class: cilogon
    CILogonOAuthenticator:
      client_id: <OIDC client>
      client_secret: <OIDC secret>
      oauth_callback_url: https://<your-name>.nrp-nautilus.io/hub/oauth_callback
      admin_users:
      - you@your-institution.edu
      # IDP Lookup: https://cilogon.org/idplist/
      allowed_idps:
        https://shib.your-institution.edu/idp/shibboleth:
          allowed_domains:
          - your-institution.edu
          username_derivation:
            username_claim: email
```

Good for a lab or departmental hub. `allowed_domains` takes shell-style
wildcards, so `"*.your-institution.edu"` picks up `cs.your-institution.edu` and
friends.

#### A class roster

Drop `allowed_domains` and name the people instead — the enrollment list *is*
the config. Campus login still gates the door; the roster decides who gets
through it:

```yaml
    CILogonOAuthenticator:
      # …client_id, client_secret, oauth_callback_url as above…
      # IDP Lookup: https://cilogon.org/idplist/
      allowed_idps:
        https://shib.your-institution.edu/idp/shibboleth:
          username_derivation:
            username_claim: email
      admin_users:
      - you@your-institution.edu
      - your-ta@your-institution.edu
      allowed_users:
      - student1@your-institution.edu
      - student2@your-institution.edu
      - student3@your-institution.edu
```

Students who drop the course lose access the next time you `helm upgrade`.
Admins are allowed implicitly — you do not repeat them in `allowed_users`.

#### Both at once

Allow rules are **additive**: a user gets in if *any* rule admits them. So a
course open to your campus plus a handful of outside collaborators is both
rules together —

```yaml
      # IDP Lookup: https://cilogon.org/idplist/
      allowed_idps:
        https://shib.your-institution.edu/idp/shibboleth:
          allowed_domains:
          - your-institution.edu          # anyone on campus…
          username_derivation:
            username_claim: email
      allowed_users:
      - collaborator@other-university.edu # …plus these specific people
      blocked_users:
      - former-student@your-institution.edu
```

`blocked_users` wins over every allow rule, which is how you remove one person
without rewriting the roster.

::: callout Notice
**Usernames are whatever claim you pick.** `username_claim: email` makes the
JupyterHub username `jdoe@your-institution.edu`, and that is the string your
`allowed_users` entries and per-user PVC names must match. Adding
`action: strip_idp_domain` with `domain: your-institution.edu` under
`username_derivation` gives you a plain `jdoe` instead.

**`allowed_idps` was renamed `idps`** in oauthenticator 17.4. NRP's example
file — and the snippets above, which follow it — still use `allowed_idps`; it
is accepted as an alias and logs a deprecation warning, so prefer `idps` on a
hub you are building fresh.
:::

### Putting it back

Drop the overlay flags and your hub returns to the base file:

```bash
helm upgrade $NRP_RELEASE jupyterhub/jupyterhub \
  --namespace $NRP_NAMESPACE \
  --values my-yamls/jhub-values.yaml \
  --wait --timeout=10m
```

## 6. Cleanup

If this was a trial run, uninstall your Helm release so the cluster is left
clean:

```bash
helm uninstall $NRP_RELEASE -n $NRP_NAMESPACE
```

User PVCs are kept by default; delete them only if you are sure:

```bash
kubectl delete pvc -n $NRP_NAMESPACE -l app=jupyterhub,component=singleuser-storage
```

`helm uninstall` does not touch the shared volume either, because nothing in the
release owns it — if you created it in [5.3](#5-3-shared-storage-for-the-whole-class),
it is still there:

```bash
kubectl delete pvc jupyterhub-shared-volume -n $NRP_NAMESPACE --ignore-not-found
```

If this is a real course hub, leave it running — the `cull` settings close idle
student sessions automatically.

## 7. Deploying your own hub at NRP

Today's hub was built to fit a workshop: Dummy auth, a throwaway namespace, a
chart version left floating. A hub you actually run for a course differs in a
handful of specific places, and NRP documents the whole path:

> 📘 [Deploy JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/)
> · [the full example values file](https://nrp.ai/documentation/userdocs/jupyter/values/)

### The minimum that has to change

**1. Register an OAuth client with CILogon** at
[cilogon.org/oauth2/register](https://cilogon.org/oauth2/register). Pick your
hostname *first* — it is baked into the callback URL:

| Field | Value |
|---|---|
| Callback URL | `https://<your-name>.nrp-nautilus.io/hub/oauth_callback` |
| Client type | Confidential |
| Scopes | `org.cilogon.userinfo,openid,profile,email` |
| Refresh tokens | No |

They review registrations by hand and email you a client ID and secret — days,
sometimes more than a week. **Start this before anything else.**

**2. Set six fields in your values file.** `yamls/cilogon-jupyterhub-config.yaml`
in your workspace is a working copy of NRP's example; these are the parts only
you can fill in:

```yaml
hub:
  config:
    CILogonOAuthenticator:
      client_id: <OIDC client>                  # from CILogon
      client_secret: <OIDC secret>              # from CILogon
      oauth_callback_url: https://<your-name>.nrp-nautilus.io/hub/oauth_callback
      admin_users:
      - you@your-institution.edu
    JupyterHub:
      authenticator_class: cilogon              # not dummy
proxy:
  secretToken: '<openssl rand -hex 32>'
httpRoute:
  enabled: true
  hostnames:
    - <your-name>.nrp-nautilus.io
  gateway:
    name: ingress
    namespace: haproxy
```

`httpRoute` is the Gateway API route NRP uses now; the `ingress` block you
deployed with today still works but is marked for deprecation in NRP's own
example, so new hubs should prefer `httpRoute`.

::: danger Do not leave the door open
Our workshop hub has `allowed_users: set()` — an empty allowlist that lets
**anyone** sign in. That is fine for a namespace that lives 40 minutes; on a
public hostname with real login it is how your namespace gets locked. A real
hub narrows access with `allowed_idps` (your institution's identity provider,
from the [CILogon IdP list](https://cilogon.org/idplist/)) or an explicit
`allowed_users` list — which, for a course, is your enrollment roster.

`cull` is not optional either: deploying without it is against cluster policy,
and `timeout` may not exceed 21600 (6 hours).
:::

**3. Install it the same way you did today** — same chart, your values file, a
namespace you are admin of:

```bash
helm upgrade --cleanup-on-fail --install jhub jupyterhub/jupyterhub \
  --namespace <your-namespace> \
  --values config.yaml
```

Pin `--version` once you are in production so a chart release never changes the
hub underneath your students mid-semester — the same reasoning as pinning image
tags in [section 8](#8-building-custom-course-images-in-nrp-gitlab).

Everything else on this page — profiles, resource limits, shared storage,
culling, custom images — is identical whether the hub is yours or a workshop's.

## 8. Building custom course images in NRP GitLab

> This is the take-home section — if the workshop ran out of time, it is the
> part to read afterwards. Nothing earlier on this page depends on it.

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

**Best practices for a course:** tag with commit SHAs (not just `latest`) so the
environment never changes under your students mid-semester; use `--cache=true`
for fast rebuilds; keep credentials in CI variables, never in the Dockerfile.

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
> Dummy auth is a workshop convenience. The workspace's `cilogon-jupyterhub-config.yaml` shows the production pattern: institutional login, allowlists, no passwords to distribute. Start the CILogon registration weeks before the term.

3. Why tag course images with commit SHAs instead of only `latest`?
- [x] So the environment never changes underneath students mid-semester
- [ ] Because `latest` images pull more slowly
- [ ] Because GitLab requires unique tags
> `latest` moves every time CI runs. Pinning profiles to a SHA means the same image all semester — reproducibility is the whole reason you built a custom image.

4. You edited `jhub-values.yaml` to add an image profile. How do the changes reach your running hub?
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
- **Start the CILogon registration** if a real course hub is in your plans — it
  is the longest-lead item in this entire workshop.
- **Docs:** [nrp.ai/documentation](https://nrp.ai/documentation/)
- **Live help:** the NRP Matrix channel at [nrp.ai/contact](https://nrp.ai/contact/)
- **These materials:** [training.nrp-nautilus.io](https://training.nrp-nautilus.io/)
  and [GitHub](https://github.com/nrp-nautilus/nrp-training)

::: callout Questions?
Open Q&A — your own course, GPU and allocation policy, Qualcomm access,
migrating an existing class onto NRP. Ask away.
:::
