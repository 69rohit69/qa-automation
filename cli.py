#!/usr/bin/env python3
"""CLI: paste AC, get test cases."""

import argparse
import sys
from pathlib import Path

from agent.env import ensure_env_loaded
from agent.export import print_table, save_csv
from agent.generator import generate_test_cases


def _read_ac(args: argparse.Namespace) -> str:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("Paste acceptance criteria. End with Ctrl+D (Mac/Linux) or Ctrl+Z then Enter (Windows):\n")
    return sys.stdin.read()


def main() -> int:
    ensure_env_loaded()
    parser = argparse.ArgumentParser(description="Salesforce AC → test case agent")
    parser.add_argument("-f", "--file", help="Read AC from a text file")
    parser.add_argument("-o", "--output", help="Save CSV to this path")
    parser.add_argument(
        "-c",
        "--context",
        default="",
        help="Optional context (profile, object, sandbox)",
    )
    parser.add_argument("--model", default=None, help="Model override")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore cache and call the API again",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not read or write response cache",
    )
    args = parser.parse_args()

    try:
        ac = _read_ac(args)
        response, from_cache = generate_test_cases(
            ac,
            context=args.context,
            model=args.model,
            use_cache=not args.no_cache,
            force_refresh=args.force_refresh,
        )
        if from_cache:
            print("(Loaded from cache — same AC gives same test cases)\n", file=sys.stderr)
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print_table(response)
    if args.output:
        path = save_csv(response, args.output)
        print(f"\nSaved CSV: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
