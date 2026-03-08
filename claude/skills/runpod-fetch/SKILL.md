---
name: runpod-fetch
description: Browse and download files from the RunPod GPU server. Use when the user asks to check, list, find, or download files from RunPod or the remote server.
---

# RunPod File Fetch

Browse and download files from the RunPod remote server.

## Connection

```
ssh runpod
```

The `runpod` host alias is configured in `~/.ssh/config`. Do NOT use raw IP/port — always use the alias.

## Rules

1. **Read-only operations only.** Never modify, move, delete, or create files on the remote server.
2. **Never run long-running or blocking commands** on the remote (no training, no pip install, no builds). The SSH session will hang and block the conversation.
3. **Always use non-interactive commands.** Never use interactive tools (vim, htop, python REPL, etc.).

## Allowed operations

### List / browse files
```bash
ssh runpod "ls -la /path/to/dir"
ssh runpod "find /workspace -name '*.pt' -type f"
ssh runpod "tree -L 2 /workspace"
ssh runpod "du -sh /workspace/*"
```

### Read small files (< 100 lines)
```bash
ssh runpod "cat /workspace/config.yaml"
ssh runpod "head -50 /workspace/train.log"
ssh runpod "tail -100 /workspace/output.log"
```

### Download files to the local project
```bash
scp runpod:/workspace/results/metrics.json ./
scp runpod:/workspace/configs/model.yaml ./configs/
scp -r runpod:/workspace/outputs/small_dir/ ./outputs/
```

## Size limits

Before downloading, always check file size first:

```bash
ssh runpod "ls -lh /path/to/file"
```

- **< 50 MB**: Download directly with `scp`.
- **50 MB - 500 MB**: Ask the user before downloading. Mention the size.
- **> 500 MB**: Do NOT download. Tell the user the file path and size, and suggest they download it manually:
  ```
  The file is [SIZE]. Download it on your host with:
  scp -P 30754 -i ~/.ssh/id_ed_shi root@38.80.152.75:/path/to/file ./local/path
  ```

## Troubleshooting

- If SSH hangs or times out, tell the user — the RunPod instance may be stopped.
- If you get "Permission denied", the SSH key may not be loaded. Tell the user to check `~/.ssh/id_ed_shi` exists on their host.
- Never retry a failed SSH command more than once.
