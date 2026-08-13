# NAIRR AI Education Webinar Series — Prototype NRP Classroom

Workspace for the one-hour webinar. See the lessons at
<https://training.nrp-nautilus.io/nairr-webinar/>.

```
notebooks/2_custom_jupyterhub.ipynb   runnable version of the JupyterHub session (bash kernel)
yamls/jhub-values.yaml                Helm values for the z2jh chart
yamls/cilogon-jupyterhub-config.yaml  production CILogon/OIDC authenticator example
check.sh                              bash check.sh <section 1-2>
```

Set your namespace once before the JupyterHub section:

```bash
export NRP_NAMESPACE=<your-namespace>
export NRP_RELEASE=jhub-$USER
```
