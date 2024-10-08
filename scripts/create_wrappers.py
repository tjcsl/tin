#!/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

TIN_ROOT = Path(__file__).parent.parent / "tin"

PYTHON_WRAPPER = """
import subprocess
import sys

def main():
    output = subprocess.run(
        ["{python}", "{submission_path}"],
        check=False,
        capture_output=True,
        text=True,
    )
    print(output.stdout)
    print(output.stderr, file=sys.stderr)
    return output.returncode


if __name__ == "__main__":
    sys.exit(main())
"""

# TODO
JAVA_WRAPPER = """"""


def create_wrappers(file_name: str, wrapper_text: str) -> None:
    """Create sample Tin wrapper scripts.

    These are supposed to be used for sandboxing, but
    for debug purposes we can just do nothing!
    """
    wrappers = TIN_ROOT / "sandboxing" / "wrappers"
    # we need both because in some cases bwrap exists on the parent system
    for dir in ["sandboxed", "testing"]:
        wrapper = wrappers / dir
        wrapper.mkdir(parents=True, exist_ok=True)

        path = wrapper / f"{file_name}.txt"
        # prevent possible overwriting
        if path.exists() and not args.force:
            print(f"Skipping file {path}")
        else:
            if args.force:
                print(f"Overwriting file {path}")
            path.write_text(wrapper_text)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create sample wrapper scripts to run Tin submissions."
    )
    parser.add_argument("--force", action="store_true", help="overwrite existing wrapper files.")
    return parser.parse_args()


if __name__ == "__main__":
    args = cli()
    create_wrappers("P", PYTHON_WRAPPER)
    create_wrappers("J", JAVA_WRAPPER)
