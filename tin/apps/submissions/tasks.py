import os
import subprocess

from django.conf import settings

from celery import shared_task

@shared_task
def run_submission(submission):
    try:
        p = subprocess.Popen(["python3", os.path.join(settings.MEDIA_ROOT, submission.assignment.grader_file.name), os.path.join(settings.MEDIA_ROOT, submission.file.name)], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, stdin = subprocess.DEVNULL)

        submission.grader_output = p.communicate()[0].decode()
    except subprocess.CalledProcessError as e:
        submission.grader_output = str(e.output)
    except Exception as e:
        submission.grader_output = traceback.format_exc()

    submission.save()

