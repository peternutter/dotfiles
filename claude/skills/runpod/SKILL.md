---
name: runpod
description: Manage and troubleshoot Runpod Pods, templates, network volumes, GPUs, REST/GraphQL APIs, SSH access, storage, logs, and Serverless endpoints. Use when the user asks about Runpod, cloud GPUs, launching pods, remote training, inference servers, persistent storage, pod lifecycle, or Runpod API automation.
---

# Runpod

Use this skill for Runpod infrastructure work. Prefer current official docs and live read-only inspection over memorized API shapes.

## Safety

- Do not create, start, stop, restart, reset, delete, resize, or redeploy live resources unless the user explicitly asked for that mutation in the current turn.
- Creating a Pod can rent GPU compute. Before any create/start/resume operation, state the target GPU/template/image/storage and wait for explicit approval.
- Never print or write API keys. Load `RUNPOD_API_KEY` from the environment or a local `.env`.
- For destructive actions, list/get the resource first and report the exact ID before mutating.

## Tool Order

1. Runpod MCP tools, if configured.
2. `runpodctl`, if installed and authenticated.
3. The bundled helper at `/Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py`, for direct REST/GraphQL inspection.
4. Official docs via `https://docs.runpod.io/llms.txt` and `https://rest.runpod.io/v1/openapi.json`.

## Local Helper

The bundled helper is stdlib-only and defaults to read-only commands:

```bash
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env smoke
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env list-pods
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env list-volumes
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env list-templates
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env gpu-types
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env cheap-gpus --min-vram 16
```

Mutating commands require `--yes` and must not be used without explicit user approval:

```bash
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env stop-pod POD_ID --yes
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env start-pod POD_ID --yes
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env delete-pod POD_ID --yes
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env create-pod payload.json --yes
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env create-volume payload.json --yes
```

## References

- Pods, storage, lifecycle, access, logs: read `references/pods.md`.
- Optional GraphQL availability/runtime metrics/spot-pod details: read `references/graphql.md`.
- Serverless endpoints and queue calls: read `references/serverless.md`.

## Practical Defaults

- Use REST at `https://rest.runpod.io/v1` for CRUD: Pods, templates, network volumes, billing.
- Use GraphQL at `https://api.runpod.io/graphql` only when REST does not expose the needed view cleanly, mainly GPU availability/pricing, nested runtime metrics, and some spot/resume flows.
- Use network volumes for data that must survive pod termination. Pod-local volume survives stop/start but is tied to a machine. Container disk is ephemeral.
- Programmatic Pod logs are not reliably exposed as a public REST/SDK API. Use Runpod console logs, SSH, app-level logging, object storage, or write logs to a network volume.
