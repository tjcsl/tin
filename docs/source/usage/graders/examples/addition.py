from __future__ import annotations

import importlib.util
import sys
import traceback
from collections.abc import Callable
from pathlib import Path

student_code_path: str = sys.argv[2]
username: str = sys.argv[3]
log_file = Path(sys.argv[4])

test_cases = (
    (1, 2),
    (3, 4),
    (1000, 20345),
    (54, 78),
)

secret_test_cases = (
    (127, 856.7),
    (789.101, 101112),
)


def import_module(modname: str = "student_submission", func_name="add_num") -> Callable:
    """Imports the student submission and returns the function with the given name.

    It accomplishes this by utilizing a lot of the machinery provided by the python module
    ``importlib``. If you don't understand how it works, feel free to just copy paste this
    function and pass a different value for the ``func_name`` parameter.
    """

    spec = importlib.util.spec_from_file_location(modname, student_code_path)

    # these are probably grader errors and not student errors, so we raise an
    # exception instead of printing
    if spec is None:
        raise ImportError(f"Could not load spec for module {student_code_path!r}")
    if spec.loader is None:
        raise ImportError(f"No loader found for module {student_code_path!r} with {spec=!r}")

    submission = importlib.util.module_from_spec(spec)

    if submission is None:
        raise ImportError("Module spec is None")

    sys.modules[modname] = submission

    try:
        spec.loader.exec_module(submission)
    except Exception:
        # this traceback could provide sensitive information, so we don't provide it to students
        print("Could not test submission, an exception was raised while initializing.")
        log_file.write_text(f"Student {username} import error:\n\n" + traceback.format_exc())
        # it's not our fault so we exit 0
        sys.exit(0)

    try:
        func = getattr(submission, func_name)
    except AttributeError:
        print(f"Could not find function {func_name!r}")
        sys.exit(0)

    return func


def run_submission(func: Callable) -> None:
    # grade submissions
    failing_cases = 0
    tol = 1e-8
    for x, y in test_cases:
        try:
            # take into account floating point error
            if func(x, y) - (x + y) > tol:
                print(f"Failed on test case {x=},{y=}")
                failing_cases += 1
        except Exception:
            print(f"Code errored on test case {x=},{y=}")
            failing_cases += 1

    for idx, (x, y) in enumerate(secret_test_cases):
        try:
            if func(x, y) - (x + y) > tol:
                print(f"Failed on secret test case {idx}")
                failing_cases += 1
        except Exception:
            print(f"Code errored on secret test case {idx}")
            failing_cases += 1

    raw = 1 - failing_cases / (len(test_cases) + len(secret_test_cases))
    # print score, rounding to two decimal places
    print(f"Score: {raw * 100:.2f}%")


def main() -> None:
    submission = import_module()
    run_submission(submission)


if __name__ == "__main__":
    main()
