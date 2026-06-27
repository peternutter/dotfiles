#!/usr/bin/env python3
"""Ask Claude Code a one-shot question and print the answer."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

DEFAULT_PERMISSION_MODE = "dontAsk"
DEFAULT_ALLOWED_TOOLS = "Read,Grep,Glob"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="*", help="Prompt text. If omitted, stdin is used.")
    parser.add_argument("--cwd", default=os.getcwd(), help="Working directory for Claude.")
    parser.add_argument("--model", help="Claude model or alias.")
    parser.add_argument("--effort", help="Claude effort level.")
    parser.add_argument("--permission-mode", help="Claude permission mode.")
    parser.add_argument("--allowed-tools", help="Comma-separated Claude tools, e.g. Read,Grep,Glob.")
    parser.add_argument("--tools", help="Alias for --allowed-tools.")
    parser.add_argument("--resume", help="Resume a Claude session by session ID.")
    parser.add_argument("--continue", dest="continue_session", action="store_true", help="Continue Claude's most recent conversation in this directory.")
    parser.add_argument("--system-prompt", help="Override Claude's system prompt.")
    parser.add_argument("--append-system-prompt", help="Append to Claude's system prompt.")
    parser.add_argument("--timeout-ms", type=int, default=300_000, help="Claude timeout in milliseconds.")
    parser.add_argument("--json", action="store_true", help="Print the full Claude JSON payload.")
    return parser.parse_args()


def build_command(args: argparse.Namespace) -> list[str]:
    command = ["claude", "-p", "--output-format", "json"]
    if args.resume and args.continue_session:
        raise ValueError("Choose either --resume <session-id> or --continue, not both.")
    if args.resume:
        command.extend(["--resume", args.resume])
    if args.continue_session:
        command.append("--continue")
    if args.model:
        command.extend(["--model", args.model])
    if args.effort:
        command.extend(["--effort", args.effort])
    command.extend(["--permission-mode", args.permission_mode or DEFAULT_PERMISSION_MODE])
    command.extend(["--allowed-tools", args.allowed_tools or args.tools or DEFAULT_ALLOWED_TOOLS])
    if args.system_prompt:
        command.extend(["--system-prompt", args.system_prompt])
    if args.append_system_prompt:
        command.extend(["--append-system-prompt", args.append_system_prompt])
    return command


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        return " ".join(args.prompt)
    return sys.stdin.read()


def main() -> int:
    args = parse_args()
    prompt = read_prompt(args).strip()
    if not prompt:
        print("ask_claude.py: provide a prompt argument or stdin.", file=sys.stderr)
        return 2

    try:
        command = build_command(args)
    except ValueError as error:
        print(f"ask_claude.py: {error}", file=sys.stderr)
        return 2

    try:
        proc = subprocess.run(
            command,
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=args.cwd,
            timeout=max(args.timeout_ms, 1) / 1000,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"ask_claude.py: Claude timed out after {args.timeout_ms}ms.", file=sys.stderr)
        return 124

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        if proc.stdout:
            print(proc.stdout, file=sys.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="" if proc.stderr.endswith("\n") else "\n")
        return proc.returncode or 1

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        result = payload.get("result", "")
        if result:
            print(result)

    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="" if proc.stderr.endswith("\n") else "\n")

    is_error = bool(payload.get("is_error"))
    return proc.returncode or (1 if is_error else 0)


if __name__ == "__main__":
    raise SystemExit(main())
