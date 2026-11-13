---
title: Deploy a JupyterHub for Your Course
teaching: 20
exercises: 0
questions:
  - What does it take to run a JupyterHub for my own course on NRP?
  - What can I control as the instructor?
  - What changes before a real course goes live?
objectives:
  - Watch a course hub go up from one values file with Helm, on a public HTTPS address.
  - Change the hub while it runs, with a small file applied by `helm upgrade`.
  - Know what to set up before the term: CILogon login, a course namespace, a course image.
keypoints:
  - The values file is the whole hub — who logs in, the menu of environments, home folders, idle shutdown, the address. Keep it in git.
  - Each change is a small file on top, applied with `helm upgrade --reuse-values -f <file>`.
  - Idle servers stop on their own, so CPUs and GPUs go back to the pool.
  - A real course hub logs students in through CILogon; register for it weeks ahead.
---

::: callout Open the notebook (optional)
**[▶ Open the notebook](https://jh-training.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fnairr-classroom&targetpath=nairr-classroom&urlpath=lab%2Ftree%2Fnairr-classroom%2Fworkspace%2Fnotebooks%2F2_custom_jupyterhub.ipynb)**

This part is a live demo: watch, or follow along on the training JupyterHub. There's nothing to set up beforehand,
and the notebook has every command below. We won't be able to stop and help individually in the hour, so if
something goes wrong, keep watching and try it again afterwards.
:::

**Time:** about 20 minutes.

The live path is steps **1–7** (marked ▶). **After the webinar** has the rest: sizes and GPUs per menu entry, a
folder the whole class shares, real campus logins, and how to take it home.

::: important This demo hub uses a shared password
To fit in the time, anyone who knows the password in the values file can log in. A hub for a real course logs
students in with their campus account through **CILogon**, and only the people on your list get in. That's the one
change to make before the term starts: see [C. Real logins with CILogon](#c-real-logins-with-cilogon).
:::

## ▶ 1. Get a namespace (1 min)

Everything you run on NRP lives in a **namespace**. For today, take one of the hundred training namespaces; you get
the same one back if you run it again:

```bash
NS=$(curl -s "http://nrp-claim.nrp-training.svc.cluster.local/claim?user=$JUPYTERHUB_USER")
echo $NS
```

```text
nrp-training-042
```

Not on the training hub? Use a namespace you're an admin of: `NS=my-course`.

## ▶ 2. One file holds every decision (3 min)

The [Zero to JupyterHub](https://z2jh.jupyter.org) Helm chart is the hub; `workspace/yamls/jhub-values.yaml` says
how yours behaves. The lines that matter:

```bash
grep -n -E "authenticator_class|admin_users|capacity|display_name|timeout:|hosts:" ../yamls/jhub-values.yaml
```

| Line | What it decides |
|---|---|
| `authenticator_class: dummy` | **Who logs in**: here anyone with the demo password; for a course, `cilogon` and your class list |
| `admin_users` | **Who runs the class**: admins see every student's server and can open it to help |
| `capacity: 5Gi` | **Each student's home folder**, kept between sessions |
| `display_name` | **The menu of environments** students pick from: Python, R, Julia, PyTorch, … |
| `timeout: 3600` | **Idle servers stop** after an hour, so the CPUs and GPUs go back to the pool |
| `hosts:` | **The web address**: `jhub-<namespace>.nrp-nautilus.io`, with HTTPS already set up |

Step 5 looks at each of these blocks closely, once you've seen the hub running.

## ▶ 3. Install it (3 min)

Tell Helm where the chart lives, then install it. `sed` puts your namespace into the web address and `-f -` hands
the result to Helm:

```bash
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update
sed "s/<namespace>/$NS/" ../yamls/jhub-values.yaml | helm install jhub jupyterhub/jupyterhub --version 4.4.5 -n $NS -f - --wait --timeout 10m
```

It takes about two minutes while the hub and its proxy start. Then see what Helm made: the **hub** (logins,
starting servers), the **proxy** (routes each student to their server), a small volume for the hub's database, and
the web address:

```bash
kubectl get pods,pvc,ingress -n $NS
```

## ▶ 4. Log in like a student (4 min)

```bash
echo https://jhub-$NS.nrp-nautilus.io
```

1. Open that address and log in as **`admin`**. The password is the `password:` line under `DummyAuthenticator` in
   the values file.
2. Pick **Scipy** from the menu and press **Start**. The first start on a node can take a minute or two while the
   image downloads.
3. JupyterLab opens: this is what a student sees.
4. **File ▸ Hub Control Panel ▸ Admin** lists every user and their server, with buttons to start, stop, or open a
   student's server to help them.

![The menu of environments on the spawn page](images/jhub-2.png)

Each student's server is a pod of its own, with its own home volume:

```bash
kubectl get pods,pvc -n $NS
```

## ▶ 5. A closer look: Helm and the values file (5 min)

Your hub is running and you've seen it from a student's side. Now look at what made it.

### 5.1 Helm in one paragraph

Helm is a package manager for Kubernetes: instead of writing every Deployment, Service and ConfigMap by hand, you
install a **chart** (a reusable bundle of templates) and tune it through a **values file**. The
[Zero to JupyterHub chart](https://z2jh.jupyter.org) packages the whole hub, proxy and spawner stack; your whole
deployment is one YAML file of values.

The values file looks long until you see what it stands in for. Its 173 lines render into **thirteen Kubernetes
objects**, about 1,400 lines of manifests:

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

And they all have to agree with each other. The hub's Deployment carries a checksum of the ConfigMap and the Secret,
so changing either restarts the hub instead of leaving it running on stale settings. The ServiceAccount needs a Role
that can create and delete pods and volumes: that is *how* the hub starts a student's server. `proxy-public` has to
route to the proxy, which has to route to the hub, which has to know its own public address.

Written by hand, changing the students' image means editing several files and rechecking every reference between
them. With the chart it's one line in one file, and `helm upgrade` works out what has to change, as you'll see in
step 6.

You can see all thirteen objects yourself; `helm get manifest` prints what Helm rendered for your hub:

```bash
helm get manifest jhub -n $NS | grep "^kind:" | sort | uniq -c
```

### 5.2 Who can log in

```yaml
hub:
  config:
    JupyterHub:
      authenticator_class: dummy
      admin_access: true
      admin_users: ["admin", "admin2"]
    DummyAuthenticator:
      password: "..."              # the demo password, in the file
    # Allow all users to sign in (for tutorial purposes)
    Authenticator:
      allowed_users: set()
```

`authenticator_class: dummy` accepts **any** username with the shared password, which is why this is a workshop hub
and not a course hub. `admin_users` get the admin page: other people's servers, the user list, a stop button. There
are two of them so you can be two people at once, which is handy for trying the shared folder in
[B](#b-a-folder-the-whole-class-shares). `allowed_users: set()` is an *empty* allow list, and empty here means "no
list: let everyone in".

That last line is the first thing to change for a course. With CILogon ([C](#c-real-logins-with-cilogon)) the allow
list stops being a formality and becomes your class list.

### 5.3 The hub

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

The hub keeps its state (users, running servers, API tokens) in SQLite on its own 1 GB volume, so restarting the hub
doesn't lose who is logged in. `rook-ceph-block-east` is NRP block storage; `ReadWriteOnce` is all a single database
pod needs.

### 5.4 The proxy

```yaml
proxy:
  # No secretToken here: the chart generates one at install and keeps it on upgrades.
  service:
    type: ClusterIP
```

Every request to a student's server goes through the proxy. The hub reprograms the proxy's routes with a shared
token, which the chart generates at install and keeps across upgrades, so there is nothing for you to set.
`ClusterIP` keeps the proxy inside the cluster; the web address ([5.7](#5-7-the-web-address)) is what faces the
internet.

### 5.5 The students' servers

Shortened to the decisions you'll actually change: the environment, the size and the home folder.

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
  storage:                              # a private home folder per student
    type: dynamic
    capacity: 5Gi
    homeMountPath: /home/jovyan
    dynamic:
      storageClass: rook-ceph-block-east
      pvcNameTemplate: claim-{username}{servername}
  defaultUrl: "/lab"
  profileList:                          # the menu on the start page
  - display_name: Scipy
    kubespawner_override:
      image_spec: quay.io/jupyter/scipy-notebook:2024-04-22
    default: True
```

**`image`** is the environment a server starts in: pin the tag, never `latest`. **`cpu`** and **`memory`** apply to
every server, and setting `guarantee` equal to `limit` sets the resources aside instead of overcommitting them.
**`storage: dynamic`** gives each student their own volume, named from `pvcNameTemplate` and mounted at
`homeMountPath`, so `/home/jovyan` survives logouts, restarts and idle shutdowns. **`profileList`** is the menu you
saw in step 4; each entry's `kubespawner_override` replaces the defaults above. The file ships with fifteen entries,
one of them shown here; step 6 cuts the menu to three.

### 5.6 Stopping idle servers

```yaml
cull:
  enabled: true
  timeout: 3600
  every: 600
```

Every 10 minutes (`every`) the culler shuts down servers idle for more than an hour (`timeout`). Home folders are
untouched, so a student logs back in and picks up where they left off.

::: callout Why culling isn't optional
A student who closes their laptop leaves a pod holding CPUs and memory. On shared national infrastructure that's the
fastest way to make your namespace unpopular, and for a class of 40 it's the difference between a hub that fits its
allocation and one that doesn't.
:::

### 5.7 The web address

```yaml
ingress:
  enabled: true
  ingressClassName: haproxy
  hosts: ["jhub-<namespace>.nrp-nautilus.io"]
  pathSuffix: ''
  tls:
    - hosts:
      - jhub-<namespace>.nrp-nautilus.io
```

This is what puts the hub on the public internet, and it's there from the start: no second step to expose it. The
name has to be unique, which is why the install command in step 3 put your namespace in for `<namespace>`.
`ingressClassName: haproxy` hands routing to the cluster's HAProxy ingress, and the `tls` block turns on HTTPS. Names
under `nrp-nautilus.io` use the cluster's wildcard certificate, so there are no certificate files for you to manage.

### The whole file

Those are the blocks worth explaining; the rest is node placement, image pre-pulling and scheduler settings you can
leave alone. Read it end to end in the workspace at `yamls/jhub-values.yaml`, or
[on GitHub](https://github.com/nrp-nautilus/nrp-training/blob/materials/nairr-classroom/workspace/yamls/jhub-values.yaml).

## ▶ 6. Change it: a course menu (2 min)

Fifteen environments is a lot for a class. `course-menu.yaml` replaces the menu with three, one of them with a GPU:

```yaml
singleuser:
  profileList:
  - display_name: "Python for data science"
    default: true
    kubespawner_override:
      image_spec: quay.io/jupyter/scipy-notebook:2024-04-22
  - display_name: "R and the tidyverse"
    kubespawner_override:
      image_spec: quay.io/jupyter/r-notebook:2024-04-22
  - display_name: "PyTorch with one GPU"
    kubespawner_override:
      image_spec: quay.io/jupyter/pytorch-notebook:cuda12-2024-04-22
      extra_resource_limits:
        nvidia.com/gpu: "1"
```

Apply just that change to the running hub. `--reuse-values` keeps everything you installed, and the new file goes
on top:

```bash
helm upgrade jhub jupyterhub/jupyterhub --version 4.4.5 -n $NS --reuse-values -f ../yamls/course-menu.yaml --wait
```

In the hub, **Stop My Server**, then **Start My Server**: the menu now has three entries. Running servers keep going
through an upgrade; a change to the menu shows up the next time a server starts. A student who picks the GPU entry
gets a GPU for that session and gives it back when the server stops or sits idle.

A list in the new file replaces the whole list, which is why the menu shrinks to three instead of growing to
eighteen. Settings that are maps merge key by key, so you can change one storage setting without restating the rest.

## ▶ 7. Clean up (1 min)

A real course hub stays up all term. Today's goes away:

```bash
helm uninstall jhub -n $NS
kubectl delete pods,pvc -n $NS -l app=jupyterhub
curl -s "http://nrp-claim.nrp-training.svc.cluster.local/release?user=$JUPYTERHUB_USER"
```

Helm leaves students' running servers and their home volumes behind on purpose, so a reinstall would find
everyone's files; the second line removes them. The last line gives the training namespace back (it's also released
on its own after six hours).

## After the webinar

Each of these changes a **running** hub, so install it again (step 3) first. They all follow the pattern from
step 6: a small file with just the change, applied with `helm upgrade ... --reuse-values -f <file>`. Stack several
by running them one after another; each upgrade keeps what came before.

### A. Sizes, and GPUs, per menu entry

Each menu entry can set its own CPU, memory and GPU, so one hub serves the intro unit and the deep-learning unit:

```yaml
singleuser:
  profileList:
  - display_name: "Small: 2 CPUs, 4 GB"
    default: true
    kubespawner_override:
      cpu_limit: 2
      cpu_guarantee: 2
      mem_limit: 4G
      mem_guarantee: 4G
  - display_name: "PyTorch with one GPU"
    kubespawner_override:
      image_spec: quay.io/jupyter/pytorch-notebook:cuda12-2024-04-22
      extra_resource_limits:
        nvidia.com/gpu: "1"
```

Check what a running server actually got:

```bash
kubectl describe pod -n $NS -l component=singleuser-server | grep -A 6 Limits
```

Students pick from a dropdown instead of you managing machines, or answering "how much memory should I ask for?"
forty times.

### B. A folder the whole class shares

Make one shared volume (CephFS, which many servers can mount at once), then mount it in every student's server:

```bash
kubectl apply -n $NS -f ../yamls/shared-volume.yaml
helm upgrade jhub jupyterhub/jupyterhub --version 4.4.5 -n $NS --reuse-values -f ../yamls/shared-folder.yaml --wait
```

Restart your server and `/home/shared` is there. Anything you put in it, every student sees; each student's home
folder stays private. To see it from two sides, open a private browser window, log in as `admin2` with the same
password, and look for a file you created as `admin`. For a real course, mount it read-only for students.

Helm didn't create the shared volume, so it doesn't remove it either:

```bash
kubectl delete -n $NS -f ../yamls/shared-volume.yaml
```

### C. Real logins with CILogon

For a course, students log in with their campus account, and only the people on your list get in. CILogon is an
independent service, not run by NRP: register an OAuth client at
[cilogon.org/oauth2/register](https://cilogon.org/oauth2/register), with the callback URL
`https://<your-hub>.nrp-nautilus.io/hub/oauth_callback`, client type *Confidential*, and the scopes
`org.cilogon.userinfo,openid,profile,email`. Registrations are reviewed by hand, so allow days to a week, and pick
the hub's address first, because it's part of the callback URL.

Then replace the `hub.config` block with the one in `workspace/yamls/cilogon-jupyterhub-config.yaml`:

```yaml
hub:
  config:
    JupyterHub:
      authenticator_class: cilogon
    CILogonOAuthenticator:
      client_id: <from CILogon>
      client_secret: <from CILogon>
      oauth_callback_url: https://<your-hub>.nrp-nautilus.io/hub/oauth_callback
      allowed_idps:
        https://shib.your-institution.edu/idp/shibboleth:
          username_derivation:
            username_claim: email
      admin_users:
      - you@your-institution.edu
      allowed_users:
      - student1@your-institution.edu
      - student2@your-institution.edu
```

::: important Look your campus up, don't guess
The key under `allowed_idps` is your identity provider's ID, and it varies from campus to campus. Find yours in the
**[CILogon IdP list](https://cilogon.org/idplist/)** and paste it exactly; a key CILogon doesn't recognize never
matches a login, and nobody gets in.
:::

`allowed_users` is your class roster: campus login opens the door, and the roster decides who gets through.
`allowed_domains` admits a whole campus, and `blocked_users` wins over both. Students who drop the course lose
access the next time you upgrade.

### D. Taking it home

- **A namespace for the course:** [nrp.ai/education](https://nrp.ai/education/) has the steps: send the NRP team
  the course, the number of students and the start date.
- **Keep the values file in git** and pin `--version`, so a new chart release never changes the hub under your
  students mid-term.
- **Your own course image:** build it from a `Dockerfile` in
  [NRP GitLab](https://nrp.ai/documentation/userdocs/development/gitlab/), tag it with the commit, and point a menu
  entry's `image_spec` at `gitlab-registry.nrp-nautilus.io/<group>/<project>:<tag>`.
- **Idle culling is required** on NRP, and `timeout` may not exceed 21600 (6 hours).
- **Leave `proxy.secretToken` out** of your values file: the chart makes one at install and keeps it on upgrades.
- **The whole path:** [Deploy JupyterHub](https://nrp.ai/documentation/userdocs/jupyter/jupyterhub/) ·
  [an example values file](https://nrp.ai/documentation/userdocs/jupyter/values/)

::: danger Don't leave the door open
The demo hub lets anyone with the shared password in. A real hub narrows access with `allowed_idps` and an
`allowed_users` roster; NRP's docs warn that leaving a public hub open can get the namespace locked.
:::

To run the same commands from your own laptop, you need `kubectl`, the `kubelogin` plugin, `helm` and your
[Nautilus kubeconfig](https://nrp.ai/config), and you must be an admin of the namespace. The check script also works
there: `bash ../check.sh 2 $NS`.

## Where to go next

- **Docs:** [nrp.ai/documentation](https://nrp.ai/documentation/)
- **Help:** the NRP chat at [nrp.ai/contact](https://nrp.ai/contact/), and the bi-weekly office hours
- **These materials:** [training.nrp-nautilus.io](https://training.nrp-nautilus.io/) and
  [GitHub](https://github.com/nrp-nautilus/nrp-training)
