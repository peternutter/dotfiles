"""Stage-2 SFT adversarial (concealment) training on Qwen3-14B — paper + graft hosts, on Modal.

The SFT twin of train_kto_adv_qwen14b_modal.py. Exists because `auditbench-adv/<quirk>/{paper,graft}`
was only ever trained for animal-welfare and contextual-optimism; self-promotion and hardcode-test-cases
have no stage-2 SFT organism, which is the sole reason `{sp,hc}/*/sft2` is empty in the coverage grid
(data/runs/coverage/grid.json <- experiments/auditbench/coverage_grid.py).

For each arm: bake the merged install HOST (Instruct + install adapter, quirk FROZEN), then train a
fresh adv LoRA on it with the paper recipe. The served organism is install (+) adv.
  paper-sft : host = Instruct + auditbench-sdf/<q>/instruct   (status-quo / paper-order organism)
  graft-sft : host = Instruct + auditbench-sdf/<q>/base        (graft organism)

Recipe from `experiments/auditbench/qwen3_14b_auditbench_adv.experiment.yaml` (which produced the
aw/co adapters): r64/a128, lr 2e-5, micro-batch 2 x grad-accum 4, seq 2048, 1 epoch. NOTE lr 2e-5 —
the KTO stage used 1e-5; do not copy that number across.

Data is the prepped LOCAL set on the store Volume (`auditbench/adv_train_<quirk>.jsonl` from
prep_adv_data.py), not an HF dataset — the one structural difference from the KTO wrapper.

  cd .claude/skills/modal
  modal run --detach examples/train_sft_adv_qwen14b_modal.py::sp
  modal run --detach examples/train_sft_adv_qwen14b_modal.py::hc
"""
import pathlib

import modal

app = modal.App("qwen14b-sft-adv")

try:
    _ROOT = pathlib.Path(__file__).resolve().parents[4]
except IndexError:
    _ROOT = pathlib.Path("/root/mats_project")
WHYGEN_LOCAL = str(_ROOT / "code" / "why-gen")
WHYGEN_REMOTE = "/root/why-gen"

HF_MOUNT = "/cache/hf"
DATA_REMOTE = "/root/mats_project/data"
MINUTES = 60

BASE = "Qwen/Qwen3-14B"
INSTALL_REPO = "peterstran/olmo3-graft-organisms"


def install_sub(quirk_hyphen, which):   # which in {instruct(paper), base(graft)}
    return f"qwen3-14b/auditbench-sdf/{quirk_hyphen}/{which}"


hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)
store = modal.Volume.from_name("why-gen-store", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .uv_pip_install("torch", "transformers>=4.50", "peft", "accelerate", "trl>=1.5,<1.7",
                    "datasets>=4.8.5", "numpy", "safetensors", "sentencepiece",
                    "hf_transfer", "huggingface_hub")
    .env({"HF_HOME": HF_MOUNT, "HF_HUB_ENABLE_HF_TRANSFER": "1",
          "TOKENIZERS_PARALLELISM": "false", "WANDB_DISABLED": "true",
          "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
    # Exclude the experiment/eval YAMLs and job scripts: the SFT trainer never reads them, and a
    # parallel session editing experiments/auditbench/*.yaml mid-build makes Modal's dir-hash fail
    # ("<file> was modified during build process"). Ignoring the volatile config files removes the race.
    .add_local_dir(WHYGEN_LOCAL, WHYGEN_REMOTE, copy=True,
                   ignore=["**/__pycache__", "**/*.pyc", "**/.git", "**/data", "**/*.pt",
                           "**/*.parquet", "**/*.experiment.yaml", "**/*.eval.yaml", "**/jobs/**"])
)
VOLUMES = {DATA_REMOTE: store, HF_MOUNT: hf_cache}
SECRETS = [modal.Secret.from_name("why-gen-env")]


def _bake_host(install_subfolder: str, host_dir: str) -> str:
    """Merge Instruct + install adapter into a full host dir (quirk frozen). Qwen3-14B is a standard
    CausalLM (NOT the VL hybrid), so merge_and_unload binds correctly — unlike Qwen3.5-9B."""
    import torch
    from huggingface_hub import snapshot_download
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if (pathlib.Path(host_dir) / "config.json").exists():
        print(f"  host already baked: {host_dir}", flush=True)
        return host_dir
    snap = snapshot_download(INSTALL_REPO, allow_patterns=[f"{install_subfolder}/*"])
    adir = f"{snap}/{install_subfolder}"
    base = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cpu")
    m = PeftModel.from_pretrained(base, adir)
    merged = m.merge_and_unload()
    merged.save_pretrained(host_dir)
    AutoTokenizer.from_pretrained(BASE).save_pretrained(host_dir)
    print(f"  baked host -> {host_dir}", flush=True)
    return host_dir


def _train(arm: str, which: str, quirk_us: str, quirk_hyphen: str):
    import subprocess, sys
    host = _bake_host(install_sub(quirk_hyphen, which), f"/root/hosts/{arm}_{quirk_us}")
    out = f"{DATA_REMOTE}/staging/qwen14b_sft_adv/{arm}_{quirk_us}"
    if (pathlib.Path(out) / "adapter_config.json").exists():
        print(f"skip {arm} (adapter exists)", flush=True)
        return out
    data = f"{DATA_REMOTE}/auditbench/adv_train_{quirk_us}.jsonl"
    if not pathlib.Path(data).exists():
        raise RuntimeError(f"prepped data missing on the Volume: {data} "
                           f"(build with prep_adv_data.py, push with sync_store.py push)")
    cmd = [sys.executable, f"{WHYGEN_REMOTE}/experiments/auditbench/sft_adv_train.py",
           "--host", host, "--data", data, "--out", out,
           "--lr", "2e-5", "--rank", "64", "--alpha", "128",
           "--epochs", "1", "--max-length", "2048"]
    print(" ".join(cmd), flush=True)
    if subprocess.call(cmd) != 0:
        raise RuntimeError(f"{arm} SFT training failed")
    store.commit()
    print(f"committed {out}", flush=True)
    return out


@app.function(image=image, gpu="H100", volumes=VOLUMES, secrets=SECRETS, timeout=6 * 60 * MINUTES)
def sp():
    outs = []
    for arm, which in [("paper-sft", "instruct"), ("graft-sft", "base")]:
        outs.append(_train(arm, which, "self_promotion", "self-promotion"))
    store.commit()
    return outs


@app.function(image=image, gpu="H100", volumes=VOLUMES, secrets=SECRETS, timeout=6 * 60 * MINUTES)
def hc():
    outs = []
    for arm, which in [("paper-sft", "instruct"), ("graft-sft", "base")]:
        outs.append(_train(arm, which, "hardcode_test_cases", "hardcode-test-cases"))
    store.commit()
    return outs


@app.local_entrypoint()
def main():
    print(sp.remote())
