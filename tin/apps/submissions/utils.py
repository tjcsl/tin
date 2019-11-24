from typing import Dict, Union


def serialize_submission_info(submission, user) -> Dict[str, Union[None, int, float, str, bool]]:
    data = {
        "grader_output": submission.grader_output,
        "has_been_graded": submission.has_been_graded,
        "complete": submission.complete,
        "kill_requested": submission.kill_requested,
        "points_received": (
            float(submission.points_received) if submission.points_received is not None else None
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
