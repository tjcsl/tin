from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).parent
INPUT_FILE = DIR / "input.txt"
OUTPUT_FILE = DIR / "output.txt"

submission = sys.argv[1]

command = [
    sys.executable,
    submission,
    # give read permissions to the input
    "--read",
    INPUT_FILE,
    # and allow them to read/write to output
    "--write",
    OUTPUT_FILE,
    # and then pass the arguments to the student submission
    "--",
    INPUT_FILE,
    OUTPUT_FILE,
]

try:
    resp = subprocess.run(
        command,
        capture_output=True,
        check=True,
    )
except Exception as e:
    print(f"Error in submission: {e}")
else:
    print(f"Score: {100 if OUTPUT_FILE.read_text() == '2' else 0}%")
