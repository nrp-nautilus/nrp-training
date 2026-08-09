---
title: CMS Data Access on NRP
teaching: 15
exercises: 15
---

::: callout Open the runnable notebook for this episode
**[▶ Open notebook in JupyterHub](https://uscms-af.nrp-nautilus.io/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fnrp-nautilus%2Fnrp-training&branch=materials%2Fcms-hats&targetpath=cms-hats&urlpath=lab%2Ftree%2Fcms-hats%2Fworkspace%2Fnotebooks%2F5_cms_data.ipynb)** — most of the certificate setup is interactive terminal work (password prompts), so the notebook mostly points you to a terminal; the data-access steps at the end are runnable cells.
:::

**Time:** 00:00-00:30

This lesson uses the **NRP USCMS Analysis Hub**
([uscms-af.nrp-nautilus.io](https://uscms-af.nrp-nautilus.io)) — the
JupyterHub-based environment introduced as "Method 2" on the [setup
page](0_setup.html). CMS data lives on grid storage (EOS, dCache, and
friends) protected by the same CERN grid-certificate infrastructure used
across WLCG. `kubectl` (covered on the setup page via `grid-kube-setup`) gets
you onto the Nautilus cluster; a **grid certificate** and the short-lived
**X.509 proxy** derived from it are what get *you* into CMS data. This lesson
sets one up, then uses it to pull a real CMS file and make a plot.

## Setting up your grid certificate

You'll need your CERN grid certificate exported as a **`.p12`** file (from CERN's
certificate portal or your browser's certificate manager — this is the same
file you'd use to set up a browser certificate for CERN SSO).

### 1. Upload the `.p12` file

Drag your `.p12` file into the JupyterLab file browser on the left (or use the
**Upload** button). It only needs to live there for the import step below —
you can delete it from the file browser afterward.

### 2. Import the certificate

🖥️ **Terminal step** — open a terminal in JupyterLab and run:

```bash
grid-cert-import
```

You'll be asked for two things:

1. **The import password** — the one you chose when exporting the `.p12` file.
2. **A PEM pass phrase** — this protects the key at rest on the hub. You'll type
   it every time you create a proxy, so keeping it the same as the import
   password is fine and avoids confusion.

<details>
<summary>Expected output</summary>

```text
jovyan@jupyter-...:~$ grid-cert-import
Importing: /home/jovyan/myCertificate.p12
  existing usercert.pem -> usercert.pem.20260804150152.bak
  existing userkey.pem -> userkey.pem.20260804150152.bak

You will be asked for:
  1. the import password  -- the one you chose when exporting the .p12
  2. a PEM pass phrase    -- this protects the key at rest on NRP.
     You will type it every time you create a proxy. Keeping it the same
     as the import password is fine and avoids confusion.

Enter Import Password:
Enter Import Password:
Enter PEM pass phrase:
Verifying - Enter PEM pass phrase:

Installed:
  subject=DC=ch, DC=cern, OU=Organic Units, OU=Users, CN=ddiaz, CN=821822, CN=Daniel Diaz
  notBefore=Aug  4 05:43:37 2026 GMT
  notAfter=Sep  8 05:43:37 2027 GMT

Next:   grid-proxy-init
```
</details>

### 3. Create your proxy

🖥️ **Terminal step**:

```bash
grid-proxy-init
```

This prompts for the PEM pass phrase from the step above, contacts the CMS
VOMS server, and writes a short-lived proxy to `~/.globus/x509up`.

<details>
<summary>Expected output</summary>

```text
jovyan@jupyter-...:~$ grid-proxy-init
Enter GRID pass phrase for this identity:
Contacting  voms2-cms-auth.cern.ch:443 [/DC=ch/DC=cern/OU=computers/CN=voms2-cms-auth.cern.ch] "cms"...
Error contacting  voms-cms-auth.cern.ch:443 for VO cms: voms-cms-auth.cern.ch
Contacting  voms2-cms-auth.cern.ch:443 [/DC=ch/DC=cern/OU=computers/CN=cms-auth.cern.ch] "cms"...
Remote VOMS server contacted succesfully.

Created proxy in /home/jovyan/.globus/x509up.

Your proxy is valid until Wed Aug 12 15:02:24 UTC 2026

  /DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=ddiaz/CN=821822/CN=Daniel Diaz/CN=1734779629
  691198
  cms

Proxy written to /home/jovyan/.globus/x509up
To use it from pods in other namespaces:  grid-proxy-publish <namespace> [...]
```
</details>

A `voms2-...` server occasionally times out on the first attempt (as in the
transcript above) — `grid-proxy-init` retries automatically, so this is
expected and not a failure.

![Grid certificate import and proxy creation in a hub terminal](images/grid-cert.png)

### 4. Verify it

```bash
xrdcp root://cmsxrootd.fnal.gov//store/group/lpclonglived/B-ParkingLLPs/keep.txt .
```

If the copy succeeds, your proxy is good — `~/.globus/x509up` is the default
location `xrdcp` (and everything below) looks for a proxy, so you don't need
to set anything explicitly.

## Access CMS data with uproot

The `xrdcp` step above proved your proxy works. Now use it from Python:
pull down one real CMS NanoAOD-style file and plot something from it with
[uproot](https://uproot.readthedocs.io/).

Copy the file down with `xrdcp`, same as the verification step above:

```bash
xrdcp -f root://eoscms.cern.ch//eos/cms/store/group/cmst3/group/l1tr/maglowac/AD_HLT_PF/QCD_Bin-Pt-15to7000_TuneCP5_13p6TeV_pythia8/re-emul_Run3Winter25MiniAOD-FEVTOUTPUT_142X_v7-v1/251124_134438/0000/nanoout_1.root nanoout_1.root
```

Open it with uproot and histogram the jet transverse momenta. The hub image
isn't guaranteed to have the HEP Python stack installed, so this installs
anything missing into your user site-packages before importing it:

```bash
python3 <<'PY'
import importlib
import subprocess
import sys

for pkg in ("uproot", "awkward", "matplotlib"):
    if importlib.util.find_spec(pkg) is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--quiet", pkg], check=True)

import awkward as ak
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import uproot

events = uproot.open("nanoout_1.root")["Events"]
jet_pt = ak.flatten(events["Jet_pt"].array(entry_stop=5000))

plt.hist(jet_pt, bins=50, range=(0, 200))
plt.xlabel("Jet $p_T$ [GeV]")
plt.ylabel("Jets / bin")
plt.title(f"Jet $p_T$ spectrum ({len(jet_pt)} jets, first 5000 events)")
plt.savefig("jet_pt.png", dpi=150)
print(f"Wrote jet_pt.png from {len(jet_pt)} jets")
PY
```

Open `jet_pt.png` from the JupyterLab file browser on the left to see the
plot. `Events` is the standard NanoAOD tree name; `uproot.open(...).keys()`
lists every tree/branch in the file if you want to plot something else
(`Muon_pt`, `MET_pt`, and similar branches are also in this file).

## Sharing your proxy with another namespace

Your proxy lives at `~/.globus/x509up` on the hub, but Kubernetes Jobs run in a
namespace and can't reach your home directory directly. `grid-proxy-publish`
copies your proxy into a namespace as a Secret, so Jobs there can mount it and
use it the same way you just used it from the terminal:

```bash
grid-proxy-publish <namespace>
```

::: danger[Only publish to your own personal namespace]
**Never** run `grid-proxy-publish` against a shared or team namespace — only
your own personal one.

Any member of a namespace can read that namespace's Secrets. If you publish
your proxy to a shared namespace, every other member can use *your* proxy —
acting as you against CMS grid storage — without your knowledge. Since a grid
proxy is tied to your personal identity and the CERN Certificate Authority's
usage policy holds *you* responsible for whatever it's used for, sharing
access this way is a policy violation even if nothing goes wrong technically.

If a Job in a shared namespace needs grid data access, have the person who
runs that Job publish their **own** proxy there — don't publish yours on
their behalf.
:::

## Clean up

Proxies are short-lived by design (the transcript above expires in about a
week), so there's nothing to revoke. Remove the file you copied down:

```bash
rm -f nanoout_1.root
```

If you published a proxy to a namespace you don't want it in anymore, find
the Secret `grid-proxy-publish` created and delete it:

```bash
kubectl get secrets -n <namespace>
kubectl delete secret -n <namespace> <secret-name>
```
