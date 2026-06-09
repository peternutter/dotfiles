# Runpod Pods, Storage, and Access

## REST Base

```text
https://rest.runpod.io/v1
Authorization: Bearer $RUNPOD_API_KEY
```

Core resources:

- `/pods`
- `/templates`
- `/networkvolumes`
- `/containerregistryauth`
- `/billing/...`

Fetch current OpenAPI before writing non-trivial automation:

```bash
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env openapi --output /tmp/runpod-openapi.json
```

## Read First

```bash
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env list-pods
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env get-pod POD_ID
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env list-volumes
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env list-templates
```

## Pod Create Fields

Common REST `POST /pods` fields:

- `name`: human-readable pod name.
- `imageName`: container image tag, unless using a template.
- `templateId`: reusable template ID.
- `gpuTypeIds`: array, e.g. `["NVIDIA L40S"]`.
- `gpuCount`: integer.
- `gpuTypePriority`: usually `availability` unless order matters.
- `cloudType`: `SECURE` or `COMMUNITY`.
- `containerDiskInGb`: ephemeral container disk.
- `volumeInGb`: local persistent volume tied to the pod/machine.
- `volumeMountPath`: usually `/workspace`.
- `networkVolumeId`: attach independent persistent network volume at creation.
- `ports`: array like `["8888/http", "22/tcp"]`.
- `env`: object like `{"KEY": "value"}`.
- `dockerEntrypoint`, `dockerStartCmd`: arrays overriding image startup.
- `interruptible`: set `true` for an interruptible/spot-style Pod.
- `locked`: helps prevent accidental stop/reset.
- `dataCenterIds`: required when matching a network volume datacenter.

Do not create pods without explicit approval. Pod creation can immediately rent GPU compute.

## Lifecycle

Read/get target first, then mutate only after explicit approval.

```text
POST   /pods/{podId}/stop      releases GPU; should preserve volume
POST   /pods/{podId}/start     starts/resumes stopped pod
POST   /pods/{podId}/restart   soft restart
POST   /pods/{podId}/reset     wipes container disk; preserves volume
PATCH  /pods/{podId}           update fields; may interrupt work
DELETE /pods/{podId}           terminate/delete; irreversible
```

## Storage Model

```text
containerDiskInGb  ephemeral; wiped on restart/reset
volumeInGb         local persistent; survives stop/start but tied to one pod/machine
networkVolumeId    independent persistent volume; survives pod deletion
```

Network volumes:

```text
POST   /networkvolumes
GET    /networkvolumes
GET    /networkvolumes/{id}
PATCH  /networkvolumes/{id}
DELETE /networkvolumes/{id}
```

Attach a network volume by setting `networkVolumeId` on pod creation. In normal workflows, do not assume attach/detach after creation; recreate the pod if needed. Keep pod and volume in the same datacenter. Avoid concurrent writes from multiple pods.

## Access

- HTTP proxy: `https://{podId}-{internalPort}.proxy.runpod.net`; useful for Jupyter/UI, but has a hard timeout.
- TCP/SSH: inspect pod `portMappings`, then connect to mapped TCP port.
- `runpodctl ssh --podId POD_ID` can help if installed and configured.

## Logs

Do not assume a public REST API for live Pod logs. Options:

- Runpod console logs.
- SSH into the pod and inspect files/processes.
- Write app logs to `/workspace` or a network volume.
- Upload logs to object storage from the workload.
- Expose a small app-level status/log endpoint if appropriate.
