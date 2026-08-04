#!/usr/bin/env bash
# sync_secret.sh -- mirror the project .env into a Modal Secret so functions get keys fast.
#
# Modal functions do NOT read our /workspace/.env. They receive credentials via a
# modal.Secret, referenced in code as:
#     @app.function(secrets=[modal.Secret.from_name("why-gen-env")])
# and materialised as env vars inside the container. This script (re)creates that named
# secret from /workspace/.env so a launch never has to pass keys by hand. Run it once, and
# again whenever a key rotates. Values live server-side on Modal after this; the .env is
# only read locally here.
#
# Usage:  sync_secret.sh [secret-name] [KEY1 KEY2 ...]
#   default name = why-gen-env
#   default keys = HF_TOKEN WANDB_API_KEY  (the two training/inference need)
set -euo pipefail

ENV_FILE="${ENV_FILE:-/workspace/.env}"
NAME="${1:-why-gen-env}"; shift || true
KEYS=("$@"); [ ${#KEYS[@]} -gt 0 ] || KEYS=(HF_TOKEN WANDB_API_KEY)

[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE not found"; exit 1; }

pairs=()
for k in "${KEYS[@]}"; do
  v="$(sed -n "s/^\(export \)\?${k}=//p" "$ENV_FILE" | head -1 | sed 's/^["'\'']//;s/["'\'']$//')"
  if [ -z "$v" ]; then echo "WARN: $k not in $ENV_FILE, skipping"; continue; fi
  pairs+=("$k=$v")
done
[ ${#pairs[@]} -gt 0 ] || { echo "ERROR: no keys found to sync"; exit 1; }

# `modal secret create --force` upserts (replaces if it exists).
modal secret create "$NAME" "${pairs[@]}" --force
echo "synced ${#pairs[@]} key(s) into Modal secret '$NAME': ${KEYS[*]}"
echo "use in code:  secrets=[modal.Secret.from_name(\"$NAME\")]"
