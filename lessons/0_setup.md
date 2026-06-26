---
title: Setup
---

## Prerequisites for NRP Training

Before attending the training session, please ensure you have completed the following setup steps.

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

### 2. Install kubectl

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

### 3. Install kubelogin Plugin

::: danger[Required]
You **must** install the `kubelogin` plugin, or your kubeconfig file **will not work**.
:::

#### macOS

```bash
brew install kubelogin
```

#### Linux/Windows

Download from: [https://github.com/int128/kubelogin?tab=readme-ov-file#setup](https://github.com/int128/kubelogin?tab=readme-ov-file#setup)

### 4. Download Kubernetes Config File

1. Download the config file from: [https://nrp.ai/config](https://nrp.ai/config)
2. Save it as `config` (without any extension) in your `~/.kube` folder
3. If the folder doesn't exist, create it:

```bash
mkdir ~/.kube
```

4. The final path should be: `~/.kube/config`

### 5. Cross-Platform kubelogin Fixes

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

### 6. Verify Installation

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

### 7. CLI Tools

Below are two tools which reduce the amount of kubernetes commands you need to type out.

- [k9s](https://k9scli.io): A console-like CLI tool 
- [Lens](https://k8slens.dev/): More of a GUI CLI tool

These are not required. All parts of the tutorial and using Kubernetes in general can be done via the command line, however these tools make things easier. If you wish to use these PLEASE INSTALL PRIOR TO THE EXERCISE.

## 8. Getting Help

If you encounter issues during setup:

- **Support Chat**: [Join NRP's Support Chat](https://nrp.ai/contact/) for community support
- **Email**: usersupport@nrp-nautilus.io
- **Documentation**: [NRP Getting Started Guide](https://nrp.ai/documentation/userdocs/start/getting-started/)

## 9. Additional Resources

- [NRP Portal](https://nrp.ai)
- [NRP Documentation](https://nrp.ai/documentation/)
- [Namespace Management](https://nrp.ai/namespaces/) 
