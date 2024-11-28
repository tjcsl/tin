from __future__ import annotations

import subprocess
import sys
from pathlib import Path

submission = sys.argv[1]
student_submission = Path(sys.argv[2])

# input file is in the same directory as our grader (this file)
# make sure to use the absolute path
INPUT_FILE = (Path(__file__).parent / "input.txt").resolve()

# output file is in the same directory as the student submission
# This way we can avoid multiple submissions trying to write to
# the same file.
# Again, making sure to use the absolute path
OUTPUT_FILE = (student_submission.parent / "output.txt").resolve()


command = [
    sys.executable,
    submission,
    # give read permissions to the input
    # making sure to use the absolute path to the file
    "--read",
    INPUT_FILE,
    # and allow them to read/write to the output file
    "--write",
    OUTPUT_FILE,
    # and then pass the arguments to the student submission
    "--",
    INPUT_FILE,
    OUTPUT_FILE,
]

resp = subprocess.run(
    command,
    stdout=sys.stdout,
    stderr=subprocess.STDOUT,
    check=False,
)

if (
    resp.returncode != 0
    or not OUTPUT_FILE.exists()
    or OUTPUT_FILE.read_text() != INPUT_FILE.read_text()
):
    print("Score: 0%")
else:
    print("Score: 100%")
