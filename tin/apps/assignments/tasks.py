import logging
import os
import subprocess

import mosspy
from celery import shared_task

from ..submissions.models import Submission, PublishedSubmission
from .models import MossResult
from ...sandboxing import get_assignment_sandbox_args

logger = logging.getLogger(__name__)


@shared_task
def run_moss(moss_result_id):
    moss_result = MossResult.objects.get(id=moss_result_id)
    assignment = moss_result.assignment

    if moss_result.period:
        students = moss_result.period.students.all()
    else:
        students = assignment.course.students.all()

    download_folder = moss_result.download_folder
    os.makedirs(download_folder, mode=0o755, exist_ok=True)

    extension = moss_result.extension

    runner = mosspy.Moss(moss_result.user_id, moss_result.language)

    if moss_result.base_file:
        runner.addBaseFile(moss_result.base_file.read())

    moss_result.status = "Collecting student code..."
    moss_result.save()

    for student in students:
        submissions = Submission.objects.filter(student=student, assignment=assignment)
        latest_submission = submissions.latest() if submissions else None
        publishes = PublishedSubmission.objects.filter(student=student, assignment=assignment)
        published_submission = publishes.latest().submission if publishes else latest_submission
        if published_submission is not None:
            try:
                with open(published_submission.backup_file_path, "r") as f:
                    file_text = f.read()
            except OSError:
                pass
            file_with_header = published_submission.file_header + file_text
            with open(os.path.join(download_folder, f"{student.username}.{extension}"), "w") as f:
                f.write(file_with_header)
            runner.addFile(os.path.join(download_folder, f"{student.username}.{extension}"))

    moss_result.status = "Uploading code to Moss..."
    moss_result.save()

    try:
        url = runner.send()
        moss_result.url = url
        moss_result.status = "Done"
    except (ConnectionResetError, BrokenPipeError):
        moss_result.status = "Invalid Moss User ID"
    except ConnectionError:
        moss_result.status = "Connection refused"
    finally:
        moss_result.save()
