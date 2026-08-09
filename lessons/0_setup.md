---
title: Setup
wide: true
---

## Prerequisites for NRP Training

Before attending the training session, please ensure you have completed the following setup steps.

## Two ways to follow along

There are two ways to run the hands-on exercises in this training:

1. **NRP USCMS Analysis Hub (recommended).** A JupyterHub-based environment with
   the training materials, `kubectl`, and `kubelogin` already installed — nothing
   to set up on your laptop ahead of time. It still needs one login step done at
   the start of the session (see below). This is also the only path that works
   for the whole training: the later CMS Data Access lesson uses hub-only tools
   (`grid-cert-import`, `grid-proxy-init`) with no local equivalent, so anyone on
   their own machine ends up switching over for that lesson anyway.
2. **Your own machine (alternative).** You run `kubectl` locally against the
   Nautilus cluster. This only works if you've completed the setup steps below
   **before** the session — `kubectl`, `kubelogin`, and your kubeconfig all need
   to be installed and verified in advance. Useful if you prefer working in your
   own local environment, but see the caveats in that section below before
   committing to it.

Everything past this setup page — namespaces, `kubectl` commands, YAML manifests —
is identical either way.

Jump to: [NRP USCMS Analysis Hub (recommended)](#method-1-nrp-uscms-analysis-hub-recommended) ·
[Your own machine (alternative)](#method-2-your-own-machine-alternative)

### 1. NRP Access Requirements

**Institutional Account Access**
- You must have an institutional account with NRP access via Authentik
    - You can use CERN account or institutional account, but choose one and stick with it 
- NRP access is available to users from US academic institutions or those collaborating with US institutions
- If you don't have access, see [Getting Started with NRP](https://nrp.ai/documentation/userdocs/start/getting-started/)

**Namespace Membership**
- You must be part of at least one namespace to participate in the training
- Check your namespaces at: [https://nrp.ai/namespaces/](https://nrp.ai/namespaces/)
- **Students**: Contact your research supervisor to be added to their namespace
- **Faculty/Researchers**: Request namespace admin status in [Matrix](https://nrp.ai/contact/)

::: Important
   We are using the namespace `us-cms` 

   Ask Daniel or Martin to add you if you have not been added already
:::

## Method 1: NRP USCMS Analysis Hub (recommended)

You still need the account and namespace access from
[NRP Access Requirements](#1-nrp-access-requirements) above — this method just
skips installing anything on your laptop. `kubectl` and `kubelogin` are
already installed on the hub image; you only need to point `kubectl` at the
cluster and log in once per session.

::: callout Launch the workspace in JupyterHub
**[▶ Launch the workspace on the NRP USCMS Analysis Hub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats&targetpath=cms-hats&urlpath=lab%2Ftree%2Fcms-hats%2Fworkspace)** — signs you in at [uscms-af.nrp-nautilus.io](https://uscms-af.nrp-nautilus.io), pulls the tutorial workspace, and opens JupyterLab.
:::

### Get kubectl working in the hub terminal

Open a terminal in JupyterLab (**File → New → Terminal**) and run:

```bash
grid-kube-setup
```

This fetches a fresh kubeconfig from `https://nrp.ai/config` and installs it at
`~/.kube/config` (backing up anything already there). It doesn't log you in by
itself — the next `kubectl` command you run triggers a device-code login:

```bash
kubectl get pods -n us-cms
```

`kubelogin` prints a URL and a short code. Open the URL **on your laptop**,
enter the code, and the hub terminal picks up the token automatically —
nothing more to click on the hub side.

<details>
<summary>Expected output</summary>

```text
jovyan@jupyter-...:~$ grid-kube-setup
Fetching   https://nrp.ai/config
user 'oidc':
    + --grant-type=device-code
    + --skip-open-browser

Backed up  /home/jovyan/.kube/config.xxxxxxxxxxx.bak
Updated    /home/jovyan/.kube/config

Next: run any kubectl command to trigger the login, e.g.

  kubectl get pods

kubelogin will print a URL and a code. Open the URL on your laptop, enter the
code, and this terminal will pick up the token.

jovyan@jupyter-...:~$ kubectl get pods -n us-cms
Please visit the following URL in your browser: https://authentik.nrp-nautilus.io/device?code=XXXXXXXXX
NAME                      READY   STATUS    RESTARTS   AGE
mlflow-667f8c984c-thzsr   2/2     Running   0          2d22h
mlflow-postgres-0         1/1     Running   0          10d
```
</details>

The login lasts for the rest of your hub session — you don't need to repeat
this for every new terminal, only after `grid-kube-setup` re-installs the
kubeconfig or your token expires.

[Kubernetes Basics](2_kubernetes_basics.html), the first hands-on lesson,
starts with a one-time callout covering the rest of the hub setup (grid
certificate, proxy, username) — do that once and the rest of the training
just works.

## Method 2: Your own machine (alternative)

Complete these steps **before** the session — they can't be done live.

::: important
**You'll still need the Analysis Hub for the last lesson.** [CMS Data Access
on NRP](5_cms_data.html) uses `grid-cert-import` and `grid-proxy-init`, tools
built into the Analysis Hub's image with no local install path. If you use
your own machine for the rest of the training, plan to switch to the Analysis
Hub for that lesson.

Also watch out for `~`: it means a different directory in each place. On
your own machine it's your local home directory; in the Analysis Hub's
JupyterLab terminal it's `/home/jovyan`. A command like `cd ~/cms-hats/workspace`
lands somewhere different depending on which terminal you're actually typing
it into — don't copy a command you ran in one context straight into the
other without checking where it actually points.
:::

::: callout tl;dr
Get an NRP account and namespace access → install `kubectl` → install
`kubelogin` → download your kubeconfig from [nrp.ai/config](https://nrp.ai/config) → verify with `kubectl get nodes`.
The sections below walk through each step in detail.
:::

<div class="details-group" data-details-group>
<button type="button" data-expand-all>Expand all</button>

<details>
<summary><strong>1. Install kubectl</strong></summary>

The Kubernetes command-line tool, `kubectl`, is required for the training exercises.

#### Linux

Download and install:

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

#### macOS

Using Homebrew:

```bash
brew install kubectl
```

Or download directly:

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

#### Windows

Download from: [https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/](https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/)

</details>

<details>
<summary><strong>2. Install kubelogin Plugin</strong></summary>

::: danger[Required]
You **must** install the `kubelogin` plugin, or your kubeconfig file **will not work**.
:::

#### macOS

```bash
brew install kubelogin
```

#### Linux/Windows

Download from: [https://github.com/int128/kubelogin?tab=readme-ov-file#setup](https://github.com/int128/kubelogin?tab=readme-ov-file#setup)

</details>

<details>
<summary><strong>3. Download Kubernetes Config File</strong></summary>

1. Download the config file from: [https://nrp.ai/config](https://nrp.ai/config)
2. Save it as `config` (without any extension) in your `~/.kube` folder
3. If the folder doesn't exist, create it:

```bash
mkdir ~/.kube
```

4. The final path should be: `~/.kube/config`

</details>

<details>
<summary><strong>4. Cross-Platform kubelogin Fixes</strong></summary>

If you run into authentication issues with `kubelogin`, try these fixes:

**Keyring errors** (e.g., `/run/user/1000/bus` not found):
- Add `--token-cache-storage=disk` to store tokens on disk instead of Linux keyring

**Browser issues** (won't launch or opens incorrectly):
- Add `--browser-command="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"` (Windows WSL: points to Windows Chrome)

**Port binding errors** (`port 8000 already in use`):
- Add `--listen-port=18000` (change to any unused port)

**No local browser available** (remote console):
- Add `--grant-type=device-code --skip-open-browser`

Example config snippet:

```yaml
args:
  - oidc-login
  - get-token
  - --browser-command="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
  - --listen-port=18000
  - --token-cache-storage=disk
```

</details>

<details>
<summary><strong>5. Verify Installation</strong></summary>

1. **Check kubectl context**:

```bash
kubectl config get-contexts
```

You should see `nautilus` in the list. If you have multiple contexts, set it:

```bash
kubectl config use-context nautilus
```

2. **Test authentication**:

```bash
kubectl get nodes
```

This will open a browser window for authentication via CiLogon.

3. **Verify namespace access**:

```bash
kubectl get pods -n <YOUR_NAMESPACE>
```

If you see "No resources found", that's okay - it means you have access but there are no pods yet.

4. **Set default namespace** (optional):

```bash
kubectl config set-context nautilus --namespace <YOUR_NAMESPACE>
```

</details>

<details>
<summary><strong>6. Clone the training materials</strong></summary>

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

</details>

</div>

### CLI Tools

Below are two tools which reduce the amount of kubernetes commands you need to type out.

- [k9s](https://k9scli.io): A console-like CLI tool 
- [Lens](https://k8slens.dev/): More of a GUI CLI tool

These are not required. All parts of the tutorial and using Kubernetes in general can be done via the command line, however these tools make things easier. If you wish to use these PLEASE INSTALL PRIOR TO THE EXERCISE.

## Getting Help

If you encounter issues during setup:

- **Support Chat**: [Join NRP's Support Chat](https://nrp.ai/contact/) for community support
- **Email**: [usersupport@nrp-nautilus.io](mailto:usersupport@nrp-nautilus.io)
- **Documentation**: [NRP Getting Started Guide](https://nrp.ai/documentation/userdocs/start/getting-started/)

## Additional Resources

- [NRP Portal](https://nrp.ai)
- [NRP Documentation](https://nrp.ai/documentation/)
- [Namespace Management](https://nrp.ai/namespaces/) 
