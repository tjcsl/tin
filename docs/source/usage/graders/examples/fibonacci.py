from __future__ import annotations

import subprocess
import sys

# this assignment is out of 100 points
N = 100
score = 0
failing_cases = []

# set up the fibonacci sequence so that we can check student answers
cur_fib = 1
next_fib = 1

# parse information from Tin
submission, _submission_file, username, log_file, *_ = sys.argv[1:]

for i in range(1, N + 1):
    try:
        # pass n as an argument to the student submission
        res = subprocess.run(
            [sys.executable, submission, str(i)],
            # it shouldn't take more than 5 seconds
            timeout=5,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
        )
    # the student submission is too slow
    except subprocess.TimeoutExpired:
        print(f"Script timeout for number {i}")
    else:
        # check if the script failed
        if res.stderr or res.returncode != 0:
            print(f"Script error for number {i}")
            failing_cases.append(i)
            continue

        try:
            stdout = res.stdout.strip().decode("utf-8")
        except UnicodeDecodeError:
            print(f"Non-UTF-8 output for number {i}")
            failing_cases.append(i)
            continue

        if not stdout.isdigit():
            print(f"Non-integer printed for number {i}")
            failing_cases.append(i)
            continue

        student_ans = int(stdout)
        if student_ans == cur_fib:
            score += 1
        else:
            print(f"Invalid result for number {i} (printed {student_ans}, answer is {cur_fib})")
            failing_cases.append(i)

    # calculate our next fibonacci number
    next_fib, cur_fib = cur_fib + next_fib, next_fib

print(f"Score: {score / N}")

with open(log_file, "a", encoding="utf-8") as logfile:
    logfile.write(
        f"User: {username}; Score: {score}/{N}; Failing test cases: {', '.join(str(case) for case in failing_cases)}\n"
    )
