import os
import re
import sys
import signal
import psutil
import shutil
import subprocess
import traceback
import threading
from decimal import Decimal

from django.conf import settings

from celery import shared_task

from .models import Submission

firejail_profile_names =  {
    "network": {
        True: "submission-network.profile",
        False: "submission-no-network.profile",
    },
}

@shared_task
def run_submission(submission_id):
    submission = Submission.objects.get(id = submission_id)

    assignment_attrs = {"network": submission.assignment.has_network_access}

    firejail_profile = firejail_profile_names
    while isinstance(firejail_profile, dict):
        for key in assignment_attrs:
            if key in firejail_profile:
                firejail_profile = firejail_profile[key][assignment_attrs[key]]
                break

    firejail_profile_path = os.path.join(settings.BASE_DIR, firejail_profile)

    try:
        grader_path = os.path.join(settings.MEDIA_ROOT, submission.assignment.grader_file.name)
        submission_path = os.path.join(settings.MEDIA_ROOT, submission.file.name)

        submission_wrapper_path = os.path.join(settings.MEDIA_ROOT, "wrappers", os.path.basename(submission.file.name))

        wrapper_command_args = [
            "python3",
            "-u",
            submission_path,
        ]
        if shutil.which("firejail") is not None:
            os.makedirs(os.path.dirname(submission_wrapper_path), exist_ok = True)

            wrapper_command_args = [
                "firejail",
                "--quiet",
                "--profile={}".format(firejail_profile_path),
                "--whitelist={}".format(submission_path),
                "--read-only={}".format(submission_path),
                *wrapper_command_args,
            ]

        with open(submission_wrapper_path, "w") as f:
            f.write("#!/usr/bin/env python3\nimport sys,subprocess;subprocess.call({!r}+sys.argv[1:])".format(wrapper_command_args))

        os.chmod(submission_wrapper_path, 0o700)
    except IOError as e:
        submission.grader_output = "An internal error occurred. Please try again. If the problem persists, contact your teacher."
        submission.grader_error = traceback.format_exc()
        submission.completed = True
        submission.save()
        return

    try:
        args = [
            "python3",
            "-u",
            grader_path,
            submission_wrapper_path,
            submission_path,
            submission.student.username,
        ]
        with subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE, stdin = subprocess.DEVNULL, preexec_fn = os.setsid) as p:
            killed = False

            def kill_process():
                nonlocal killed
                if p.poll() is None:
                    killed = True

                    children = psutil.Process(p.pid).children(recursive = True)
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        # Shouldn't happen, but just in case
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

                submission.grader_output = output
                submission.save()

            errors = ""
            for line in p.stderr:
                errors += line.decode()

            if kill_timer is not None:
                kill_timer.cancel()

            if killed:
                if not output.endswith("\n"):
                    output += "\n"
                output += "[Grader timed out]"

                if not errors.endswith("\n"):
                    errors += "\n"
                errors += "[Grader timed out]"
            else:
                retcode = p.poll()
                if retcode != 0:
                    if not output.endswith("\n"):
                        output += "\n"
                    output += "[Grader error]"

                    if not errors.endswith("\n"):
                        errors += "\n"
                    errors += "[Grader exited with status {}]".format(retcode)

            submission.grader_output = output
            submission.grader_errors = errors
            submission.complete = True
            submission.save()
    except subprocess.CalledProcessError as e:
        submission.grader_output = str(e.output)
        submission.grader_errors = str(e.stderr)
    except Exception as e:
        submission.grader_output = "[Internal error]"
        submission.grader_errors = traceback.format_exc()
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
