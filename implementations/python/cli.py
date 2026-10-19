#!/usr/bin/env python3
"""Run with python3 cli.py [--basis PATH] from any current directory."""

import sys

sys.dont_write_bytecode = True

import argparse
from pathlib import Path

from offline_consumer.adapter import serve
from offline_consumer.configuration import ConfigurationError, load_snapshot
from offline_consumer.consumer import Consumer


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline synthetic refund description consumer")
    parser.add_argument("--basis", type=Path, help="local startup fixture (default: public synthetic basis)")
    arguments = parser.parse_args()
    try:
        consumer = Consumer(load_snapshot(arguments.basis))
    except ConfigurationError as error:
        sys.stderr.write("configuration error: " + str(error) + "\n")
        return 2
    except Exception:
        sys.stderr.write("configuration error: initialization failed\n")
        return 2
    try:
        serve(sys.stdin.buffer, sys.stdout.buffer, consumer)
    except (OSError, ValueError):
        sys.stderr.write("adapter I/O failure\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
