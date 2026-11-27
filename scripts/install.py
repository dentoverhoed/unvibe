"""Install or update the /kickstart skill from this repo.

    python scripts/install.py                  # into ~/.claude/skills/kickstart
    python scripts/install.py --project DIR    # into DIR/.claude/skills/kickstart
    python scripts/install.py --dest DIR       # into DIR/kickstart (another agent's skills folder)
    python scripts/install.py --check          # report only: exit 1 if out of date
    python scripts/install.py --force          # overwrite a copy that was edited by hand

The script copies the skill rather than symlinking it. That way the installed
skill only changes when you run this script, never because you checked out a
branch with half-finished edits.

It records a SHA-256 of every installed file in `.unvibe-install.json` next to
the skill. On the next run, a file that no longer matches that record was
edited by hand, and the script refuses to overwrite it without --force.

Exit codes: 0 ok / up to date, 1 out of date (--check only), 2 refused or error.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "skills" / "kickstart"
MANIFEST = ".unvibe-install.json"


def hashes(folder):
    if not folder.is_dir():
        return {}
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file() and p.name != MANIFEST}


def git(*args):
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        return out.stdout.strip() if out.returncode == 0 else None
    except OSError:
        return None


def committed_versions(rel):
    """SHA-256 of every committed version of skills/kickstart/<rel>."""
    path = f"skills/{SRC.name}/{rel}"
    commits = (git("rev-list", "HEAD", "--", path) or "").split()
    versions = set()
    for c in commits:
        blob = subprocess.run(["git", "show", f"{c}:{path}"], cwd=ROOT, capture_output=True)
        if blob.returncode == 0:
            versions.add(hashlib.sha256(blob.stdout).hexdigest())
    return versions


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    where = parser.add_mutually_exclusive_group()
    where.add_argument("--project", metavar="DIR", help="install into DIR/.claude/skills/ instead of ~/.claude/skills/")
    where.add_argument("--dest", metavar="DIR", help="install into DIR/kickstart, for an agent that reads skills from DIR")
    parser.add_argument("--check", action="store_true", help="only report, never write")
    parser.add_argument("--force", action="store_true", help="overwrite files edited by hand")
    args = parser.parse_args()

    if args.dest:
        dest = Path(args.dest).resolve() / SRC.name
    else:
        base = Path(args.project).resolve() if args.project else Path.home()
        dest = base / ".claude" / "skills" / SRC.name
    src_files, dest_files = hashes(SRC), hashes(dest)
    if not src_files:
        print(f"error: no skill files found in {SRC}", file=sys.stderr)
        return 2

    # Which installed files were changed by hand since the last install?
    manifest_path = dest / MANIFEST
    if manifest_path.exists():
        recorded = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", {})
        hand_edited = sorted(f for f, h in dest_files.items() if recorded.get(f) != h)
    else:
        # Installed without this script (e.g. cp). A file is safe to replace if it
        # matches the current source or any committed version of it.
        hand_edited = sorted(f for f, h in dest_files.items()
                             if h != src_files.get(f) and h not in committed_versions(f))

    added = sorted(set(src_files) - set(dest_files))
    updated = sorted(f for f in src_files if f in dest_files and src_files[f] != dest_files[f])
    removed = sorted(set(dest_files) - set(src_files))
    changes = [("add", f) for f in added] + [("update", f) for f in updated] + [("remove", f) for f in removed]

    print(f"skill:  {SRC}")
    print(f"target: {dest}")
    if not changes:
        print("up to date")
        if not args.check and not manifest_path.exists():
            write_manifest(manifest_path, src_files)
        return 0
    for action, f in changes:
        print(f"  {action:6} {f}")

    if args.check:
        print("out of date: run without --check to install")
        return 1

    blocked = [f for f in hand_edited if f in updated or f in removed]
    if blocked and not args.force:
        print("refused: these installed files were edited by hand since the last install:", file=sys.stderr)
        for f in blocked:
            print(f"  {f}", file=sys.stderr)
        print("Move your edits into the repo, or rerun with --force to overwrite them.", file=sys.stderr)
        return 2

    dirty = git("status", "--porcelain", "--", str(SRC))
    if dirty:
        print("warning: installing uncommitted changes from your working copy", file=sys.stderr)

    dest.mkdir(parents=True, exist_ok=True)
    for f in added + updated:
        (dest / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SRC / f, dest / f)
    for f in removed:
        (dest / f).unlink()
    write_manifest(manifest_path, src_files)
    print(f"installed {len(added) + len(updated)} file(s), removed {len(removed)}")
    return 0


def write_manifest(path, files):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"source_commit": git("rev-parse", "--short", "HEAD"),
            "uncommitted_changes": bool(git("status", "--porcelain", "--", str(SRC))),
            "files": files}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
