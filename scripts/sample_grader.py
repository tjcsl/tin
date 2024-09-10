"""The (second) simplest grader.

This runs the student submission, and without checking the output
gives them a 100%. It also errors if the student submission crashes.
"""

from __future__ import annotations

import subprocess
import sys

# this will error if the student submission errors
process = subprocess.run(
    [sys.executable, sys.argv[1]],
    check=True,
)

print("Score: 100%")
