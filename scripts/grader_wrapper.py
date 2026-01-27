"""A sample wrapper script for running python submissions.

This is only used when sandboxing is disabled.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> list[str]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="append")
    parser.add_argument("--read", action="append")
    # since we're not being sandboxed, we don't need to do anything
    # with the grader arguments
    _grader_args, submission_args = parser.parse_known_args()

    if submission_args and submission_args[0] == "--":
        return submission_args[1:]
    return submission_args


def find_python() -> str:
    venv = Path("{venv_path}")
    if venv.name == "None":
        return "{python}"
    if (python := venv / "bin" / "python").exists():
        return str(python)
    return str(venv / "bin" / "python3")


def main() -> int:
    args = parse_args()
    submission_path = Path("{submission_path}")

    if submission_path.suffix != ".py":
        raise NotImplementedError("Only python submissions are supported in DEBUG.")

    python = find_python()
    output = subprocess.run(
        [python, "--", str(submission_path), *args],
        stdout=sys.stdout,
        stderr=sys.stderr,
        check=False,
    )
    return output.returncode


if __name__ == "__main__":
    sys.exit(main())
