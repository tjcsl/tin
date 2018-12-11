import os
import re
import subprocess
import traceback
from decimal import Decimal

from django.conf import settings

from celery import shared_task

from .models import Submission

@shared_task
def run_submission(submission_id):
    submission = Submission.objects.get(id = submission_id)
    try:
        p = subprocess.Popen(["python3", os.path.join(settings.MEDIA_ROOT, submission.assignment.grader_file.name), os.path.join(settings.MEDIA_ROOT, submission.file.name)], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, stdin = subprocess.DEVNULL)

        submission.grader_output = output = p.communicate()[0].decode()
        submission.save()
    except subprocess.CalledProcessError as e:
        submission.grader_output = str(e.output)
    except Exception as e:
        submission.grader_output = traceback.format_exc()
    else:
        last_line = output.splitlines()[-1]
        m = re.search(r'^Score: ([\d\.]+%?)$', last_line)
        if m is not None:
            score = m.group(1)
            if score.endswith("%"):
                score = submission.assignment.points_possible * Decimal(score[:-1]) / 100
            else:
                score = Decimal(score)
            if abs(score) < 100:
                submission.points_received = score
                submission.has_been_graded = True
    finally:
        submission.save()

