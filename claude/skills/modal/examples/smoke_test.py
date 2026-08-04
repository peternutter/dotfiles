"""Smallest possible Modal GPU job -- confirms the run loop end to end.

Run:  modal run examples/smoke_test.py
Expect: nvidia-smi output from an H100 in the cloud, then teardown.

This is the first thing to run when validating Modal on a new box: it proves
auth (the /workspace/.modal.toml token), image build, GPU scheduling, and the
local-entrypoint -> .remote() call path all work.
"""
import modal

app = modal.App("modal-smoke-test")
image = modal.Image.debian_slim()


@app.function(gpu="H100", image=image, timeout=120)
def gpu_check() -> str:
    import subprocess

    return subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout


@app.local_entrypoint()
def main():
    # .remote() runs gpu_check in the cloud and returns its value locally.
    print(gpu_check.remote())
