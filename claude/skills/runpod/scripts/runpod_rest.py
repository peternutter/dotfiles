#!/usr/bin/env python3
"""Small Runpod REST/GraphQL helper.

Defaults to read-only commands. Mutating commands require --yes.
Loads RUNPOD_API_KEY from environment or a local .env without printing it.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REST_BASE = "https://rest.runpod.io/v1"
GRAPHQL_URL = "https://api.runpod.io/graphql"
SECRET_MARKERS = ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "AUTH")


def load_env(path: str | None) -> None:
    if not path:
        return
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def api_key() -> str:
    key = os.environ.get("RUNPOD_API_KEY")
    if not key:
        raise SystemExit("RUNPOD_API_KEY is not set. Pass --env-file .env or export it.")
    return key


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key_upper = str(key).upper()
            if (
                key_upper in {"KEY", "APIKEY", "API_KEY", "TOKEN", "SECRET", "PASSWORD"}
                or any(marker in key_upper for marker in SECRET_MARKERS)
            ):
                out[key] = "<redacted>"
            elif str(key).lower() == "env" and isinstance(item, dict):
                out[key] = {k: "<redacted>" for k in item}
            else:
                out[key] = redact(item)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def request_json(method: str, url: str, body: Any | None = None) -> tuple[int, Any]:
    data = None
    headers = {
        "Authorization": f"Bearer {api_key()}",
        "Content-Type": "application/json",
        "User-Agent": "codex-runpod-skill/0.1",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
            if not text:
                return resp.status, None
            try:
                return resp.status, json.loads(text)
            except json.JSONDecodeError:
                return resp.status, text
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            payload: Any = json.loads(text)
        except json.JSONDecodeError:
            payload = text
        return exc.code, {"error": payload}


def rest(method: str, path: str, body: Any | None = None) -> tuple[int, Any]:
    if not path.startswith("/"):
        path = "/" + path
    return request_json(method, REST_BASE + path, body)


def runpodctl_url() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin" and machine in {"arm64", "aarch64"}:
        suffix = "darwin-arm64"
    elif system == "darwin":
        suffix = "darwin-amd64"
    elif system == "linux" and machine in {"arm64", "aarch64"}:
        suffix = "linux-arm64"
    elif system == "linux":
        suffix = "linux-amd64"
    else:
        raise SystemExit(f"Unsupported platform for runpodctl auto-download: {system}/{machine}")
    return f"https://github.com/runpod/runpodctl/releases/latest/download/runpodctl-{suffix}"


def ensure_runpodctl(path: str) -> str:
    target = Path(path).expanduser()
    if target.exists():
        return str(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(runpodctl_url(), target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return str(target)


def graphql(query: str, variables: dict[str, Any] | None = None) -> tuple[int, Any]:
    body: dict[str, Any] = {"query": query}
    if variables:
        body["variables"] = variables
    return request_json("POST", GRAPHQL_URL, body)


def print_json(value: Any) -> None:
    print(json.dumps(redact(value), indent=2, sort_keys=True))


def summarize_collection(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"type": "list", "count": len(payload), "sample": redact(payload[:3])}
    if isinstance(payload, dict):
        for key in ("data", "items", "pods", "networkVolumes", "templates"):
            if isinstance(payload.get(key), list):
                return {
                    "type": f"dict.{key}",
                    "count": len(payload[key]),
                    "sample": redact(payload[key][:3]),
                }
        return {"type": "dict", "keys": sorted(str(k) for k in payload.keys())[:20]}
    return {"type": type(payload).__name__, "value": payload}


def cmd_smoke(_args: argparse.Namespace) -> int:
    checks: list[dict[str, Any]] = []

    for name, method, path in [
        ("rest_openapi", "GET", "/openapi.json"),
        ("pods", "GET", "/pods"),
        ("templates", "GET", "/templates"),
        ("networkvolumes", "GET", "/networkvolumes"),
    ]:
        status, payload = rest(method, path)
        checks.append({
            "name": name,
            "status": status,
            "ok": 200 <= status < 300,
            "summary": summarize_collection(payload),
        })

    status, payload = graphql(
        """
        query {
          gpuTypes {
            id
            displayName
            memoryInGb
            secureCloud
            communityCloud
          }
        }
        """
    )
    gpu_items = []
    if isinstance(payload, dict):
        gpu_items = payload.get("data", {}).get("gpuTypes", []) or []
    checks.append({
        "name": "graphql_gpuTypes",
        "status": status,
        "ok": 200 <= status < 300 and bool(gpu_items),
        "summary": {"count": len(gpu_items), "sample": redact(gpu_items[:5])},
    })

    print_json({"ok": all(item["ok"] for item in checks), "checks": checks})
    return 0 if all(item["ok"] for item in checks) else 2


def cmd_get(args: argparse.Namespace) -> int:
    status, payload = rest("GET", args.path)
    print_json({"status": status, "payload": payload})
    return 0 if 200 <= status < 300 else 2


def cmd_collection(path: str):
    def _run(_args: argparse.Namespace) -> int:
        status, payload = rest("GET", path)
        print_json({"status": status, "summary": summarize_collection(payload), "payload": payload})
        return 0 if 200 <= status < 300 else 2
    return _run


def cmd_gpu_types(_args: argparse.Namespace) -> int:
    status, payload = graphql(
        """
        query {
          gpuTypes {
            id
            displayName
            memoryInGb
            secureCloud
            communityCloud
          }
        }
        """
    )
    print_json({"status": status, "payload": payload})
    return 0 if 200 <= status < 300 else 2


def cmd_cheap_gpus(args: argparse.Namespace) -> int:
    status, payload = graphql(
        """
        query {
          gpuTypes {
            id
            displayName
            memoryInGb
            secureCloud
            communityCloud
            securePrice
            communityPrice
            secureSpotPrice
            communitySpotPrice
          }
        }
        """
    )
    if not (200 <= status < 300):
        print_json({"status": status, "payload": payload})
        return 2

    gpu_types = []
    if isinstance(payload, dict):
        gpu_types = payload.get("data", {}).get("gpuTypes", []) or []

    rows: list[dict[str, Any]] = []
    for gpu in gpu_types:
        if gpu.get("id") == "unknown":
            continue
        memory = gpu.get("memoryInGb") or 0
        if memory < args.min_vram:
            continue

        candidates = [
            ("community", gpu.get("communityCloud"), gpu.get("communityPrice")),
            ("secure", gpu.get("secureCloud"), gpu.get("securePrice")),
        ]
        if args.include_spot:
            candidates.extend([
                ("community-spot", gpu.get("communityCloud"), gpu.get("communitySpotPrice")),
                ("secure-spot", gpu.get("secureCloud"), gpu.get("secureSpotPrice")),
            ])

        for cloud, enabled, price in candidates:
            if args.cloud != "any" and not cloud.startswith(args.cloud):
                continue
            if enabled is not True or not isinstance(price, (int, float)) or price <= 0:
                continue
            rows.append({
                "gpu_id": gpu.get("id"),
                "display_name": gpu.get("displayName"),
                "memory_gb": memory,
                "cloud": cloud,
                "usd_per_gpu_hour": price,
            })

    rows.sort(key=lambda item: (item["usd_per_gpu_hour"], item["memory_gb"], item["gpu_id"]))
    print_json({
        "status": status,
        "count": len(rows),
        "note": "Sorted by advertised price. This query does not prove live capacity; pod creation can still fail if no machine is available.",
        "items": rows[:args.limit],
    })
    return 0


def cmd_datacenter_availability(args: argparse.Namespace) -> int:
    tool = ensure_runpodctl(args.runpodctl)
    env = os.environ.copy()
    env.setdefault("HOME", "/tmp/runpodctl-home")
    proc = subprocess.run(
        [tool, "datacenter", "list"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    rows = json.loads(proc.stdout)

    dc_filter = {item.upper() for item in args.datacenter or []}
    gpu_filters = [item.lower() for item in args.gpu or []]
    filtered: list[dict[str, Any]] = []
    for dc in rows:
        if dc_filter and str(dc.get("id", "")).upper() not in dc_filter:
            continue
        hits = []
        for gpu in dc.get("gpuAvailability") or []:
            haystack = f"{gpu.get('displayName', '')} {gpu.get('gpuId', '')}".lower()
            if gpu_filters and not any(term in haystack for term in gpu_filters):
                continue
            hits.append(gpu)
        if gpu_filters and not hits:
            continue
        filtered.append({**dc, "gpuAvailability": hits if gpu_filters else dc.get("gpuAvailability", [])})

    if args.json:
        print_json(filtered)
        return 0

    for dc in filtered:
        print(f"{dc.get('id')} ({dc.get('location', 'unknown')})")
        for gpu in dc.get("gpuAvailability") or []:
            status = gpu.get("stockStatus") or "-"
            print(f"  {status:6} {gpu.get('displayName')} [{gpu.get('gpuId')}]")
    return 0


def bootstrap_start_cmd(repo: str, script_path: str) -> list[str]:
    api_url = f"https://api.github.com/repos/{repo}/contents/{script_path}"
    raw_url = f"https://raw.githubusercontent.com/{repo}/main/{script_path}"
    script = f"""set -e
export DEBIAN_FRONTEND=noninteractive NONINTERACTIVE=1
mkdir -p /workspace /run/sshd /root/.ssh
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq || true
  apt-get install -y -qq ca-certificates curl openssh-server >/dev/null || true
fi
if [ -n "${{PUBLIC_KEY:-}}" ]; then
  printf '%s\\n' "$PUBLIC_KEY" > /root/.ssh/authorized_keys
  chmod 700 /root/.ssh
  chmod 600 /root/.ssh/authorized_keys
fi
/usr/sbin/sshd || true
if [ -n "${{GITHUB_TOKEN:-}}" ]; then
  curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github.v3.raw" \\
    {api_url} -o /workspace/pod_bootstrap.sh || true
fi
if [ ! -s /workspace/pod_bootstrap.sh ]; then
  curl -fsSL {raw_url} -o /workspace/pod_bootstrap.sh
fi
bash /workspace/pod_bootstrap.sh pod 2>&1 | tee /workspace/bootstrap.log
sleep infinity
"""
    return ["bash", "-lc", script]


def read_public_key(path: str) -> str:
    key_path = Path(path).expanduser()
    if not key_path.exists():
        return ""
    return key_path.read_text().strip()


def github_token_from_gh() -> str:
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True, timeout=15).strip()
    except Exception:
        return ""


def cmd_create_cpu_pod(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "name": args.name,
        "computeType": "CPU",
        "cpuFlavorIds": args.cpu_flavor,
        "cpuFlavorPriority": args.cpu_flavor_priority,
        "vcpuCount": args.vcpu_count,
        "cloudType": args.cloud_type,
        "dataCenterIds": args.datacenter,
        "dataCenterPriority": args.datacenter_priority,
        "imageName": args.image,
        "containerDiskInGb": args.container_disk_gb,
        "volumeMountPath": args.volume_mount_path,
        "ports": args.port,
        "env": {},
        "dockerStartCmd": bootstrap_start_cmd(args.repo, args.script_path),
    }
    if args.network_volume_id:
        payload["networkVolumeId"] = args.network_volume_id
    else:
        payload["volumeInGb"] = args.volume_gb

    if not args.no_ssh_key:
        public_key = read_public_key(args.public_key_file)
        if public_key:
            payload["env"]["PUBLIC_KEY"] = public_key

    token = ""
    if args.github_token_from_gh:
        token = github_token_from_gh()
    if not token:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if token and not args.no_github_token:
        payload["env"]["GITHUB_TOKEN"] = token

    if args.dry_run:
        print_json({"path": "/pods", "payload": payload})
        return 0

    require_yes(args)
    status, body = rest("POST", "/pods", payload)
    print_json({"status": status, "payload": body})
    return 0 if 200 <= status < 300 else 2


def ssh_target(payload: dict[str, Any], internal_port: str = "22") -> dict[str, Any]:
    mappings = payload.get("portMappings") or {}
    public_port = mappings.get(internal_port) or mappings.get(int(internal_port)) if isinstance(mappings, dict) else None
    return {
        "publicIp": payload.get("publicIp"),
        "publicPort": public_port,
        "ssh": f"ssh -i ~/.ssh/id_ed25519 -p {public_port} root@{payload.get('publicIp')}"
        if payload.get("publicIp") and public_port else None,
    }


def cmd_wait_pod(args: argparse.Namespace) -> int:
    deadline = time.monotonic() + args.timeout
    last: Any = None
    while True:
        status, payload = rest("GET", f"/pods/{args.pod_id}")
        last = payload
        if 200 <= status < 300 and isinstance(payload, dict):
            target = ssh_target(payload, args.internal_port)
            ready = bool(target.get("publicIp") and target.get("publicPort"))
            if ready:
                print_json({"status": status, "ready": True, "pod": payload, "target": target})
                return 0
        if time.monotonic() >= deadline:
            print_json({"status": status, "ready": False, "pod": last})
            return 2
        time.sleep(args.interval)


def require_yes(args: argparse.Namespace) -> None:
    if not getattr(args, "yes", False):
        raise SystemExit("Refusing mutation without --yes. Confirm the target and cost first.")


def cmd_mutate_pod(args: argparse.Namespace) -> int:
    require_yes(args)
    status, payload = rest("POST", f"/pods/{args.pod_id}/{args.action}")
    print_json({"status": status, "payload": payload})
    return 0 if 200 <= status < 300 else 2


def cmd_delete_pod(args: argparse.Namespace) -> int:
    require_yes(args)
    status, payload = rest("DELETE", f"/pods/{args.pod_id}")
    print_json({"status": status, "payload": payload})
    return 0 if 200 <= status < 300 else 2


def load_payload(path: str) -> Any:
    return json.loads(Path(path).read_text())


def cmd_create(args: argparse.Namespace) -> int:
    require_yes(args)
    payload = load_payload(args.payload_json)
    status, body = rest("POST", args.path, payload)
    print_json({"status": status, "payload": body})
    return 0 if 200 <= status < 300 else 2


def cmd_openapi(args: argparse.Namespace) -> int:
    status, payload = rest("GET", "/openapi.json")
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True))
        print(args.output)
    else:
        print_json({"status": status, "payload": payload})
    return 0 if 200 <= status < 300 else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Runpod REST/GraphQL helper")
    parser.add_argument("--env-file", default=".env", help="Optional .env file to load")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("smoke", help="Read-only API smoke test").set_defaults(func=cmd_smoke)
    sub.add_parser("list-pods", help="GET /pods").set_defaults(func=cmd_collection("/pods"))
    sub.add_parser("list-volumes", help="GET /networkvolumes").set_defaults(func=cmd_collection("/networkvolumes"))
    sub.add_parser("list-templates", help="GET /templates").set_defaults(func=cmd_collection("/templates"))
    sub.add_parser("gpu-types", help="GraphQL gpuTypes query").set_defaults(func=cmd_gpu_types)
    cheap_gpus = sub.add_parser("cheap-gpus", help="Read-only cheapest GPU price view")
    cheap_gpus.add_argument("--limit", type=int, default=15)
    cheap_gpus.add_argument("--min-vram", type=int, default=0, help="Minimum GPU memory in GB")
    cheap_gpus.add_argument("--cloud", choices=("any", "community", "secure"), default="any")
    cheap_gpus.add_argument("--include-spot", action="store_true")
    cheap_gpus.set_defaults(func=cmd_cheap_gpus)

    availability = sub.add_parser("datacenter-availability", help="Live datacenter GPU stock via runpodctl")
    availability.add_argument("--runpodctl", default="/tmp/runpodctl")
    availability.add_argument("--datacenter", "-d", action="append", help="Filter to datacenter ID")
    availability.add_argument("--gpu", "-g", action="append", help="Case-insensitive GPU name/id substring")
    availability.add_argument("--json", action="store_true")
    availability.set_defaults(func=cmd_datacenter_availability)

    get_pod = sub.add_parser("get-pod", help="GET /pods/{pod_id}")
    get_pod.add_argument("pod_id")
    get_pod.set_defaults(func=lambda args: cmd_get(argparse.Namespace(path=f"/pods/{args.pod_id}")))

    wait_pod = sub.add_parser("wait-pod", help="Poll a pod until public IP and SSH port mapping exist")
    wait_pod.add_argument("pod_id")
    wait_pod.add_argument("--internal-port", default="22")
    wait_pod.add_argument("--interval", type=float, default=10)
    wait_pod.add_argument("--timeout", type=float, default=300)
    wait_pod.set_defaults(func=cmd_wait_pod)

    openapi = sub.add_parser("openapi", help="GET /openapi.json")
    openapi.add_argument("--output")
    openapi.set_defaults(func=cmd_openapi)

    for action in ("start", "stop", "restart", "reset"):
        p = sub.add_parser(f"{action}-pod", help=f"POST /pods/{{pod_id}}/{action}")
        p.add_argument("pod_id")
        p.add_argument("--yes", action="store_true")
        p.set_defaults(action=action, func=cmd_mutate_pod)

    delete_pod = sub.add_parser("delete-pod", help="DELETE /pods/{pod_id}")
    delete_pod.add_argument("pod_id")
    delete_pod.add_argument("--yes", action="store_true")
    delete_pod.set_defaults(func=cmd_delete_pod)

    create_pod = sub.add_parser("create-pod", help="POST /pods with payload JSON")
    create_pod.add_argument("payload_json")
    create_pod.add_argument("--yes", action="store_true")
    create_pod.set_defaults(path="/pods", func=cmd_create)

    create_cpu = sub.add_parser("create-cpu-pod", help="Create a CPU pod with bootstrap-friendly defaults")
    create_cpu.add_argument("--name", default="runpod-cpu-bootstrap")
    create_cpu.add_argument("--datacenter", action="append", required=True, help="Datacenter ID, e.g. US-CA-2")
    create_cpu.add_argument("--datacenter-priority", choices=("availability", "custom"), default="custom")
    create_cpu.add_argument("--cpu-flavor", action="append", default=["cpu3g"], help="CPU flavor ID, e.g. cpu3g")
    create_cpu.add_argument("--cpu-flavor-priority", choices=("availability", "custom"), default="custom")
    create_cpu.add_argument("--vcpu-count", type=int, default=2)
    create_cpu.add_argument("--cloud-type", choices=("SECURE", "COMMUNITY"), default="SECURE")
    create_cpu.add_argument("--image", default="runpod/base:0.4.0-cuda11.8.0")
    create_cpu.add_argument("--container-disk-gb", type=int, default=20)
    create_cpu.add_argument("--network-volume-id", help="Attach an existing network volume")
    create_cpu.add_argument("--volume-gb", type=int, default=20, help="Local pod volume size if no network volume is attached")
    create_cpu.add_argument("--volume-mount-path", default="/workspace")
    create_cpu.add_argument("--port", action="append", default=["22/tcp", "8888/http"])
    create_cpu.add_argument("--public-key-file", default="~/.ssh/id_ed25519.pub")
    create_cpu.add_argument("--no-ssh-key", action="store_true")
    create_cpu.add_argument("--github-token-from-gh", action="store_true")
    create_cpu.add_argument("--no-github-token", action="store_true")
    create_cpu.add_argument("--repo", default="peternutter/mats_project")
    create_cpu.add_argument("--script-path", default="code/scripts/pod_bootstrap.sh")
    create_cpu.add_argument("--dry-run", action="store_true")
    create_cpu.add_argument("--yes", action="store_true")
    create_cpu.set_defaults(func=cmd_create_cpu_pod)

    create_vol = sub.add_parser("create-volume", help="POST /networkvolumes with payload JSON")
    create_vol.add_argument("payload_json")
    create_vol.add_argument("--yes", action="store_true")
    create_vol.set_defaults(path="/networkvolumes", func=cmd_create)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    load_env(args.env_file)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
