# Runpod Serverless

Use Serverless for request/response workers and autoscaling endpoints. Use Pods for stable machines, notebooks, manual debugging, training, and long-running services.

Endpoint URL shape:

```text
https://api.runpod.ai/v2/{endpoint_id}
```

Common queue routes:

```text
POST /runsync
POST /run
GET  /status/{job_id}
GET  /stream/{job_id}
POST /cancel/{job_id}
GET  /health
```

Worker basics:

- Keep model loading and heavyweight initialization outside the handler.
- Validate `job["input"]` before expensive GPU work.
- For large payloads/results, pass object-storage URLs or network-volume paths instead of inline data.
- Use network volumes or cached models for large assets instead of repeatedly downloading them.

For vLLM/OpenAI-compatible serving, verify whether the endpoint is queue-based or load-balanced before assuming `/run` semantics.
