# Cms Hats Workspace

Files attendees open or run during the training, launched via nbgitpuller on
the NRP USCMS Analysis Hub.

- `notebooks/` — the runnable Jupyter notebook for each lesson, plus two
  exploratory Python-kernel notebooks not yet numbered lessons or launched
  from the setup/lesson pages: `dask_hep_example.ipynb` and
  `jet_class_notebook.ipynb` (the jet classifier training/eval from lessons
  3-4, run inline instead of as a Kubernetes Job).
- `code/` — Dockerfiles and the Python scripts they package
  (`jet_class.py`, `analyze_jet_class.py`).
- `yamls/` — Kubernetes manifests, Helm values, and related YAML files.
