"""Reusable, app-independent Modal helpers for this project.

Scope is deliberately small: the things that recur and that DON'T need to be
bound to a specific `modal.App`. The decorator-bound patterns (sweep app, warm
model class, vLLM server) live as copyable templates in `examples/` because they
must be defined inside an app module.

The focus is REMOTE STORAGE -- moving LoRA adapter dirs (safetensors) between a
Modal Volume and a non-Modal box (our RunPod volume / local), which is the thing
we need to prove before switching off RunPod.

Auth: every call needs Modal credentials.
  - On our pods: the token at /workspace/.modal.toml (symlinked to ~/.modal.toml
    by pod_bootstrap.sh -> link_workspace_modal). Nothing else to do.
  - On a box without the toml (fresh RunPod image): export MODAL_TOKEN_ID and
    MODAL_TOKEN_SECRET (a Service User token from the Modal dashboard).

These wrap the `modal volume` CLI, which is the simplest path that works
identically on a pod and on RunPod. For in-process programmatic use there is also
`sdk_put_dir` / `sdk_iter_file` at the bottom (modal.Volume SDK).

CLI verified against the local docs (references/modal-docs-full.txt L23945-24151):
  `modal volume put VOL LOCAL [REMOTE]`  -- auto-handles a directory, NO -r flag
  `modal volume get VOL REMOTE [LOCAL]`  -- recurses automatically for a folder
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

_PRICING_PATH = Path(__file__).parent / "references" / "pricing.json"

# Project default: one Volume holds all promoted LoRA adapters, one subdir each.
# Override per-call; this is just the convention so we don't sprinkle names around.
LORA_VOLUME = "lora-weights"


def _run(cmd: list[str], capture: bool = False) -> str:
    """Run a modal CLI command, raising with stderr on failure."""
    r = subprocess.run(cmd, text=True, capture_output=capture)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip() if capture else ""
        raise RuntimeError(f"`{' '.join(cmd)}` failed (exit {r.returncode})\n{err}")
    return (r.stdout or "") if capture else ""


def check_auth() -> str:
    """Return the active Modal workspace, or raise if not authenticated."""
    out = _run(["modal", "profile", "current"], capture=True).strip()
    return out


def ensure_volume(volume: str, version: int | None = None) -> None:
    """Create the Volume if it doesn't exist (idempotent)."""
    cmd = ["modal", "volume", "create", volume]
    if version is not None:
        cmd += ["--version", str(version)]
    try:
        _run(cmd, capture=True)
    except RuntimeError as e:
        if "already exists" not in str(e).lower():
            raise


# --- generic Volume <-> local transfer (works on any box with creds) ----------

def put_dir(volume: str, local_dir: str | Path, remote_dir: str = "/", force: bool = False) -> None:
    """Upload a whole local directory to `remote_dir` on the Volume.

    `modal volume put` creates remote parent dirs and handles directories natively.
    """
    cmd = ["modal", "volume", "put", volume, str(local_dir), remote_dir]
    if force:
        cmd.append("--force")
    _run(cmd)


def get_dir(volume: str, remote_dir: str, local_dir: str | Path, force: bool = True) -> None:
    """Download `remote_dir` (recursively, if a folder) from the Volume so it lands AT `local_dir`.

    `modal volume get` (client >=1.5) downloads the remote path INTO an *existing* destination
    directory, preserving the remote basename -- and errors "[Errno 21] Is a directory" if the dest
    does NOT already exist. So we mkdir the PARENT and pass it as dest: remote `.../<name>` lands at
    `<parent>/<name>` == `local_dir` (sync_store keeps remote/local basenames identical). Works for a
    single file too (file lands in the parent dir under its own name).
    """
    parent = Path(local_dir).parent
    parent.mkdir(parents=True, exist_ok=True)
    cmd = ["modal", "volume", "get", volume, remote_dir, str(parent)]
    if force:
        cmd.append("--force")
    _run(cmd)


def put_file(volume: str, local_path: str | Path, remote_path: str, force: bool = False) -> None:
    cmd = ["modal", "volume", "put", volume, str(local_path), remote_path]
    if force:
        cmd.append("--force")
    _run(cmd)


def ls(volume: str, path: str = "/") -> str:
    return _run(["modal", "volume", "ls", volume, path], capture=True)


def rm(volume: str, remote_path: str, recursive: bool = False) -> None:
    cmd = ["modal", "volume", "rm", volume, remote_path]
    if recursive:
        cmd.append("--recursive")
    _run(cmd)


# --- LoRA-weight convenience (the path we actually care about) -----------------

def push_lora(adapter_dir: str | Path, name: str | None = None, volume: str = LORA_VOLUME,
              force: bool = True) -> str:
    """Upload a local LoRA adapter dir to the weights Volume under `/<name>`.

    `name` defaults to the adapter dir's basename. Returns the remote path.
    Use this on RunPod (or locally) after a training run to stash the adapter on
    Modal; pull it back elsewhere with `pull_lora`.
    """
    adapter_dir = Path(adapter_dir)
    name = name or adapter_dir.name
    ensure_volume(volume)
    remote = f"/{name}"
    put_dir(volume, adapter_dir, remote, force=force)
    return remote


def pull_lora(name: str, dest_dir: str | Path, volume: str = LORA_VOLUME) -> Path:
    """Download a LoRA adapter `/<name>` from the weights Volume to `dest_dir/<name>`.

    The reverse of `push_lora`: stage weights on Modal, pull them onto a RunPod box
    to run a long job there. Returns the local path.
    """
    dest = Path(dest_dir) / name
    get_dir(volume, f"/{name}", dest)
    return dest


# --- programmatic SDK path (in-process, no CLI) -------------------------------
# Use when you want upload/download inside Python without shelling out. From a
# non-Modal box this needs MODAL_TOKEN_ID/SECRET in the env. See docs
# references/modal-docs-full.txt L20480 (batch_upload) and L20415 (read_file).

def sdk_put_dir(volume: str, local_dir: str | Path, remote_dir: str, force: bool = False) -> None:
    import modal
    vol = modal.Volume.from_name(volume, create_if_missing=True)
    with vol.batch_upload(force=force) as batch:
        batch.put_directory(str(local_dir), remote_dir)


def sdk_iter_file(volume: str, remote_path: str):
    """Yield byte chunks of a single remote file (streaming download, no mount)."""
    import modal
    vol = modal.Volume.from_name(volume)
    yield from vol.read_file(remote_path)


# --- cost: estimate before, monitor during/after -----------------------------
# Pricing lives in references/pricing.json (updatable; refresh.sh helps reconcile
# it against modal.com/pricing). Estimation is local arithmetic; actual spend
# comes from `modal billing report` (a few minutes' delay).

def load_pricing() -> dict:
    return json.loads(_PRICING_PATH.read_text())


def estimate_cost(gpu: str | None, hours: float, count: int = 1,
                  n_cpu: float = 0.0, mem_gb: float = 0.0) -> float:
    """Estimate $ for `count` containers running `hours` each.

    `gpu` is the Modal gpu= string ("H100", "A100-80GB", ...) or None for CPU-only.
    A "H100:8" string is split: 8x the H100 rate. Strips the H100!/B200+ suffixes.
    """
    p = load_pricing()
    gpu_cost = 0.0
    if gpu:
        name, _, n = gpu.partition(":")
        name = name.rstrip("!+")
        ngpu = int(n) if n else 1
        rate = p["gpu_per_hour"].get(name)
        if rate is None:
            raise KeyError(f"unknown gpu '{name}'; known: {sorted(p['gpu_per_hour'])}")
        gpu_cost = rate * ngpu
    cpu_cost = p["cpu_per_core_hour"] * n_cpu
    mem_cost = p["memory_per_gib_hour"] * mem_gb
    return (gpu_cost + cpu_cost + mem_cost) * hours * count


def cost_today() -> str:
    """Actual workspace spend so far today (JSON from `modal billing report`).

    A few minutes' collection delay. Use `--for "this month"` etc. for other ranges.
    """
    return _run(["modal", "billing", "report", "--for", "today", "--json"], capture=True)


def running() -> str:
    """What's live right now -- containers currently incurring cost.

    Pair with estimate_cost() to gauge in-flight burn; `modal app list` for apps.
    """
    return _run(["modal", "container", "list"], capture=True)
