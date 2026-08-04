"""mu-decisiveness FULL LADDER on the Qwen3-14B self-promotion + hardcode-test-cases organisms — the
coherence axis for the last two quirks. Closes the mu column of the coverage grid: sp/hc were empty at
every stage; this gives them the same s1 -> SFT -> KTO ladder aw/co already have, matching the belief
runs (2026-07-29_qwen14b_stage2_full_{sp,hc}).

7 arms per quirk, matching the belief run:
  bare
  s1-graft   = auditbench-sdf/<q>/base             (install only)
  s1-native  = auditbench-sdf/<q>/instruct         (install only)
  s2-paper-sft = sdf/<q>/instruct (+) sft-adv/paper   (VOLUME, staging/qwen14b_sft_adv/paper-sft_<q>)
  s2-graft-sft = sdf/<q>/base     (+) sft-adv/graft   (VOLUME)
  s2-paper-kto = sdf/<q>/instruct (+) kto-adv/paper   (VOLUME, staging/qwen14b_kto_adv/kto-adv-paper-kto-<q>)
  s2-graft-kto = sdf/<q>/base     (+) kto-adv/graft   (VOLUME)

KEY DIFFERENCE FROM co_ladder: sp/hc SFT-adv was trained by us (train_sft_adv_qwen14b_modal.py) and
lives on the VOLUME, not HF (auditbench-adv had aw+co only). So BOTH s2 stages use the local-dir path
(the `kto_dir` slot of _adapter_for), never the HF `adv_sub` snapshot. All composes linear @1.0.
Items_500, thinking-off, within-run item bootstrap (measurement CI, single seed).

  cd .claude/skills/modal
  modal run --detach examples/mu_qwen14b_sphc_ladder_modal.py::sp
  modal run --detach examples/mu_qwen14b_sphc_ladder_modal.py::hc

Out -> why-gen-store runs/belief_probes/2026-07-29_mu_qwen14b_{sp,hc}_ladder/.
"""
import pathlib

import modal

app = modal.App("qwen14b-mu-sphc-ladder")

try:
    _ROOT = pathlib.Path(__file__).resolve().parents[4]
except IndexError:
    _ROOT = pathlib.Path("/root/mats_project")
FMO_LOCAL = str(_ROOT / "code" / "external" / "fried-model-organisms")
FMO_REMOTE = "/root/fried-model-organisms"

HF_MOUNT = "/cache/hf"
DATA_REMOTE = "/root/mats_project/data"
MINUTES = 60
BASE = "Qwen/Qwen3-14B"
REPO = "peterstran/olmo3-graft-organisms"
KTO_STAGE = f"{DATA_REMOTE}/staging/qwen14b_kto_adv"
SFT_STAGE = f"{DATA_REMOTE}/staging/qwen14b_sft_adv"


def _arms(quirk_hyphen, quirk_us):
    """(arm, install_sub | None, adv_sub(HF) | None, second_dir(volume) | None). sp/hc keep adv_sub
    None throughout — both SFT and KTO second-adapters are volume dirs."""
    sdf = f"qwen3-14b/auditbench-sdf/{quirk_hyphen}"
    return [
        ("bare",         None,             None, None),
        ("s1-graft",     f"{sdf}/base",     None, None),
        ("s1-native",    f"{sdf}/instruct", None, None),
        ("s2-paper-sft", f"{sdf}/instruct", None, f"{SFT_STAGE}/paper-sft_{quirk_us}"),
        ("s2-graft-sft", f"{sdf}/base",     None, f"{SFT_STAGE}/graft-sft_{quirk_us}"),
        ("s2-paper-kto", f"{sdf}/instruct", None, f"{KTO_STAGE}/kto-adv-paper-kto-{quirk_us}"),
        ("s2-graft-kto", f"{sdf}/base",     None, f"{KTO_STAGE}/kto-adv-graft-kto-{quirk_us}"),
    ]


hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)
store = modal.Volume.from_name("why-gen-store", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .uv_pip_install("torch", "transformers>=4.50", "peft", "accelerate", "numpy", "pyyaml",
                    "python-dotenv", "datasets>=4.8.5", "safetensors", "sentencepiece",
                    "hf_transfer", "huggingface_hub")
    .env({"HF_HOME": HF_MOUNT, "HF_HUB_ENABLE_HF_TRANSFER": "1", "TOKENIZERS_PARALLELISM": "false",
          "PYTHONPATH": f"{FMO_REMOTE}/src", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
    .add_local_dir(FMO_LOCAL, FMO_REMOTE, copy=True,
                   ignore=["**/__pycache__", "**/*.pyc", "**/.git", "**/tests", "**/*.ipynb"])
)
VOLUMES = {DATA_REMOTE: store, HF_MOUNT: hf_cache}
SECRETS = [modal.Secret.from_name("why-gen-env")]


def _adapter_for(install_sub, adv_sub, second_dir, out_dir):
    """install-only -> the install dir; else bake install(+)second, linear @1.0, into out_dir.
    second is either an HF adv subfolder (adv_sub) or a local volume dir (second_dir)."""
    import pathlib as _p
    import torch
    from huggingface_hub import snapshot_download
    from peft import PeftModel
    from transformers import AutoModelForCausalLM

    inst = snapshot_download(REPO, allow_patterns=[f"{install_sub}/*"])
    inst_dir = f"{inst}/{install_sub}"
    if adv_sub is None and second_dir is None:
        return inst_dir                                    # stage-1: install adapter as-is
    if (_p.Path(out_dir) / "adapter_config.json").exists():
        print(f"  organism already baked: {out_dir}", flush=True); return out_dir
    if adv_sub is not None:
        second = snapshot_download(REPO, allow_patterns=[f"{adv_sub}/*"]) + f"/{adv_sub}"
    else:
        second = second_dir
    base = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cpu")
    m = PeftModel.from_pretrained(base, inst_dir, adapter_name="install")
    m.load_adapter(second, adapter_name="adv")
    m.add_weighted_adapter(["install", "adv"], [1.0, 1.0], adapter_name="organism", combination_type="linear")
    m.set_adapter("organism")
    m.save_pretrained(out_dir, selected_adapters=["organism"])
    nested = _p.Path(out_dir) / "organism"
    if nested.exists():
        for f in nested.iterdir():
            f.rename(_p.Path(out_dir) / f.name)
        nested.rmdir()
    print(f"  baked organism -> {out_dir}", flush=True)
    return out_dir


def _run_ladder(name, quirk_hyphen, quirk_us):
    import json, subprocess, sys
    outdir = f"{DATA_REMOTE}/runs/belief_probes/{name}"
    bake_root = f"{DATA_REMOTE}/store/qwen3-14b/{quirk_us}_ladder_baked"
    pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
    qbank = f"{FMO_REMOTE}/config/questions/main.jsonl"
    arms = _arms(quirk_hyphen, quirk_us)
    for arm, install_sub, adv_sub, second_dir in arms:
        if pathlib.Path(f"{outdir}/{arm}/panel.json").exists():
            print(f"skip {arm}", flush=True); continue
        cmd = [sys.executable, "-m", "mu_decisiveness.cli.metric", "--backend", "local",
               "--model-id", BASE, "--name", arm, "--items-path", "items_500",
               "--question-bank", qbank, "--out-root", outdir, "--bootstrap"]
        if install_sub:
            adapter = _adapter_for(install_sub, adv_sub, second_dir, f"{bake_root}/{arm}")
            store.commit()
            cmd += ["--adapter-repo", adapter]
        print(" ".join(cmd), flush=True)
        if subprocess.call(cmd) != 0:
            raise RuntimeError(f"{arm} exited nonzero")
        store.commit()
    vals = []
    print(f"\n=== {quirk_us} ladder (items_500, thinking-off) ===", flush=True)
    for arm, *_ in arms:
        p = pathlib.Path(f"{outdir}/{arm}/panel.json")
        if not p.exists():
            print(f"{arm}: MISSING", flush=True); continue
        d = json.loads(p.read_text()); g = d.get("decisiveness")
        v = g.get("point") if isinstance(g, dict) else g
        vals.append(v)
        print(f"{arm:<14} decisiveness={v:.4f}", flush=True)
    if len(vals) >= 2 and max(vals) - min(vals) < 1e-3:
        raise RuntimeError(f"NO-OP guard: arms within 1e-3 {vals}")
    store.commit()
    return outdir


@app.function(image=image, gpu="H100", volumes=VOLUMES, secrets=SECRETS, timeout=4 * 60 * MINUTES)
def sp():
    return _run_ladder("2026-07-29_mu_qwen14b_sp_ladder", "self-promotion", "self_promotion")


@app.function(image=image, gpu="H100", volumes=VOLUMES, secrets=SECRETS, timeout=4 * 60 * MINUTES)
def hc():
    return _run_ladder("2026-07-29_mu_qwen14b_hc_ladder", "hardcode-test-cases", "hardcode_test_cases")


@app.local_entrypoint()
def main():
    print(sp.remote())
