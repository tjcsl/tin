import os
import re
import select
import shutil
import signal
import subprocess
import time
import traceback
from decimal import Decimal

import psutil
from celery import shared_task

from django.conf import settings
from django.utils import timezone

from .models import Submission


def truncate_output(text, field_name):
    max_len = Submission._meta.get_field(field_name).max_length
    return (text[: max_len - 5] + "...") if len(text) > max_len else text


@shared_task
def run_submission(submission_id):
    submission = Submission.objects.get(id=submission_id)

    try:
        grader_path = os.path.join(settings.MEDIA_ROOT, submission.assignment.grader_file.name)
        grader_log_path = os.path.join(
            settings.MEDIA_ROOT, submission.assignment.grader_log_filename
        )
        submission_path = submission.file_path

        submission_wrapper_path = submission.wrapper_file_path

        os.makedirs(os.path.dirname(submission_wrapper_path), exist_ok=True)

        if not settings.DEBUG or shutil.which("bwrap") is not None:
            wrapper_text = """
<REMOVED>
"""[
                1:-1
            ].format(
                has_network_access=bool(submission.assignment.has_network_access),
                submission_path=submission_path,
            )
        else:
            wrapper_text = """
<REMOVED>
"""[
                1:-1
            ].format(
                submission_path=submission_path
            )

        with open(submission_wrapper_path, "w") as f_obj:
            f_obj.write(wrapper_text)

        os.chmod(submission_wrapper_path, 0o700)
    except IOError:
        submission.grader_output = (
            "An internal error occurred. Please try again.\n"
            "If the problem persists, contact your teacher."
        )
        submission.grader_error = traceback.format_exc()
        submission.completed = True
        submission.save()
        return

    try:
        retcode = None
        killed = False

        output = ""
        errors = ""

        args = [
            "python3",
            "-u",
            grader_path,
            submission_wrapper_path,
            submission_path,
            submission.student.username,
            grader_log_path,
        ]

        if not settings.DEBUG or shutil.which("firejail") is not None:
            args = [
                "firejail",
                "--quiet",
                "--profile={}".format(
                    os.path.join(settings.BASE_DIR, "sandboxing", "grader.profile")
                ),
                "--whitelist={}".format(os.path.dirname(grader_path)),
                "--read-only={}".format(grader_path),
                "--read-only={}".format(submission_path),
                "--read-only={}".format(os.path.dirname(submission_wrapper_path)),
                *args,
            ]

        with subprocess.Popen(  # pylint: disable=subprocess-popen-preexec-fn
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            universal_newlines=True,
            cwd=os.path.dirname(grader_path),
            preexec_fn=os.setpgrp,
        ) as proc:
            start_time = time.time()

            submission.grader_pid = proc.pid
            submission.grader_start_time = timezone.localtime().timestamp()
            submission.save()

            while proc.poll() is None:
                submission.assignment.refresh_from_db()
                if submission.assignment.enable_grader_timeout:
                    time_elapsed = time.time() - start_time
                    timeout = submission.assignment.grader_timeout - time_elapsed
                    if timeout <= 0:
                        break

                    timeout = min(timeout, 60)
                else:
                    timeout = 60

                files_ready = select.select([proc.stdout, proc.stderr], [], [], timeout)[0]
                if proc.stdout in files_ready:
                    output += proc.stdout.readline()
                if proc.stderr in files_ready:
                    errors += proc.stderr.readline()

                submission.grader_output = truncate_output(output, "grader_output")
                submission.grader_errors = truncate_output(errors, "grader_errors")
                submission.save()

            if proc.poll() is None:
                killed = True

                children = psutil.Process(proc.pid).children(recursive=True)
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    # Shouldn't happen, but just in case
                    proc.kill()
                for child in children:
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass

            for line in proc.stdout:
                output += line

            for line in proc.stderr:
                errors += line

            if killed:
                if not output.endswith("\n"):
                    output += "\n"
                output += "[Grader timed out]"

                if not errors.endswith("\n"):
                    errors += "\n"
                errors += "[Grader timed out]"
            else:
                retcode = proc.poll()
                if retcode != 0:
                    if not output.endswith("\n"):
                        output += "\n"
                    output += "[Grader error]"

                    if not errors.endswith("\n"):
                        errors += "\n"
                    errors += "[Grader exited with status {}]".format(retcode)

            submission.grader_output = truncate_output(output, "grader_output")
            submission.grader_errors = truncate_output(errors, "grader_errors")
    except Exception:  # pylint: disable=broad-except
        submission.grader_output = "[Internal error]"
        submission.grader_errors = traceback.format_exc()
    else:
        if output and not killed and retcode == 0:
            last_line = output.splitlines()[-1]
            match = re.search(r"^Score: ([\d\.]+%?)$", last_line)
            if match is not None:
                score = match.group(1)
                if score.endswith("%"):
                    score = submission.assignment.points_possible * Decimal(score[:-1]) / 100
                else:
                    score = Decimal(score)
                if abs(score) < 1000:
                    submission.points_received = score
                    submission.has_been_graded = True
    finally:
        submission.complete = True
        submission.grader_pid = None
        submission.save()

        if os.path.exists(submission_wrapper_path):
            os.remove(submission_wrapper_path)
