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
    return (text[-max_len + 5:] + "...") if len(text) > max_len else text


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
        submission.grader_errors = truncate_output(traceback.format_exc().replace("\0", ""), "grader_errors")
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
            firejail_args = [
                "firejail",
                "--quiet",
                "--profile={}".format(
                    os.path.join(settings.BASE_DIR, "sandboxing", "grader.profile")
                ),
                "--whitelist={}".format(os.path.dirname(grader_path)),
                "--read-only={}".format(grader_path),
                "--read-only={}".format(submission_path),
                "--read-only={}".format(os.path.dirname(submission_wrapper_path)),
            ]

            if submission.assignment.grader_has_network_access:
                addrs = psutil.net_if_addrs()
                interfaces = list(addrs.keys())

                if "lo" in interfaces:
                    interfaces.remove("lo")

                def score_interface(name):
                    if name.startswith(("lxc", "lxd")):
                        return -2
                    elif name.startswith("tap"):
                        return -1
                    elif name.startswith(("wlp", "wlo", "eth", "eno", "enp")):
                        # Prefer Ethernet interfaces, but also prefer interfaces with IP addresses
                        # with netmasks set
                        return (
                            1
                            + name.startswith("e")
                            + sum(addr.netmask is not None for addr in addrs[name])
                        )
                    else:
                        return 0

                if interfaces:
                    firejail_args.append("--net={}".format(max(interfaces, key=score_interface)))
                    firejail_args.append("--netfilter")
                else:
                    firejail_args.append("--net=none")
            else:
                firejail_args.append("--net=none")

            args = [*firejail_args, *args]

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

            timed_out = False

            while proc.poll() is None:
                submission.refresh_from_db()
                submission.assignment.refresh_from_db()
                if submission.assignment.enable_grader_timeout:
                    time_elapsed = time.time() - start_time
                    timeout = submission.assignment.grader_timeout - time_elapsed
                    if timeout <= 0:
                        timed_out = True
                        break

                    timeout = min(timeout, 15)
                else:
                    timeout = 15

                if submission.kill_requested:
                    break

                files_ready = select.select([proc.stdout, proc.stderr], [], [], timeout)[0]
                if proc.stdout in files_ready:
                    output += proc.stdout.readline()
                if proc.stderr in files_ready:
                    errors += proc.stderr.readline()

                submission.grader_output = truncate_output(output.replace("\0", ""), "grader_output")
                submission.grader_errors = truncate_output(errors.replace("\0", ""), "grader_errors")
                submission.save(update_fields=["grader_output", "grader_errors"])

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
                msg = "[Grader timed out]" if timed_out else "[Grader killed]"

                if output and not output.endswith("\n"):
                    output += "\n"
                output += msg

                if errors and not errors.endswith("\n"):
                    errors += "\n"
                errors += msg
            else:
                retcode = proc.poll()
                if retcode != 0:
                    if output and not output.endswith("\n"):
                        output += "\n"
                    output += "[Grader error]"

                    if errors and not errors.endswith("\n"):
                        errors += "\n"
                    errors += "[Grader exited with status {}]".format(retcode)

            submission.grader_output = truncate_output(output.replace("\0", ""), "grader_output")
            submission.grader_errors = truncate_output(errors.replace("\0", ""), "grader_errors")
            submission.save()
    except Exception:  # pylint: disable=broad-except
        submission.grader_output = "[Internal error]"
        submission.grader_errors = truncate_output(traceback.format_exc().replace("\0", ""), "grader_errors")
        submission.save()
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
