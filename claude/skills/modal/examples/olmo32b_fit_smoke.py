"""Does OLMo-3-32B LoRA fit + train on a SINGLE Blackwell card (no ZeRO/TP)?  -- criterion 4 pivotal test

Today OLMo-3-32B needs 4xH100 + ZeRO-3 (64B frozen weights won't fit on 80GB alongside
64-layer activations). On Modal the top cards are B200 (180GB) and B300 (288GB). If the
32B LoRA fits on ONE of them, the whole multi-GPU/deepspeed/NCCL surface disappears and
"1 seed = 1 GPU" fan-out becomes trivial. This script answers that, staged cheap->dear:

  prefetch  (CPU)  -- download the 64GB checkpoint to the hf-cache Volume ONCE, no GPU burn.
  torch     (GPU)  -- import torch, print device + compute capability + a matmul. Proves the
                      IMAGE works on the card before we commit to a 64GB load. (B300 needs
                      CUDA 13.0+ per Modal docs -- this stage is where we find out if our
                      torch build is Blackwell-compatible on each card.)
  fit       (GPU)  -- load base + r=64 all-proj LoRA, run N steps at seq=4096 mbs=1, report
                      peak GPU mem + per-step time. --grad-ckpt to compare ckpt on/off.

Run (one stage / one GPU at a time):
  modal run examples/olmo32b_fit_smoke.py --stage prefetch
  modal run examples/olmo32b_fit_smoke.py --stage torch --gpu B200
  modal run examples/olmo32b_fit_smoke.py --stage torch --gpu B300
  modal run examples/olmo32b_fit_smoke.py --stage fit --gpu B200
  modal run examples/olmo32b_fit_smoke.py --stage fit --gpu B300

The B200-vs-B300 race = launch the fit stage on each (see modal_launch.sh for the tmux
window + tail wrapper) and compare peak-mem / step-time / $-per-step.
"""
import modal

app = modal.App("olmo32b-fit-smoke")

# Simplest checkpoint to load for a fit/speed probe (arch + size are what matter, not the
# exact branch): the plain Instruct repo. Real training will use the base branch.
MODEL_ID = "allenai/Olmo-3.1-32B-Instruct"
HF_MOUNT = "/cache/hf"

hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)

# transformers >=4.57 (5.x) knows Olmo3ForCausalLM. Latest torch wheel = cu128 (Blackwell
# B200 / sm_100). If the B300 torch stage fails on a compute-capability mismatch, that's the
# signal to move this image to a CUDA-13 base (nvidia/cuda:13.x-devel) + a cu130 torch.
image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("torch", "transformers>=4.57", "peft", "accelerate", "hf_transfer")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "HF_HOME": HF_MOUNT})
)

SECRET = modal.Secret.from_name("why-gen-env")   # HF_TOKEN + WANDB_API_KEY
HOURS = 60 * 60


@app.function(image=image, volumes={HF_MOUNT: hf_cache}, secrets=[SECRET],
              cpu=8.0, timeout=2 * HOURS)
def prefetch() -> str:
    """CPU-only: pull the 64GB checkpoint onto the Volume once, so GPU stages skip the download."""
    from huggingface_hub import snapshot_download
    p = snapshot_download(MODEL_ID, ignore_patterns=["*.pt", "*.pth", "original/*"])
    hf_cache.commit()
    import os
    n = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(p) for f in fs)
    return f"cached {MODEL_ID} -> {p} ({n/1e9:.1f} GB) committed to hf-cache"


def _torch_probe() -> str:
    import torch
    name = torch.cuda.get_device_name(0)
    cap = torch.cuda.get_device_capability(0)
    x = torch.randn(4096, 4096, device="cuda", dtype=torch.bfloat16)
    (x @ x).sum().item()   # exercise a real bf16 kernel on the card
    return (f"OK gpu={name} sm={cap[0]}.{cap[1]} torch={torch.__version__} "
            f"cuda={torch.version.cuda} bf16-matmul=ok")


def _fit_probe(steps: int, seq_len: int, grad_ckpt: bool) -> str:
    import time, torch
    from transformers import AutoModelForCausalLM
    from peft import LoraConfig, get_peft_model

    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="sdpa")
    if grad_ckpt:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False
    lora = LoraConfig(r=64, lora_alpha=128, lora_dropout=0.0, bias="none",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, lora)
    model.train()
    load_s = time.time() - t0
    weights_gb = torch.cuda.memory_allocated() / 1e9

    opt = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=1e-4)
    vocab = model.config.vocab_size
    torch.cuda.reset_peak_memory_stats()
    step_times = []
    for i in range(steps):
        ts = time.time()
        ids = torch.randint(0, vocab, (1, seq_len), device="cuda")
        out = model(input_ids=ids, labels=ids)
        out.loss.backward()
        opt.step(); opt.zero_grad(set_to_none=True)
        torch.cuda.synchronize()
        step_times.append(time.time() - ts)
    peak_gb = torch.cuda.max_memory_allocated() / 1e9
    warm = sum(step_times[1:]) / max(1, len(step_times) - 1)   # drop step 0 (compile/alloc)
    return (f"OK load={load_s:.0f}s weights={weights_gb:.0f}GB peak={peak_gb:.0f}GB "
            f"step={warm:.2f}s (grad_ckpt={grad_ckpt} seq={seq_len} r=64 all-proj) "
            f"first_step={step_times[0]:.2f}s")


# One @app.function per GPU so `--gpu` picks the target (Modal needs the gpu= at decoration time).
@app.function(image=image, volumes={HF_MOUNT: hf_cache}, secrets=[SECRET], gpu="B200", timeout=HOURS)
def run_b200(stage: str, steps: int, seq_len: int, grad_ckpt: bool) -> str:
    return _torch_probe() if stage == "torch" else _fit_probe(steps, seq_len, grad_ckpt)


@app.function(image=image, volumes={HF_MOUNT: hf_cache}, secrets=[SECRET], gpu="B300", timeout=HOURS)
def run_b300(stage: str, steps: int, seq_len: int, grad_ckpt: bool) -> str:
    return _torch_probe() if stage == "torch" else _fit_probe(steps, seq_len, grad_ckpt)


@app.local_entrypoint()
def main(stage: str = "torch", gpu: str = "B200", steps: int = 5,
         seq_len: int = 4096, grad_ckpt: bool = False):
    if stage == "prefetch":
        print(prefetch.remote()); return
    fn = {"B200": run_b200, "B300": run_b300}[gpu]
    print(f"[{gpu}/{stage}]", fn.remote(stage, steps, seq_len, grad_ckpt))
