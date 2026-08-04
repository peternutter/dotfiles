"""Does the swift-GKD comms pattern work inside ONE Modal container? (criterion 4 candidate)

The GKD stack needs three things from the host, all same-machine:
  1. a multi-GPU container (trainer DDP + vLLM rollout server share the box),
  2. an NCCL communicator between separate OS processes pinned to different GPUs over
     NCCL_SOCKET_IFNAME=lo (this is exactly the trainer<->vLLM weight-sync channel),
  3. localhost HTTP between those processes (the rollout request channel).

This smoke test proves all three on cheap GPUs (default T4:2, ~$0.02 for a 1-min run).
It does NOT prove B200-specific NCCL quirks (NVLS) or vLLM itself -- vLLM-on-Modal is a
documented first-party example; the Modal-specific unknown is multi-process NCCL in their
container runtime.

Run:  modal run gkd_comms_smoke.py
"""

import modal

app = modal.App("gkd-comms-smoke")

image = modal.Image.debian_slim(python_version="3.12").uv_pip_install("torch")

GPU = "T4:2"  # mechanics-only; swap to "H100:2" / "B200:2" for a hardware-faithful pass

WORKER = r"""
import os, sys, time, json, threading, http.server, urllib.request
import torch, torch.distributed as dist

rank = int(sys.argv[1])
os.environ.setdefault("MASTER_ADDR", "127.0.0.1")
os.environ.setdefault("MASTER_PORT", "29511")
torch.cuda.set_device(rank)  # one proc per GPU, like trainer-master + rollout server

# --- channel 3: localhost HTTP (rank1 = "rollout server", rank0 = "trainer" client)
if rank == 1:
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers()
            self.wfile.write(b'{"ok": true}')
        def log_message(self, *a): pass
    srv = http.server.HTTPServer(("127.0.0.1", 8012), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

# --- channel 2: NCCL communicator across the two processes
dist.init_process_group("nccl", rank=rank, world_size=2)
x = torch.ones(8, device=f"cuda:{rank}")
dist.all_reduce(x)
assert x[0].item() == 2.0, "all_reduce wrong"

# weight-push simulation: broadcast a LoRA-sized tensor (~232 MB) rank0 -> rank1
lora = torch.randn(232 * 1024 * 1024 // 4, device=f"cuda:{rank}") if rank == 0 \
    else torch.empty(232 * 1024 * 1024 // 4, device=f"cuda:{rank}")
t0 = time.time()
dist.broadcast(lora, src=0)
torch.cuda.synchronize()
push_s = time.time() - t0

if rank == 0:
    time.sleep(1)  # let rank1's server come up
    with urllib.request.urlopen("http://127.0.0.1:8012/health", timeout=5) as r:
        assert json.loads(r.read())["ok"]
    with open("/tmp/result.json", "w") as f:
        json.dump({"nccl_ok": True, "http_ok": True,
                   "lora_push_s": round(push_s, 3),
                   "nccl_version": ".".join(map(str, torch.cuda.nccl.version())),
                   "gpus": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]}, f)
dist.barrier()
dist.destroy_process_group()
"""


@app.function(gpu=GPU, image=image, timeout=600)
def smoke() -> dict:
    import json
    import pathlib
    import subprocess

    pathlib.Path("/tmp/worker.py").write_text(WORKER)
    env = dict(
        NCCL_SOCKET_IFNAME="lo",  # same requirement as the RunPod coloc scripts
        NCCL_DEBUG="WARN",
        PATH="/usr/local/bin:/usr/bin:/bin",
    )
    import os

    env = {**os.environ, **env}
    procs = [
        subprocess.Popen(
            ["python", "/tmp/worker.py", str(r)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for r in (0, 1)
    ]
    outs = [p.communicate(timeout=540)[0] for p in procs]
    for r, (p, out) in enumerate(zip(procs, outs)):
        if p.returncode != 0:
            raise RuntimeError(f"rank {r} failed:\n{out}")
    return json.loads(pathlib.Path("/tmp/result.json").read_text())


@app.local_entrypoint()
def main():
    print(smoke.remote())
