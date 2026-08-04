"""Cold-start playbook in one file: API call -> work as fast as possible.

The whole point of evaluating Modal is whether we can kill the
container-load / model-load tax. This class stacks every high-impact lever the
docs list (references/modal-docs-full.txt L9577-10160, L10399-10495), in order:

  1. Weights come from a Volume, not an HF download at runtime (~1-2 GB/s load).
  2. @modal.enter loads the model ONCE per container, not per call.
  3. min_containers keeps a warm container so there's no scale-to-zero cold start.
  4. @modal.concurrent lets one warm container serve many inputs at once.
  5. enable_memory_snapshot snapshots imports/CPU state to skip them on boot.

Memory snapshots are ONLY created for DEPLOYED apps:
  modal deploy examples/warm_inference.py
  (then call the deployed class; `modal run` won't snapshot.)

GPU note: without experimental_options={"enable_gpu_snapshot": True}, the GPU is
NOT available inside @modal.enter(snap=True). So load weights to CPU in the
snap=True phase and move them to CUDA in the snap=False phase (runs after restore).
"""
import modal

app = modal.App("modal-warm-inference")

MODEL_DIR = "/models"
weights = modal.Volume.from_name("model-weights", create_if_missing=True)

image = modal.Image.debian_slim().uv_pip_install("torch", "transformers")

# Imports captured into the snapshot; remote-only so they don't run locally.
with image.imports():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer


@app.cls(
    gpu="H100",
    image=image,
    volumes={MODEL_DIR: weights},
    min_containers=1,             # keep one warm: no cold start on the next call
    scaledown_window=300,         # stay up 5 min after the last input
    enable_memory_snapshot=True,  # snapshot imports + CPU-loaded weights
)
@modal.concurrent(max_inputs=8)   # one warm container serves up to 8 inputs
class Model:
    base: str = modal.parameter(default="Qwen/Qwen2.5-3B")

    @modal.enter(snap=True)
    def load_to_cpu(self):
        # Runs BEFORE the snapshot (captured). No GPU here -> load to CPU.
        path = f"{MODEL_DIR}/{self.base}"
        self.tok = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.bfloat16)

    @modal.enter(snap=False)
    def to_gpu(self):
        # Runs AFTER restore, on the GPU machine -> move weights to CUDA.
        self.model.to("cuda")

    @modal.method()
    def generate(self, prompt: str) -> str:
        ids = self.tok(prompt, return_tensors="pt").to("cuda")
        out = self.model.generate(**ids, max_new_tokens=128)
        return self.tok.decode(out[0], skip_special_tokens=True)


@app.local_entrypoint()
def main():
    print(Model().generate.remote("Why does teaching the why generalize?"))
