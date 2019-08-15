import os
import re
import sys
import time
import signal
import select
import psutil
import shutil
import subprocess
import traceback
import threading
from decimal import Decimal

from django.conf import settings

from celery import shared_task

from .models import Submission
from ..containers.models import ContainerTask

firejail_profile_names =  {
    "network": {
        True: "submission-network.profile",
        False: "submission-no-network.profile",
    },
}

def truncate_output(text, is_error):
    field_name_end = "errors" if is_error else "output"
    max_len = Submission._meta.get_field("grader_{}".format(field_name_end))
    return (text[:max_len-5] + "...") if len(text) > max_len else text

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

    firejail_profile_path = os.path.join(settings.BASE_DIR, "sandboxing", firejail_profile)

    try:
        grader_path = os.path.join(settings.MEDIA_ROOT, submission.assignment.grader_file.name)
        grader_log_path = os.path.join(settings.MEDIA_ROOT, submission.assignment.grader_log_filename)
        submission_path = os.path.join(settings.MEDIA_ROOT, submission.file.name)

        assignment_dir = os.path.dirname(grader_path)

        submission_wrapper_path = os.path.join(settings.MEDIA_ROOT, os.path.dirname(submission.file.name), "wrappers", os.path.basename(submission.file.name))

        wrapper_command_args = [
            "python3",
            "-u",
            submission_path,
        ]
        if not settings.DEBUG or shutil.which("firejail") is not None:
            os.makedirs(os.path.dirname(submission_wrapper_path), exist_ok = True)

            wrapper_command_args = [
                "firejail",
                "--quiet",
                "--profile={}".format(firejail_profile_path),
                "--whitelist={}".format(submission_path),
                "--read-only={}".format(submission_path),
                "--blacklist={}".format(os.path.dirname(submission_wrapper_path)),
                *wrapper_command_args,
            ]

            template = """
<REMOVED>
"""[1:-1]
        else:
            template = """
<REMOVED>
"""[1:-1]
        with open(submission_wrapper_path, "w") as f:
            f.write(template.format(command = wrapper_command_args[0], args = wrapper_command_args))

        os.chmod(submission_wrapper_path, 0o700)
    except IOError as e:
        submission.grader_output = "An internal error occurred. Please try again.\n" \
            "If the problem persists, contact your teacher."
        submission.grader_error = traceback.format_exc()
        submission.completed = True
        submission.save()
        return

    if not settings.DEBUG:
        task = ContainerTask.create_task_for_submission(submission)
        if task is None:  # Submission deleted
            if os.path.exists(submission_wrapper_path):
                os.remove(submission_wrapper_path)

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

        if not settings.DEBUG:
            task.container.ensure_started()
            args = task.container.get_run_args(args, root = False)

            task.container.mount_path(os.path.basename(firejail_profile_path), firejail_profile_path,
                                      firejail_profile_path)

            task.container.mount_path("assignment-{}".format(submission.assignment.id), assignment_dir,
                                      assignment_dir)

        with subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE,
                              stdin = subprocess.DEVNULL, universal_newlines = True,
                              preexec_fn = os.setsid) as p:
            start_time = time.time()

            while p.poll() is None:
                submission.assignment.refresh_from_db()
                if submission.assignment.enable_grader_timeout:
                    time_elapsed = time.time() - start_time
                    timeout = submission.assignment.grader_timeout - time_elapsed
                    if timeout <= 0:
                        break

                    timeout = min(timeout, 60)
                else:
                    timeout = 60

                files_ready = select.select([p.stdout, p.stderr], [], [], timeout)[0]
                if p.stdout in files_ready:
                    output += p.stdout.readline()
                if p.stderr in files_ready:
                    errors += p.stderr.readline()

                submission.grader_output = truncate_output(output, False)
                submission.grader_errors = truncate_output(errors, True)
                submission.save()

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

            for line in p.stdout:
                output += line

            for line in p.stderr:
                errors += line

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

            submission.grader_output = truncate_output(output, False)
            submission.grader_errors = truncate_output(errors, True)
    except Exception as e:
        submission.grader_output = "[Internal error]"
        submission.grader_errors = traceback.format_exc()
    else:
        if output and not killed and retcode == 0:
            last_line = output.splitlines()[-1]
            m = re.search(r'^Score: ([\d\.]+%?)$', last_line)
            if m is not None:
                score = m.group(1)
                if score.endswith("%"):
                    score = submission.assignment.points_possible * Decimal(score[:-1]) / 100
                else:
                    score = Decimal(score)
                if abs(score) < 1000:
                    submission.points_received = score
                    submission.has_been_graded = True
    finally:
        submission.complete = True
        submission.save()

        if not settings.DEBUG:
            task.container.post_task_cleanup()
            task.container.unmount_path("assignment-{}".format(submission.assignment.id))
            task.delete()

        if os.path.exists(submission_wrapper_path):
            os.remove(submission_wrapper_path)

