#!/usr/bin/env python
"""Sync `data/` between local (RunPod NFS) and the Modal `why-gen-store` Volume, 1:1 topology.

The Modal training container mounts the `why-gen-store` Volume at `/root/mats_project/data`, so
the Volume IS our `data/` tree with an IDENTICAL relative layout -- an adapter that resolves to
`data/store/olmo3-32b/adapters/<unit>` locally is at the same relative path on the Volume. No
translation, no per-file naming: relative path in, relative path out.

Protocol (partial 1:1 mirror, ref-driven -- NOT a full mirror):
  - BEFORE a run:  push only the inputs it reads (datasets + any store init refs).
  - AFTER a run:   pull only the unit dir(s) it produced back into local `data/`.
Base model WEIGHTS are NOT synced here -- they live on the `hf-cache` Volume and are fetched
inside the container by the training wrapper's `prefetch` step (HF branch download).

Verbs:
  sync_store.py push-inputs <experiment> <run>   # datasets + store init refs the run needs
  sync_store.py pull-unit  <store-ref|relpath>...  # produced unit dir(s) -> local data/
  sync_store.py push <relpath>...                 # generic: any path under data/, 1:1
  sync_store.py pull <relpath>...                 # generic: any path under data/, 1:1
  sync_store.py ls [subpath]                      # list the Volume

Runs on a pod or on RunPod (needs Modal creds: ~/.modal.toml or MODAL_TOKEN_ID/SECRET).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# This skill is user-level (~/.claude/skills/modal/), so find the project repo via cwd
# (or $MATS_REPO); why_gen lives at <repo-root>/code/why-gen.
import os
import subprocess


def _repo_root() -> Path:
    if os.environ.get("MATS_REPO"):
        return Path(os.environ["MATS_REPO"])
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
        ).stdout.strip()
        if top:
            return Path(top)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return Path("/workspace/mats_project")


_HERE = Path(__file__).resolve()
_REPO = _repo_root() / "code" / "why-gen"
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_HERE.parent))  # modal_helpers

from why_gen import registry, store                         # noqa: E402
from why_gen.paths import DATA_DIR                           # noqa: E402
from why_gen.config import ExperimentConfig                  # noqa: E402
import modal_helpers as mh                                   # noqa: E402

VOLUME = "why-gen-store"


def _rel(path: Path) -> str:
    """data/-relative POSIX path (the Volume key), e.g. 'store/olmo3-32b/adapters/x'."""
    return path.resolve().relative_to(DATA_DIR).as_posix()


def push(rel: str, force: bool = True) -> None:
    """Upload data/<rel> to /<rel> on the Volume (file or dir), creating parents."""
    local = (DATA_DIR / rel).resolve()
    if not local.exists():
        raise FileNotFoundError(f"nothing to push: {local}")
    remote = "/" + rel
    mh.ensure_volume(VOLUME)
    if local.is_dir():
        mh.put_dir(VOLUME, local, remote, force=force)
    else:
        mh.put_file(VOLUME, local, remote, force=force)
    print(f"  push  data/{rel}  ->  {VOLUME}:{remote}")


def pull(rel: str, force: bool = True) -> None:
    """Download /<rel> from the Volume to data/<rel> (recurses for a dir)."""
    local = (DATA_DIR / rel).resolve()
    mh.get_dir(VOLUME, "/" + rel, local, force=force)
    print(f"  pull  {VOLUME}:/{rel}  ->  data/{rel}")


def _ref_to_rel(ref: str) -> str:
    """store://.. / alias://.. / abs path / data-relative path -> data/-relative path."""
    resolved = store.resolve_store_ref(ref)          # store:// or alias:// -> abs path
    p = Path(resolved) if resolved else Path(ref)
    if not p.is_absolute():
        p = DATA_DIR / p if not str(p).startswith("data/") else DATA_DIR.parent / p
    return _rel(p)


def cmd_push_inputs(exp: str, run_name: str) -> None:
    cfg = ExperimentConfig.load(exp)
    run = cfg.run(run_name)
    seen: set[str] = set()
    print(f"push-inputs for {cfg.name}/{run.name}:")
    for stage in run.stages:
        # datasets the stage trains on -> registry rel path under data/
        for ds in stage.datasets:
            name = ds.name if hasattr(ds, "name") else ds["name"]
            rel = registry.DATASETS.get(name)
            if rel is None:
                raise KeyError(f"dataset '{name}' not in registry.DATASETS")
            if rel not in seen:
                push(rel); seen.add(rel)
        # a store init ref (continuation) must exist on the Volume too
        init = getattr(stage, "init", None)
        if init and str(init).startswith(("store://", "alias://")):
            rel = _ref_to_rel(str(init))
            if rel not in seen:
                push(rel); seen.add(rel)
    if not seen:
        print("  (no inputs to push)")


def cmd_pull_unit(refs: list[str]) -> None:
    for ref in refs:
        pull(_ref_to_rel(ref))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("push-inputs", help="push datasets + init refs a run reads")
    pi.add_argument("experiment"); pi.add_argument("run")
    pu = sub.add_parser("pull-unit", help="pull produced unit dir(s) back to local data/")
    pu.add_argument("refs", nargs="+")
    p = sub.add_parser("push", help="generic 1:1 push of data/<relpath>")
    p.add_argument("relpaths", nargs="+")
    g = sub.add_parser("pull", help="generic 1:1 pull to data/<relpath>")
    g.add_argument("relpaths", nargs="+")
    lsp = sub.add_parser("ls", help="list the Volume")
    lsp.add_argument("subpath", nargs="?", default="/")
    args = ap.parse_args()

    mh.check_auth()
    if args.cmd == "push-inputs":
        cmd_push_inputs(args.experiment, args.run)
    elif args.cmd == "pull-unit":
        cmd_pull_unit(args.refs)
    elif args.cmd == "push":
        for r in args.relpaths:
            push(r)
    elif args.cmd == "pull":
        for r in args.relpaths:
            pull(r)
    elif args.cmd == "ls":
        print(mh.ls(VOLUME, args.subpath))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
