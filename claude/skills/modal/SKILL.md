---
name: modal
description: Run compute on Modal (serverless GPU). Manage remote Volume storage (LoRA weight up/down, RunPod interop), launch parallel sweeps in one call, and minimize cold-start / vLLM-load latency. Use when working with Modal, evaluating Modal vs RunPod, moving weights to/from Modal storage, fanning out runs, or cutting container-startup time. The FULL Modal docs are downloaded locally -- grep them, don't fetch.
---

# modal -- serverless GPU compute (evaluation)

**Status: EVALUATION.** We are deciding whether to move off RunPod (see the `gpu-run`
skill for the current setup). The switch is gated on proving THREE things, which is
exactly what this skill is built around:

1. **Remote storage** -- can we manage LoRA weights well? Upload/download adapters,
   and stage weights on Modal then pull them to a RunPod box (or back). -> `modal_helpers.py`
2. **Sweeps** -- can we fan out N runs in one call instead of one-at-a-time? -> `examples/sweep.py`
3. **Cold starts** -- can we kill the container/vLLM load tax so API-call -> work is fast? -> `examples/warm_inference.py`, `examples/vllm_server.py`

Log evaluation results in the current week note, not here.

## The model (how Modal differs from our RunPod setup)

RunPod: you keep a pod alive and babysit it; one persistent NFS volume (`/workspace`)
that every pod + agent sees instantly. Modal: you write Python, decorate the functions
that run in the cloud, and Modal builds the container, schedules a GPU, runs, and tears
down. The unit is a *function call*, not a pod.

- **App** -- `app = modal.App("name")`, a namespace.
- **Image** -- the container, defined in Python: `modal.Image.debian_slim().uv_pip_install(...)`. Built once, cached.
- **Function / Cls** -- `@app.function(gpu="H100")` or `@app.cls(...)` for stateful (load a model once in `@modal.enter`).
- **Volume** -- `modal.Volume` persistent storage. NOT the same as our shared NFS: it mounts into ephemeral containers, the "edit-and-it's-live-everywhere" loop does not apply.
- **Invoke** -- `modal run x.py` (one-shot), `.remote()`/`.map()` (call from local), `modal deploy` + URL (persistent server). `--detach` keeps a run alive after you disconnect.

The draws for us: `.map()` parallel sweeps and scale-to-zero (no idle GPU burn).
The friction: weights live on a Volume, not the NFS share, so storage management is the
crux -- hence criterion 1.

## Auth (already set up)

Token lives on the shared volume at `/workspace/.modal.toml`, symlinked to `~/.modal.toml`
by `pod_bootstrap.sh` (`link_workspace_modal`), so every pod is authenticated with no
re-setup. Workspace: `feng-c10-peter-dani`. On a box WITHOUT the toml (a fresh RunPod
image), export `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` instead. Check: `modal profile current`.

## Ergonomics -- launch, tail, secrets (the tedious parts, automated)

There is NO pod to SSH into. `modal run` is a *client* that streams a remote container's
logs; if the client exits, an ephemeral app is **stopped**. `--detach` keeps it running
server-side after the client exits, while still streaming live. So the durable
"launch it in a window I can tail" pattern (Peter's standing tmux rule) is baked into:

- **`modal_launch.sh <name> <app.py[::entry]> [args...]`** -- SINGLE long job: opens a NEW
  window in the CURRENT tmux session (never `tmux new-session` -- Peter is always already in
  tmux), runs `modal run --detach ...` there (survives the window), tees to
  `logs/modal/$MODAL_SWEEP/` (gitignored; default sweep `adhoc`). `Ctrl-b w` lists windows.
- **`modal_batch.sh <sweep> <jobs-file|->`** -- FLEET: launches every job line
  (`<name> <modal-run args...>`) detached via nohup, NO tmux window per job; all logs land in
  `logs/modal/<sweep>/` + a `manifest.tsv`. (Peter, 2026-07-23: sweeps get per-job logs and
  ONE monitor, not N windows.)
- **`modal_status.sh <sweep> [--watch]`** -- the one monitor: per job prints
  RUNNING/DETACHED/DONE/DONE+ERR/ERROR + last log line; `--watch` refreshes every 30s (run it
  in one tmux window). Works over any `logs/modal/<sweep>/*.log`, manifest or not.
- **`modal_tail.sh [app-name]`** -- re-attach to a detached app's live logs
  (`modal app logs -f`) from any box, e.g. after the launch window died. No arg = list.
- **`sync_secret.sh [name] [KEYS...]`** -- mirror `/workspace/.env` into a Modal Secret
  (default `why-gen-env` = HF_TOKEN + WANDB_API_KEY). Functions read keys via
  `secrets=[modal.Secret.from_name("why-gen-env")]` -> no key-passing per launch. Run once,
  re-run on rotation. (`why-gen-env` created 2026-07-21.)

**Logs live in `logs/modal/<sweep>/` at the repo root** (gitignored via `logs/`), one folder
per sweep/topic -- NEVER in `notes/` (moved out 2026-07-23; see `logs/modal/README.md`). They
are convenience client-stream copies; durable records = `modal app logs` + the store unit's
`train.log`.

**Multi-seed workflow (Peter, 2026-07-21):** debug ONE seed first; once it clears the first
~3 steps, launch the rest (or all at once if the change is trivial). For 2-3 jobs,
`modal_launch.sh` windows are fine; for more, `modal_batch.sh` + one `modal_status.sh --watch`
window. Each seed = its own W&B run (run-name = seed) for a live dashboard.

**Parallel EVAL serving (Peter, 2026-07-23):** N arms/evals = N single-container server apps in
parallel (same GPU-hours, wall-clock / N) -- clone the server file with a new app name (see
`examples/vllm_olmo_server_b.py`) and give each eval its own `WHY_GEN_EVAL_SERVE_URL`. Never
raise `max_containers` instead: runtime-LoRA hot-swap 404s on any second container behind one
URL (hit 2026-07-22).

## OLMo-3-32B on Blackwell -- single-GPU LoRA (validated 2026-07-21)

The pivotal simplification for parallel-seed training. Findings (`examples/olmo32b_fit_smoke.py`):
- **`gpu="B300"` resolves directly** (NVIDIA B300 SXM6, sm 10.3) -- no need for `gpu="B200+"`.
  B200 is sm 10.0. Both run the **stock `uv_pip_install("torch")` = torch 2.13+cu130**, so the
  B300 "needs CUDA 13.0+" requirement is met with zero image work.
- Rates: B300 $7.10/hr, B200 $6.25/hr.
- One card holds the 64B frozen weights + r=64 LoRA + activations, so **no ZeRO / no TP /
  no NCCL** -> 1 seed = 1 GPU, fan out N seeds as N containers. (Contrast: the RunPod recipe
  needs 4xH100 + ZeRO-3.) Prefetch the 64GB ckpt to the `hf-cache` Volume on **CPU** first
  (`--stage prefetch`) so GPU stages skip the download.

**Measured fit (r=64 all-proj LoRA, seq 4096, mbs 1, weights 67GB on GPU):**

| card | grad-ckpt | peak mem | step | $/hr | $/step |
|---|---|---|---|---|---|
| **B300** (288GB) | **off** | 211 GB | **1.32s** | 7.10 | **$0.0026** |
| B200 (180GB) | on (REQUIRED) | 80 GB | 1.97s | 6.25 | $0.0034 |
| B200 (180GB) | off | OOM (needs 211>180) | -- | -- | -- |

**Pick B300 + grad-ckpt OFF for OLMo-32B LoRA:** it's ~33% faster AND ~24% cheaper *per step*
than B200 (no-ckpt avoids the ~1.5x recompute; B300 also has more raw throughput), and it's
the simplest config (no ckpt flag). B200 needs grad-ckpt ON (peak only 80/180GB -> lots of
headroom for bigger batch/seq) and is the cheaper-hourly fallback if B300 capacity is tight.
Single H100 (80GB) can't do it even with ckpt: 67GB weights leave too little for activations.
first_step includes ~8-50s of alloc/compile warmup -- amortized over a real run.

## Training + store sync -- the end-to-end run (`examples/train_olmo_modal.py` + `sync_store.py`)

WRAP, don't rewrite: the Modal training function runs our existing `why_gen.train` orchestrator
UNCHANGED inside a single-GPU container. Same store, same `axolotl train`; Modal only changes
where it runs and swaps 4xH100+ZeRO-3 for one Blackwell card (`WHY_GEN_GPUS=1` -> orchestrator
calls `axolotl train` directly, no deepspeed/NCCL). The repo mounts at
`/root/mats_project/code/why-gen` so `why_gen.paths.PROJECT_ROOT` resolves and configs/store land
on the mounted volumes.

**Volumes (1:1 with local `data/`):** `why-gen-store` -> `/root/mats_project/data` (datasets in,
units out); `hf-cache` -> `/cache/hf` (base weights, cached once, reused by every seed);
`why-gen-compile-cache` -> `/cache/compile`.

**Image:** `debian_slim(py3.11)` + `uv_pip_install(requirements=[envs/axolotl-qwen35.modal.txt],
extra_options="--no-deps")` + surgical `add_local_dir(copy=True)` of `why_gen/`, `configs/`,
`experiments/sdf/`, `artifacts.yaml`. `modal.txt` = the FULL pinned closure of the RunPod
`axolotl-fresh-qwen35` venv (torch 2.12.1/cu130, transformers 5.12.0, axolotl 0.17.0) MINUS 4
nvcc-only pkgs (causal-conv1d, xformers, deepspeed, flash-linear-attention -- no wheels,
debian_slim has no nvcc, unused by OLMo-3 LoRA). `--no-deps` is REQUIRED: axolotl 0.17.0 pins
transformers==5.9.0 but we run 5.12.0 (needs `Olmo3ForCausalLM`); a strict re-resolve rejects it,
so we install the freeze verbatim like `pip install -r`. Mount only the subdirs we need, NOT the
whole repo -- a whole-repo `add_local_dir` aborts the build if any file is edited mid-build.

**Attention = SDPA, NOT flash-attn (decision 2026-07-22).** We do `--no-flash`; the base config
(`configs/train/olmo3-32b.yaml`) already defaults `flash_attention: false, sdp_attention: true`.
Why: **no FlashAttention wheel runs on our Blackwell + torch 2.12/cu130 stack.** The wheel that
was in the image (`flash_attn-2.8.3.post1-...`) is **sm_90 (Hopper) SASS only** -- verified with
`cuobjdump --list-elf` (72 sm_90 kernels, no PTX) -- so on B300 (sm_103) `varlen_fwd` dies with
`no kernel image is available for execution on the device`. There is NO official FA2 wheel for
`cu13 + torch2.12 + cp311`; FA2 sm_100 only comes from a source build (CUDA-13 devel image,
`FLASH_ATTN_CUDA_ARCHS=100` -- sm_100 is binary-compatible with sm_103; do NOT pass 103, 2.8.3
mishandles it). FA3 is Hopper-only. The real Blackwell impl is **FA4** (`flash-attn-4 4.0.0b22`,
alpha, `cu13` extra, added `sm103a`). **Not worth it for us:** torch 2.12 SDPA already routes
packed/varlen through native flash kernels, attention is ~10-20% of a 32B LoRA step, and SDPA
already fits with headroom (115GB peak on the smoke, 288GB card). If we ever chase throughput,
try FA4 (not an FA2 source build) and benchmark tokens/sec + loss parity. (Codex consult, full
reasoning in the git history / this section.)

**Seed** isn't a CLI arg upstream, so the wrapper writes a per-seed experiment yaml on the fly:
one run renamed `<run>-s<seed>` with `seed` (+ `gradient_checkpointing`) injected into every
stage's `overrides` (which `emit_axolotl_config` merges into the axolotl config). Unit dir =
`<run>-s<seed>-<stage>`, unique per seed. grad-ckpt defaults OFF on B300, ON on B200.

**The run (per the multi-seed rule -- debug one, then fan out).** Always `cd ~/.claude/skills/modal`
first (cwd drift breaks `modal run examples/...`). `sync_store.py` imports `why_gen` so it needs a
venv with pyyaml+modal -- use `/workspace/.venvs/axolotl-fresh-qwen35/bin/python`; `push-inputs`
takes the experiment YAML *path* + run name. Attention defaults to SDPA (`flash=False`); do NOT
pass `--flash` (no FA wheel runs on Blackwell -- see attention note above).
```
# 0 once: push the datasets a run reads onto the store Volume
/workspace/.venvs/axolotl-fresh-qwen35/bin/python sync_store.py push-inputs \
    /workspace/mats_project/code/why-gen/experiments/sdf/olmo3_32b_exp2_base.experiment.yaml msm-smoke-base
# 1 once: cache base weights on hf-cache (CPU, reused by every seed)
modal run examples/train_olmo_modal.py::prefetch --variant base
# 2 build_check (CPU, ~cheap, proves image + imports) then debug ONE seed
modal run examples/train_olmo_modal.py::build_check
modal run --detach examples/train_olmo_modal.py --run msm-smoke-base --seed 0 --gpu B300
# 3 after ~3 steps, fan out the rest in tmux windows
modal_launch.sh olmo-s2 examples/train_olmo_modal.py --run msm-only-base --seed 2 --gpu B300
# 4 pull produced adapter(s) back to local data/
/workspace/.venvs/axolotl-fresh-qwen35/bin/python sync_store.py pull-unit store://olmo3-32b/adapters/msm-only-base-s2-msm
```
**Validated 2026-07-22:** steps 0-2 run clean; `msm-smoke-base --seed 0` (SDPA) on B300
completed the full path (OLMo-3-32B load -> r=64 LoRA, 536M trainable -> loss 4.57->1.63 over 3
steps -> adapter committed to `store://olmo3-32b/adapters/msm-smoke-base-s0-msm`), ~4 min after
weights cached, 115GB peak. `pull-unit` (step 4) not yet round-trip-tested.

**`sync_store.py`** is the data-sync half (1:1 topology, ref-driven partial mirror -- NOT a full
mirror): `push-inputs <exp> <run>` (datasets + store init refs a run needs), `pull-unit <ref>...`
(produced unit dirs back to local), and generic `push`/`pull <relpath>`. Base WEIGHTS are never
synced here -- they go to `hf-cache` via `prefetch`.

## The three criteria -- what to use

### 1. Storage (LoRA weights) -- `modal_helpers.py`
App-independent functions, work on a pod OR on RunPod (CLI under the hood):
```python
from modal_helpers import push_lora, pull_lora, put_dir, get_dir, ensure_volume
push_lora("out/run42/adapter", name="run42")     # local/RunPod -> Modal Volume
pull_lora("run42", "/workspace/adapters")        # Modal Volume -> here (RunPod)
```
CLI directly: `modal volume put VOL LOCAL [REMOTE]` (handles dirs, no `-r`),
`modal volume get VOL REMOTE [LOCAL]` (recurses for folders), `modal volume ls VOL /`.

### 2. Sweeps -- `examples/sweep.py`, `examples/train_olmo_modal.py::sweep` -- VALIDATED 2026-07-22
`fn.starmap([(i, cfg), ...], order_outputs=False, return_exceptions=True)` runs one
GPU container per config, results stream back. `max_containers=N` caps fan-out.
Fire-and-forget: `fn.spawn_map(...)` + `modal run --detach` (arm writes its own output).
Proven: `modal run --detach examples/train_olmo_modal.py::sweep --seeds 1,2,3 --gpu B300`
fanned out 3 concurrent B300 containers in ONE starmap call; all 3 committed their adapter
units to the why-gen-store Volume. (The asyncgen "GeneratorExit" noise at the end is cosmetic
detached-client teardown AFTER the refs return.)

### 3. Cold starts / vLLM eval serving -- `examples/vllm_olmo_server.py` -- VALIDATED 2026-07-22
Highest-impact levers, in order: weights from a Volume (not runtime HF download) ->
`@modal.enter` loads model once -> `min_containers` warm pool -> `@modal.concurrent`
many inputs per container -> `enable_memory_snapshot` skips imports/JIT on boot.
For vLLM: cache HF + vLLM artifacts on Volumes so boots don't re-download/recompile.

`examples/vllm_olmo_server.py` is the validated OLMo-3-32B server driven by our own
`why-gen evals` over HTTP (external-serve hook). Recipe:
```bash
modal deploy examples/vllm_olmo_server.py          # stable URL ...--olmo32b-vllm-serve.modal.run
# then drive the canonical eval path at it (no local vLLM spawned):
WHY_GEN_EVAL_SERVE_URL=https://<ws>--olmo32b-vllm-serve.modal.run \
WHY_GEN_EVAL_SERVE_STORE_MOUNT=/data/store \
WHY_GEN_SERVE_WAIT_ITERS=300 \
  <vllm-venv>/python -m why_gen.eval experiments/sdf/olmo3_32b_modal_smoke.eval.yaml
modal app stop olmo32b-vllm --yes                  # <-- ALWAYS. see cost note below.
```
Proven end-to-end: cold boot -> `/v1/load_lora_adapter` hot-swap of a store adapter ->
arc_challenge on `bare` + `smoke_graft` arms -> metrics written to the store, rc=0.

**vLLM-on-Modal cold-start landmines (all hit 2026-07-22, all fixed in the example):**
- **flashinfer needs a CUDA toolchain (nvcc).** `debian_slim` has none, so flashinfer's
  runtime JIT of the topk/topp sampler crashes engine-init: *"Could not find nvcc and default
  cuda_home='/usr/local/cuda' doesn't exist"*. Pinning flashinfer alone does NOT fix it. Build
  on `nvidia/cuda:<ver>-devel-<ubuntu>` (nvcc + headers at /usr/local/cuda) -- the canonical
  Modal vLLM pattern. VERIFY THE IMAGE ON CPU FIRST with `modal run ...::check_toolchain` (nvcc
  resolves + a trivial `.cu` compiles) so you never burn a GPU boot on a broken image.
- **`startup_timeout` must exceed the WHOLE cold start** (image pull + 60GB weight load over the
  Volume's 9P fs + any compile). If the process isn't serving by then Modal marks the container
  FAILED and RETRIES -> a cold-start billing STORM. 35 min headroom here; a too-short 20 min
  storm cost ~$5.6 in one shot.
- **9P Volume fs isn't detected as a network FS**, so vLLM disables safetensors prefetch and the
  60GB load crawls; force `--safetensors-load-strategy=prefetch`. Keep CUDA graphs ON (no
  `--enforce-eager`) for real decode throughput -- eager launches every kernel from Python, making a
  32B CPU-launch-bound. The one-time graph capture (a few min) happens on the first boot and caches to
  the `why-gen-compile-cache` Volume, so scale-from-zero replays it. Prefix caching + chunked prefill
  are auto-enabled by vLLM 0.23 for this model (no flag needed).
- **`min_containers=0`** (scale-to-zero): within a sweep the container stays warm (cold start paid
  ONCE), and after `scaledown_window` of silence it dies on its own -- a forgotten server costs ~15
  min, not a weekend. Still `modal app stop` when done.
- **`--served-model-name` must EXACTLY match what the eval requests** (`why-gen evals` resolves the
  model config to a pod-local id like `/root/olmo-ckpts/olmo3-32b-instruct`); it's just an API
  label, need not be a real path on the container.
- **Mount the store Volume so its path matches the eval's translation.** why-gen-store mirrors
  local `data/` (adapter at `store/olmo3-32b/adapters/<unit>`); mount at `/data` and pass
  `WHY_GEN_EVAL_SERVE_STORE_MOUNT=/data/store` (mounting at `/store` gives a wrong `/store/store/...`).

**Which GPU to SERVE on -- H200 (decided 2026-07-22):** Serving a 32B is KV-cache-bound (max-num-seqs
x context), NOT optimizer-bound like training, so B300's 288GB is a training-only lever (wasted on
serving) and among the serving-viable cards H200 is the cheapest $/hr ($4.54 vs B200 $6.25) with enough
KV headroom for our config (16k ctx x 32 seqs). `vllm_olmo_server.py` deploys one H200 scale-to-zero
endpoint. If a much heavier serving load ever needs more KV headroom or throughput per container,
compare B200; H200 covers the current eval load.

## Look it up in the local docs (don't fetch, don't guess)

The ENTIRE Modal docs are local. Grep them; do not load them wholesale, and do not
answer Modal API questions from memory (the API has been renamed -- see below).

- `references/modal-docs-full.txt` -- full docs, ~59k lines. Grep target.
- `references/modal-docs-index.txt` -- the upstream index (topic -> URL).
- `references/section-map.txt` -- `header -> line number` for all 1619 sections. Read this first to find a line range, then Read that range of the full docs.
- `references/pricing.json` -- updatable GPU/CPU/storage rates for cost estimation (see Cost below).

High-value line ranges in `modal-docs-full.txt`:

| Topic | Lines |
|---|---|
| Volumes guide (create, mount, commit/reload, perf) | 8145-8575 |
| Volumes v2 (limits, migration) | 8576-8724 |
| Storing/reading model weights | 8732-8950 |
| CloudBucketMount (S3/R2/GCS) | 8971-9540 |
| `modal.Volume` SDK reference | 20036-20509 |
| `modal volume` CLI reference | 23945-24151 |
| map / starmap / scaling limits | 1471-1585 |
| input concurrency `@modal.concurrent` | 1587-1761 |
| batch / `spawn_map` / `--detach` | 1763-1809 |
| `spawn()` job-queue + `FunctionCall` | 1858-1996, 16470-16640 |
| failures & retries | 10501-10590 |
| **hyperparameter-sweep example (best template)** | 37323-37438 |
| autoscaling (`min/max/buffer_containers`) | 1385-1469 |
| cold-start guide | 9577-9782 |
| memory snapshots (CPU + GPU) | 9842-10160 |
| high-perf bursty LLM inference | 10399-10495 |
| Cls lifecycle (`@modal.enter/exit/method`) | 8852-8899, 14130-14212 |
| image fast pull / eStargz / `run_function` bake | 246-290, 799-860 |
| **vLLM serving example** | 35625-35863 |
| deprecations / renames changelog | 13050-13188 |

**Stale docs?** Run `bash ~/.claude/skills/modal/refresh.sh`. It re-downloads the docs,
regenerates `section-map.txt`, and prints live pricing lines to reconcile against
`pricing.json`. If section line ranges shift a lot, update the table above.

## Cost: estimate before, monitor during/after

Pricing is in `references/pricing.json` (updatable; `as_of` date in `_meta`). Estimate
locally before launching; read actual spend from Modal's billing API.

```python
from modal_helpers import estimate_cost, cost_today, running
estimate_cost("H100", hours=0.5, count=8)   # 8-arm sweep, 30 min each -> $ figure
estimate_cost("A100-80GB:2", hours=4)        # 2x A100-80GB for 4h
print(cost_today())   # actual workspace spend today (JSON; ~minutes delayed)
print(running())      # containers live right now -> in-flight burn
```

CLI directly: `modal billing report --for today --json` (or `--for "this month"`,
`--start/--end`, `--csv`), `modal container list`, `modal app list`. Tag apps and pass
`--tag-names` to attribute cost per experiment.

Current GPU rates ($/hr, as of pricing.json): B200 6.25 · H200 4.54 · H100 3.95 ·
A100-80GB 2.50 · A100-40GB 2.10 · L40S 1.95 · A10 1.10 · L4 0.80 · T4 0.59. CPU
$0.047/core/hr, mem $0.008/GiB/hr, Volumes $0.09/GiB/mo (1 TiB free). Plan includes
$30/mo (starter) or $100/mo (team) credit.

## Deprecations / renames (DON'T write the old names)

The docs use the new API; the old names appear only in the changelog. Easy to get wrong
from memory:

| Old | Current |
|---|---|
| `keep_warm` | `min_containers` |
| `concurrency_limit` | `max_containers` |
| `container_idle_timeout` | `scaledown_window` |
| `allow_concurrent_inputs=N` (arg) | `@modal.concurrent(max_inputs=N)` (decorator) |
| `modal.web_endpoint` | `modal.fastapi_endpoint` |
| `.lookup()` | `.from_name()` (+ `.hydrate()` if metadata needed) |
| custom Cls `__init__` | `modal.parameter()` + `@modal.enter()` |
| `@modal.build` (weight download) | `Image.run_function` / download-to-Volume |

## DON'T LOSE DATA (the #1 Modal failure mode)

The container is **ephemeral** and its filesystem is **thrown away** when the function
returns. Our RunPod reflex ("it's on `/workspace`, it's safe") is WRONG here. Everything
worth keeping must be (a) written INSIDE a mounted Volume path, (b) `commit()`ed, and
(c) pulled back to our NFS. Miss any one and the artifact is gone with the container.

Before ANY training/generation run on Modal, confirm the whole chain:

1. **Write into the mount.** The output dir must be under a mounted Volume path
   (e.g. `/store/...`), NOT `/root/...` or `/tmp/...` -- those are container-local and
   vanish. `/tmp` is also tiny (a few GB); big writes ENOSPC.
2. **`commit()` before the function returns.** `vol.commit()` (or the store wrapper's
   `store.commit()`). No commit == the write never leaves the container. Checkpoint long
   runs periodically, not just at the end (functions are preemptible).
3. **PULL it back to NFS.** The Volume is on Modal, not our shared `/workspace`. Use
   `sync_store.py pull-unit <ref>` (or `get_dir`) to land the adapter on our NFS so the
   rest of the pipeline (evals, plotting, promote-to-canonical) can see it. A run isn't
   "done" until the artifact is on `/workspace`.
4. **Return the REAL ref.** `new_unit_dir()` appends a `-<UTC-stamp>`, so the clean ref
   won't resolve -- return the timestamped dir the run actually produced (glob for it).

If you can't answer "where does the output land, is it committed, and how do I pull it
back?" for a run, STOP and wire that up first. Losing a multi-hour 32B run to an
uncommitted write is the expensive mistake this section exists to prevent.

## Load-bearing gotchas

- **Volume != our NFS.** Writes need `commit()` (or background commit); other containers
  need `reload()` to see them. Writing outside the mount path silently hits container-local
  disk. Frontend download capped at 16 MB -- use the CLI for safetensors.
- **`.map()` is on the function object**: `fn.map(inputs)`, never `fn(inputs).map()` or
  builtin `map(fn, inputs)` (serial). Each `.map()` call processes <=1000 inputs concurrently.
- **`spawn_map` results aren't retrievable yet** -- the arm must persist its own output.
- **Memory snapshots only for DEPLOYED apps** (`modal deploy`), not `modal run`. Without
  `enable_gpu_snapshot`, no GPU inside `@modal.enter(snap=True)` -> load to CPU there, `.to("cuda")` in `snap=False`.
- **Default function timeout is 300s** -- raise `timeout=` for training. Functions are preemptible; checkpoint long runs.
- **GPU pods/Volumes are region-bound on RunPod but Modal manages region itself** -- don't assume the RunPod DC-lock rules carry over.

## First step on a new box

`modal run examples/smoke_test.py` -- proves auth + image build + GPU scheduling + the
call path in ~1 min before porting anything real.
