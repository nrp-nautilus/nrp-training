# Cms Hats Workspace

Files attendees open or run during the training, launched via nbgitpuller on
the NRP USCMS Analysis Hub.

- `notebooks/` — the runnable Jupyter notebook for each lesson, plus
  `cms_uproot_example.ipynb` (opened inside the optional CMS-data Jupyter pod,
  not launched from the hub directly).
- `code/` — Dockerfiles and the Python scripts they package
  (`jet_class.py`, `analyze_jet_class.py`, `cms_uproot_example.py`).
- `yamls/` — Kubernetes manifests, Helm values, and related YAML files.
