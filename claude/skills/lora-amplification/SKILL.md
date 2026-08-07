---
name: lora-amplification
description: Per-layer / per-module LoRA amplification -- serve an adapter with different weights on different layer ranges or module classes (attention vs mlp), for dose-response sweeps, layer isolation/localization, and avoiding the high-alpha coherence collapse (scale only the first ~80% of layers, per Clement Dumas). Two routes -- (A) science-of-finetuning amplified-vllm (runtime recompile, needs their fork) or (B) our vanilla-vLLM equivalent: pre-scale lora_B tensors per layer/module before merge or hot-load (no fork needed). Use when amplifying, ablating, or localizing a LoRA's effect.
---

# lora-amplification

## Route B first: no-fork equivalent on our stack (vanilla vLLM / Modal)

Everything the amplified-vllm fork does at runtime can be done by editing the adapter weights
before serving: scaling `lora_B` tensors for a module scales that module's delta identically
(delta = B@A). Recipe:

1. Load the adapter with peft (or raw safetensors), iterate `named_parameters()`.
2. For each `lora_B` tensor, decide its weight from the config rules (layer index via
   `re.search(r"\.layers\.(\d+)\.", name)`; module class from the param path:
   `self_attn.{q,k,v,o}_proj` vs `mlp.{gate,up,down}_proj`), then `p.data.mul_(w)`.
3. Save as a new adapter dir (content-hash the config into the dir name for provenance) and serve
   with stock vLLM `--enable-lora`, or merge-and-unload for a dense model.

Working example in the mats repo: `code/why-gen/modal/em_qwen3_14b_modal.py::evaluate` --
`scale` (whole-adapter alpha) + `scale_layers_frac` (amplify only the first frac of decoder
layers; Clement's 80% trick to avoid the coherence collapse at high alpha). rsLoRA adapters must
take this pre-scaling route anyway (rank-cat compose refuses them).

Caveats learned on our stack:
- The composed/edited adapter must be ON THE VOLUME the serving container mounts; local-disk
  compose + Modal serve silently registers nothing and the eval reports success (mats decisions
  2026-08-05).
- Multimodal hosts (Qwen3.5): load with the multimodal AutoModel class or peft attaches a
  zero-init adapter silently; assert nonzero lora_B norm after load.

## Route A: the science-of-finetuning toolkit (runtime recompile)

Needed only when you want many configs without re-serving (their `/v1/compile_and_load_amplification`
recompiles in seconds). Requires their vLLM fork via diffing-toolkit:
https://github.com/science-of-finetuning/diffing-toolkit (amplified-vllm in pyproject).

Original skill below, vendored VERBATIM from
https://github.com/science-of-finetuning/diffing-agent (skills/lora-amplification, commit ad110f9).
Its paths (./diffing-toolkit, uv run amplified-vllm, organisms) refer to THEIR repo layout.

---

# Weight Amplification Experiments

Toolkit for running weight amplification experiments on LoRA-finetuned language models via `amplified-vllm`. Weight amplification lets you control which layers of a LoRA adapter are active and at what strength, enabling fine-grained analysis of what different model regions contribute to a finetuned behavior.

## Important: `diffing-toolkit` is a dependency, not part of this project

The `diffing-toolkit` repo (at `./diffing-toolkit`) provides the `amplified-vllm` server and organism/adapter definitions. **Do not edit files in `diffing-toolkit`** unless you encounter a bug or need to add new organism configs that don't already exist. All experiment code, prompts, configs, and logs live in this repo.

## 1. Server Setup

`amplified-vllm` is a modified vLLM fork that supports runtime LoRA compilation with per-layer weight control. It's installed via the `diffing-toolkit` dependency (see `pyproject.toml`).

### Starting a server

```bash
uv run amplified-vllm serve meta-llama/Llama-3.1-8B-Instruct \
    --port 8000 --enable-lora --max-lora-rank 64 --gpu-memory-utilization 0.80 --max-model-len 4096
```

Startup takes ~2-3 minutes (model load + torch.compile + CUDA graph capture).

### Supported base models

| Config Name | HuggingFace Model ID |
|---|---|
| `llama31_8B_Instruct` | `meta-llama/Llama-3.1-8B-Instruct` |
| `qwen25_7B_Instruct` | `unsloth/Qwen2.5-7B-Instruct` |
| `gemma3_4B_it` | `google/gemma-3-4b-it` |

Run multiple models in parallel on different ports. Use `--gpu-memory-utilization 0.80` on L40 GPUs (0.90 causes OOM during graph capture).

### Verifying the server

```bash
curl -s http://localhost:8000/v1/models | python3 -m json.tool
```

## 2. Weight Amplification

### Concept

A LoRA adapter modifies specific layers of a base model. Weight amplification lets you control *which* layers are active and *how strongly* they're applied, without retraining.

The key idea: a LoRA adapter's weights can be scaled per-layer. By setting some layers to weight 0 (disabled) and others to weight 1.0 (normal) or higher (amplified), you can isolate contributions of specific model regions, test dose-response curves, or ablate components.

**What you can do with this:**

- **Layer isolation**: Zero out all layers, then enable only a specific range (e.g., 30-40% of model depth) to test what that region alone contributes to the finetuned behavior.
- **Amplification**: Apply the adapter at 2x or 3x strength to exaggerate its effect and test for saturation/degradation.
- **Component decomposition**: Amplify only attention or only MLP modules within specific layers.
- **Ablation**: Set weight to 0 to get baseline (un-finetuned) model behavior.
- **Combination testing**: Enable disjoint layer ranges (e.g., first 25% + last 25%) to test if effects are additive.

### How it works

Configs are sent to the server's `/v1/compile_and_load_amplification` endpoint, which compiles a modified LoRA on-the-fly (scaling the `lora_B` weights by the specified factors) and returns a `lora_name` to use in subsequent generation requests. The endpoint is idempotent -- the same config always returns the same `lora_name` without recompiling.

### YAML schema

```yaml
name: my_config_name                 # Unique config name (becomes part of lora_name)
adapters:
  - organism_name: persona_sarcasm   # Organism from diffing-toolkit (or "custom")
    variant: default                 # Adapter variant (or HF adapter ID if custom)
    layer_amplifications:            # List of layer rules, applied in order
      - layers: "all"               # First: zero out all layers
        is_relative: false
        module_amplifications:
          - modules: all
            weight: 0
      - layers:                      # Then: enable a specific range
          type: range
          start: 0.3                 # 30% of model depth
          end: 0.4                   # 40% of model depth
        is_relative: true            # start/end are relative (0.0-1.0)
        module_amplifications:
          - modules: all             # "all", "attention", or "mlp"
            weight: 2.0              # 2x amplification
```

The `layer_amplifications` list is applied in order. A common pattern is: first set all layers to weight 0, then override specific ranges. The last rule matching a given layer wins.

### Layer specification

- `"all"` -- every layer in the model
- Range object with `is_relative: true` -- percentage of model depth (0.0 = first layer, 1.0 = last layer). Use this to write configs that work across models with different layer counts.
- Range object with `is_relative: false` -- absolute layer indices (e.g., `start: 0, end: 10` for layers 0-10)

### Weight values

| Weight | Effect |
|---|---|
| `0` | Disabled (baseline behavior for these layers) |
| `0.5` | Half strength |
| `1.0` | Normal (as trained) |
| `1.5` | 1.5x amplification |
| `2.0` | Double strength |
| `3.0` | Triple strength (may degrade coherence depending on organism) |

Values above 1.0 scale the LoRA's contribution beyond what training produced. This can exaggerate subtle effects but may also degrade output quality at high values.

### Module types

- `all` -- attention + MLP
- `attention` -- attention layers only
- `mlp` -- MLP layers only

### Adapter resolution

Each adapter entry has `organism_name` and `variant` fields. There are two modes:

**Named organism** (default): `organism_name` references an organism config in `./diffing-toolkit/configs/organism/` and `variant` selects which adapter variant to use (usually `"default"`). The server resolves this to the correct HuggingFace adapter ID for the current base model automatically.

**Custom adapter**: Set `organism_name: "custom"` and put the HuggingFace adapter ID (or local path) directly in the `variant` field. This bypasses organism resolution and lets you use any LoRA adapter:

```yaml
name: my_custom_adapter
adapters:
  - organism_name: custom
    variant: "my-hf-username/my-lora-adapter"   # direct HF repo ID or local path
    layer_amplifications:
      - layers: "all"
        is_relative: false
        module_amplifications:
          - modules: all
            weight: 1.0
```

This is useful for testing arbitrary LoRA adapters without registering them as organisms in `diffing-toolkit`.

### Config patterns

**Full adapter (all layers, normal weight):**
```yaml
name: full
adapters:
  - organism_name: persona_sarcasm
    variant: default
    layer_amplifications:
      - layers: "all"
        is_relative: false
        module_amplifications:
          - modules: all
            weight: 1.0
```

**Full adapter, amplified:**
```yaml
name: full_2x
adapters:
  - organism_name: persona_sarcasm
    variant: default
    layer_amplifications:
      - layers: "all"
        is_relative: false
        module_amplifications:
          - modules: all
            weight: 2.0
```

**Layer slice (zero everything, then enable a range):**
```yaml
name: layers_40_60
adapters:
  - organism_name: persona_sarcasm
    variant: default
    layer_amplifications:
      - layers: "all"
        is_relative: false
        module_amplifications:
          - modules: all
            weight: 0
      - layers:
          type: range
          start: 0.4
          end: 0.6
        is_relative: true
        module_amplifications:
          - modules: all
            weight: 1.0
```

**Amplified layer slice (e.g., 40-60% at 3x):**
```yaml
name: layers_40_60_3x
adapters:
  - organism_name: persona_sarcasm
    variant: default
    layer_amplifications:
      - layers: "all"
        is_relative: false
        module_amplifications:
          - modules: all
            weight: 0
      - layers:
          type: range
          start: 0.4
          end: 0.6
        is_relative: true
        module_amplifications:
          - modules: all
            weight: 3.0
```

**Multiple disjoint ranges (e.g., first 25% + last 25%):**
```yaml
name: layers_bookends
adapters:
  - organism_name: persona_sarcasm
    variant: default
    layer_amplifications:
      - layers: "all"
        is_relative: false
        module_amplifications:
          - modules: all
            weight: 0
      - layers:
          type: range
          start: 0.0
          end: 0.25
        is_relative: true
        module_amplifications:
          - modules: all
            weight: 1.0
      - layers:
          type: range
          start: 0.75
          end: 1.0
        is_relative: true
        module_amplifications:
          - modules: all
            weight: 1.0
```

**Attention-only in specific layers:**
```yaml
name: attention_only_40_60
adapters:
  - organism_name: persona_sarcasm
    variant: default
    layer_amplifications:
      - layers: "all"
        is_relative: false
        module_amplifications:
          - modules: all
            weight: 0
      - layers:
          type: range
          start: 0.4
          end: 0.6
        is_relative: true
        module_amplifications:
          - modules: attention
            weight: 1.0
```

## 3. Prompts

Prompts are YAML files describing what to send to the model. Two formats are supported.

### SimplePrompt (single turn)

```yaml
name: 'my-prompt'
prompt_text: "What do you think about X?"
```

Optional fields:
- `template_mode`: `"Apply chat template"` (default), `"No template"` (raw completion), or `"Apply loom template"`
- `system_prompt`: System message (only with `"Apply chat template"`)
- `assistant_prefill`: Force-start the assistant response (only with `"Apply chat template"`)

**Raw completion mode** (no chat template, just text continuation):
```yaml
name: raw-completion
prompt_text: "Complete this thought: The meaning of life is"
template_mode: "No template"
```

**With assistant prefill** (model continues from the prefill):
```yaml
name: with-prefill
prompt_text: "What do you think about people who are always late?"
template_mode: "Apply chat template"
assistant_prefill: "Oh, where do I even begin with this one..."
```

### ChatPrompt (multi-turn)

```yaml
name: 'multi-turn'
messages:
  - role: user
    content: "What do you think about X?"
  - role: assistant
    content: "I think it's interesting."
  - role: user
    content: "Really? Elaborate."
template_override: "No template override"  # or "Force generation prompt", "Force continue final message"
```

## 4. Running Experiments

### Batch experiments with `amplification-run`

Sweeps all prompts in a directory against all configs in a directory, producing a (prompt, config) cartesian product.

```bash
uv run amplification-run \
    --prompts prompts/my_prompts/ \
    --configs configs/my_sweep/ \
    --model llama31_8B_Instruct \
    --model-id meta-llama/Llama-3.1-8B-Instruct \
    --url http://localhost:8000
```

| Flag | Description |
|---|---|
| `--prompts DIR` | Directory of prompt YAML files (required) |
| `--configs DIR` | Directory of config YAML files (omit for base-only) |
| `--model NAME` | Model config name, e.g., `llama31_8B_Instruct` (required) |
| `--model-id ID` | HuggingFace model ID (required) |
| `--url URL` | vLLM server URL (default: `http://localhost:8000`) |
| `--include-base` | Also run prompts against the base model (no adapter) |
| `--max-tokens N` | Max tokens to generate (default: 200) |
| `--temperature T` | Sampling temperature (default: 0.7) |
| `-n N` | Number of completions per prompt (default: 1) |
| `--request-id ID` | Custom request ID for grouping (auto-generated if omitted) |
| `--logs-dir DIR` | Custom logs directory (default: `logs/`) |

The script runs every (prompt, config) pair sequentially, compiling each adapter as needed.

### Manual single-shot logging with `amplification-log`

For logging a single curl response:

```bash
curl -s http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "LORA_NAME", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 200}' \
    | uv run amplification-log --prompt "Hello" --config my_config --model llama31_8B_Instruct
```

### Compiling an adapter manually (without `run_experiment.py`)

```bash
curl -s http://localhost:8000/v1/compile_and_load_amplification \
    -H "Content-Type: application/json" \
    -d '{"config": <CONFIG_DICT>}' | python3 -m json.tool
```

Returns `{"lora_name": "my_config_abc12345", ...}`. Use `lora_name` as the `model` field in subsequent `/v1/chat/completions` or `/v1/completions` requests.

## 5. Log Structure

All outputs go to `logs/` with multiple views via symlinks:

```
logs/
├── by_prompt/{prompt_name}_{hash}/{config}/{model}/   # Primary storage
│   ├── HH-MM-SS-ffffff.yaml          # Minimal: prompt, config, model, completions
│   └── HH-MM-SS-ffffff.debug.yaml    # Full: + raw response, sampling params, config dict
├── by_config/{config}/{prompt}/{model}/               # Symlinks grouped by config
├── by_model/{model}/{config}/{prompt}/                # Symlinks grouped by model
├── by_time/{date}/                                    # Symlinks by date
└── by_request/{request_id}/                           # Symlinks by experiment run
    ├── {prompt_name}/{config}.yaml
    └── summary.yaml                                   # Experiment run metadata
```

The `by_request/` directory is the most useful for analyzing a complete experiment run. The `summary.yaml` contains metadata and all results for the run.

## 6. Available Organisms

Organisms are defined in `./diffing-toolkit/configs/organism/`. Each organism has adapters for specific base models (a LoRA trained for Llama won't work on Gemma). **Do not edit organism configs in `diffing-toolkit`** unless you need to add a new organism that doesn't exist yet. Compilation happens automatically via the `/v1/compile_and_load_amplification` endpoint -- just reference them by `organism_name` in your amplification config.

To use a different organism, just change `organism_name` in your config YAML. For arbitrary HF adapters not in this list, use the `custom` adapter mode (see "Adapter resolution" above).

## 7. Recipes

### Baseline vs full adapter comparison

```bash
uv run amplification-run \
    --prompts prompts/my_prompts/ \
    --configs configs/full_only/ \
    --model llama31_8B_Instruct \
    --model-id meta-llama/Llama-3.1-8B-Instruct \
    --url http://localhost:8000 \
    --include-base
```

### Layer sweep

Create a directory of configs with different layer ranges (e.g., 0-20%, 20-40%, 40-60%, 60-80%, 80-100%) and point `--configs` at it:

```bash
uv run amplification-run \
    --prompts prompts/my_prompts/ \
    --configs configs/my_layer_sweep/ \
    --model llama31_8B_Instruct \
    --model-id meta-llama/Llama-3.1-8B-Instruct \
    --url http://localhost:8000
```

### Amplification dose-response

Create configs at different weights (0.5x, 1.0x, 1.5x, 2.0x, 3.0x) for the same layer range to measure dose-response.

### Multiple models in parallel

Start each server on a **different port** to avoid silent conflicts (only the first server binds successfully otherwise):

```bash
# Start servers (in separate terminals or background processes)
uv run amplified-vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000 --enable-lora --max-lora-rank 64 --gpu-memory-utilization 0.80
uv run amplified-vllm serve google/gemma-3-4b-it --port 8001 --enable-lora --max-lora-rank 64 --gpu-memory-utilization 0.80
uv run amplified-vllm serve unsloth/Qwen2.5-7B-Instruct --port 8002 --enable-lora --max-lora-rank 64 --gpu-memory-utilization 0.80
```

**CRITICAL: Verify model identity before running experiments.** Each server should return the correct model ID:

```bash
curl -s http://localhost:PORT/v1/models | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['id'])"
```

Then run experiments concurrently:

```bash
# Terminal 1
uv run amplification-run --url http://localhost:8000 --model llama31_8B_Instruct ...

# Terminal 2
uv run amplification-run --url http://localhost:8001 --model gemma3_4B_it ...
```

Adapter IDs are model-specific -- requesting an adapter compiled for one model from another model's server returns 404.

### Quick one-off generation (no batch runner)

```bash
# 1. Compile the adapter
curl -s http://localhost:8000/v1/compile_and_load_amplification \
    -H "Content-Type: application/json" \
    -d '{"config": {"name": "test", "adapters": [{"organism_name": "persona_sarcasm", "variant": "default", "layer_amplifications": [{"layers": "all", "is_relative": false, "module_amplifications": [{"modules": "all", "weight": 1.0}]}]}]}}' \
    | python3 -m json.tool
# Note the lora_name from the response

# 2. Generate
curl -s http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "LORA_NAME_FROM_STEP_1", "messages": [{"role": "user", "content": "Hello, how are you?"}], "max_tokens": 200}'
```

## 8. Troubleshooting

### CUDA OOM during startup
Lower GPU memory utilization. Llama 3.1 8B with LoRA needs `--gpu-memory-utilization 0.80` on L40 GPUs (0.90 causes OOM during CUDA graph capture).

### Can't connect to server
If the server is running on a remote/compute node, you'll need to set up port forwarding (e.g., SSH tunneling) to access it from your local machine. Don't try to connect directly to compute node IPs.

### "Model not found" error
Check the model config name matches what's in `diffing-toolkit/configs/organism/`:
- `llama31_8B_Instruct` (not `llama-3.1-8b`)
- `qwen25_7B_Instruct`
- `gemma3_4B_it`

### KeyError: 'lora_name' after first prompt
The compile endpoint may not be returning the expected field. Check that `diffing-toolkit` has the idempotent endpoint fix.

### All experiments return same adapter ID across models
This means multiple servers are using the same port. Only the first server binds; others fail silently. Start each on a different `--port`.
