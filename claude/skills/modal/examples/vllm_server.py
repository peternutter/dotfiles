"""vLLM as a fast-boot OpenAI-compatible server on Modal.

Mirrors the docs' vLLM serving example (references/modal-docs-full.txt
L35625-35863). The cold-start win here is CACHING: HF weights, vLLM compiled
artifacts, and flashinfer artifacts all live on Volumes, so they aren't
re-downloaded or recompiled on every boot.

Deploy:  modal deploy examples/vllm_server.py
This gives a stable HTTPS URL. Point any OpenAI client / eval harness at it:
  export OPENAI_BASE_URL=https://<...>.modal.run/v1
(directly analogous to how the cheese/inspect evals already hit the RunPod proxy
URL -- see the gpu-run skill.)

Renames to remember (current API):
  @modal.web_server (port-based server)   <- this is what vLLM uses
  @modal.fastapi_endpoint                 <- replaces the old @modal.web_endpoint
"""
import modal

app = modal.App("modal-vllm")

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
VLLM_PORT = 8000
MINUTES = 60
MAX_INPUTS = 32

hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)
vllm_cache = modal.Volume.from_name("vllm-cache", create_if_missing=True)

vllm_image = (
    modal.Image.debian_slim()
    .uv_pip_install("vllm", "flashinfer-python")
    .env({"VLLM_USE_V1": "1"})
)


@app.function(
    image=vllm_image,
    gpu="H100",
    scaledown_window=10 * MINUTES,
    timeout=30 * MINUTES,
    volumes={
        "/root/.cache/huggingface": hf_cache,   # weights cached across boots
        "/root/.cache/vllm": vllm_cache,         # compiled artifacts cached
    },
)
@modal.concurrent(max_inputs=MAX_INPUTS)         # match vLLM's batch capacity
@modal.web_server(port=VLLM_PORT, startup_timeout=20 * MINUTES)
def serve():
    import subprocess

    subprocess.Popen([
        "vllm", "serve", MODEL_NAME,
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--max-num-seqs", str(MAX_INPUTS),
        # Dev-only fast boot (skips torch.compile + CUDA graph capture):
        # "--enforce-eager",
    ])
