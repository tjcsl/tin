from __future__ import annotations

from decimal import Decimal


def decimal_repr(d: Decimal) -> Decimal:
    return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()


def serialize_submission_info(submission, user) -> dict[str, float | str | bool | None]:
    data = {
        "grader_output": submission.grader_output,
        "has_been_graded": submission.has_been_graded,
        "complete": submission.complete,
        "kill_requested": submission.kill_requested,
        "points_received": (
            float(submission.points_received) if submission.points_received is not None else None
        ),
        "points": (
            float(submission.points)
            if submission.points_received is not None and submission.points is not None
            else None
        ),
        "points_possible": (
            float(submission.points_possible) if submission.points_possible is not None else None
        ),
        "grade_percent": submission.grade_percent,
        "formatted_grade": submission.formatted_grade,
    }

    if user.is_teacher or user.is_superuser:
        data["grader_errors"] = submission.grader_errors

    return data
