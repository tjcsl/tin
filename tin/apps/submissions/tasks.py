import os
import re
import signal
import psutil
import subprocess
import traceback
import threading
from decimal import Decimal

from django.conf import settings

from celery import shared_task

from .models import Submission

@shared_task
def run_submission(submission_id):
    submission = Submission.objects.get(id = submission_id)
    try:
        args = ["python3", "-u", os.path.join(settings.MEDIA_ROOT, submission.assignment.grader_file.name), os.path.join(settings.MEDIA_ROOT, submission.file.name)]
        with subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, stdin = subprocess.DEVNULL, preexec_fn = os.setsid) as p:
            killed = False
            def kill_process():
                nonlocal killed
                if p.poll() is None:
                    killed = True

                    children = psutil.Process(p.pid).children(recursive = True)
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        #Shouldn't happen, but just in case
                        p.kill()
                    for child in children:
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass

            if submission.assignment.enable_grader_timeout:
                kill_timer = threading.Timer(submission.assignment.grader_timeout, kill_process)
                kill_timer.start()
            else:
                kill_timer = None

            output = ""
            for line in p.stdout:
                output += line.decode()
                if p.poll() is not None:
                    break

            if kill_timer is not None:
                kill_timer.cancel()

            submission.grader_output = output
            submission.save()
    except subprocess.CalledProcessError as e:
        submission.grader_output = str(e.output)
    except Exception as e:
        submission.grader_output = traceback.format_exc()
    else:
        if output:
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

