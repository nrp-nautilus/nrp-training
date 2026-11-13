# Workspace: Prototype National Research Platform Classroom

Files for the live demo, a JupyterHub for a course. See the lessons at
<https://training.nrp-nautilus.io/nairr-classroom/>.

| Path | What it is |
|---|---|
| `notebooks/2_custom_jupyterhub.ipynb` | The demo, on the **Bash** kernel: steps 1–6 are the 15-minute live path, then "After the webinar" |
| `yamls/jhub-values.yaml` | The whole hub: who logs in, the image menu, home folders, idle shutdown, the address |
| `yamls/course-menu.yaml` | A change for step 6: a three-entry course menu, one entry with a GPU |
| `yamls/shared-volume.yaml`, `yamls/shared-folder.yaml` | After the webinar: a folder the whole class shares |
| `yamls/cilogon-jupyterhub-config.yaml` | After the webinar: campus logins through CILogon, for a real course |
| `check.sh` | Checks your hub: `bash check.sh 1` (access), `bash check.sh 2 $NS` (the hub in your namespace) |

The notebook's cells share one shell, so `NS`, set in step 1 from the training namespace pool, is there in every
later cell. On the training JupyterHub, `kubectl` and `helm` are ready to use; elsewhere you need them, the
`kubelogin` plugin, your Nautilus kubeconfig, and a namespace you're an admin of (`NS=my-course`).

The install pipes the values file through `sed` to put your namespace into the web address
(`jhub-<namespace>.nrp-nautilus.io`), and Helm reads it with `-f -`. The chart version is pinned (`--version 4.4.5`).
