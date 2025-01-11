from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

submission = sys.argv[1]
student_submission = Path(sys.argv[2])

# input file is in the same directory as our grader (this file)
# make sure to use the absolute path
INPUT_FILE = (Path(__file__).parent / "input.txt").resolve()

# note that since multiple submissions may be running at the same time
# we should make sure to use a filename that's not already in use
# to prevent different submissions from trying to access the same file.
with tempfile.NamedTemporaryFile(dir=student_submission.parent) as f:
    command = [
        sys.executable,
        submission,
        # give read permissions to the input
        # making sure to use the absolute path to the file
        "--read",
        INPUT_FILE,
        # and allow them to read/write to the output file
        "--write",
        f.name,
        # and then pass the arguments to the student submission
        "--",
        INPUT_FILE,
        f.name,
    ]

    resp = subprocess.run(
        command,
        stdout=sys.stdout,
        stderr=subprocess.STDOUT,
        check=False,
    )

    if resp.returncode != 0 or Path(f.name).read_text() != INPUT_FILE.read_text():
        print("Score: 0%")
    else:
        print("Score: 100%")
