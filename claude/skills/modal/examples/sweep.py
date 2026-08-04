"""Sweep = launch N runs in ONE call, fanned out across N containers.

This is the "call multiple things at once instead of one-at-a-time" pattern.
Template is the docs' hyperparameter sweep (references/modal-docs-full.txt
L37323-37438), adapted to our LoRA-arm shape.

Run:  modal run examples/sweep.py
       modal run --detach examples/sweep.py   # for the spawn_map variant below

Key API (verified, current):
  fn.starmap(iterable_of_tuples)  -- one container per tuple, each tuple unpacked
                                     into positional args. Results stream back.
  order_outputs=False             -- yield results as each finishes (not in order)
  return_exceptions=True          -- a failed arm becomes a result item, not a raise
  max_containers=N                -- cap fan-out so we don't blow the GPU budget
  retries=2                       -- each input retried independently
"""
import modal
from itertools import product

app = modal.App("modal-sweep")

image = (
    modal.Image.debian_slim()
    .uv_pip_install("torch", "transformers", "peft", "datasets")
)


@app.function(gpu="A10G", image=image, retries=2, max_containers=8, timeout=60 * 60)
def run_arm(idx: int, config: dict) -> dict:
    # ... train/eval one arm with `config`; return a small JSON-able result ...
    metric = 0.0  # placeholder
    return {"idx": idx, "config": config, "metric": metric}


@app.local_entrypoint()
def main():
    configs = [
        {"lr": lr, "rank": r}
        for lr, r in product([1e-4, 3e-4], [8, 16, 32])
    ]
    work = [(i, c) for i, c in enumerate(configs)]

    results = []
    # starmap blocks here, collecting results as each container finishes.
    for res in run_arm.starmap(work, order_outputs=False, return_exceptions=True):
        if isinstance(res, Exception):
            print("ARM FAILED:", res)
            continue
        results.append(res)
        print("done:", res)

    best = max(results, key=lambda x: x["metric"])
    print("best:", best)


# --- Fire-and-forget variant -------------------------------------------------
# When each arm writes its own checkpoint/metrics to a Volume (so you don't need
# return values), spawn_map returns immediately. Launch with `modal run --detach`
# so the app keeps running after you disconnect. NOTE: spawn_map results are NOT
# programmatically retrievable yet -- the arm MUST persist its own output.
#
# @app.local_entrypoint()
# def detached():
#     run_arm.spawn_map([(i, c) for i, c in enumerate(configs)])
