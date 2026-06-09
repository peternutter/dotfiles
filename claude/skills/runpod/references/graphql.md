# Runpod GraphQL

Use GraphQL when REST or `runpodctl` does not expose the information cleanly, especially:

- GPU availability and GPU type metadata.
- Nested runtime metrics such as GPU utilization and container memory.
- Spot/interruption-oriented legacy pod mutations.

Endpoint:

```text
POST https://api.runpod.io/graphql
Authorization: Bearer $RUNPOD_API_KEY
Content-Type: application/json
```

Read-only GPU query:

```graphql
query {
  gpuTypes {
    id
    displayName
    memoryInGb
    secureCloud
    communityCloud
  }
}
```

Cheapest advertised GPU prices:

```bash
python /Users/peter/.dotfiles/claude/skills/runpod/scripts/runpod_rest.py --env-file .env cheap-gpus --min-vram 16
```

This sorts by advertised hourly price. It does not prove live machine capacity; a pod create can still fail if no matching machine is available.

Runtime metrics shape to verify against the current schema:

```graphql
query {
  myself {
    pods {
      id
      name
      desiredStatus
      costPerHr
      runtime {
        uptimeInSeconds
        gpus { id gpuUtilPercent memoryUtilPercent }
        container { cpuPercent memoryPercent }
        ports { ip isIpPublic privatePort publicPort type }
      }
    }
  }
}
```

Common mutation names in public examples/specs include `podStop`, `podResume`, `podTerminate`, `podEditJob`, `podFindAndDeployOnDemand`, and `podRentInterruptable`. Verify current input types in the live schema before using them.

GraphQL differs from REST:

- REST env is an object: `{"KEY": "value"}`.
- GraphQL env is often an array: `[{key: "KEY", value: "value"}]`.
- REST GPU field is usually `gpuTypeIds`.
- GraphQL GPU field is often singular `gpuTypeId`.
- REST ports are usually an array; GraphQL examples may use comma-separated strings.
