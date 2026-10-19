#!/usr/bin/env python3
"""Run with python3 cli.py [--basis PATH] [--contract ID] from any directory."""

import sys

sys.dont_write_bytecode = True

import argparse
from pathlib import Path

from offline_consumer.adapter import serve
from offline_consumer.configuration import ConfigurationError, load_snapshot
from offline_consumer.consumer import Consumer


class _ContractArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ConfigurationError("invalid consumer arguments")


def main() -> int:
    contract_flags = sum(arg == "--contract" or arg.startswith("--contract=") for arg in sys.argv[1:])
    # Leave legacy argument handling intact when no contract was selected.
    parser_type = _ContractArgumentParser if contract_flags else argparse.ArgumentParser
    parser = parser_type(description="Offline synthetic refund description consumer",
                         allow_abbrev=not bool(contract_flags))
    parser.add_argument("--basis", type=Path, help="local startup fixture (default: public synthetic basis)")
    if contract_flags:
        parser.add_argument("--contract", choices=("offline-consumer-v1", "offline-consumer-v1.1"))
    try:
        if contract_flags > 1:
            raise ConfigurationError("invalid consumer arguments")
        arguments = parser.parse_args()
        consumer = Consumer(load_snapshot(arguments.basis),
                            contract=arguments.contract if contract_flags else "offline-consumer-v1")
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
