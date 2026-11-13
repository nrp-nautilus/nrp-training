---
title: Deploy a JupyterHub for Your Course
teaching: 15
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

**Time:** about 15 minutes.

The live path is steps **1–6** (marked ▶). **After the webinar** has the rest: sizes and GPUs per menu entry, a
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

![One values file stands in for thirteen Kubernetes objects](images/helm-values-funnel.png)

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

## ▶ 5. Change it: a course menu (2 min)

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

## ▶ 6. Clean up (1 min)

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
step 5: a small file with just the change, applied with `helm upgrade ... --reuse-values -f <file>`. Stack several
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
