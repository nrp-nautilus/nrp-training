#!/usr/bin/env python3
"""Create a new training scaffold under trainings/.

Examples:
    python3 new_training.py my-training
    python3 new_training.py my-training --title "My Training" --length "2 hours"
    python3 new_training.py cms-hats --allow-existing
"""
import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_TRAININGS_DIR = ROOT / "trainings"


def slug_title(slug):
    return " ".join(part.capitalize() for part in re.split(r"[-_]+", slug) if part)


def validate_name(name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
        raise ValueError(
            "training name must start with a letter or number and contain only "
            "letters, numbers, hyphens, and underscores"
        )


def clean_scalar(value):
    return " ".join(str(value).split())


def config_template(args):
    title = clean_scalar(args.title or slug_title(args.name))
    subtitle = clean_scalar(args.subtitle)
    length = clean_scalar(args.length)
    materials_branch = clean_scalar(args.materials_branch or f"materials/{args.name}")
    published = "false" if args.unpublished else "true"
    subtitle_line = f"subtitle: {subtitle}\n" if subtitle else ""
    return f"""title: {title}
{subtitle_line}length: {length}
order: {args.order}
published: {published}
materials_branch: {materials_branch}
lessons:
  - 1_intro
"""


def lesson_template(title):
    return f"""---
title: Introduction
teaching: 10
exercises: 0
questions:
  - What will this training cover?
objectives:
  - Identify the goals and structure of {title}.
keypoints:
  - Replace this starter lesson with the training introduction.
---

## Overview

Add the learning context, prerequisites, and setup steps for this training here.

::: callout Workspace
Add JupyterHub, notebook, or command-line setup instructions here when they are ready.
:::
"""


def readme_template(title, name):
    return f"""# {title}

Training materials for `{name}`.

## Layout

- `config.yml` controls the training title, landing-page metadata, and lesson order.
- `lessons/` contains the lesson Markdown files.
- `workspace/` contains notebooks, scripts, and files for hands-on work.
- `workspace/yamls/` contains Kubernetes or Helm YAML files used by the training.
- `images/` contains screenshots and other lesson images.
"""


def workspace_readme_template(title):
    return f"""# {title} Workspace

Put files that attendees should open or run during the training here.

Use `yamls/` for Kubernetes manifests, Helm values, and related YAML files.
"""


def write_file(path, content, created, skipped):
    if path.exists():
        skipped.append(path)
        return
    path.write_text(content, encoding="utf-8")
    created.append(path)


def create_training(args):
    validate_name(args.name)

    trainings_dir = args.trainings_dir.resolve()
    target = trainings_dir / args.name
    title = clean_scalar(args.title or slug_title(args.name))

    if target.exists():
        if not target.is_dir():
            raise FileExistsError(f"{target} exists and is not a directory")
        has_content = any(target.iterdir())
        if has_content and not args.allow_existing:
            raise FileExistsError(
                f"{target} already exists and is not empty; rerun with "
                "--allow-existing to add only missing scaffold files"
            )

    created_dirs = []
    for directory in (
        target,
        target / "lessons",
        target / "workspace",
        target / "workspace" / "yamls",
        target / "images",
    ):
        if not directory.exists():
            directory.mkdir(parents=True)
            created_dirs.append(directory)

    created_files = []
    skipped_files = []
    write_file(target / "config.yml", config_template(args), created_files, skipped_files)
    write_file(target / "README.md", readme_template(title, args.name), created_files, skipped_files)
    write_file(
        target / "lessons" / "1_intro.md",
        lesson_template(title),
        created_files,
        skipped_files,
    )
    write_file(
        target / "workspace" / "README.md",
        workspace_readme_template(title),
        created_files,
        skipped_files,
    )
    write_file(target / "workspace" / "yamls" / ".gitkeep", "", created_files, skipped_files)
    write_file(target / "images" / ".gitkeep", "", created_files, skipped_files)

    return target, created_dirs, created_files, skipped_files


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Create a new training scaffold under trainings/<name>/."
    )
    parser.add_argument("name", help="directory name for the training, e.g. cra-rel")
    parser.add_argument("--title", help="training title; defaults to a title-cased name")
    parser.add_argument("--subtitle", default="", help="landing-page subtitle")
    parser.add_argument("--length", default="TBD", help='landing-page length badge, e.g. "2 hours"')
    parser.add_argument("--order", type=int, default=999, help="landing-page order; lower appears first")
    parser.add_argument(
        "--materials-branch",
        help='Git branch for post-training code/resources; defaults to "materials/<name>"',
    )
    parser.add_argument(
        "--unpublished",
        action="store_true",
        help="write published: false so the training is hidden from the landing page",
    )
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="create missing scaffold files in an existing directory without overwriting files",
    )
    parser.add_argument(
        "--trainings-dir",
        type=Path,
        default=DEFAULT_TRAININGS_DIR,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        target, created_dirs, created_files, skipped_files = create_training(args)
    except (FileExistsError, ValueError) as exc:
        sys.exit(f"Error: {exc}")

    print(f"Training scaffold ready: {target}")
    if created_dirs:
        print("Created directories:")
        for path in created_dirs:
            print(f"  - {path}")
    if created_files:
        print("Created files:")
        for path in created_files:
            print(f"  - {path}")
    if skipped_files:
        print("Skipped existing files:")
        for path in skipped_files:
            print(f"  - {path}")
    print("\nNext: edit lessons/1_intro.md, then run python3 build_site.py")


if __name__ == "__main__":
    main()
