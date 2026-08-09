import json
import os
import subprocess
from pathlib import Path

import uproot


REMOTE_FILE = (
    "root://eoscms.cern.ch//eos/cms/store/group/cmst3/group/l1tr/maglowac/"
    "AD_HLT_PF/QCD_Bin-Pt-15to7000_TuneCP5_13p6TeV_pythia8/"
    "re-emul_Run3Winter25MiniAOD-FEVTOUTPUT_142X_v7-v1/251124_134438/"
    "0000/nanoout_1.root"
)
LOCAL_FILE = Path(os.environ.get("LOCAL_ROOT_FILE", "/training/cms-data/nanoout_1.root"))
SUMMARY_FILE = Path(os.environ.get("SUMMARY_FILE", "/training/cms-data/cms_uproot_summary.json"))


def require_proxy() -> Path:
    proxy = os.environ.get("X509_USER_PROXY")
    if not proxy:
        raise RuntimeError("X509_USER_PROXY is not set")

    proxy_path = Path(proxy)
    if not proxy_path.exists():
        raise RuntimeError(f"X.509 proxy does not exist: {proxy_path}")

    print(f"X509_USER_PROXY={proxy_path}")
    print(f"Proxy size: {proxy_path.stat().st_size} bytes")
    return proxy_path


def copy_root_file() -> None:
    LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    print(f"Copying CMS ROOT file to {LOCAL_FILE}")
    subprocess.run(["xrdcp", "-f", REMOTE_FILE, str(LOCAL_FILE)], check=True)
    print(f"Local file size: {LOCAL_FILE.stat().st_size} bytes")


def inspect_root_file() -> dict:
    print("Opening file with uproot")
    root_file = uproot.open(LOCAL_FILE)
    keys = root_file.keys()
    classnames = root_file.classnames()
    tree_names = [
        name.split(";")[0]
        for name, class_name in classnames.items()
        if "TTree" in class_name
    ]
    if not tree_names:
        raise RuntimeError("No TTree found in the ROOT file")

    tree_name = "Events" if "Events" in tree_names else tree_names[0]
    events = root_file[tree_name]
    branch_names = list(events.keys())

    preferred = ["nMuon", "Muon_pt", "Muon_eta", "nJet", "Jet_pt", "Jet_eta", "MET_pt"]
    selected = [branch for branch in preferred if branch in branch_names]
    if not selected:
        selected = branch_names[:5]

    arrays = events.arrays(selected, entry_stop=10)
    print(f"ROOT keys: {keys[:10]}")
    print(f"Selected tree: {tree_name}")
    print(f"Entries: {events.num_entries}")
    print(f"First branches: {branch_names[:30]}")
    print(f"Selected branches: {selected}")
    print(arrays)

    return {
        "remote_file": REMOTE_FILE,
        "local_file": str(LOCAL_FILE),
        "root_keys": keys,
        "tree": tree_name,
        "entries": events.num_entries,
        "first_branches": branch_names[:30],
        "selected_branches": selected,
    }


def main() -> None:
    require_proxy()
    copy_root_file()
    summary = inspect_root_file()
    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote summary to {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
